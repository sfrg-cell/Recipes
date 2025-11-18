from django.test import TestCase
from django.contrib.auth.models import User
from api.models import Recipe, Category, Cuisine, Complexity, Ingredient
from api.filters import RecipeFilter
import django_filters

class RecipeFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.category_dessert = Category.objects.create(name='Desserts')
        self.category_main = Category.objects.create(name='Main Course')
        
        self.cuisine_italian = Cuisine.objects.create(name='Italian')
        self.cuisine_ukrainian = Cuisine.objects.create(name='Ukrainian')
        
        self.complexity_easy = Complexity.objects.create(name='Easy')
        self.complexity_hard = Complexity.objects.create(name='Hard')
        
        self.ingredient_flour = Ingredient.objects.create(name='Flour')
        self.ingredient_sugar = Ingredient.objects.create(name='Sugar')
        
        self.recipe1 = Recipe.objects.create(
            name='Chocolate Cake',
            description='Sweet chocolate cake',
            cooking_time=60,
            category=self.category_dessert,
            cuisine=self.cuisine_italian,
            complexity=self.complexity_easy,
            user=self.user
        )
        self.recipe1.ingredients.add(self.ingredient_flour, self.ingredient_sugar)
        
        self.recipe2 = Recipe.objects.create(
            name='Pasta Carbonara',
            description='Italian pasta dish',
            cooking_time=30,
            category=self.category_main,
            cuisine=self.cuisine_italian,
            complexity=self.complexity_hard,
            user=self.user
        )
        self.recipe2.ingredients.add(self.ingredient_flour)
        
        self.recipe3 = Recipe.objects.create(
            name='Borscht',
            description='Ukrainian soup',
            cooking_time=90,
            category=self.category_main,
            cuisine=self.cuisine_ukrainian,
            complexity=self.complexity_medium,
            user=self.user
        )

    def test_filter_by_category(self):
        filter_set = RecipeFilter(
            data={'category': self.category_dessert.id},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Chocolate Cake')

    def test_filter_by_cuisine(self):
        filter_set = RecipeFilter(
            data={'cuisine': self.cuisine_italian.id},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 2)
        self.assertEqual(results[0].name, 'Chocolate Cake')
        self.assertEqual(results[1].name, 'Pasta Carbonara')

    def test_filter_by_complexity(self):
        filter_set = RecipeFilter(
            data={'complexity': self.complexity_easy.id},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Chocolate Cake')

    def test_filter_by_cooking_time_max(self):
        filter_set = RecipeFilter(
            data={'cooking_time_max': 45},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Pasta Carbonara')

    def test_filter_by_cooking_time_min(self):
        filter_set = RecipeFilter(
            data={'cooking_time_min': 60},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 2)

    def test_search_by_name(self):
        filter_set = RecipeFilter(
            data={'search': 'cake'},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Chocolate Cake')

    def test_search_by_description(self):
        filter_set = RecipeFilter(
            data={'search': 'sweet'},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().description, 'Sweet chocolate cake')

    def test_multiple_filters(self):
        filter_set = RecipeFilter(
            data={
                'category': self.category_main.id,
                'cuisine': self.cuisine_italian.id
            },
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, 'Pasta Carbonara')

    def test_empty_filter_returns_all(self):
        filter_set = RecipeFilter(
            data={},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 3)

    def test_invalid_filter_ignored(self):
        filter_set = RecipeFilter(
            data={'invalid_param': 'some_value'},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 3)

    def test_filter_by_ingredients(self):
        filter_set = RecipeFilter(
            data={'ingredients': self.ingredient_flour.id},
            queryset=Recipe.objects.all()
        )
        results = filter_set.qs
        self.assertEqual(results.count(), 2)

    def test_filter_field_types(self):
        filter_set = RecipeFilter()
        
        self.assertIsInstance(filter_set.filters['category'], django_filters.ModelChoiceFilter)
        self.assertIsInstance(filter_set.filters['search'], django_filters.CharFilter)
        self.assertIsInstance(filter_set.filters['cooking_time_min'], django_filters.NumberFilter)
        self.assertIsInstance(filter_set.filters['cooking_time_max'], django_filters.NumberFilter)