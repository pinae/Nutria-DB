import json
import re
from datetime import datetime, timedelta, timezone

import jwt
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from backend.helpers import split_name
from backend.models import Category, Ingredient, Product, Recipe, Serving
from jsonAPI.helpers import NoDigitError, convert_digits_to_bytes
from nutriaDB.settings import JWT_SECRET

TOKEN_LIFETIME = timedelta(minutes=30)

#: Nutrient JSON keys accepted when saving and returned in details.
NUTRIENT_KEYS = ['total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar',
                 'dietary_fiber', 'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium', 'manganese',
                 'zinc', 'phosphorous', 'sulphur', 'chloro', 'fluoric',
                 'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c', 'vitamin_d', 'vitamin_e']

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")
PASSWORD_RE = re.compile(r"^[a-zA-Z0-9_\-\\\$\/\^\[\]\(\)\{\}\#\.\:\,\;\@\~\`\+\%\!\<\>\=\&\"\'\§\°]+$")
HUMAN_NAME_RE = re.compile(r"^[a-zA-Z0-9ÄÖÜäöüß\-]+$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9ÄÖÜäöüß\-\.]+\@[a-zA-Z0-9ÄÖÜäöüß\-\.]+\.[a-zA-Z]+$")


def json_error(message, **extra):
    """A JSON formatted bad request response."""
    return HttpResponseBadRequest(json.dumps({"error": message, **extra}, ensure_ascii=False),
                                  content_type="application/json")


def json_response(payload):
    return HttpResponse(json.dumps(payload, ensure_ascii=False), content_type="application/json")


def parse_json_body(request):
    """Return (data, None) for a valid JSON body or (None, error_response)."""
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, json_error("The body of your POST request is not valid JSON.")


