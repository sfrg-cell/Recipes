import pytest
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from api.models import Recipe, Category, Cuisine, Complexity

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user('testuser', 'testpass123')
