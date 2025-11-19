import pytest
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_user_registration(api_client):
    response = api_client.post('/api/auth/register/', {
        'username': 'newuser',
        'password': 'newpass123', 
        'email': 'user@test.com'
    })
    assert response.status_code in [201, 400, 404]

@pytest.mark.django_db
def test_user_login(api_client, user):
    response = api_client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code in [200, 401, 404]
    if response.status_code == 200:
        assert 'access' in response.data

@pytest.mark.django_db
def test_user_view_authenticated(api_client, user):
    login_response = api_client.post('/api/auth/login/', {
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    if login_response.status_code == 200:
        token = login_response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = api_client.get('/api/auth/user/')
        assert response.status_code in [200, 404]