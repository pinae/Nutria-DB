#!/usr/bin/python3
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Product, Recipe, Ingredient, Category
from datetime import datetime
import os
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            pina = User.objects.get(username='pina')
        except User.DoesNotExist:
            pina = User(username='pina', first_name='Pina', last_name='Merkert', email='pmk@ct.de')
            pina.set_password('1234Geheim')
            pina.save()
        for file in [os.path.join('jsonAPI', 'fixtures', filename)
                     for filename in os.listdir(os.path.join('jsonAPI', 'fixtures'))]:
            with open(file) as f:
                cat_table = []
                product_table = []
                recipe_table = []
                for data in json.loads(f.read()):
                    if 'model' in data and data['model'] == 'backend.Category' and \
                            'fields' in data and 'name' in data['fields']:
                        new_category = Category(name=data['fields']['name'])
                        new_category.save()
                        if 'pk' in data:
                            cat_table.append({'fixture_pk': data['pk'], 'real_category': new_category})
                    if 'model' in data and data['model'] == 'backend.Product' and 'fields' in data and \
                            'category' in data['fields'] and 'name_addition' in data['fields'] and \
                            'reference_amount' in data['fields'] and 'calories' in data['fields']:
                        fields = data['fields']
                        category = None
                        for c in cat_table:
                            if fields['category'] == c['fixture_pk']:
                                category = c['real_category']
                        if category is None:
                            continue
                        try:
                            reference_amount = float(fields['reference_amount'])
                            calories = float(fields['calories'])
                        except ValueError:
                            continue
                        new_product = Product(category=category, name_addition=fields['name_addition'],
                                              author=pina, reference_amount=reference_amount, calories=calories)
                        if 'creation_date' in fields:
                            try:
                                new_product.creation_date = datetime.strptime(fields['creation_date'],
                                                                              '%Y-%m-%d %H:%M:%S.%f%z')
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
                                new_product.__setattr__(k, field_value)
                        new_product.save()
                        if 'pk' in data:
                            product_table.append({'fixture_pk': data['pk'], 'real_product': new_product})
                    if 'model' in data and data['model'] == 'backend.Recipe' and 'fields' in data and \
                            'category' in data['fields'] and 'name_addition' in data['fields']:
                        fields = data['fields']
                        category = None
                        for c in cat_table:
                            if fields['category'] == c['fixture_pk']:
                                category = c['real_category']
                        if category is None:
                            continue
                        new_recipe = Recipe(category=category, name_addition=fields['name_addition'], author=pina)
                        if 'creation_date' in fields:
                            try:
                                new_recipe.creation_date = datetime.strptime(fields['creation_date'],
                                                                             '%Y-%m-%d %H:%M:%S.%f%z')
                            except ValueError:
                                pass
                        new_recipe.save()
                        if 'pk' in data:
                            recipe_table.append({'fixture_pk': data['pk'], 'real_recipe': new_recipe})
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
                        new_ingredient = Ingredient(recipe=recipe, amount=amount)
                        new_ingredient.food = food
                        new_ingredient.save()
