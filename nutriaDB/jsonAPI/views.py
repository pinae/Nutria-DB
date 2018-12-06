from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import re
import jwt
from backend.models import Product, Recipe, Category, Ingredient
from jsonAPI.helpers import convert_digits_to_bytes
from nutriaDB.settings import JWT_SECRET


def index(request):
    return HttpResponse("Hello, world. You're at the API index.")


def query_food(request):
    query_count = 15
    if (request.method == 'GET' and 'ean' in request.GET) or (request.method == 'POST' and 'ean' in request.POST):
        return query_ean(request)
    elif request.method == 'GET' and 'name' in request.GET:
        query_string = request.GET['name']
        if 'count' in request.GET:
            try:
                query_count = int(request.GET['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
    elif request.method == 'POST' and 'name' in request.POST:
        query_string = request.POST['name']
        if 'count' in request.POST:
            try:
                query_count = int(request.POST['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "The request needs to contain either a name of the food ' +
                                      '(may be a part of it) or a ean. You can use GET or POST."}',
                                      content_type="application/json")
    products = Product.objects.filter(Q(name_addition__icontains=query_string) |
                                      Q(category__name__icontains=query_string)).\
        prefetch_related('category').order_by('category__name', 'name_addition')[:query_count]
    recipes = Recipe.objects.filter(Q(name_addition__icontains=query_string) |
                                    Q(category__name__icontains=query_string)).\
        prefetch_related('category').order_by('category__name', 'name_addition')[:query_count]
    response_dict = {
        'food': [('0{0:d}'.format(p.pk), p.category.name + ': ' + p.name_addition) for p in products] +
                [('1{0:d}'.format(r.pk), r.category.name + ': ' + r.name_addition) for r in recipes]
    }
    return HttpResponse(json.dumps(response_dict), content_type="application/json")


def query_ean(request):
    query_count = 15
    if request.method == 'GET' and 'ean' in request.GET:
        query_ean = request.GET['ean']
        if not re.search("^\d+$", query_ean):
            return HttpResponseBadRequest('{"error": "The ean must contain only digits."}',
                                          content_type="application/json")
        if 'count' in request.GET:
            try:
                query_count = int(request.GET['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
    elif request.method == 'POST' and 'ean' in request.POST:
        query_ean = request.POST['ean']
        if not re.search("^\d+$", query_ean):
            return HttpResponseBadRequest('{"error": "The ean must contain only digits."}',
                                          content_type="application/json")
        if 'count' in request.POST:
            try:
                query_count = int(request.POST['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "The request needs to contain a ean. You can use GET or POST."}',
                                      content_type="application/json")
    products = Product.objects.filter(ean__exact=convert_digits_to_bytes(query_ean)).\
        prefetch_related('category').order_by('category__name', 'name_addition')[:query_count]
    response_dict = {
        'food': [('0{0:d}'.format(p.pk), p.category.name + ': ' + p.name_addition) for p in products]
    }
    return HttpResponse(json.dumps(response_dict), content_type="application/json")


def details(request, id_str, amount=None):
    if id_str[0] == '0':
        try:
            food = Product.objects.get(pk=int(id_str[1:]))
        except Product.DoesNotExist:
            return HttpResponseBadRequest('{"error": "There is no product with the id ' + id_str + '."}',
                                          content_type="application/json")
    elif id_str[1] == '1':
        try:
            food = Recipe.objects.get(pk=int(id_str[1:]))
        except Recipe.DoesNotExist:
            return HttpResponseBadRequest('{"error": "There is no recipe with the id ' + id_str + '."}',
                                          content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "The id begins with ' + id_str[0] +
                                      ' which is an unknown type."}', content_type="application/json")
    scaler_ingredient = Ingredient()
    if amount is None:
        scaler_ingredient.amount = food.reference_amount
    else:
        try:
            scaler_ingredient.amount = float(amount)
        except ValueError:
            return HttpResponseBadRequest('{"error": "The given amount of ' + amount +
                                          ' is not a number."}', content_type="application/json")
    scaler_ingredient.food = food
    author_name = food.author.first_name + ' ' + food.author.first_name
    response_dict = {
        'name': str(food),
        'author': author_name,
        'creation_date': str(food.creation_date),
        'manufacturer': str(food.manufacturer) if type(food) is Product else author_name,
        'reference_amount': food.reference_amount
    }
    for element in ['calories', 'total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar',
                    'dietary_fiber', 'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium', 'manganese',
                    'zinc', 'phosphorous', 'sulphur', 'chloro', 'fluoric',
                    'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c', 'vitamin_d', 'vitamin_e']:
        response_dict[element] = scaler_ingredient.__getattribute__(element)
    if type(food) is Recipe:
        response_dict['ingredients'] = []
        for ingredient in food.ingredients.all():
            if type(ingredient.food) is Product:
                ingredient_id = '0' + str(ingredient.food.pk)
            elif type(ingredient.food) is Recipe:
                ingredient_id = '1' + str(ingredient.food.pk)
            else:
                raise Exception("Inconsistent Database!")
            ingredient_overview = {
                'id': ingredient_id,
                'name': str(ingredient.food)
            }
            for element in ['amount', 'calories', 'total_fat', 'protein', 'total_carbs', 'dietary_fiber']:
                ingredient_overview[element] = (ingredient.__getattribute__(element)
                                                / food.reference_amount * scaler_ingredient.amount)
            response_dict['ingredients'].append(ingredient_overview)
    return HttpResponse(json.dumps(response_dict), content_type="application/json")


def save_food(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to save data via POST."}',
                                      content_type="application/json")
    data = json.loads(request.body)
    if 'token' not in data or 'food' not in data:
        return HttpResponseBadRequest('{"error": "Please supply a \'token\' and the \'food\' to save."}',
                                      content_type="application/json")
    try:
        token_payload = jwt.decode(data['token'], JWT_SECRET, 'HS256')
    except jwt.InvalidSignatureError:
        return HttpResponseBadRequest('{"error": "Invalid signature of the authentication token."}',
                                      content_type="application/json")
    except jwt.ExpiredSignatureError:
        return HttpResponseBadRequest('{"error": "This authentication token is expired. ' +
                                      'Please log in again and get a new token."}',
                                      content_type="application/json")
    except jwt.InvalidTokenError:
        return HttpResponseBadRequest('{"error": "Invalid authentication token."}',
                                      content_type="application/json")
    try:
        user = User.objects.get(pk=token_payload['id'])
    except User.DoesNotExist:
        return HttpResponseBadRequest('{"error": "Could not find the user for this token. Was it deleted?"}',
                                      content_type="application/json")
    if not user:
        return HttpResponseBadRequest('{"error": "Could not find the user with id=' +
                                      token_payload['id'] + '. Was it deleted?"}',
                                      content_type="application/json")
    food_dict = data['food']
    if 'name' not in food_dict:
        return HttpResponseBadRequest('{"error": "Please supply at least a \'name\' for each food item."}',
                                      content_type="application/json")
    mao = re.match("^\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*:\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*$",
                   food_dict['name'])
    category = mao.groups()[0]
    name_addition = mao.groups()[1]
    try:
        cat = Category.objects.get(name=category)
    except Category.DoesNotExist:
        return HttpResponseBadRequest(json.dumps(
            {"error": category + ' is not a valid category. All valid categories are listed in this error.',
             "categories": [c.name for c in Category.objects.all()]}), content_type="application/json")
    if 'ingredients' in food_dict and 'ean' not in food_dict:
        food = Recipe(category=cat, name_addition=name_addition, author=user)
        ingredient_list = []
        for ingredient in food_dict['ingredients']:
            if ingredient['food'][0] == '0':
                food_class = Product
            elif ingredient['food'][0] == '1':
                food_class = Recipe
            else:
                return HttpResponseBadRequest(json.dumps(
                        {"error": "The id begins with " + ingredient['food'][0] + " which is an unknown type."}),
                        content_type="application/json")
            try:
                ingredient_food = food_class.objects.get(pk=int(ingredient['food'][1:]))
            except food_class.DoesNotExist:
                return HttpResponseBadRequest(json.dumps(
                    {"error": "There is no " + str(food_class.__name__) + " with the id " + ingredient['food'] + "!"}),
                    content_type="application/json")
            try:
                amount = float(ingredient['amount'])
            except ValueError:
                return HttpResponseBadRequest(json.dumps(
                    {"error": "The amount you gave for the " + food_class.__name__ + " " + str(ingredient_food) +
                              "(id: " + ingredient['food'] + ") is not a number."}),
                    content_type="application/json")
            ingredient_list.append({'food': ingredient_food, 'amount': amount})
        food.save()
        for ingredient in ingredient_list:
            i = Ingredient(recipe=food, amount=ingredient['amount'])
            i.food = ingredient['food']
            i.save()
        return HttpResponse('{"success": "Recipe successfully added."}', content_type="application/json")
    elif all(k in food_dict for k in ['calories', 'reference_amount']):
        try:
            food = Product(category=cat, name_addition=name_addition, author=user,
                           calories=float(food_dict['calories']),
                           reference_amount=float(food_dict['reference_amount']))
        except ValueError:
            return HttpResponseBadRequest('{"error": "Either the calories or the reference amount are no float ' +
                                          'values. Please supply floats."}', content_type="application/json")
        if 'ean' in food_dict:
            food.ean = convert_digits_to_bytes(food_dict['ean'])
        for element in ['total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar',
                        'dietary_fiber', 'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium',
                        'manganese', 'zinc', 'phosphorous', 'sulphur', 'chloro', 'fluoric',
                        'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c', 'vitamin_d', 'vitamin_e']:
            if element in food_dict:
                try:
                    food.__setattr__(element, float(food_dict[element]))
                except ValueError:
                    return HttpResponseBadRequest('{"error": "The amount of ' + element + ' must be a float."}',
                                                  content_type="application/json")
        food.save()
        return HttpResponse('{"success": "Product successfully added."}', content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "You supplied data for a product but it misses a reference ' +
                                      'amount or calorie count. Please make sure the \'calories\' and ' +
                                      '\'reference_amount\' fields are present. If you wanted to save a ' +
                                      'recipe you have to supply a list of ingredients."}',
                                      content_type="application/json")


def log_in(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to log in via POST."}',
                                      content_type="application/json")
    data = json.loads(request.body)
    if 'username' not in data or 'password' not in data:
        return HttpResponseBadRequest('{"error": "Please supply a \'username\' and a \'password\'."}',
                                      content_type="application/json")
    try:
        user = User.objects.get(username=data['username'])
    except User.DoesNotExist:
        return HttpResponseBadRequest('{"error": "Could not find a user with this username."}',
                                      content_type="application/json")
    if not user:
        return HttpResponseBadRequest('{"error": "Invalid user."}',
                                      content_type="application/json")
    if not user.check_password(data['password']):
        return HttpResponseBadRequest('{"error": "Wrong password."}',
                                      content_type="application/json")
    payload = {'id': user.pk, 'email': user.email, 'exp': datetime.utcnow() + timedelta(minutes=30)}
    jwt_token = {'token': str(jwt.encode(payload, JWT_SECRET, 'HS256'), encoding='utf-8')}
    return HttpResponse(json.dumps(jwt_token),
                        content_type="application/json")


def register(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to register in via POST."}',
                                      content_type="application/json")
    data = json.loads(request.body)
    if not all(k in data for k in ['username', 'password', 'first_name', 'last_name', 'email']):
        return HttpResponseBadRequest('{"error": "Please supply a \'username\', a \'password\', ' +
                                      'a \'first_name\', a \'last_name\' and a \'email\'."}',
                                      content_type="application/json")
    username = data['username']
    password = data['password']
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    if not re.search("^[a-zA-Z0-9_\-]+$", username):
        HttpResponseBadRequest('{"error": "The username must only contain big and small letters, ' +
                               'digits, underscores and hyphens (^[a-zA-Z0-9_\-]+$)."}',
                               content_type="application/json")
    if not re.search("^[a-zA-Z0-9_\-\\\$\/\^\[\]\(\)\{\}\#\.\:\,\;\@\~\`\+\%\!\<\>\=\&\"\'\§\°]+$", password):
        HttpResponseBadRequest('{"error": "The password must only contain big and small letters, ' +
                               'digits, underscores, hyphens and some other special characters ' +
                               '(^[a-zA-Z0-9_\-\\\$\/\^\[\]\(\)\{\}\#\.\:\,\;\@\~\`\+\%\!\<\>\=\&\"\'\§\°]+$)."}',
                               content_type="application/json")
    if not re.search("^[a-zA-Z0-9ÄÖÜäöüß\-]+$", first_name):
        HttpResponseBadRequest('{"error": "The first name must only contain big and small letters, ' +
                               'digits, umlauts and hyphens (^[a-zA-Z0-9ÄÖÜäöüß\-]+$)."}',
                               content_type="application/json")
    if not re.search("^[a-zA-Z0-9ÄÖÜäöüß\-]+$", last_name):
        HttpResponseBadRequest('{"error": "The last name must only contain big and small letters, ' +
                               'digits, umlauts and hyphens (^[a-zA-Z0-9ÄÖÜäöüß\-]+$)."}',
                               content_type="application/json")
    if not re.search("^[a-zA-Z0-9ÄÖÜäöüß\-\.]+\@[a-zA-Z0-9ÄÖÜäöüß\-\.]+\.[a-zA-Z]+$", email):
        HttpResponseBadRequest('{"error": "The email must only contain big and small letters, ' +
                               'digits, umlauts and hyphens ' +
                               '(^[a-zA-Z0-9ÄÖÜäöüß\-\.]+\@[a-zA-Z0-9ÄÖÜäöüß\-\.]+\.[a-zA-Z]+$)."}',
                               content_type="application/json")
    new_user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    new_user.set_password(password)
    new_user.save()
    payload = {'id': new_user.pk, 'email': new_user.email, 'exp': datetime.utcnow() + timedelta(minutes=30)}
    jwt_token = {'token': str(jwt.encode(payload, JWT_SECRET, 'HS256'), encoding='utf-8')}
    return HttpResponse(json.dumps(jwt_token),
                        content_type="application/json")
