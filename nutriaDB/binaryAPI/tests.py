from django.test import TestCase

from backend.models import Product, Recipe


def build_name_query(query, count=15, product_chunk=0, recipe_chunk=0):
    query_bytes = query.encode('utf-8')
    return (bytes([len(query_bytes)]) + query_bytes +
            bytes([count, product_chunk, recipe_chunk]))


def parse_response(payload):
    """Parse the binary response into ([(id, name)], product_chunk, recipe_chunk)."""
    result_count = payload[0]
    pos = 1
    results = []
    for _ in range(result_count):
        id_len = payload[pos]
        pos += 1
        id_str = "".join(str(d) for d in payload[pos:pos + id_len])
        pos += id_len
        name_len = payload[pos]
        pos += 1
        name = payload[pos:pos + name_len].decode('utf-8')
        pos += name_len
        results.append((id_str, name))
    product_chunk = payload[pos] if payload[pos] != 255 else -1
    recipe_chunk = None
    if pos + 1 < len(payload):
        recipe_chunk = payload[pos + 1] if payload[pos + 1] != 255 else -1
    return results, product_chunk, recipe_chunk


class BinaryQueryTests(TestCase):
    fixtures = ['broetchen.json']

    def testNameQuery(self):
        response = self.client.post('/b/q', data=build_name_query("brö"),
                                    content_type="application/octet-stream")
        results, product_chunk, recipe_chunk = parse_response(response.content)
        self.assertEqual(product_chunk, -1)
        self.assertEqual(recipe_chunk, -1)
        self.assertEqual(len(results), 1)
        recipe = Recipe.objects.get(name_addition="Weizenbrötchen")
        self.assertEqual(results[0][0], '1' + str(recipe.pk))
        self.assertEqual(results[0][1], "Backware: Weizenbrötchen")

    def testNameQueryUmlautName(self):
        # The name length byte must count utf-8 bytes, not characters,
        # otherwise names with umlauts desynchronize the parser.
        response = self.client.post('/b/q', data=build_name_query("Hühnerei"),
                                    content_type="application/octet-stream")
        results, _, _ = parse_response(response.content)
        egg = Product.objects.get(name_addition="Hühnerei")
        self.assertIn(('0' + str(egg.pk), "Ei: Hühnerei"), results)

    def testNameQueryPagination(self):
        response = self.client.post('/b/q', data=build_name_query("e", count=2),
                                    content_type="application/octet-stream")
        results, product_chunk, recipe_chunk = parse_response(response.content)
        # More than 2 products match "e" in the fixture, so a next chunk is offered.
        self.assertEqual(product_chunk, 2)
        second = self.client.post('/b/q', data=build_name_query("e", count=2, product_chunk=2),
                                  content_type="application/octet-stream")
        second_results, _, _ = parse_response(second.content)
        first_page_products = [r for r in results if r[0].startswith('0')]
        second_page_products = [r for r in second_results if r[0].startswith('0')]
        self.assertFalse(set(first_page_products) & set(second_page_products))

    def testEanQueryBranchReachable(self):
        # A body starting with a zero byte selects the ean query branch.
        body = bytes([0]) + (12345).to_bytes(4, byteorder='big') + bytes([15, 0])
        response = self.client.post('/b/q', data=body, content_type="application/octet-stream")
        results, product_chunk, recipe_chunk = parse_response(response.content)
        self.assertEqual(results, [])
        self.assertEqual(product_chunk, -1)
        self.assertIsNone(recipe_chunk)
