from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=30)

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
    creation_date = models.DateTimeField(auto_now=True)

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
        null=True, help_text="Amount of choleserol in mg in the reference amount.")    # Cholesterin
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
    def adjust_ingredient_amounts(self, old_value, new_value):
        for i in Ingredient.objects.filter(recipe=self):
            i.amount = i.amount/old_value*new_value
            i.save()

    def get_ingredients(self):
        return Ingredient.objects.filter(recipe=self)

    @property
    def reference_amount(self):
        return sum([i.amount for i in self.get_ingredients()])

    @reference_amount.setter
    def reference_amount(self, new_amount):
        self.adjust_ingredient_amounts(self.reference_amount, new_amount)

    @property
    def calories(self):
        return sum([i.calories for i in self.get_ingredients()])

    @calories.setter
    def calories(self, new_calories_count):
        self.adjust_ingredient_amounts(self.calories, new_calories_count)

    @property
    def total_fat(self):
        try:
            return sum([i.total_fat for i in self.get_ingredients()])
        except TypeError:
            return None

    @total_fat.setter
    def total_fat(self, new_total_fat_amount):
        self.adjust_ingredient_amounts(self.total_fat, new_total_fat_amount)

    @property
    def saturated_fat(self):
        try:
            return sum([i.saturated_fat for i in self.get_ingredients()])
        except TypeError:
            return None

    @saturated_fat.setter
    def saturated_fat(self, new_saturated_fat_amount):
        self.adjust_ingredient_amounts(self.saturated_fat, new_saturated_fat_amount)

    @property
    def cholesterol(self):
        try:
            return sum([i.cholesterol for i in self.get_ingredients()])
        except TypeError:
            return None

    @cholesterol.setter
    def cholesterol(self, new_cholesterol_value):
        self.adjust_ingredient_amounts(self.cholesterol, new_cholesterol_value)

    @property
    def protein(self):
        try:
            return sum([i.protein for i in self.get_ingredients()])
        except TypeError:
            return None

    @protein.setter
    def protein(self, new_protein_value):
        self.adjust_ingredient_amounts(self.protein, new_protein_value)

    @property
    def total_carbs(self):
        try:
            return sum([i.total_carbs for i in self.get_ingredients()])
        except TypeError:
            return None

    @total_carbs.setter
    def total_carbs(self, new_total_carbs_value):
        self.adjust_ingredient_amounts(self.total_carbs, new_total_carbs_value)

    @property
    def sugar(self):
        try:
            return sum([i.sugar for i in self.get_ingredients()])
        except TypeError:
            return None

    @sugar.setter
    def sugar(self, new_sugar_value):
        self.adjust_ingredient_amounts(self.sugar, new_sugar_value)

    @property
    def dietary_fiber(self):
        try:
            return sum([i.dietary_fiber for i in self.get_ingredients()])
        except TypeError:
            return None

    @dietary_fiber.setter
    def dietary_fiber(self, new_dietary_fiber_value):
        self.adjust_ingredient_amounts(self.dietary_fiber, new_dietary_fiber_value)

    @property
    def salt(self):
        try:
            return sum([i.salt for i in self.get_ingredients()])
        except TypeError:
            return None

    @salt.setter
    def salt(self, new_salt_value):
        self.adjust_ingredient_amounts(self.salt, new_salt_value)

    @property
    def sodium(self):
        try:
            return sum([i.sodium for i in self.get_ingredients()])
        except TypeError:
            return None

    @sodium.setter
    def sodium(self, new_sodium_value):
        self.adjust_ingredient_amounts(self.sodium, new_sodium_value)

    @property
    def potassium(self):
        try:
            return sum([i.potassium for i in self.get_ingredients()])
        except TypeError:
            return None

    @potassium.setter
    def potassium(self, new_potassium_value):
        self.adjust_ingredient_amounts(self.potassium, new_potassium_value)

    @property
    def copper(self):
        try:
            return sum([i.copper for i in self.get_ingredients()])
        except TypeError:
            return None

    @copper.setter
    def copper(self, new_copper_value):
        self.adjust_ingredient_amounts(self.copper, new_copper_value)

    @property
    def iron(self):
        try:
            return sum([i.iron for i in self.get_ingredients()])
        except TypeError:
            return None

    @iron.setter
    def iron(self, new_iron_value):
        self.adjust_ingredient_amounts(self.iron, new_iron_value)

    @property
    def magnesium(self):
        try:
            return sum([i.magnesium for i in self.get_ingredients()])
        except TypeError:
            return None

    @magnesium.setter
    def magnesium(self, new_magnesium_value):
        self.adjust_ingredient_amounts(self.magnesium, new_magnesium_value)

    @property
    def manganese(self):
        try:
            return sum([i.manganese for i in self.get_ingredients()])
        except TypeError:
            return None

    @manganese.setter
    def manganese(self, new_manganese_value):
        self.adjust_ingredient_amounts(self.manganese, new_manganese_value)

    @property
    def zinc(self):
        try:
            return sum([i.zinc for i in self.get_ingredients()])
        except TypeError:
            return None

    @zinc.setter
    def zinc(self, new_zinc_value):
        self.adjust_ingredient_amounts(self.zinc, new_zinc_value)

    @property
    def phosphorous(self):
        try:
            return sum([i.phosphorous for i in self.get_ingredients()])
        except TypeError:
            return None

    @phosphorous.setter
    def phosphorous(self, new_phosphorous_value):
        self.adjust_ingredient_amounts(self.phosphorous, new_phosphorous_value)

    @property
    def sulphur(self):
        try:
            return sum([i.sulphur for i in self.get_ingredients()])
        except TypeError:
            return None

    @sulphur.setter
    def sulphur(self, new_sulphur_value):
        self.adjust_ingredient_amounts(self.sulphur, new_sulphur_value)

    @property
    def chloro(self):
        try:
            return sum([i.chloro for i in self.get_ingredients()])
        except TypeError:
            return None

    @chloro.setter
    def chloro(self, new_chloro_value):
        self.adjust_ingredient_amounts(self.chloro, new_chloro_value)

    @property
    def fluoric(self):
        try:
            return sum([i.fluoric for i in self.get_ingredients()])
        except TypeError:
            return None

    @fluoric.setter
    def fluoric(self, new_fluoric_value):
        self.adjust_ingredient_amounts(self.fluoric, new_fluoric_value)

    @property
    def vitamin_b1(self):
        try:
            return sum([i.vitamin_b1 for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_b1.setter
    def vitamin_b1(self, new_vitamin_b1_value):
        self.adjust_ingredient_amounts(self.vitamin_b1, new_vitamin_b1_value)

    @property
    def vitamin_b12(self):
        try:
            return sum([i.vitamin_b12 for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_b12.setter
    def vitamin_b12(self, new_vitamin_b12_value):
        self.adjust_ingredient_amounts(self.vitamin_b12, new_vitamin_b12_value)

    @property
    def vitamin_b6(self):
        try:
            return sum([i.vitamin_b6 for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_b6.setter
    def vitamin_b6(self, new_vitamin_b6_value):
        self.adjust_ingredient_amounts(self.vitamin_b6, new_vitamin_b6_value)

    @property
    def vitamin_c(self):
        try:
            return sum([i.vitamin_c for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_c.setter
    def vitamin_c(self, new_vitamin_c_value):
        self.adjust_ingredient_amounts(self.vitamin_c, new_vitamin_c_value)

    @property
    def vitamin_d(self):
        try:
            return sum([i.vitamin_d for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_d.setter
    def vitamin_d(self, new_vitamin_d_value):
        self.adjust_ingredient_amounts(self.vitamin_d, new_vitamin_d_value)

    @property
    def vitamin_e(self):
        try:
            return sum([i.vitamin_e for i in self.get_ingredients()])
        except TypeError:
            return None

    @vitamin_e.setter
    def vitamin_e(self, new_vitamin_e_value):
        self.adjust_ingredient_amounts(self.vitamin_e, new_vitamin_e_value)


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
            self.food_is_recipe = f
        elif type(f) is Product:
            self.product = f
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

    @property
    def total_fat(self):
        return self.scale_to_amount(self.food.total_fat)

    @total_fat.setter
    def total_fat(self, new_total_fat_amount):
        self.amount = self.amount / self.total_fat * new_total_fat_amount

    @property
    def saturated_fat(self):
        return self.scale_to_amount(self.food.saturated_fat)

    @saturated_fat.setter
    def saturated_fat(self, new_saturated_fat_amount):
        self.amount = self.amount / self.saturated_fat * new_saturated_fat_amount

    @property
    def cholesterol(self):
        return self.scale_to_amount(self.food.cholesterol)

    @cholesterol.setter
    def cholesterol(self, new_cholesterol_value):
        self.amount = self.amount / self.cholesterol * new_cholesterol_value

    @property
    def protein(self):
        return self.scale_to_amount(self.food.protein)

    @protein.setter
    def protein(self, new_protein_value):
        self.amount = self.amount / self.protein * new_protein_value

    @property
    def total_carbs(self):
        return self.scale_to_amount(self.food.total_carbs)

    @total_carbs.setter
    def total_carbs(self, new_total_carbs_value):
        self.amount = self.amount / self.total_carbs * new_total_carbs_value

    @property
    def sugar(self):
        return self.scale_to_amount(self.food.sugar)

    @sugar.setter
    def sugar(self, new_sugar_value):
        self.amount = self.amount / self.sugar * new_sugar_value

    @property
    def dietary_fiber(self):
        return self.scale_to_amount(self.food.dietary_fiber)

    @dietary_fiber.setter
    def dietary_fiber(self, new_dietary_fiber_value):
        self.amount = self.amount / self.dietary_fiber * new_dietary_fiber_value

    @property
    def salt(self):
        return self.scale_to_amount(self.food.salt)

    @salt.setter
    def salt(self, new_salt_value):
        self.amount = self.amount / self.salt * new_salt_value

    @property
    def sodium(self):
        return self.scale_to_amount(self.food.sodium)

    @sodium.setter
    def sodium(self, new_sodium_value):
        self.amount = self.amount / self.sodium * new_sodium_value

    @property
    def potassium(self):
        return self.scale_to_amount(self.food.potassium)

    @potassium.setter
    def potassium(self, new_potassium_value):
        self.amount = self.amount / self.potassium * new_potassium_value

    @property
    def copper(self):
        return self.scale_to_amount(self.food.copper)

    @copper.setter
    def copper(self, new_copper_value):
        self.amount = self.amount / self.copper * new_copper_value

    @property
    def iron(self):
        return self.scale_to_amount(self.food.iron)

    @iron.setter
    def iron(self, new_iron_value):
        self.amount = self.amount / self.iron * new_iron_value

    @property
    def magnesium(self):
        return self.scale_to_amount(self.food.magnesium)

    @magnesium.setter
    def magnesium(self, new_magnesium_value):
        self.amount = self.amount / self.iron * new_magnesium_value

    @property
    def manganese(self):
        return self.scale_to_amount(self.food.manganese)

    @manganese.setter
    def manganese(self, new_manganese_value):
        self.amount = self.amount / self.manganese * new_manganese_value

    @property
    def zinc(self):
        return self.scale_to_amount(self.food.zinc)

    @zinc.setter
    def zinc(self, new_zinc_value):
        self.amount = self.amount / self.zinc * new_zinc_value

    @property
    def phosphorous(self):
        return self.scale_to_amount(self.food.phosphorous)

    @phosphorous.setter
    def phosphorous(self, new_phosphorous_value):
        self.amount = self.amount / self.phosphorous * new_phosphorous_value

    @property
    def sulphur(self):
        return self.scale_to_amount(self.food.sulphur)

    @sulphur.setter
    def sulphur(self, new_sulphur_value):
        self.amount = self.amount / self.sulphur * new_sulphur_value

    @property
    def chloro(self):
        return self.scale_to_amount(self.food.chloro)

    @chloro.setter
    def chloro(self, new_chloro_value):
        self.amount = self.amount / self.chloro * new_chloro_value

    @property
    def fluoric(self):
        return self.scale_to_amount(self.food.fluoric)

    @fluoric.setter
    def fluoric(self, new_fluoric_value):
        self.amount = self.amount / self.fluoric * new_fluoric_value

    @property
    def vitamin_b1(self):
        return self.scale_to_amount(self.food.vitamin_b1)

    @vitamin_b1.setter
    def vitamin_b1(self, new_vitamin_b1_value):
        self.amount = self.amount / self.vitamin_b1 * new_vitamin_b1_value

    @property
    def vitamin_b12(self):
        return self.scale_to_amount(self.food.vitamin_b12)

    @vitamin_b12.setter
    def vitamin_b12(self, new_vitamin_b12_value):
        self.amount = self.amount / self.vitamin_b12 * new_vitamin_b12_value

    @property
    def vitamin_b6(self):
        return self.scale_to_amount(self.food.vitamin_b6)

    @vitamin_b6.setter
    def vitamin_b6(self, new_vitamin_b6_value):
        self.amount = self.amount / self.vitamin_b6 * new_vitamin_b6_value

    @property
    def vitamin_c(self):
        return self.scale_to_amount(self.food.vitamin_c)

    @vitamin_c.setter
    def vitamin_c(self, new_vitamin_c_value):
        self.amount = self.amount / self.vitamin_c * new_vitamin_c_value

    @property
    def vitamin_d(self):
        return self.scale_to_amount(self.food.vitamin_d)

    @vitamin_d.setter
    def vitamin_d(self, new_vitamin_d_value):
        self.amount = self.amount / self.vitamin_d * new_vitamin_d_value

    @property
    def vitamin_e(self):
        return self.scale_to_amount(self.food.vitamin_e)

    @vitamin_e.setter
    def vitamin_e(self, new_vitamin_e_value):
        self.amount = self.amount / self.vitamin_e * new_vitamin_e_value
