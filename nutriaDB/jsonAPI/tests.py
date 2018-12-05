from django.test import TestCase
from django.contrib.auth.models import User
import json
import jwt
from nutriaDB.settings import JWT_SECRET


class QueryTests(TestCase):
    fixtures = ['broetchen.json']

    def setUp(self):
        # Fix passwords for users from fixtures
        for user in User.objects.all():
            user.set_password(user.password)
            user.save()

    def testFlourQuery(self):
        response = self.client.get('/json/find?name=brö')
        rc = json.loads(response.content)
        self.assertIn('food', rc)
        self.assertGreaterEqual(len(rc['food']), 0)
        self.assertEqual(int(rc['food'][0][0]), 11)
        self.assertEqual(rc['food'][0][1], "Backware: Weizenbrötchen")

    def testFlourQueryWithCount(self):
        response = self.client.get('/json/find?name=brö&count=1')
        rc = json.loads(response.content)
        self.assertIn('food', rc)
        self.assertGreaterEqual(len(rc['food']), 0)
        self.assertEqual(int(rc['food'][0][0]), 11)
        self.assertEqual(rc['food'][0][1], "Backware: Weizenbrötchen")

    def testFlourQueryWithCount0(self):
        response = self.client.get('/json/find?name=brö&count=0')
        rc = json.loads(response.content)
        self.assertIn('food', rc)
        self.assertEqual(len(rc['food']), 0)

    def testNoParams(self):
        response = self.client.get('/json/find')
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)

    def testQueryCountNoInteger(self):
        response = self.client.get('/json/find?name=brö&count=a')
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)


class UserTests(TestCase):
    def testRegistration(self):
        response = self.client.post('/json/register', data=json.dumps({
            "username": "maxm",
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@mustermann.de",
            "password": "test1234"
        }), content_type='application/json')
        rc = json.loads(response.content)
        self.assertIn('token', rc)
        user = User.objects.get(username="maxm")
        self.assertEqual(user.username, "maxm")
        self.assertEqual(user.first_name, "Max")
        self.assertEqual(user.last_name, "Mustermann")
        self.assertEqual(user.email, "max@mustermann.de")
        self.assertTrue(user.check_password("test1234"))
        pl = jwt.decode(rc['token'], JWT_SECRET, 'HS256')
        self.assertIn('id', pl)
        self.assertEqual(pl['email'], "max@mustermann.de")
