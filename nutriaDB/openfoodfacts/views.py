import json
import urllib.parse

import requests
from django.http import HttpResponse, HttpResponseBadRequest

REQUEST_TIMEOUT = 10  # seconds

#: (openfoodfacts_name, our_name, our_unit) for all nutriments we import.
NUTRIMENT_MAPPING = [
    ('energy', 'calories', 'kcal'),
    ('carbohydrates', 'total_carbs', 'g'),
    ('sugars', 'sugar', 'g'),
    ('fat', 'total_fat', 'g'),
    ('saturated-fat', 'saturated_fat', 'g'),
    ('proteins', 'protein', 'g'),
    ('fiber', 'dietary_fiber', 'g'),
    ('salt', 'salt', 'g'),
    ('sodium', 'sodium', 'mg'),
]

#: Multipliers to convert a value from one unit into another.
UNIT_CONVERSIONS = {
    ('g', 'mg'): 1000.0,
    ('mg', 'g'): 0.001,
    ('ug', 'mg'): 0.001,
    ('ug', 'g'): 0.000001,
    ('kj', 'kcal'): 1 / 4.184,
    ('kcal', 'kj'): 4.184,
}


def scale_by_unit(value, current_unit, target_unit):
    if current_unit.lower() == target_unit.lower():
        return value
    try:
        return value * UNIT_CONVERSIONS[(current_unit.lower(), target_unit.lower())]
    except KeyError:
        raise ValueError("Cannot convert from " + current_unit + " to " + target_unit + ".") from None


def add_nutriment(product_data, openfoodfacts_data, openfoodfacts_name, our_name, our_unit):
    """Copy one nutriment from an OpenFoodFacts record, converting units.

    Prefers the value for the product as sold over the value for the
    prepared product.
    """
    nutriments = openfoodfacts_data['nutriments']
    unit = nutriments.get(openfoodfacts_name + '_unit', '').strip()
    if not unit:
        # OpenFoodFacts reports energy in kJ unless stated otherwise;
        # everything else defaults to g.
        unit = 'kJ' if our_unit == 'kcal' else 'g'
    for source_key in [openfoodfacts_name + '_prepared_100g', openfoodfacts_name + '_100g']:
        if source_key in nutriments:
            try:
                product_data[our_name] = scale_by_unit(float(nutriments[source_key]), unit, our_unit)
            except ValueError:
                pass
    return product_data


def name_from_openfoodfacts(record):
    """Build "<brand> - <localized product name>" from an OpenFoodFacts record."""
    name = ""
    if 'brands' in record:
        name += record['brands'].split(",", 1)[0]
    for key in ['product_name_de', 'generic_name_de', 'product_name_en',
                'generic_name_en', 'product_name_fr', 'generic_name_fr']:
        if record.get(key):
            name += " - " + record[key]
            break
    return name


def ask_openfoodfacts_org(request, ean):
    r = requests.get("https://food.openfoodfacts.org/api/v0/product/" + ean, timeout=REQUEST_TIMEOUT)
    data = r.json()
    if 'product' not in data:
        return HttpResponseBadRequest('{"error": "OpenFoodFacts does not know this ean."}',
                                      content_type="application/json")
    record = data['product']
    product_data = {}
    if 'brands' in record:
        product_data['manufacturer'] = record['brands'].split(",", 1)[0]
    product_data['name_addition'] = name_from_openfoodfacts(record)
    product_data['reference_amount'] = 100
    if 'nutriments' in record:
        for off_name, our_name, our_unit in NUTRIMENT_MAPPING:
            product_data = add_nutriment(product_data, record, off_name, our_name, our_unit)
    return HttpResponse(json.dumps(product_data, ensure_ascii=False), content_type="application/json")


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
    r = requests.get("https://world.openfoodfacts.org/cgi/search.pl?" + params, timeout=REQUEST_TIMEOUT)
    data = r.json()
    result_list = []
    for record in data.get('products', []):
        result = {}
        if 'id' in record:
            result['ean'] = record['id']
        if 'brands' in record:
            result['manufacturer'] = record['brands'].split(',')[0]
        result['name'] = name_from_openfoodfacts(record)
        if 'nutriments' in record:
            for off_name, our_name, our_unit in NUTRIMENT_MAPPING:
                result = add_nutriment(result, record, off_name, our_name, our_unit)
        if 'calories' in result and len(result['name']) > 0:
            result_list.append(result)
    return HttpResponse(json.dumps(result_list, ensure_ascii=False), content_type="application/json")
