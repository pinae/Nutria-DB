# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Q
from backend.models import Product, Recipe, Ingredient, Category
from backend.helpers import split_name
from datetime import datetime
import os
import json


class Command(BaseCommand):
    @staticmethod
    def get_category_and_name_addition(fields, cat_table):
        if 'category' in fields and 'name_addition' in fields:
            category = None
            for c in cat_table:
                if fields['category'] == c['fixture_pk']:
                    category = c['real_category']
            if category is None:
                return None, None
            name_addition = fields['name_addition']
            return category, name_addition
        elif 'name' in fields:
            category_str, name_addition = split_name(fields['name'])
            try:
                category = Category.objects.get(name=category_str)
            except Category.DoesNotExist:
                print("The Category {} from {} does not exist. Skipping...".format(
                    category_str, fields['name']
                ))
                return None, None
            return category, name_addition
        else:
            return None, None

    def handle(self, *args, **options):
        try:
            pina = User.objects.get(username='pina')
        except User.DoesNotExist:
            pina = User(username='pina', first_name='Pina', last_name='Merkert', email='pmk@ct.de')
            pina.set_password('1234Geheim')
            pina.save()
        paths = [os.path.join('jsonAPI', 'fixtures', filename)
                 for filename in os.listdir(os.path.join('jsonAPI', 'fixtures'))]
        paths = sorted(paths)
        for file in paths:
            print("Loading data from {}.".format(file))
            with open(file, 'r', encoding='utf-8') as f:
                cat_table = []
                product_table = []
                recipe_table = []
                for data in json.loads(f.read()):
                    if 'model' in data and data['model'] == 'backend.Category' and \
                            'fields' in data and 'name' in data['fields']:
                        try:
                            category = Category.objects.get(name=data['fields']['name'])
                        except Category.DoesNotExist:
                            category = Category(name=data['fields']['name'])
                            category.save()
                        if 'pk' in data:
                            cat_table.append({'fixture_pk': data['pk'], 'real_category': category})
                    if 'model' in data and data['model'] == 'backend.Product' and 'fields' in data and \
                            'reference_amount' in data['fields'] and 'calories' in data['fields']:
                        fields = data['fields']
                        category, name_addition = self.get_category_and_name_addition(fields, cat_table)
                        if type(category) is not Category or type(name_addition) is not str:
                            continue
                        try:
                            reference_amount = float(fields['reference_amount'])
                            calories = float(fields['calories'])
                        except ValueError:
                            continue
                        product_query = Product.objects.filter(category=category, name_addition=name_addition,
                                                               reference_amount=reference_amount, calories=calories)
                        save_new_product = False
                        if product_query.count() >= 1:
                            product = product_query[0]
                        else:
                            save_new_product = True
                            product = Product(category=category, name_addition=name_addition,
                                              author=pina, reference_amount=reference_amount, calories=calories)
                        field_cache = {}
                        if 'creation_date' in fields:
                            try:
                                creation_date = datetime.strptime(fields['creation_date'],
                                                                  '%Y-%m-%d %H:%M:%S.%f%z')
                                if product.creation_date is None or product.creation_date != creation_date:
                                    product.creation_date = creation_date
                                    save_new_product = True
                                field_cache['creation_date'] = creation_date
                            except ValueError:
                                pass
                        for k in ["total_fat", "saturated_fat", "cholesterol", "protein", "total_carbs", "sugar",
                                  "dietary_fiber", "salt", "sodium", "potassium", "copper", "iron", "magnesium",
                                  "manganese", "zinc", "phosphorous", "sulphur", "chloro", "fluoric",
                                  "vitamin_b1", "vitamin_b12", "vitamin_b6", "vitamin_c", "vitamin_d", "vitamin_e"]:
                            if k in fields:
                                try:
                                    field_value = float(fields[k])
                                except ValueError:
                                    continue
                                if product.__getattribute__(k) is None:
                                    product.__setattr__(k, field_value)
                                    save_new_product = True
                                if product.__getattribute__(k) != field_value:
                                    product = Product(category=category, name_addition=name_addition,
                                                      author=pina, reference_amount=reference_amount, calories=calories)
                                    product.__setattr__(k, field_value)
                                    save_new_product = True
                                field_cache[k] = field_value
                        for k in field_cache.keys():
                            product.__setattr__(k, field_cache[k])
                        if save_new_product:
                            product.save()
                            print("Adding Product: " + str(product))
                        else:
                            print("Product " + str(product) + " is already up to date.")
                        if 'pk' in data:
                            product_table.append({'fixture_pk': data['pk'], 'real_product': product})
                    if 'model' in data and data['model'] == 'backend.Recipe' and 'fields' in data:
                        fields = data['fields']
                        category, name_addition = self.get_category_and_name_addition(fields, cat_table)
                        if type(category) is not Category or type(name_addition) is not str:
                            continue
                        creation_date = None
                        if 'creation_date' in fields:
                            try:
                                creation_date = datetime.strptime(fields['creation_date'],
                                                                  '%Y-%m-%d %H:%M:%S.%f%z')
                            except ValueError:
                                pass
                        recipe_query = Recipe.objects.filter(category=category, name_addition=name_addition)
                        if recipe_query.count() == 1:
                            recipe = recipe_query[0]
                            print("Found existing Recipe: " + str(recipe))
                        else:
                            recipe = Recipe(category=category, name_addition=name_addition, author=pina)
                            if creation_date is not None:
                                recipe.creation_date = creation_date
                            recipe.save()
                            print("Adding empty Recipe: " + str(recipe))
                        if 'pk' in data:
                            recipe_table.append({'fixture_pk': data['pk'], 'real_recipe': recipe})
                        if 'ingredients' in data:
                            for ing_data in data['ingredients']:
                                if 'name' not in ing_data or 'amount' not in ing_data:
                                    print("This ingredient needs a 'name' and an 'amount': " + str(ing_data))
                                    continue
                                cat_str, name_add = split_name(ing_data['name'])
                                food = None
                                products = Product.objects.filter(Q(name_addition__icontains=ing_data['name']) |
                                                                  Q(category__name__icontains=ing_data['name']) |
                                                                  Q(category__name=cat_str,
                                                                    name_addition__icontains=name_add)).\
                                    prefetch_related('category').order_by('category__name', 'name_addition')
                                recipes = Recipe.objects.filter(Q(name_addition__icontains=ing_data['name']) |
                                                                Q(category__name__icontains=ing_data['name']) |
                                                                Q(category__name=cat_str,
                                                                  name_addition__icontains=name_add)).\
                                    prefetch_related('category').order_by('category__name', 'name_addition')
                                if products.count() + recipes.count() == 0:
                                    print("Unable to find this ingredient: " + ing_data['name'])
                                elif products.count() + recipes.count() > 1:
                                    exact_match_found = False
                                    for p in products:
                                        if str(p) == ing_data['name']:
                                            food = p
                                            exact_match_found = True
                                    for r in recipes:
                                        if str(r) == ing_data['name']:
                                            food = r
                                            exact_match_found = True
                                    if not exact_match_found:
                                        print("It's unclear which Product or Recipe was meant for this ingredient.")
                                        print("There were these options:")
                                        for p in products:
                                            print("- " + str(p))
                                        for r in recipes:
                                            print("- " + str(r))
                                        print("Please change the 'name' so that only one of these is found.")
                                        continue
                                else:
                                    if products.count() == 1:
                                        food = products.all()[0]
                                    else:
                                        food = recipes.all()[0]
                                try:
                                    amount = float(ing_data['amount'])
                                except ValueError:
                                    continue
                                ingredient_query = Ingredient.objects.filter(
                                    recipe=recipe, amount=amount,
                                    product=food if type(food) is Product else None,
                                    food_is_recipe=food if type(food) is Recipe else None)
                                if ingredient_query.count() == 1:
                                    ingredient = ingredient_query[0]
                                    print("Found existing Ingredient: \"" + str(ingredient) +
                                          "\" for Recipe: " + str(ingredient.recipe))
                                else:
                                    ingredient = Ingredient(recipe=recipe, amount=amount)
                                    ingredient.food = food
                                    ingredient.save()
                                    print("Added Ingredient: \"" + str(ingredient) +
                                          "\" for Recipe: " + str(ingredient.recipe))
                    if 'model' in data and data['model'] == 'backend.Ingredient' and 'fields' in data and \
                            'recipe' in data['fields'] and 'amount' in data['fields'] and \
                            ('food' in data['fields'] or
                             'product' in data['fields'] or
                             'food_is_recipe' in data['fields']):
                        fields = data['fields']
                        try:
                            amount = float(fields['amount'])
                        except ValueError:
                            continue
                        recipe = None
                        for r in recipe_table:
                            if fields['recipe'] == r['fixture_pk']:
                                recipe = r['real_recipe']
                        food = None
                        if 'food' in fields:
                            for p in product_table:
                                if fields['food'][0] == '0' and fields['food'][1:] == p['fixture_pk']:
                                    food = p['real_product']
                            for r in recipe_table:
                                if fields['food'][0] == '1' and fields['food'][1:] == r['fixture_pk']:
                                    food = r['real_recipe']
                        if 'product' in fields:
                            for p in product_table:
                                if fields['product'] == p['fixture_pk']:
                                    food = p['real_product']
                        if 'food_is_recipe' in fields:
                            for r in recipe_table:
                                if fields['food_is_recipe'] == r['fixture_pk']:
                                    food = r['real_recipe']
                        if recipe is None or food is None:
                            continue
                        ingredient_query = Ingredient.objects.filter(
                            recipe=recipe, amount=amount,
                            product=food if type(food) is Product else None,
                            food_is_recipe=food if type(food) is Recipe else None)
                        if ingredient_query.count() != 1:
                            new_ingredient = Ingredient(recipe=recipe, amount=amount)
                            new_ingredient.food = food
                            new_ingredient.save()
                            print("Added Ingredient: \"" + str(new_ingredient) +
                                  "\" for Recipe: " + str(new_ingredient.recipe))
                        else:
                            print("Ingredient: \"" + str(ingredient_query[0]) +
                                  "\" for Recipe: " + str(ingredient_query[0].recipe) + " was already in the database.")
