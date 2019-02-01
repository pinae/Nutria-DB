from django.test import TestCase
from django.contrib.auth.models import User
from backend.models import Product, Recipe, Ingredient, Category, NoFoodException


class ModelTests(TestCase):
    def testRecipeCalculations(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.protein = 30.0
        a.save()
        b = Product(category=cat, name_addition='b', author=author, reference_amount=100.0, calories=20.0)
        b.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        i1 = Ingredient(recipe=r, amount=10.0)
        i1.food = a
        i2 = Ingredient(recipe=r, amount=200.0)
        i2.food = b
        i1.save()
        i2.save()
        # Recipe created
        self.assertAlmostEqual(r.calories, 50.0, 5)
        self.assertIsNone(r.protein)
        b.protein = 10.0
        b.save()
        self.assertAlmostEqual(r.protein, 23.0, 5)

    def testIngredientNoFood(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        i = Ingredient(recipe=r, amount=10.0)
        self.assertRaises(NoFoodException, i.food, cat)

    def testPrintIngredtient(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.protein = 30.0
        a.save()
        i = Ingredient(recipe=r, amount=10.0)
        i.food = a
        self.assertEqual(str(i), "10.0g of test: a")

    def testIngredientSetProperties(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.save()
        i = Ingredient(recipe=r, amount=10.0)
        i.food = a
        i.save()
        i.calories = 20
        self.assertAlmostEqual(i.amount, 20, 5)
        i.total_fat = 1
        i.saturated_fat = 1
        i.cholesterol = 1
        i.protein = 1
        i.total_carbs = 1
        i.sugar = 1
        i.dietary_fiber = 1
        i.salt = 1
        i.sodium = 1
        i.potassium = 1
        i.copper = 1
        i.iron = 1
        i.magnesium = 1
        i.manganese = 1
        i.zinc = 1
        i.phosphorous = 1
        i.sulphur = 1
        i.chloro = 1
        i.fluoric = 1
        i.vitamin_b1 = 1
        i.vitamin_b12 = 1
        i.vitamin_b6 = 1
        i.vitamin_c = 1
        i.vitamin_d = 1
        i.vitamin_e = 1
        for prop in ['total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar', 'dietary_fiber',
                     'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium', 'manganese', 'zinc', 'phosphorous',
                     'sulphur', 'chloro', 'fluoric', 'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c',
                     'vitamin_d', 'vitamin_e']:
            i.amount = 20
            i.__setattr__(prop, 10)
            self.assertAlmostEqual(i.amount, 20, 5)
            a.__setattr__(prop, 5)
            a.save()
            i.__setattr__(prop, 10)
            self.assertAlmostEqual(i.amount, 200, 5)
