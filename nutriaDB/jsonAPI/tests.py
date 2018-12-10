from django.test import TestCase
from django.contrib.auth.models import User
import json
import jwt
from nutriaDB.settings import JWT_SECRET
from backend.models import Category, Product, Recipe


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

    def testFlourQueryPost(self):
        response = self.client.post('/json/find', data=json.dumps({
            "name": "brö"
        }), content_type="application/json")
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

    def testFlourQueryWithCountPost(self):
        response = self.client.post('/json/find', data=json.dumps({
            "name": "brö",
            "count": 1
        }), content_type="application/json")
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

    def testFlourQueryWithCount0Post(self):
        response = self.client.post('/json/find', data=json.dumps({
            "name": "brö",
            "count": 0
        }), content_type="application/json")
        rc = json.loads(response.content)
        self.assertIn('food', rc)
        self.assertEqual(len(rc['food']), 0)

    def testNoParams(self):
        response = self.client.get('/json/find')
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)

    def testNoParamsPost(self):
        response = self.client.post('/json/find', data="{}", content_type="application/json")
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)

    def testQueryCountNoInteger(self):
        response = self.client.get('/json/find?name=brö&count=a')
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)

    def testQueryCountNoIntegerPost(self):
        response = self.client.post('/json/find', data=json.dumps({
            "name": "brö",
            "count": "a"
        }), content_type="application/json")
        rc = json.loads(response.content)
        self.assertNotIn('food', rc)
        self.assertIn('error', rc)

    def testProductDetails(self):
        response = self.client.get('/json/food/05')
        rc = json.loads(response.content)
        self.assertNotIn('error', rc)
        self.assertEqual(rc['name'], "Ei: Hühnerei")
        egg_values = {
            "reference_amount": 100.0,
            "calories": 137.0,
            "total_fat": 9.32,
            "saturated_fat": 2.71,
            "cholesterol": 396.0,
            "protein": 11.85,
            "total_carbs": 1.53,
            "sugar": 1.53,
            "dietary_fiber": 0.0,
            "salt": 0.3,
            "sodium": 144.0,
            "potassium": 147.0,
            "copper": 65.0,
            "iron": 1.83,
            "magnesium": 11.0,
            "manganese": 0.071,
            "zinc": 1.49,
            "phosphorous": 210.0,
            "sulphur": 180.0,
            "chloro": 180.0,
            "fluoric": 0.11,
            "vitamin_b1": 0.1,
            "vitamin_b12": 0.0019,
            "vitamin_b6": 0.08,
            "vitamin_c": 0.0,
            "vitamin_d": 0.00293,
            "vitamin_e": 1.96
        }
        for k in egg_values.keys():
            self.assertAlmostEqual(rc[k], egg_values[k], 5)

    def testProductDetailsPost(self):
        response = self.client.post('/json/food', data=json.dumps({
            "id": "05"
        }), content_type="application/json")
        rc = json.loads(response.content)
        self.assertNotIn('error', rc)
        self.assertEqual(rc['name'], "Ei: Hühnerei")
        egg_values = {
            "reference_amount": 100.0,
            "calories": 137.0,
            "total_fat": 9.32,
            "saturated_fat": 2.71,
            "cholesterol": 396.0,
            "protein": 11.85,
            "total_carbs": 1.53,
            "sugar": 1.53,
            "dietary_fiber": 0.0,
            "salt": 0.3,
            "sodium": 144.0,
            "potassium": 147.0,
            "copper": 65.0,
            "iron": 1.83,
            "magnesium": 11.0,
            "manganese": 0.071,
            "zinc": 1.49,
            "phosphorous": 210.0,
            "sulphur": 180.0,
            "chloro": 180.0,
            "fluoric": 0.11,
            "vitamin_b1": 0.1,
            "vitamin_b12": 0.0019,
            "vitamin_b6": 0.08,
            "vitamin_c": 0.0,
            "vitamin_d": 0.00293,
            "vitamin_e": 1.96
        }
        for k in egg_values.keys():
            self.assertAlmostEqual(rc[k], egg_values[k], 5)

    def testRecipeDetails(self):
        response = self.client.get('/json/food/11')
        rc = json.loads(response.content)
        self.assertNotIn('error', rc)
        self.assertEqual(rc['name'], "Backware: Weizenbrötchen")
        bread_bun_values = {
            "reference_amount": 528.0,
            "calories": 1817.66,
            "total_fat": 5.86,
            "saturated_fat": 0.8854,
            "cholesterol": 0.0,
            "protein": 58.46,
            "total_carbs": 366.69,
            "sugar": 7.866,
            "dietary_fiber": 20.665,
            "salt": 9.8905,
            "sodium": 3904.9,
            "potassium": 1057.3,
            "copper": 750.716,
            "iron": 8.271,
            "magnesium": 164.5,
            "manganese": 3.5795,
            "zinc": 5.165,
            "phosphorous": 752.5,
            "sulphur": 550.6,
            "chloro": 6293.1,
            "fluoric": 255.033,
            "vitamin_b1": 1.0075,
            "vitamin_b12": 0.0,
            "vitamin_b6": 0.818,
            "vitamin_c": 0.0,
            "vitamin_d": 0.0,
            "vitamin_e": 1.045
        }
        for k in bread_bun_values.keys():
            self.assertAlmostEqual(rc[k], bread_bun_values[k], 5)
        self.assertIn('ingredients', rc)
        ingredient_list = [
            {'id': '01', 'name': 'Mehl: Weizenmehl Type 550', 'amount': 500, 'calories': 352*5},
            {'id': '02', 'name': 'Backzutat: frische Backhefe', 'amount': 15, 'calories': 328*0.15},
            {'id': '03', 'name': 'Gewürz: Speisesalz', 'amount': 10, 'calories': 0},
            {'id': '04', 'name': 'Backzutat: Biomalz', 'amount': 3, 'calories': 282*0.03}
        ]
        for i, ing in enumerate(rc['ingredients']):
            self.assertEqual(ing['id'], ingredient_list[i]['id'])
            self.assertEqual(ing['name'], ingredient_list[i]['name'])
            self.assertAlmostEqual(ing['amount'], ingredient_list[i]['amount'], 5)
            self.assertAlmostEqual(ing['calories'], ingredient_list[i]['calories'], 5)

    def testRecipeDetailsScaled(self):
        response = self.client.get('/json/food/11/52.8')
        rc = json.loads(response.content)
        self.assertNotIn('error', rc)
        self.assertEqual(rc['name'], "Backware: Weizenbrötchen")
        bread_bun_values = {
            "reference_amount": 528,
            "calories": 181.766,
            "total_fat": 0.586,
            "saturated_fat": 0.08854,
            "cholesterol": 0.0,
            "protein": 5.846,
            "total_carbs": 36.669,
            "sugar": 0.7866,
            "dietary_fiber": 2.0665,
            "salt": 0.98905,
            "sodium": 390.49,
            "potassium": 105.73,
            "copper": 75.0716,
            "iron": 0.8271,
            "magnesium": 16.45,
            "manganese": 0.35795,
            "zinc": 0.5165,
            "phosphorous": 75.25,
            "sulphur": 55.06,
            "chloro": 629.31,
            "fluoric": 25.5033,
            "vitamin_b1": 0.10075,
            "vitamin_b12": 0.0,
            "vitamin_b6": 0.0818,
            "vitamin_c": 0.0,
            "vitamin_d": 0.0,
            "vitamin_e": 0.1045
        }
        for k in bread_bun_values.keys():
            self.assertAlmostEqual(rc[k], bread_bun_values[k], 5)
        self.assertIn('ingredients', rc)
        ingredient_list = [
            {'id': '01', 'name': 'Mehl: Weizenmehl Type 550', 'amount': 50, 'calories': 352*5/10},
            {'id': '02', 'name': 'Backzutat: frische Backhefe', 'amount': 1.5, 'calories': 328*0.15/10},
            {'id': '03', 'name': 'Gewürz: Speisesalz', 'amount': 1, 'calories': 0},
            {'id': '04', 'name': 'Backzutat: Biomalz', 'amount': 0.3, 'calories': 282*0.03/10}
        ]
        for i, ing in enumerate(rc['ingredients']):
            self.assertEqual(ing['id'], ingredient_list[i]['id'])
            self.assertEqual(ing['name'], ingredient_list[i]['name'])
            self.assertAlmostEqual(ing['amount'], ingredient_list[i]['amount'], 5)
            self.assertAlmostEqual(ing['calories'], ingredient_list[i]['calories'], 5)

    def testRecipeDetailsScaledPost(self):
        response = self.client.post('/json/food', data=json.dumps({
            "id": "11",
            "amount": 52.8
        }), content_type="application/json")
        rc = json.loads(response.content)
        self.assertNotIn('error', rc)
        self.assertEqual(rc['name'], "Backware: Weizenbrötchen")
        bread_bun_values = {
            "reference_amount": 528,
            "calories": 181.766,
            "total_fat": 0.586,
            "saturated_fat": 0.08854,
            "cholesterol": 0.0,
            "protein": 5.846,
            "total_carbs": 36.669,
            "sugar": 0.7866,
            "dietary_fiber": 2.0665,
            "salt": 0.98905,
            "sodium": 390.49,
            "potassium": 105.73,
            "copper": 75.0716,
            "iron": 0.8271,
            "magnesium": 16.45,
            "manganese": 0.35795,
            "zinc": 0.5165,
            "phosphorous": 75.25,
            "sulphur": 55.06,
            "chloro": 629.31,
            "fluoric": 25.5033,
            "vitamin_b1": 0.10075,
            "vitamin_b12": 0.0,
            "vitamin_b6": 0.0818,
            "vitamin_c": 0.0,
            "vitamin_d": 0.0,
            "vitamin_e": 0.1045
        }
        for k in bread_bun_values.keys():
            self.assertAlmostEqual(rc[k], bread_bun_values[k], 5)
        self.assertIn('ingredients', rc)
        ingredient_list = [
            {'id': '01', 'name': 'Mehl: Weizenmehl Type 550', 'amount': 50, 'calories': 352*5/10},
            {'id': '02', 'name': 'Backzutat: frische Backhefe', 'amount': 1.5, 'calories': 328*0.15/10},
            {'id': '03', 'name': 'Gewürz: Speisesalz', 'amount': 1, 'calories': 0},
            {'id': '04', 'name': 'Backzutat: Biomalz', 'amount': 0.3, 'calories': 282*0.03/10}
        ]
        for i, ing in enumerate(rc['ingredients']):
            self.assertEqual(ing['id'], ingredient_list[i]['id'])
            self.assertEqual(ing['name'], ingredient_list[i]['name'])
            self.assertAlmostEqual(ing['amount'], ingredient_list[i]['amount'], 5)
            self.assertAlmostEqual(ing['calories'], ingredient_list[i]['calories'], 5)


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
                "name": "Mehl: Weizenmehl Type 405",
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
        p = Product.objects.filter(category=mehl_cat, name_addition="Weizenmehl Type 405")[0]
        self.assertEqual(str(p), "Mehl: Weizenmehl Type 405")
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

    def testSaveRecipe(self):
        token = self.createUserAndGetToken()
        response = self.client.post('/json/save', data=json.dumps({
            "token": token,
            "food": {
                "name": "Mehl: Weizenmehl Type 405",
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
        mehl_cat = Category.objects.get(name="Mehl")
        mehl405 = Product.objects.filter(category=mehl_cat, name_addition="Weizenmehl Type 405")[0]
        response = self.client.post('/json/save', data=json.dumps({
            "token": token,
            "food": {
                "name": "Backware: Toastbrot selbstgemacht",
                "ingredients": [
                    {'food': '0' + str(mehl405.pk), 'amount': 450},
                    {'food': '03', 'amount': 10},
                    {'food': '07', 'amount': 75},
                    {'food': '06', 'amount': 10},
                    {'food': '02', 'amount': 21},
                    {'food': '05', 'amount': 68}
                ]
            }
        }), content_type='application/json')
        self.assertIn('success', json.loads(response.content))
        backware_cat = Category.objects.get(name="Backware")
        toast = Recipe.objects.filter(category=backware_cat, name_addition="Toastbrot selbstgemacht")[0]
        self.assertEqual(str(toast), "Backware: Toastbrot selbstgemacht")
        self.assertAlmostEqual(toast.reference_amount, 634, 5)
        self.assertAlmostEqual(toast.calories, 2431.54, 5)
        self.assertAlmostEqual(toast.total_fat, 85.9996, 5)
        self.assertAlmostEqual(toast.saturated_fat, 10.5248, 5)
        self.assertAlmostEqual(toast.cholesterol, 269.28, 5)
        self.assertAlmostEqual(toast.protein, 60.714, 5)
        self.assertAlmostEqual(toast.total_carbs, 343.2704, 5)
        self.assertAlmostEqual(toast.sugar, 15.1118, 5)
        self.assertAlmostEqual(toast.dietary_fiber, 16.785, 5)
        self.assertAlmostEqual(toast.salt, 10.1023, 5)
        self.assertAlmostEqual(toast.sodium, 3998.67, 5)
        self.assertAlmostEqual(toast.potassium, 1277.31, 5)
        self.assertAlmostEqual(toast.copper, 1571.21225, 5)
        self.assertAlmostEqual(toast.iron, 8.1009, 5)
        self.assertAlmostEqual(toast.magnesium, 130.78, 5)
        self.assertAlmostEqual(toast.manganese, 1.95808, 5)
        self.assertAlmostEqual(toast.zinc, 5.0327, 5)
        self.assertAlmostEqual(toast.phosphorous, 707.7, 5)
        self.assertAlmostEqual(toast.sulphur, 637.7, 5)
        self.assertAlmostEqual(toast.chloro, 6411.85, 5)
        self.assertAlmostEqual(toast.fluoric, 5.3418, 5)
        self.assertAlmostEqual(toast.vitamin_b1, 1.0073, 5)
        self.assertAlmostEqual(toast.vitamin_b12, 0.001292, 5)
        self.assertAlmostEqual(toast.vitamin_b6, 0.6544, 5)
        self.assertAlmostEqual(toast.vitamin_c, 0.0, 5)
        self.assertAlmostEqual(toast.vitamin_d, 0.0019924, 5)
        self.assertAlmostEqual(toast.vitamin_e, 48.8558, 5)

    def testDeleteProduct(self):
        token = self.createUserAndGetToken()
        response = self.client.post('/json/save', data=json.dumps({
            "token": token,
            "food": {
                "name": "Mehl: Testmehl",
                "reference_amount": 123,
                "calories": 973,
            }
        }), content_type='application/json')
        self.assertIn('success', json.loads(response.content))
        mehl_cat = Category.objects.get(name="Mehl")
        p = Product.objects.filter(category=mehl_cat, name_addition="Testmehl")[0]
        self.assertEqual(str(p), "Mehl: Testmehl")
        self.assertAlmostEqual(p.reference_amount, 123, 5)
        self.assertAlmostEqual(p.calories, 973, 5)
        response = self.client.post('/json/delete', data=json.dumps({
            "token": token,
            "id": "0" + str(p.pk)
        }), content_type='application/json')
        self.assertIn('success', json.loads(response.content))
        p = Product.objects.filter(category=mehl_cat, name_addition="Testmehl")
        self.assertEqual(p.count(), 0)
