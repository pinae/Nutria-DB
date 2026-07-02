from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

#: All optional nutrient fields shared by Product (as real columns) and
#: Recipe/Ingredient (as computed properties). Values are stored per
#: reference amount; units are documented on the Product fields.
NUTRIENT_FIELDS = [
    'total_fat', 'saturated_fat', 'cholesterol', 'protein', 'total_carbs',
    'sugar', 'dietary_fiber', 'salt', 'sodium', 'potassium', 'copper',
    'iron', 'magnesium', 'manganese', 'zinc', 'phosphorous', 'sulphur',
    'chloro', 'fluoric', 'vitamin_b1', 'vitamin_b12', 'vitamin_b6',
    'vitamin_c', 'vitamin_d', 'vitamin_e',
]


class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return str(self.name)


class Manufacturer(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return str(self.name)


class Food(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name_addition = models.CharField(max_length=256)
    creation_date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.category) + ': ' + str(self.name_addition)


class Product(Food):
    ean = models.BinaryField(null=True, max_length=13)
    reference_amount = models.FloatField(
        default=100, help_text="Reference amount for this food in g. This is usually 100g.")
    calories = models.FloatField(
        help_text="Number of kcal of the reference amount of this food. This must not be empty.")
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True)
    total_fat = models.FloatField(
        null=True, help_text="Total amount of fat in g in the reference amount.")      # Fett gesamt
    saturated_fat = models.FloatField(
        null=True, help_text="Amount of saturated fat in g in the reference amount.")  # gesättigte Fettsäure
    cholesterol = models.FloatField(
        null=True, help_text="Amount of cholesterol in mg in the reference amount.")   # Cholesterin
    protein = models.FloatField(
        null=True, help_text="Amount of protein in g in the reference amount.")        # Eiweiß
    total_carbs = models.FloatField(
        null=True, help_text="Total amount of carbs in g in the reference amount.")    # Kohlenhydrate gesamt
    sugar = models.FloatField(
        null=True, help_text="Amount of sugar in g in the reference amount.")          # Zucker (Kohlenhydrat)
    dietary_fiber = models.FloatField(
        null=True, help_text="Amount of dietary fiber in g in the reference amount.")  # Ballaststoffe
    salt = models.FloatField(
        null=True, help_text="Amount of salt in g in the reference amount.")           # Salz
    # total_fat, protein, total_carbs, dietary_fiber and salt should add up to the reference amount.
    sodium = models.FloatField(
        null=True, help_text="Amount of sodium in mg in the reference amount.")        # Natrium
    potassium = models.FloatField(
        null=True, help_text="Amount of potassium in mg in the reference amount.")     # Kalium
    copper = models.FloatField(
        null=True, help_text="Amount of copper in mg in the reference amount.")        # Kupfer
    iron = models.FloatField(
        null=True, help_text="Amount of iron in mg in the reference amount.")          # Eisen
    magnesium = models.FloatField(
        null=True, help_text="Amount of magnesium in mg in the reference amount.")     # Magnesium
    manganese = models.FloatField(
        null=True, help_text="Amount of manganese in mg in the reference amount.")     # Mangan
    zinc = models.FloatField(
        null=True, help_text="Amount of zinc in mg in the reference amount.")          # Zink
    phosphorous = models.FloatField(
        null=True, help_text="Amount of phosphorous in mg in the reference amount.")   # Phosphor
    sulphur = models.FloatField(
        null=True, help_text="Amount of sulphur in mg in the reference amount.")       # Schwefel
    chloro = models.FloatField(
        null=True, help_text="Amount of chloro in mg in the reference amount.")        # Chlor
    fluoric = models.FloatField(
        null=True, help_text="Amount of fluoric in mg in the reference amount.")       # Fluor
    vitamin_b1 = models.FloatField(
        null=True, help_text="Amount of Vitamin B1 in mg in the reference amount.")    # Vitamin B1
    vitamin_b12 = models.FloatField(
        null=True, help_text="Amount of Vitamin B12 in mg in the reference amount.")   # Vitamin B12
    vitamin_b6 = models.FloatField(
        null=True, help_text="Amount of Vitamin B6 in mg in the reference amount.")    # Vitamin B6
    vitamin_c = models.FloatField(
        null=True, help_text="Amount of Vitamin C in mg in the reference amount.")     # Vitamin C
    vitamin_d = models.FloatField(
        null=True, help_text="Amount of Vitamin D in mg in the reference amount.")     # Vitamin D
    vitamin_e = models.FloatField(
        null=True, help_text="Amount of Vitamin E in mg in the reference amount.")     # Vitamin E


