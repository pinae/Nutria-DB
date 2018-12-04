from django.test import TestCase
from django.contrib.auth.models import User
from backend.models import Product, Recipe, Ingredient, Category


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
