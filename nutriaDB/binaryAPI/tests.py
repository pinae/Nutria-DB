from django.test import TestCase
from django.contrib.auth.models import User


class QueryTests(TestCase):
    fixtures = ['broetchen.json']

    def setUp(self):
        # Fix passwords for users from fixtures
        for user in User.objects.all():
            user.set_password(user.password)
            user.save()

    def testFlourQuery(self):
        query = "brö".encode('utf-8')
        response = self.client.post('/b/q', data=chr(len(query)).encode('latin') + query +
                                    (chr(10) + chr(0) + chr(0)).encode('latin'),
                                    content_type="application/octet_stream")
        rc = response.content
        print(rc)
        self.assertEqual(1, rc[0])  # 1 result
        food_id = str(rc[2:2+rc[1]], encoding='latin')
        self.assertEqual('\x00\x01', food_id)
        self.assertEqual(int.from_bytes(b'\x18', byteorder='big'), rc[len(food_id)+2])
        food_name = str(rc[len(food_id)+3:len(food_id)+3+rc[len(food_id)+2]+1], encoding='utf-8')
        self.assertEqual("Backware: Weizenbrötchen", food_name)
        self.assertEqual(rc[len(food_id)+3+rc[len(food_id)+2]+1], 255)
        self.assertEqual(rc[len(food_id)+3+rc[len(food_id)+2]+2], 255)
