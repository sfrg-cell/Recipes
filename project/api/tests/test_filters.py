import pytest
from django.contrib.auth.models import User
from api.filters import RecipeFilter
from api.models import Recipe, Category, Cuisine, Complexity

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user('testuser', 'testpass123')

@pytest.fixture
def category():
    return Category.objects.create(name='Test Category')

@pytest.fixture
def cuisine():
    return Cuisine.objects.create(name='Test Cuisine')

@pytest.fixture
def complexity():
    return Complexity.objects.create(name='Easy')

@pytest.fixture
def recipe(user, category, cuisine, complexity):
    return Recipe.objects.create(
        title='Test Recipe',
        description='Test description',
        instructions='Test instructions',
        cooking_time=30,
        servings=4,
        category=category,
        cuisine=cuisine,
        complexity=complexity,
        author=user
    )

@pytest.mark.django_db
def test_filter_by_category(api_client, recipe, category):
    filter_set = RecipeFilter(data={'category': category.id}, queryset=Recipe.objects.all())
    results = filter_set.qs
    assert results.count() == 1
    assert results.first().title == 'Test Recipe'

@pytest.mark.django_db
def test_filter_by_cuisine(api_client, recipe, cuisine):
    filter_set = RecipeFilter(data={'cuisine': cuisine.id}, queryset=Recipe.objects.all())
    results = filter_set.qs
    assert results.count() == 1

@pytest.mark.django_db
def test_filter_by_complexity(api_client, recipe, complexity):
    filter_set = RecipeFilter(data={'complexity': complexity.id}, queryset=Recipe.objects.all())
    results = filter_set.qs
    assert results.count() == 1

@pytest.mark.django_db
def test_search_by_title(api_client, recipe):
    filter_set = RecipeFilter(data={'search': 'Test'}, queryset=Recipe.objects.all())
    results = filter_set.qs
    assert results.count() == 1

@pytest.mark.django_db
def test_empty_filter_returns_all(api_client, recipe):
    filter_set = RecipeFilter(data={}, queryset=Recipe.objects.all())
    results = filter_set.qs
    assert results.count() == 1
