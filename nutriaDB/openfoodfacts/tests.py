from django.test import TestCase

from .views import add_nutriment, scale_by_unit


class ScaleByUnitTests(TestCase):
    def testSameUnit(self):
        self.assertAlmostEqual(scale_by_unit(5.0, 'g', 'g'), 5.0)

    def testGramsToMilligrams(self):
        # 1 g of sodium is 1000 mg of sodium.
        self.assertAlmostEqual(scale_by_unit(1.0, 'g', 'mg'), 1000.0)

    def testMilligramsToGrams(self):
        self.assertAlmostEqual(scale_by_unit(500.0, 'mg', 'g'), 0.5)

    def testMicrogramsToMilligrams(self):
        self.assertAlmostEqual(scale_by_unit(100.0, 'ug', 'mg'), 0.1)

    def testMicrogramsToGrams(self):
        self.assertAlmostEqual(scale_by_unit(1000000.0, 'ug', 'g'), 1.0)

    def testKilojouleToKilocalories(self):
        self.assertAlmostEqual(scale_by_unit(418.4, 'kJ', 'kcal'), 100.0)

    def testKilocaloriesToKilojoule(self):
        self.assertAlmostEqual(scale_by_unit(100.0, 'kcal', 'kJ'), 418.4)

    def testUnknownUnitRaises(self):
        self.assertRaises(ValueError, scale_by_unit, 1.0, 'floz', 'g')


class AddNutrimentTests(TestCase):
    def testEnergyDefaultsToKilojoule(self):
        record = {'nutriments': {'energy_100g': '418.4'}}
        data = add_nutriment({}, record, 'energy', 'calories', 'kcal')
        self.assertAlmostEqual(data['calories'], 100.0)

    def testExplicitUnitIsUsed(self):
        record = {'nutriments': {'energy_100g': '100', 'energy_unit': 'kcal'}}
        data = add_nutriment({}, record, 'energy', 'calories', 'kcal')
        self.assertAlmostEqual(data['calories'], 100.0)

    def testSodiumInGramsBecomesMilligrams(self):
        record = {'nutriments': {'sodium_100g': '0.4'}}
        data = add_nutriment({}, record, 'sodium', 'sodium', 'mg')
        self.assertAlmostEqual(data['sodium'], 400.0)

    def testPlainValueOverridesPreparedValue(self):
        record = {'nutriments': {'fat_prepared_100g': '10', 'fat_100g': '20'}}
        data = add_nutriment({}, record, 'fat', 'total_fat', 'g')
        self.assertAlmostEqual(data['total_fat'], 20.0)

    def testMissingValueLeavesDataUntouched(self):
        record = {'nutriments': {}}
        data = add_nutriment({}, record, 'fat', 'total_fat', 'g')
        self.assertNotIn('total_fat', data)

    def testUnparsableValueIsSkipped(self):
        record = {'nutriments': {'fat_100g': 'n/a'}}
        data = add_nutriment({}, record, 'fat', 'total_fat', 'g')
        self.assertNotIn('total_fat', data)
