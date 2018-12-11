from django.http import HttpResponse, HttpResponseBadRequest
import requests
import json
import urllib


def scale_by_unit(value, current_unit, target_unit):
    if current_unit == target_unit:
        return value
    if current_unit == 'g' and target_unit == 'mg':
        return value / 1000
    if current_unit == 'mg' and target_unit == 'g':
        return value * 1000
    if current_unit == 'ug' and target_unit == 'mg':
        return value * 1000
    if current_unit == 'ug' and target_unit == 'g':
        return value * 1000000
    if current_unit.lower() == 'kj' and target_unit.lower() == 'kcal':
        return value / 4.184
    if current_unit.lower() == 'kcal' and target_unit.lower() == 'kj':
        return value * 4.184


def add_nutriment(product_data, openfoodfacts_data, openfoodfacts_name, our_name, our_unit):
    openfoodfacts_unit = openfoodfacts_data['nutriments'][openfoodfacts_name + '_unit'].strip() if \
        openfoodfacts_name + '_unit' in openfoodfacts_data['nutriments'] and \
        len(openfoodfacts_data['nutriments'][openfoodfacts_name + '_unit'].strip()) > 0 else 'g'
    if (openfoodfacts_name + '_unit' not in openfoodfacts_data['nutriments'] or
            len(openfoodfacts_data['nutriments'][openfoodfacts_name + '_unit'].strip()) <= 0) and our_unit == 'kcal':
        openfoodfacts_unit = 'kJ'
    if openfoodfacts_name + '_prepared_100g' in openfoodfacts_data['nutriments']:
        try:
            product_data[our_name] = scale_by_unit(
                float(openfoodfacts_data['nutriments'][openfoodfacts_name + '_prepared_100g']),
                openfoodfacts_unit, our_unit)
        except ValueError:
            pass
    if openfoodfacts_name + '_100g' in openfoodfacts_data['nutriments']:
        try:
            product_data[our_name] = scale_by_unit(
                float(openfoodfacts_data['nutriments'][openfoodfacts_name + '_100g']),
                openfoodfacts_unit, our_unit)
        except ValueError:
            pass
    return product_data


def ask_openfoodfacts_org(request, ean):
    r = requests.get("https://food.openfoodfacts.org/api/v0/product/" + ean)
    data = r.json()
    product_data = {}
    name = ""
    if 'brands' in data['product']:
        product_data['manufacturer'] = data['product']['brands'].split(",", 1)[0]
        name += product_data['manufacturer']
    if 'product_name_de' in data['product'] and len(data['product']['product_name_de']) > 0:
        name += " - " + data['product']['product_name_de']
    elif 'generic_name_de' in data['product'] and len(data['product']['generic_name_de']) > 0:
        name += " - " + data['product']['generic_name_de']
    elif 'product_name_en' in data['product'] and len(data['product']['product_name_en']) > 0:
        name += " - " + data['product']['product_name_en']
    elif 'generic_name_en' in data['product'] and len(data['product']['generic_name_en']) > 0:
        name += " - " + data['product']['generic_name_en']
    elif 'product_name_fr' in data['product'] and len(data['product']['product_name_fr']) > 0:
        name += " - " + data['product']['product_name_fr']
    elif 'generic_name_fr' in data['product'] and len(data['product']['generic_name_fr']) > 0:
        name += " - " + data['product']['generic_name_fr']
    product_data['name_addition'] = name
    product_data['reference_amount'] = 100
    if 'nutriments' in data['product']:
        product_data = add_nutriment(product_data, data['product'], 'energy', 'calories', 'kcal')
        product_data = add_nutriment(product_data, data['product'], 'carbohydrates', 'total_carbs', 'g')
        product_data = add_nutriment(product_data, data['product'], 'sugars', 'sugar', 'g')
        product_data = add_nutriment(product_data, data['product'], 'fat', 'fat', 'g')
        product_data = add_nutriment(product_data, data['product'], 'saturated-fat', 'saturated_fat', 'g')
        product_data = add_nutriment(product_data, data['product'], 'proteins', 'protein', 'g')
        product_data = add_nutriment(product_data, data['product'], 'fiber', 'dietary_fiber', 'g')
        product_data = add_nutriment(product_data, data['product'], 'salt', 'salt', 'g')
        product_data = add_nutriment(product_data, data['product'], 'sodium', 'sodium', 'mg')
    return HttpResponse(json.dumps(product_data), content_type="application/json")


def search_openfoodfacts_org_nopath(request):
    if request.method == "GET" and 'name' in request.GET:
        return search_openfoodfacts_org(request, query_str=request.GET['name'])
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest('{"error": "The body of your POST request is not valid JSON."}',
                                          content_type="application/json")
        if 'name' not in data:
            return HttpResponseBadRequest('{"error": "You have to pass a name as a JSON param to get details."}',
                                          content_type="application/json")
        return search_openfoodfacts_org(request, query_str=data['name'])
    else:
        return HttpResponseBadRequest('{"error": "You have to pass a name to get details."}',
                                      content_type="application/json")


def search_openfoodfacts_org(request, query_str):
    params = urllib.parse.urlencode({
        'search_terms': query_str,
        'page': '1',
        'page_size': '100',
        'sort_by': 'unique_scans',
        'search_simple': '1',
        'json': '1'
    })
    r = requests.get("https://world.openfoodfacts.org/cgi/search.pl?" + params)
    data = r.json()
    result_list = []
    if 'products' in data:
        for product in data['products']:
            result = {}
            if 'id' in product:
                result['ean'] = product['id']
            name = ""
            if 'brands' in product:
                result['manufacturer'] = product['brands'].split(',')[0]
                name += result['manufacturer']
            if 'product_name_de' in product and len(product['product_name_de']) > 0:
                name += " - " + product['product_name_de']
            elif 'generic_name_de' in product and len(product['generic_name_de']) > 0:
                name += " - " + product['generic_name_de']
            elif 'product_name_en' in product and len(product['product_name_en']) > 0:
                name += " - " + product['product_name_en']
            elif 'generic_name_en' in product and len(product['generic_name_en']) > 0:
                name += " - " + product['generic_name_en']
            elif 'product_name_fr' in product and len(product['product_name_fr']) > 0:
                name += " - " + product['product_name_fr']
            elif 'generic_name_fr' in product and len(product['generic_name_fr']) > 0:
                name += " - " + product['generic_name_fr']
            result['name'] = name
            if 'nutriments' in product:
                result = add_nutriment(result, product, 'energy', 'calories', 'kcal')
                result = add_nutriment(result, product, 'carbohydrates', 'total_carbs', 'g')
                result = add_nutriment(result, product, 'sugars', 'sugar', 'g')
                result = add_nutriment(result, product, 'fat', 'fat', 'g')
                result = add_nutriment(result, product, 'saturated-fat', 'saturated_fat', 'g')
                result = add_nutriment(result, product, 'proteins', 'protein', 'g')
                result = add_nutriment(result, product, 'fiber', 'dietary_fiber', 'g')
                result = add_nutriment(result, product, 'salt', 'salt', 'g')
                result = add_nutriment(result, product, 'sodium', 'sodium', 'mg')
            if 'calories' in result and len(result['name']) > 0:
                result_list.append(result)
    return HttpResponse(json.dumps(result_list), content_type="application/json")
