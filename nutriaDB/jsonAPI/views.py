from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import re
import jwt
from backend.models import Product, Recipe, Category
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
        'food': [('0' + str(p.pk), p.category.name + ': ' + p.name_addition) for p in products] +
                [('1' + str(r.pk), r.category.name + ': ' + r.name_addition) for r in recipes]
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
        'food': [('0' + str(p.pk), p.category.name + ': ' + p.name_addition) for p in products]
    }
    return HttpResponse(json.dumps(response_dict), content_type="application/json")


def save_food(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('{"error": "You have to save data via POST."}',
                                      content_type="application/json")
    if 'token' not in request.POST or 'food' not in request.POST:
        return HttpResponseBadRequest('{"error": "Please supply a \'token\' and the \'food\' to save."}',
                                      content_type="application/json")
    try:
        token_payload = jwt.decode(request.POST['token'], JWT_SECRET, 'HS256')
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
    food_dict = request.POST['food']
    if not all(k in food_dict for k in ['name', 'reference_amount', 'calories']):
        return HttpResponseBadRequest('{"error": "Please supply at least a \'name\', \'reference_amount\' ' +
                                      'and \'calories\' for each food item."}',
                                      content_type="application/json")
    mao = re.match("^\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*:\s*([\w \-\(\[\{\}\]\)\#\%\!\.\,\;\*]+)\s*$",
                   request.POST['name'])
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
        # TODO: Parse List of Ingredients
        food.save()
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
        if 'total_fat' in food_dict:
            try:
                food.total_fat = float(food_dict['total_fat'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of total_fat must be a float."}',
                                              content_type="application/json")
        if 'saturated_fat' in food_dict:
            try:
                food.saturated_fat = float(food_dict['saturated_fat'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of saturated_fat must be a float."}',
                                              content_type="application/json")
        if 'cholesterol' in food_dict:
            try:
                food.cholesterol = float(food_dict['cholesterol'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of cholesterol must be a float."}',
                                              content_type="application/json")
        if 'protein' in food_dict:
            try:
                food.protein = float(food_dict['protein'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of protein must be a float."}',
                                              content_type="application/json")
        if 'total_carbs' in food_dict:
            try:
                food.total_carbs = float(food_dict['total_carbs'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of total_carbs must be a float."}',
                                              content_type="application/json")
        if 'sugar' in food_dict:
            try:
                food.sugar = float(food_dict['sugar'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of sugar must be a float."}',
                                              content_type="application/json")
        if 'dietary_fiber' in food_dict:
            try:
                food.dietary_fiber = float(food_dict['dietary_fiber'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of dietary_fiber must be a float."}',
                                              content_type="application/json")
        if 'salt' in food_dict:
            try:
                food.salt = float(food_dict['salt'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of salt must be a float."}',
                                              content_type="application/json")
        if 'sodium' in food_dict:
            try:
                food.sodium = float(food_dict['sodium'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of sodium must be a float."}',
                                              content_type="application/json")
        if 'potassium' in food_dict:
            try:
                food.potassium = float(food_dict['potassium'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of potassium must be a float."}',
                                              content_type="application/json")
        if 'copper' in food_dict:
            try:
                food.copper = float(food_dict['copper'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of copper must be a float."}',
                                              content_type="application/json")
        if 'iron' in food_dict:
            try:
                food.iron = float(food_dict['iron'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of iron must be a float."}',
                                              content_type="application/json")
        if 'magnesium' in food_dict:
            try:
                food.magnesium = float(food_dict['magnesium'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of magnesium must be a float."}',
                                              content_type="application/json")
        if 'manganese' in food_dict:
            try:
                food.manganese = float(food_dict['manganese'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of manganese must be a float."}',
                                              content_type="application/json")
        if 'zinc' in food_dict:
            try:
                food.zinc = float(food_dict['zinc'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of zinc must be a float."}',
                                              content_type="application/json")
        if 'phosphorous' in food_dict:
            try:
                food.phosphorous = float(food_dict['phosphorous'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of phosphorous must be a float."}',
                                              content_type="application/json")
        if 'sulphur' in food_dict:
            try:
                food.sulphur = float(food_dict['sulphur'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of sulphur must be a float."}',
                                              content_type="application/json")
        if 'chloro' in food_dict:
            try:
                food.chloro = float(food_dict['chloro'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of chloro must be a float."}',
                                              content_type="application/json")
        if 'fluoric' in food_dict:
            try:
                food.fluoric = float(food_dict['fluoric'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of fluoric must be a float."}',
                                              content_type="application/json")
        if 'vitamin_b1' in food_dict:
            try:
                food.vitamin_b1 = float(food_dict['vitamin_b1'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_b1 must be a float."}',
                                              content_type="application/json")
        if 'vitamin_b12' in food_dict:
            try:
                food.vitamin_b12 = float(food_dict['vitamin_b12'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_b12 must be a float."}',
                                              content_type="application/json")
        if 'vitamin_b6' in food_dict:
            try:
                food.vitamin_b6 = float(food_dict['vitamin_b6'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_b6 must be a float."}',
                                              content_type="application/json")
        if 'vitamin_c' in food_dict:
            try:
                food.vitamin_c = float(food_dict['vitamin_c'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_c must be a float."}',
                                              content_type="application/json")
        if 'vitamin_d' in food_dict:
            try:
                food.vitamin_d = float(food_dict['vitamin_d'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_d must be a float."}',
                                              content_type="application/json")
        if 'vitamin_e' in food_dict:
            try:
                food.vitamin_e = float(food_dict['vitamin_e'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The amount of vitamin_e must be a float."}',
                                              content_type="application/json")
        food.save()
        return HttpResponse('{"success": "Product successfully added."}', content_type="application/json")
    else:
        return HttpResponseBadRequest('{"error": "You supplied data for a product but it misses a reference ' +
                                      'amount or calorie count. Please make sure the \'calories\' and ' +
                                      '\'reference_amount\' fields are present."}', content_type="application/json")


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
