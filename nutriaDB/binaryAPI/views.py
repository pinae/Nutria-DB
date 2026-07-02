from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from backend.models import Product, Recipe
from jsonAPI.helpers import convert_digits_to_bytes


@csrf_exempt
def query_food(request):
    """
    The query call uses the following format:
    If the first byte is 0 a ean encoded as an integer with 4 bytes (big-endian) has to follow.
    If the first byte is >0 it encodes the length of an utf-8 encoded query string.
    The next byte is a query_count.
    The last two bytes are the starting points for the chunks for products and recipes. 255 means -1. If a
    ean was given only the byte for the product chunk is read.
    The rest of the body is ignored.

    The response starts with a result count byte. For each result an id follows (length byte, then the
    digits of the id as raw byte values, the first digit being the type: 0 = product, 1 = recipe) and the
    display name (length byte, then utf-8 bytes). The response ends with the next product chunk start
    byte and, unless a ean was queried, the next recipe chunk start byte (255 means no further results).
    """
    body = request.body

    def chunk_byte(value):
        return -1 if value >= 255 else value

    if body[0] == 0:
        ean = "{0:013d}".format(int.from_bytes(body[1:5], byteorder='big'))
        query_count = body[5]
        product_chunk_start = chunk_byte(body[6])
        products = []
        new_product_chunk_start = -1
        new_recipe_chunk_start = None
        if product_chunk_start >= 0:
            products_query = Product.objects.filter(ean__exact=convert_digits_to_bytes(ean)). \
                select_related('category').order_by('category__name', 'name_addition')
            products = list(products_query[product_chunk_start:product_chunk_start + query_count])
            if products_query.count() > product_chunk_start + query_count:
                new_product_chunk_start = product_chunk_start + query_count
        results = products
    else:
        query_length = body[0]
        query_string = str(body[1:query_length + 1], encoding='utf-8')
        query_count = body[query_length + 1]
        product_chunk_start = chunk_byte(body[query_length + 2])
        recipe_chunk_start = chunk_byte(body[query_length + 3])

        def query_page(model, chunk_start):
            if chunk_start < 0:
                return [], -1
            queryset = model.objects.filter(Q(name_addition__icontains=query_string) |
                                            Q(category__name__icontains=query_string)). \
                select_related('category').order_by('category__name', 'name_addition')
            page = list(queryset[chunk_start:chunk_start + query_count])
            next_start = chunk_start + query_count
            return page, (next_start if queryset.count() > next_start else -1)

        products, new_product_chunk_start = query_page(Product, product_chunk_start)
        recipes, new_recipe_chunk_start = query_page(Recipe, recipe_chunk_start)
        results = products + recipes
    response = bytes([len(results)])
    for r in results:
        type_digit = '1' if isinstance(r, Recipe) else '0'
        id_str = type_digit + str(r.pk)
        response += bytes([len(id_str)])
        response += bytes(int(c) for c in id_str)
        name_bytes = str(r).encode('utf-8')
        response += bytes([len(name_bytes)])
        response += name_bytes
    response += bytes([new_product_chunk_start]) if new_product_chunk_start >= 0 else b'\xff'
    if new_recipe_chunk_start is not None:
        response += bytes([new_recipe_chunk_start]) if new_recipe_chunk_start >= 0 else b'\xff'
    return HttpResponse(content=response, content_type="application/octet-stream")
