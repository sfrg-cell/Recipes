import pytest
from django.contrib.auth.models import User
from api.serializers import RecipeSerializer
from api.models import Category, Cuisine, Complexity

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

# ТЕСТИ
@pytest.mark.django_db
def test_recipe_serializer_valid(user, category, cuisine, complexity):
    data = {
        'title': 'Test Recipe',
        'description': 'Test description',
        'instructions': 'Test instructions', 
        'cooking_time': 30,
        'servings': 4,
        'category': category.id,
        'cuisine': cuisine.id,
        'complexity': complexity.id,
        'author': user.id
    }
    serializer = RecipeSerializer(data=data)
    assert serializer.is_valid() == True

@pytest.mark.django_db
def test_recipe_serializer_invalid_missing_title(user):
    data = {
        'instructions': 'Test instructions',
        'author': user.id
    }
    serializer = RecipeSerializer(data=data)
    assert serializer.is_valid() == False
    assert 'title' in serializer.errors