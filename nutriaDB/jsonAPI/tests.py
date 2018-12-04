from django.test import TestCase
from django.contrib.auth.models import User
import json


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
