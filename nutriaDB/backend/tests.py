from django.test import TestCase
from django.contrib.auth.models import User
from backend.models import Product, Recipe, Ingredient, Category, Manufacturer, Serving
from backend.models import NoFoodException
from backend.helpers import split_name


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

    def testIngredientNoFood(self):
        def set_food(i, food):
            i.food = food
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        i = Ingredient(recipe=r, amount=10.0)
        self.assertRaises(NoFoodException, set_food, i, cat)

    def testIngredientSwapProductAndRecipe(self):
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
        self.assertEqual(i.product, a)
        self.assertIsNone(i.food_is_recipe)
        r2 = Recipe(category=cat, name_addition='recipe2', author=author)
        r2.save()
        i2 = Ingredient(recipe=r, amount=10.0)
        i2.food = a
        i2.save()
        i.food = r2
        i.save()
        self.assertIsNone(i.product)
        self.assertEqual(i.food_is_recipe, r2)
        i.food = a
        i.save()
        self.assertEqual(i.product, a)
        self.assertIsNone(i.food_is_recipe)

    def testPrintManufacturer(self):
        m = Manufacturer(name="Crownfield (Lidl)")
        self.assertEqual(str(m), "Crownfield (Lidl)")

    def testRecipeSetProperties(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.save()
        b = Product(category=cat, name_addition='b', author=author, reference_amount=100.0, calories=20.0)
        b.save()
        i1 = Ingredient(recipe=r, amount=100.0)
        i1.food = a
        i1.save()
        i2 = Ingredient(recipe=r, amount=200.0)
        i2.food = b
        i2.save()
        self.assertAlmostEqual(r.calories, 140, 5)
        r.calories = 280
        self.assertAlmostEqual(r.calories, 280, 5)
        self.assertAlmostEqual(r.ingredients.all()[0].amount, 200, 5)
        self.assertAlmostEqual(r.ingredients.all()[1].amount, 400, 5)
        r.total_fat = 1
        r.saturated_fat = 1
        r.cholesterol = 1
        r.protein = 1
        r.total_carbs = 1
        r.sugar = 1
        r.dietary_fiber = 1
        r.salt = 1
        r.sodium = 1
        r.potassium = 1
        r.copper = 1
        r.iron = 1
        r.magnesium = 1
        r.manganese = 1
        r.zinc = 1
        r.phosphorous = 1
        r.sulphur = 1
        r.chloro = 1
        r.fluoric = 1
        r.vitamin_b1 = 1
        r.vitamin_b12 = 1
        r.vitamin_b6 = 1
        r.vitamin_c = 1
        r.vitamin_d = 1
        r.vitamin_e = 1
        props = ['total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs', 'sugar', 'dietary_fiber',
                 'salt', 'sodium', 'potassium', 'copper', 'iron', 'magnesium', 'manganese', 'zinc', 'phosphorous',
                 'sulphur', 'chloro', 'fluoric', 'vitamin_b1', 'vitamin_b12', 'vitamin_b6', 'vitamin_c',
                 'vitamin_d', 'vitamin_e']
        for prop in props:
            a.__setattr__(prop, 3)
            b.__setattr__(prop, 10)
        a.save()
        b.save()
        for prop in props:
            self.assertAlmostEqual(r.__getattribute__(prop), 46, 5)
        for prop in props:
            r.__setattr__(prop, 23)
            for prop2 in props:
                self.assertAlmostEqual(r.__getattribute__(prop2), 23, 5)
                self.assertAlmostEqual(r.ingredients.all()[0].amount, 100, 5)
                self.assertAlmostEqual(r.ingredients.all()[1].amount, 200, 5)
            r.__setattr__(prop, 46)
            for prop2 in props:
                self.assertAlmostEqual(r.__getattribute__(prop2), 46, 5)
                self.assertAlmostEqual(r.ingredients.all()[0].amount, 200, 5)
                self.assertAlmostEqual(r.ingredients.all()[1].amount, 400, 5)

    def testRecipeAdjustReferenceAmount(self):
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.save()
        b = Product(category=cat, name_addition='b', author=author, reference_amount=100.0, calories=20.0)
        b.save()
        i1 = Ingredient(recipe=r, amount=100.0)
        i1.food = a
        i1.save()
        i2 = Ingredient(recipe=r, amount=200.0)
        i2.food = b
        i2.save()
        self.assertAlmostEqual(r.reference_amount, 300, 5)
        r.reference_amount = 100
        self.assertAlmostEqual(r.ingredients.all()[0].amount, 100/3, 5)
        self.assertAlmostEqual(r.ingredients.all()[1].amount, 200/3, 5)
        self.assertAlmostEqual(r.reference_amount, 100, 5)

    def testServingFood(self):
        def set_food(x, food):
            x.food = food
        author = User(username='foo', password='secret1234')
        author.save()
        cat = Category(name='test')
        cat.save()
        s = Serving(name="Testspoon", size=25)
        self.assertRaises(NoFoodException, set_food, s, cat)
        a = Product(category=cat, name_addition='a', author=author, reference_amount=100.0, calories=100.0)
        a.save()
        s.food = a
        s.save()
        self.assertEqual(str(s.food), "test: a")
        self.assertIsNone(s.food_is_recipe)
        r = Recipe(category=cat, name_addition='recipe', author=author)
        r.save()
        i1 = Ingredient(recipe=r, amount=100.0)
        i1.food = a
        i1.save()
        s.food = r
        self.assertEqual(str(s.food), "test: recipe")
        self.assertIsNone(s.product)
        s.food = a
        s.save()
        self.assertEqual(str(s.food), "test: a")
        self.assertIsNone(s.food_is_recipe)


class HelpersTest(TestCase):
    def testSplitName(self):
        cat, name = split_name("Foo: Bar")
        self.assertEqual(cat, "Foo")
        self.assertEqual(name, "Bar")
        cat, name = split_name("FooBar")
        self.assertIsNone(cat)
        self.assertEqual(name, "FooBar")
