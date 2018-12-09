from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from backend.models import Product, Recipe, Category, Ingredient
from jsonAPI.helpers import convert_digits_to_bytes


def query_food(request):
    """
    The query call uses the following format:
    If the first bit is 0 a ean encoded as an integer with 4 bytes (big-endian) has to follow.
    If the first bit is >0 it encodes the length of an utf-8 encoded query string.
    The next byte is a query_count.
    The last two bytes are the starting points for the chunks for products and recipes. 255 means -1. If a
    ean was given only the byte for the product chunk is read.
    The rest of the body is ignored.
    :param request:
    :return:
    """
    if request.body[0] == b'\x00':
        query_ean = "{0:013d}".format(int.from_bytes(request.body[1:5], byteorder='big'))
        query_count = int(request.body[5])
        product_chunk_start = int(request.body[6]) if request.body[6] < 255 else -1
        products = []
        new_product_chunk_start = -1
        new_recipe_chunk_start = None
        if product_chunk_start > 0:
            products_query = Product.objects.filter(ean__exact=convert_digits_to_bytes(query_ean)).\
                prefetch_related('category').order_by('category__name', 'name_addition')
            if products_query.count() > query_count:
                new_product_chunk_start = product_chunk_start + query_count
            products = products_query[product_chunk_start:query_count]
        results = list(products)
    else:
        query_string = str(request.body[1:request.body[0]+1], encoding='utf-8')
        query_count = int(request.body[request.body[0]+1])
        product_chunk_start = int(request.body[request.body[0] + 2]) if int(
            request.body[request.body[0] + 2]) < 255 else -1
        recipe_chunk_start = int(request.body[request.body[0] + 3]) if int(
            request.body[request.body[0] + 3]) < 255 else -1
        new_product_chunk_start = -1
        products = []
        if product_chunk_start >= 0:
            products_query = Product.objects.filter(Q(name_addition__icontains=query_string) |
                                                    Q(category__name__icontains=query_string)). \
                prefetch_related('category').order_by('category__name', 'name_addition')
            if products_query.count() > query_count:
                new_product_chunk_start = product_chunk_start + query_count
            products = products_query[product_chunk_start:query_count]
        new_recipe_chunk_start = -1
        recipes = []
        if recipe_chunk_start >= 0:
            recipes_query = Recipe.objects.filter(Q(name_addition__icontains=query_string) |
                                                  Q(category__name__icontains=query_string)). \
                prefetch_related('category').order_by('category__name', 'name_addition')
            if recipes_query.count() > query_count:
                new_recipe_chunk_start = recipe_chunk_start + query_count
            recipes = recipes_query[recipe_chunk_start:query_count]
        results = list(products) + list(recipes)
    response = chr(len(results)).encode('latin')
    for r in results:
        id_str = '0{0:d}'.format(r.pk)
        response += chr(len(id_str)).encode('latin')
        for c in id_str:
            response += chr(int(c)).encode('latin')
        name_str = r.category.name + ': ' + r.name_addition
        response += chr(len(name_str)).encode('latin')
        response += name_str.encode('utf-8')
    response += chr(new_product_chunk_start).encode('latin') if new_product_chunk_start > 0 else b'\xff'
    if new_recipe_chunk_start is not None:
        response += chr(new_recipe_chunk_start).encode('latin') if new_recipe_chunk_start > 0 else b'\xff'
    return HttpResponse(content=response, content_type="application/octet-stream")
