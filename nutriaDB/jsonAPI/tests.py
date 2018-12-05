from django.test import TestCase
from django.contrib.auth.models import User
import json
import jwt
from nutriaDB.settings import JWT_SECRET
from backend.models import Category, Product


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

    def testLogIn(self):
        u = User(username="maxm", first_name="Max", last_name="Mustermann", email="max@mustermann.de")
        u.set_password("test1234")
        u.save()
        response = self.client.post('/json/login', data=json.dumps({
            "username": "maxm",
            "password": "test1234"
        }), content_type='application/json')
        rc = json.loads(response.content)
        self.assertIn('token', rc)
        pl = jwt.decode(rc['token'], JWT_SECRET, 'HS256')
        self.assertIn('id', pl)
        self.assertEqual(u.pk, pl['id'])
        self.assertEqual(pl['email'], "max@mustermann.de")


class SaveTests(TestCase):
    fixtures = ['broetchen.json']

    def setUp(self):
        # Fix passwords for users from fixtures
        for user in User.objects.all():
            user.set_password(user.password)
            user.save()

    def createUserAndGetToken(self):
        u = User(username="maxm", first_name="Max", last_name="Mustermann", email="max@mustermann.de")
        u.set_password("test1234")
        u.save()
        response = self.client.post('/json/login', data=json.dumps({
            "username": "maxm",
            "password": "test1234"
        }), content_type='application/json')
        rc = json.loads(response.content)
        self.assertIn('token', rc)
        return rc['token']

    def testSaveFullProduct(self):
        token = self.createUserAndGetToken()
        response = self.client.post('/json/save', data=json.dumps({
            "token": token,
            "food": {
                "name": "Mehl: Type 405",
                "reference_amount": 100,
                "calories": 348,
                "total_fat": 0.98,
                "saturated_fat": 0.14,
                "cholesterol": 0.0,
                "protein": 10.04,
                "total_carbs": 72.34,
                "sugar": 0.73,
                "dietary_fiber": 2.75,
                "salt": 0.0,
                "sodium": 1,
                "potassium": 168,
                "copper": 106,
                "iron": 0.57,
                "magnesium": 14,
                "manganese": 0.395,
                "zinc": 0.51,
                "phosphorous": 62,
                "sulphur": 100,
                "chloro": 50,
                "fluoric": 0.05,
                "vitamin_b1": 0.1,
                "vitamin_b12": 0.0,
                "vitamin_b6": 0.04,
                "vitamin_c": 0.0,
                "vitamin_d": 0.0,
                "vitamin_e": 0.18
            }
        }), content_type='application/json')
        self.assertIn('success', json.loads(response.content))
        mehl_cat = Category.objects.get(name="Mehl")
        p = Product.objects.filter(category=mehl_cat, name_addition="Type 405")[0]
        self.assertEqual(str(p), "Mehl: Type 405")
        self.assertAlmostEqual(p.reference_amount, 100, 5)
        self.assertAlmostEqual(p.calories, 348, 5)
        self.assertAlmostEqual(p.total_fat, 0.98, 5)
        self.assertAlmostEqual(p.saturated_fat, 0.14, 5)
        self.assertAlmostEqual(p.cholesterol, 0, 5)
        self.assertAlmostEqual(p.protein, 10.04, 5)
        self.assertAlmostEqual(p.total_carbs, 72.34, 5)
        self.assertAlmostEqual(p.sugar, 0.73, 5)
        self.assertAlmostEqual(p.dietary_fiber, 2.75, 5)
        self.assertAlmostEqual(p.salt, 0, 5)
        self.assertAlmostEqual(p.sodium, 1, 5)
        self.assertAlmostEqual(p.potassium, 168, 5)
        self.assertAlmostEqual(p.copper, 106, 5)
        self.assertAlmostEqual(p.iron, 0.57, 5)
        self.assertAlmostEqual(p.magnesium, 14, 5)
        self.assertAlmostEqual(p.manganese, 0.395, 5)
        self.assertAlmostEqual(p.zinc, 0.51, 5)
        self.assertAlmostEqual(p.phosphorous, 62, 5)
        self.assertAlmostEqual(p.sulphur, 100, 5)
        self.assertAlmostEqual(p.chloro, 50, 5)
        self.assertAlmostEqual(p.fluoric, 0.05, 5)
        self.assertAlmostEqual(p.vitamin_b1, 0.1, 5)
        self.assertAlmostEqual(p.vitamin_b12, 0.0, 5)
        self.assertAlmostEqual(p.vitamin_b6, 0.04, 5)
        self.assertAlmostEqual(p.vitamin_c, 0.0, 5)
        self.assertAlmostEqual(p.vitamin_d, 0.0, 5)
        self.assertAlmostEqual(p.vitamin_e, 0.18, 5)
