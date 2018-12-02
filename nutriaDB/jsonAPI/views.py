from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
import json, re
from backend.models import Product, Recipe
from jsonAPI.helpers import convert_digits_to_bytes


def index(request):
    return HttpResponse("Hello, world. You're at the API index.")


def query_food(request):
    query_count = 15
    if (request.method == 'GET' and 'ean' in request.GET) or (request.method == 'POST' and 'ean' in request.POST):
        return query_ean(request)
    elif request.method == 'GET' and 'name' in request.GET:
        query_string = request.GET['name']
        if 'query_count' in request.GET:
            try:
                query_count = int(request.GET['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}')
    elif request.method == 'POST' and 'name' in request.POST:
        query_string = request.POST['name']
        if 'query_count' in request.POST:
            try:
                query_count = int(request.POST['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}')
    else:
        return HttpResponseBadRequest('{"error": "The request needs to contain either a name of the food ' +
                                      '(may be a part of it) or a ean. You can use GET or POST."}')
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
    return HttpResponse(json.dumps(response_dict))


def query_ean(request):
    query_count = 15
    if request.method == 'GET' and 'ean' in request.GET:
        query_ean = request.GET['ean']
        if not re.search("^\d+$", query_ean):
            return HttpResponseBadRequest('{"error": "The ean must contain only digits."}')
        if 'query_count' in request.GET:
            try:
                query_count = int(request.GET['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}')
    elif request.method == 'POST' and 'ean' in request.POST:
        query_ean = request.POST['ean']
        if not re.search("^\d+$", query_ean):
            return HttpResponseBadRequest('{"error": "The ean must contain only digits."}')
        if 'query_count' in request.POST:
            try:
                query_count = int(request.POST['count'])
            except ValueError:
                return HttpResponseBadRequest('{"error": "The given count is not an integer."}')
    else:
        return HttpResponseBadRequest('{"error": "The request needs to contain a ean. You can use GET or POST."}')
    products = Product.objects.filter(ean__exact=convert_digits_to_bytes(query_ean)).\
        prefetch_related('category').order_by('category__name', 'name_addition')[:query_count]
    response_dict = {
        'food': [('0' + str(p.pk), p.category.name + ': ' + p.name_addition) for p in products]
    }
    return HttpResponse(json.dumps(response_dict))
