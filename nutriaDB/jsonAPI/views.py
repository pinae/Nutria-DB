from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import re
import jwt
from backend.models import Product, Recipe, Category, Ingredient, Serving
from backend.helpers import split_name
from jsonAPI.helpers import convert_digits_to_bytes
from nutriaDB.settings import JWT_SECRET


def index(request):
    return HttpResponse("Hello, world. You're at the API index.")


def query_food(request):
    query_count = 15
    if request.method == 'GET' and 'ean' in request.GET:
        return query_ean(request)
    elif request.method == 'GET' and 'name' in request.GET:
        query_string = request.GET['name']
        if 'count' in request.GET:
            try:
                query_count = int(request.GET['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
        if 'chunk' in request.GET:
            try:
                product_chunk_start = int(request.GET['chunk'].split(':')[0])
                recipe_chunk_start = int(request.GET['chunk'].split(':')[1])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given chunk start does not consist of two integers. ' +
                                              'Example: \"-1:20\""}', content_type="application/json")
            except IndexError:
                return HttpResponseBadRequest('{"error": "The chunk start must consist of two integers separated by ' +
                                              '\":\".', content_type="application/json")
        else:
            product_chunk_start = 0
            recipe_chunk_start = 0
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                          content_type="application/json")
        if 'ean' in data:
            return query_ean(request)
        elif 'name' in data:
            query_string = data['name']
        else:
            return HttpResponseBadRequest('{"error": "Your POST request needs to contain either a name of the food ' +
                                          '(may be a part of it) or a ean. The params must be part of the JSON of ' +
                                          'the message body."}', content_type="application/json")
        if 'count' in data:
            try:
                query_count = int(data['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}',
                                              content_type="application/json")
        if 'chunk' in data:
            try:
                product_chunk_start = int(request.POST['chunk'].split(':')[0])
                recipe_chunk_start = int(request.POST['chunk'].split(':')[1])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given chunk start does not consist of two integers. ' +
                                              'Example: \"-1:20\""}', content_type="application/json")
            except IndexError:
                return HttpResponseBadRequest('{"error": "The chunk start must consist of two integers separated by ' +
                                              '\":\".', content_type="application/json")
        else:
            product_chunk_start = 0
            recipe_chunk_start = 0
    else:
        return HttpResponseBadRequest('{"error": "The request needs to contain either a name of the food ' +
                                      '(may be a part of it) or a ean. You can use GET or POST."}',
                                      content_type="application/json")
    new_product_chunk_start = -1
    products = []
    if product_chunk_start >= 0:
        products_query = Product.objects.filter(Q(name_addition__icontains=query_string) |
                                                Q(category__name__icontains=query_string)).\
            prefetch_related('category').order_by('category__name', 'name_addition')
        if products_query.count() > query_count:
            new_product_chunk_start = product_chunk_start + query_count
        products = products_query[product_chunk_start:query_count]
    new_recipe_chunk_start = -1
    recipes = []
    if recipe_chunk_start >= 0:
        recipes_query = Recipe.objects.filter(Q(name_addition__icontains=query_string) |
                                              Q(category__name__icontains=query_string)).\
            prefetch_related('category').order_by('category__name', 'name_addition')
        if recipes_query.count() > query_count:
            new_recipe_chunk_start = recipe_chunk_start + query_count
        recipes = recipes_query[recipe_chunk_start:query_count]
    for recipe in recipes:
        recipe.reference_amount = 100.
    response_dict = {
        'food': [('0{0:d}:{1:d}'.format(p.pk, p.category.pk),
                  p.category.name,
                  p.name_addition,
                  p.manufacturer.name if p.manufacturer is not None else
                  ("" if p.author is None else
                   (p.author.first_name + p.author.last_name if
                    (p.author.first_name is not None and p.author.last_name is not None) else
                    (p.author.username if (p.author.first_name is None and p.author.last_name is None) else
                     p.author.last_name if p.author.first_name is None else p.author.first_name))),
                  '{0:.2f}'.format(p.reference_amount),
                  '{0:.1f}'.format(p.calories),
                  '-1' if p.ean is None else "".join([str(x - b"0"[0]) for x in list(p.ean)]))
                 for p in products] +
                [('1{0:d}:{1:d}'.format(r.pk, r.category.pk),
                  r.category.name,
                  r.name_addition,
                  "" if r.author is None else
                  (r.author.first_name + r.author.last_name if
                   (r.author.first_name is not None and r.author.last_name is not None) else
                   (r.author.username if (r.author.first_name is None and r.author.last_name is None) else
                    r.author.last_name if r.author.first_name is None else r.author.first_name)),
                  '{0:.2f}'.format(r.reference_amount),
                  '{0:.1f}'.format(r.calories),
                  '-1')
                 for r in recipes],
        'chunk': "{0:d}:{1:d}".format(new_product_chunk_start, new_recipe_chunk_start)
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
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                          content_type="application/json")
        query_ean = data['ean']
        if not re.search("^\d+$", query_ean):
            return HttpResponseBadRequest('{"error": "The ean must contain only digits."}',
                                          content_type="application/json")
        if 'count' in data:
            try:
                query_count = int(data['count'])
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