class Recipe(Food):
    """
    A recipe aggregates its Ingredients. All nutrient values as well as
    ``calories`` and ``reference_amount`` are computed from the ingredients;
    the setters scale all ingredient amounts proportionally so that the
    recipe reaches the requested value.
    """

    def adjust_ingredient_amounts(self, old_value, new_value):
        for i in Ingredient.objects.filter(recipe=self):
            if old_value:
                i.amount = i.amount / old_value * new_value
                i.save()

    def get_ingredients(self):
        return Ingredient.objects.filter(recipe=self)

    @property
    def reference_amount(self):
        return sum(i.amount for i in self.get_ingredients())

    @reference_amount.setter
    def reference_amount(self, new_amount):
        self.adjust_ingredient_amounts(self.reference_amount, new_amount)

    @property
    def calories(self):
        return sum(i.calories for i in self.get_ingredients())

    @calories.setter
    def calories(self, new_calories_count):
        self.adjust_ingredient_amounts(self.calories, new_calories_count)


def _recipe_nutrient_property(name):
    def getter(self):
        try:
            return sum(getattr(i, name) for i in self.get_ingredients())
        except TypeError:
            # At least one ingredient has no value for this nutrient.
            return None

    def setter(self, new_value):
        self.adjust_ingredient_amounts(getattr(self, name), new_value)

    getter.__name__ = name
    return property(getter, setter, doc=f"Sum of {name} over all ingredients (None if unknown).")


for _name in NUTRIENT_FIELDS:
    setattr(Recipe, _name, _recipe_nutrient_property(_name))


class NoFoodException(Exception):
    pass


class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name="ingredients", on_delete=models.CASCADE)
    food_is_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, default=None)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, default=None)
    amount = models.FloatField(help_text="Amount of this food in g.")

    def __str__(self):
        return str(self.amount) + 'g of ' + str(self.food)

    @property
    def food(self):
        if self.food_is_recipe:
            return self.food_is_recipe
        else:
            return self.product

    @food.setter
    def food(self, f):
        if type(f) is Recipe:
            self.product = None
            self.food_is_recipe = f
        elif type(f) is Product:
            self.product = f
            self.food_is_recipe = None
        else:
            raise NoFoodException(f)

    def scale_to_amount(self, value):
        if value is None:
            return None
        return value / self.food.reference_amount * self.amount

    @property
    def calories(self):
        return self.scale_to_amount(self.food.calories)

    @calories.setter
    def calories(self, new_calories_count):
        self.amount = self.amount / self.calories * new_calories_count


def _ingredient_nutrient_property(name):
    def getter(self):
        return self.scale_to_amount(getattr(self.food, name))

    def setter(self, new_value):
        current = getter(self)
        if current is not None:
            self.amount = self.amount / current * new_value

    getter.__name__ = name
    return property(getter, setter,
                    doc=f"{name} contained in this ingredient's amount (None if unknown for the food).")


for _name in NUTRIENT_FIELDS:
    setattr(Ingredient, _name, _ingredient_nutrient_property(_name))


class Serving(models.Model):
    name = models.CharField(max_length=256,
                            help_text="Usually 'piece', 'slice', 'teaspoon', 'large glass' or 'handful'.")
    size = models.FloatField(help_text="Size of the serving in g")
    food_is_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, default=None,
                                       related_name='servings')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, default=None,
                                related_name='servings')

    def __str__(self):
        return str(self.name) + ' (' + str(self.size) + 'g) of ' + str(self.food)

    @property
    def food(self):
        if self.food_is_recipe:
            return self.food_is_recipe
        else:
            return self.product

    @food.setter
    def food(self, f):
        if type(f) is Recipe:
            self.product = None
            self.food_is_recipe = f
        elif type(f) is Product:
            self.product = f
            self.food_is_recipe = None
        else:
            raise NoFoodException(f)