def issue_token(user):
    payload = {'id': user.pk, 'email': user.email,
               'exp': datetime.now(timezone.utc) + TOKEN_LIFETIME}
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def authenticate_token(data):
    """Validate the JWT in ``data['token']``.

    Returns (user, None) on success or (None, error_response) on failure.
    """
    try:
        token_payload = jwt.decode(data['token'], JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None, json_error("This authentication token is expired. "
                                "Please log in again and get a new token.")
    except jwt.InvalidTokenError:
        return None, json_error("Invalid authentication token.")
    try:
        return User.objects.get(pk=token_payload['id']), None
    except User.DoesNotExist:
        return None, json_error("Could not find the user for this token. Was it deleted?")


def food_id_string(food):
    """The API-wide id format: a type prefix ('0' product / '1' recipe) followed by the pk."""
    return ('1' if isinstance(food, Recipe) else '0') + str(food.pk)


def resolve_food_id(id_str):
    """Resolve an API food id to a model instance.

    Returns (food, None) or (None, error_response).
    """
    model_by_prefix = {'0': Product, '1': Recipe}
    if not id_str or id_str[0] not in model_by_prefix:
        prefix = id_str[0] if id_str else ''
        return None, json_error("The id begins with " + prefix + " which is an unknown type.")
    model = model_by_prefix[id_str[0]]
    try:
        return model.objects.get(pk=int(id_str[1:])), None
    except (model.DoesNotExist, ValueError):
        kind = 'product' if model is Product else 'recipe'
        return None, json_error("There is no " + kind + " with the id " + id_str + ".")


def author_display_name(user):
    """A human readable name for a food's author (may be None)."""
    if user is None:
        return None
    full_name = (user.first_name + ' ' + user.last_name).strip()
    return full_name if full_name else user.username


def ean_string(ean):
    """Render a stored EAN (bytes of digit values 0-9) as a decimal string."""
    return "".join(str(b) for b in bytes(ean))


def parse_chunk(chunk_str):
    """Parse a "products:recipes" chunk cursor.

    Returns ((product_start, recipe_start), None) or (None, error_response).
    """
    try:
        parts = chunk_str.split(':')
        return (int(parts[0]), int(parts[1])), None
    except ValueError:
        return None, json_error('The given chunk start does not consist of two integers. Example: "-1:20"')
    except IndexError:
        return None, json_error('The chunk start must consist of two integers separated by ":".')


def index(request):
    return HttpResponse("Hello, world. You're at the API index.")


@csrf_exempt
def query_food(request):
    query_count = 15
    product_chunk_start = 0
    recipe_chunk_start = 0
    if request.method == 'GET' and 'ean' in request.GET:
        return query_ean(request)
    elif request.method == 'GET' and 'name' in request.GET:
        query_string = request.GET['name']
        params = request.GET
    elif request.method == 'POST':
        params, error = parse_json_body(request)
        if error:
            return error
        if 'ean' in params:
            return query_ean(request)
        if 'name' not in params:
            return json_error("Your POST request needs to contain either a name of the food "
                              "(may be a part of it) or a ean. The params must be part of the JSON of "
                              "the message body.")
        query_string = params['name']
    else:
        return json_error("The request needs to contain either a name of the food "
                          "(may be a part of it) or a ean. You can use GET or POST.")
    if 'count' in params:
        try:
            query_count = int(params['count'])
        except ValueError:
            return json_error("The given count is not an integer.")
    if 'chunk' in params:
        chunk, error = parse_chunk(params['chunk'])
        if error:
            return error
        product_chunk_start, recipe_chunk_start = chunk

    def query_page(model, chunk_start):
        """One page of matching foods plus the cursor for the next page (-1 = no more)."""
        if chunk_start < 0:
            return [], -1
        queryset = model.objects.filter(
            Q(name_addition__icontains=query_string) |
            Q(category__name__icontains=query_string)
        ).select_related('category', 'author').order_by('category__name', 'name_addition')
        page = list(queryset[chunk_start:chunk_start + query_count])
        next_start = chunk_start + query_count
        return page, (next_start if queryset.count() > next_start else -1)

    products, new_product_chunk_start = query_page(Product, product_chunk_start)
    recipes, new_recipe_chunk_start = query_page(Recipe, recipe_chunk_start)
    response_dict = {
        'food': [(food_id_string(p),
                  str(p),
                  p.manufacturer.name if p.manufacturer is not None
                  else (author_display_name(p.author) or ""),
                  '{0:.2f}'.format(p.reference_amount),
                  '{0:.1f}'.format(p.calories),
                  '-1' if p.ean is None else ean_string(p.ean))
                 for p in products] +
                [(food_id_string(r),
                  str(r),
                  author_display_name(r.author) or "",
                  '{0:.2f}'.format(r.reference_amount),
                  '{0:.1f}'.format(r.calories),
                  '-1')
                 for r in recipes],
        'chunk': "{0:d}:{1:d}".format(new_product_chunk_start, new_recipe_chunk_start)
    }
    return json_response(response_dict)


@csrf_exempt
def query_ean(request):
    query_count = 15
    if request.method == 'GET' and 'ean' in request.GET:
        params = request.GET
    elif request.method == 'POST':
        params, error = parse_json_body(request)
        if error:
            return error
        if 'ean' not in params:
            return json_error("The request needs to contain a ean. You can use GET or POST.")
    else:
        return json_error("The request needs to contain a ean. You can use GET or POST.")
    ean = params['ean']
    if not re.fullmatch(r"\d+", ean):
        return json_error("The ean must contain only digits.")
    if 'count' in params:
        try:
            query_count = int(params['count'])
        except ValueError:
            return json_error("The given count is not an integer.")
    products = Product.objects.filter(ean__exact=convert_digits_to_bytes(ean)). \
        select_related('category').order_by('category__name', 'name_addition')[:query_count]
    return json_response({'food': [(food_id_string(p), str(p)) for p in products]})


@csrf_exempt
def details_nopath(request):
    if request.method == "GET" and 'id' in request.GET:
        return details(request, id_str=request.GET['id'], amount=request.GET.get('amount'))
    elif request.method == "POST":
        data, error = parse_json_body(request)
        if error:
            return error
        if 'id' not in data:
            return json_error("You have to pass an id as a JSON param to get details.")
        return details(request, id_str=data['id'], amount=data.get('amount'))
    else:
        return json_error("You have to pass an id to get details.")


def details(request, id_str, amount=None):
    food, error = resolve_food_id(id_str)
    if error:
        return error
    scaler_ingredient = Ingredient()
    if amount is None:
        scaler_ingredient.amount = food.reference_amount
    else:
        try:
            scaler_ingredient.amount = float(amount)
        except (TypeError, ValueError):
            return json_error("The given amount of " + str(amount) + " is not a number.")
    scaler_ingredient.food = food
    response_dict = {
        'type': 1 if type(food) is Recipe else 0,
        'foodId': food.pk,
        'categoryId': food.category.pk,
        'name': str(food),
        'author': author_display_name(food.author),
        'creation_date': str(food.creation_date),
        'reference_amount': food.reference_amount,
        'servings': [{'name': s.name, 'size': s.size} for s in food.servings.all()],
        'calories': scaler_ingredient.calories,
    }
    for element in NUTRIENT_KEYS:
        response_dict[element] = getattr(scaler_ingredient, element)
    if type(food) is Product:
        if food.manufacturer is not None:
            response_dict['manufacturer'] = str(food.manufacturer)
        if food.ean is not None:
            response_dict['ean'] = ean_string(food.ean)
    if type(food) is Recipe:
        response_dict['ingredients'] = []
        for ingredient in food.ingredients.all():
            ingredient_overview = {
                'id': food_id_string(ingredient.food),
                'name': str(ingredient.food)
            }
            for element in ['amount', 'calories', 'total_fat', 'protein', 'total_carbs', 'dietary_fiber']:
                value = getattr(ingredient, element)
                ingredient_overview[element] = (value / food.reference_amount * scaler_ingredient.amount
                                                if value is not None else None)
            response_dict['ingredients'].append(ingredient_overview)
    return json_response(response_dict)


def save_servings(food_dict, food, food_kind):
    """Persist the servings of a food. Returns an error response or None."""
    for serving in food_dict.get('servings', []):
        if 'name' in serving and type(serving['name']) is str and 'size' in serving:
            try:
                new_serving = Serving(name=serving['name'], size=float(serving['size']))
            except (TypeError, ValueError):
                return json_error("The " + food_kind + " was saved but the serving " +
                                  str(serving['name']) + " could not be saved. "
                                  "This was because its size was not a number. "
                                  "All serving sizes must be a floats (in g).")
            new_serving.food = food
            new_serving.save()
        else:
            return json_error("The " + food_kind + " was saved but at least "
                              "one serving could not be saved. "
                              "Servings need a name (string) and a size in g.")
    return None


@csrf_exempt
def save_food(request):
    if request.method != 'POST':
        return json_error("You have to save data via POST.")
    data, error = parse_json_body(request)
    if error:
        return error
    if 'token' not in data or 'food' not in data:
        return json_error("Please supply a 'token' and the 'food' to save.")
    user, error = authenticate_token(data)
    if error:
        return error
    food_dict = data['food']
    if 'name' not in food_dict:
        return json_error("Please supply at least a 'name' for each food item.")
    category, name_addition = split_name(food_dict['name'])
    try:
        cat = Category.objects.get(name=category)
    except Category.DoesNotExist:
        return json_error(str(category) + ' is not a valid category. All valid categories are listed in this error.',
                          categories=[c.name for c in Category.objects.all()])
    if 'ingredients' in food_dict and 'ean' not in food_dict:
        food = Recipe(category=cat, name_addition=name_addition, author=user)
        ingredient_list = []
        for ingredient in food_dict['ingredients']:
            ingredient_food, error = resolve_food_id(ingredient['food'])
            if error:
                return error
            try:
                amount = float(ingredient['amount'])
            except (TypeError, ValueError):
                return json_error("The amount you gave for the " + type(ingredient_food).__name__ + " " +
                                  str(ingredient_food) + "(id: " + ingredient['food'] + ") is not a number.")
            ingredient_list.append({'food': ingredient_food, 'amount': amount})
        food.save()
        for ingredient in ingredient_list:
            i = Ingredient(recipe=food, amount=ingredient['amount'])
            i.food = ingredient['food']
            i.save()
        error = save_servings(food_dict, food, "recipe")
        if error:
            return error
        return json_response({"success": "Recipe successfully added."})
    elif all(k in food_dict for k in ['calories', 'reference_amount']):
        try:
            food = Product(category=cat, name_addition=name_addition, author=user,
                           calories=float(food_dict['calories']),
                           reference_amount=float(food_dict['reference_amount']))
        except (TypeError, ValueError):
            return json_error("Either the calories or the reference amount are no float "
                              "values. Please supply floats.")
        if 'ean' in food_dict:
            try:
                food.ean = convert_digits_to_bytes(food_dict['ean'])
            except NoDigitError:
                return json_error("The ean must contain only digits.")
        for element in NUTRIENT_KEYS:
            if element in food_dict:
                try:
                    setattr(food, element, float(food_dict[element]))
                except (TypeError, ValueError):
                    return json_error("The amount of " + element + " must be a float.")
        food.save()
        error = save_servings(food_dict, food, "product")
        if error:
            return error
        return json_response({"success": "Product successfully added."})
    else:
        return json_error("You supplied data for a product but it misses a reference "
                          "amount or calorie count. Please make sure the 'calories' and "
                          "'reference_amount' fields are present. If you wanted to save a "
                          "recipe you have to supply a list of ingredients.")


@csrf_exempt
def delete_food(request):
    if request.method != 'POST':
        return json_error("You have to delete food via POST.")
    data, error = parse_json_body(request)
    if error:
        return error
    if 'token' not in data or 'id' not in data:
        return json_error("Please supply a 'token' and the 'id' of the food you want to delete.")
    user, error = authenticate_token(data)
    if error:
        return error
    food, error = resolve_food_id(data['id'])
    if error:
        return error
    if food.author == user:
        food.delete()
        return json_response({"success": "The food with id " + data['id'] + " was successfully deleted."})
    else:
        return json_error("You can only delete food you added yourself.")


@csrf_exempt
def log_in(request):
    if request.method != 'POST':
        return json_error("You have to log in via POST.")
    data, error = parse_json_body(request)
    if error:
        return error
    if 'username' not in data or 'password' not in data:
        return json_error("Please supply a 'username' and a 'password'.")
    try:
        user = User.objects.get(username=data['username'])
    except User.DoesNotExist:
        return json_error("Could not find a user with this username.")
    if not user.check_password(data['password']):
        return json_error("Wrong password.")
    return json_response({'token': issue_token(user)})


@csrf_exempt
def register(request):
    if request.method != 'POST':
        return json_error("You have to register in via POST.")
    data, error = parse_json_body(request)
    if error:
        return error
    if not all(k in data for k in ['username', 'password', 'first_name', 'last_name', 'email']):
        return json_error("Please supply a 'username', a 'password', "
                          "a 'first_name', a 'last_name' and a 'email'.")
    username = data['username']
    password = data['password']
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    if not USERNAME_RE.fullmatch(username):
        return json_error("The username must only contain big and small letters, "
                          "digits, underscores and hyphens (" + USERNAME_RE.pattern + ").")
    if not PASSWORD_RE.fullmatch(password):
        return json_error("The password must only contain big and small letters, "
                          "digits, underscores, hyphens and some other special characters (" +
                          PASSWORD_RE.pattern + ").")
    if not HUMAN_NAME_RE.fullmatch(first_name):
        return json_error("The first name must only contain big and small letters, "
                          "digits, umlauts and hyphens (" + HUMAN_NAME_RE.pattern + ").")
    if not HUMAN_NAME_RE.fullmatch(last_name):
        return json_error("The last name must only contain big and small letters, "
                          "digits, umlauts and hyphens (" + HUMAN_NAME_RE.pattern + ").")
    if not EMAIL_RE.fullmatch(email):
        return json_error("The email must only contain big and small letters, "
                          "digits, umlauts and hyphens (" + EMAIL_RE.pattern + ").")
    new_user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    new_user.set_password(password)
    try:
        new_user.save()
    except IntegrityError:
        return json_error("This username is already taken.")
    return json_response({'token': issue_token(new_user)})