def details_nopath(request):
    if request.method == "GET" and 'id' in request.GET:
        if 'amount' in request.GET:
            amount = request.GET['amount']
        else:
            amount = None
        return details(request, id_str=request.GET['id'], amount=amount)
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                          content_type="application/json")
        if 'id' not in data:
            return HttpResponseBadRequest('{"error": "You have to pass an id as a JSON param to get details."}',
                                          content_type="application/json")
        if 'amount' in data:
            amount = data['amount']
        else:
            amount = None
        return details(request, id_str=data['id'], amount=amount)
    else:
        return HttpResponseBadRequest('{"error": "You have to pass an id to get details."}',
                                      content_type="application/json")


def details(request, id_str, amount=None):
    if id_str[0] == '0':
        try:
            food = Product.objects.filter(pk=int(id_str[1:])).prefetch_related('servings')[0]
        except Product.DoesNotExist:
            return HttpResponseBadRequest('{"error": "There is no product with the id ' + id_str + '."}',
                                          content_type="application/json")
    elif id_str[0] == '1':
        try:
            food = Recipe.objects.filter(pk=int(id_str[1:])).prefetch_related('servings')[0]
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
    if food.author:
        author_name = food.author.first_name + ' ' + food.author.first_name
    else:
        author_name = None
    response_dict = {
        'type': 1 if type(food) is Recipe else 0,
        'foodId': food.pk,
        'categoryId': food.category.pk,
        'name': str(food),
        'author': author_name,
        'creation_date': str(food.creation_date),
        'reference_amount': food.reference_amount,
        'servings': [{'name': s.name, 'size': s.size} for s in food.servings.all()]
    }
    for element in ['calories', 'total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar',
                    'dietary_fiber', 'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium', 'manganese',
                    'zinc', 'phosphorous', 'sulphur', 'chloro', 'fluoric',
                    'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c', 'vitamin_d', 'vitamin_e']:
        response_dict[element] = scaler_ingredient.__getattribute__(element)
    if type(food) is Product:
        if food.manufacturer is not None:
            response_dict['manufacturer'] = str(food.manufacturer)
        if food.ean is not None:
            response_dict['ean'] = "".join([str(x - b"0"[0]) for x in list(food.ean)])
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
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                      content_type="application/json")
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
    category, name_addition = split_name(food_dict['name'])
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
        if 'servings' in food_dict and len(food_dict['servings']) >= 1:
            for serving in food_dict['servings']:
                if 'name' in serving and type(serving['name']) is str and 'size' in serving:
                    try:
                        new_serving = Serving(name=serving['name'], size=float(serving['size']))
                        new_serving.food = food
                        new_serving.save()
                    except ValueError:
                        return HttpResponseBadRequest('{"error": "The recipe was saved but the serving ' +
                                                      serving['name'] + ' could not be saved. ' +
                                                      'This was because its size was not a number. ' +
                                                      'All serving sizes must be a floats (in g)."}',
                                                      content_type="application/json")
                else:
                    return HttpResponseBadRequest('{"error": "The recipe was saved but at least ' +
                                                  'one serving could not be saved. ' +
                                                  'Servings need a name (string) and a size in g."}',
                                                  content_type="application/json")
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
        if 'servings' in food_dict and len(food_dict['servings']) >= 1:
            for serving in food_dict['servings']:
                if 'name' in serving and type(serving['name']) is str and 'size' in serving:
                    try:
                        new_serving = Serving(name=serving['name'], size=float(serving['size']), product=food)
                        new_serving.save()
                    except ValueError:
                        return HttpResponseBadRequest('{"error": "The product was saved but the serving ' +
                                                      serving['name'] + ' could not be saved. ' +
                                                      'This was because its size was not a number. ' +
                                                      'All serving sizes must be a floats (in g)."}',
                                                      content_type="application/json")
                else:
                    return HttpResponseBadRequest('{"error": "The product was saved but at least ' +
                                                  'one serving could not be saved. ' +
                                                  'Servings need a name (string) and a size in g."}',
                                                  content_type="application/json")
        return HttpResponse('{"success": "Product successfully added."}', content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "You supplied data for a product but it misses a reference ' +
                                      'amount or calorie count. Please make sure the \'calories\' and ' +
                                      '\'reference_amount\' fields are present. If you wanted to save a ' +
                                      'recipe you have to supply a list of ingredients."}',
                                      content_type="application/json")


def delete_food(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to delete food via POST."}',
                                      content_type="application/json")
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                      content_type="application/json")
    if 'token' not in data or 'id' not in data:
        return HttpResponseBadRequest('{"error": "Please supply a \'token\' and the \'id\' of the food ' +
                                      'you want to delete."}', content_type="application/json")
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
    if data['id'][0] == '0':
        try:
            food = Product.objects.get(pk=int(data['id'][1:]))
        except Product.DoesNotExist:
            return HttpResponseBadRequest('{"error": "There is no product with the id ' + data['id'] + '."}',
                                          content_type="application/json")
    elif data['id'][1] == '1':
        try:
            food = Recipe.objects.get(pk=int(data['id'][1:]))
        except Recipe.DoesNotExist:
            return HttpResponseBadRequest('{"error": "There is no recipe with the id ' + data['id'] + '."}',
                                          content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "The id begins with ' + data['id'][0] +
                                      ' which is an unknown type."}', content_type="application/json")
    if food.author == user:
        food.delete()
        return HttpResponse('{"success": "The food with id ' + data['id'] + ' was successfully deleted."}',
                            content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "You can only delete food you added yourself."}',
                                      content_type="application/json")


def log_in(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to log in via POST."}',
                                      content_type="application/json")
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                      content_type="application/json")
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
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                      content_type="application/json")
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
