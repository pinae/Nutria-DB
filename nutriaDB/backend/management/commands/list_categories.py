# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from backend.models import Category, Product, Recipe


class Command(BaseCommand):
    def handle(self, *args, **options):
        for category in Category.objects.all():
            examples = []
            for product in Product.objects.filter(category=category)[:2]:
                examples.append(product.name_addition)
            for recipe in Recipe.objects.filter(category=category)[:2]:
                examples.append(recipe.name_addition)
            print("{:3d}: {:20s} Examples: {}".format(category.pk, category.name, examples))
