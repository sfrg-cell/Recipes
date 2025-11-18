from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Recipe, Category, Cuisine, Complexity

class RecipeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Main Course')
        self.cuisine = Cuisine.objects.create(name='Italian')
        self.complexity = Complexity.objects.create(name='Medium')
        
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test description',
            instructions='Test instructions',
            cooking_time=30,
            servings=4,
            category=self.category,
            cuisine=self.cuisine,
            complexity=self.complexity,
            author=self.user
        )

    def test_get_recipes_list(self):
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_random_recipe(self):
        response = self.client.get('/api/recipes/random/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)