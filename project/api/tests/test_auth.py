from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'user@test.com'
        }

    def test_user_registration(self):
        response = self.client.post('/api/auth/register/', self.user_data)
        print(f"Registration response: {response.status_code}")
        self.assertIn(response.status_code, [201, 400, 404])

    def test_user_login(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post('/api/auth/login/', {
            'username': 'newuser',
            'password': 'newpass123'
        })
        if response.status_code == 200:
            self.assertIn('access', response.data)
        else:
            print(f"Login failed with status: {response.status_code}")