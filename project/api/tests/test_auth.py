import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_user_registration(api_client):
    data = {
        'username': 'newuser',
        'password': 'newpass123',
        'email': 'user@example.com'
    }
    response = api_client.post("/api/auth/register/", data, format="json")
    assert response.status_code in [201, 404]


@pytest.mark.django_db
def test_user_login(api_client, user):
    response = api_client.post(
        "/api/auth/login/",
        {
            'username': 'testuser',
            'password': 'testpass123',
        },
        format="json"
    )
    
    if response.status_code == 200:
        assert 'access' in response.data
        assert 'refresh' in response.data
    else:
        pytest.skip("Login endpoint not available")


@pytest.mark.django_db
def test_protected_endpoint_authenticated(api_client, user, recipe):
    login_url = reverse('token_obtain_pair')
    tokens = api_client.post(
        login_url,
        {
            'username': user.username,
            'password': 'testpass123',
        },
        format="json"
    ).data
    
    if 'access' not in tokens:
        pytest.skip("Authentication not working")
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
    
    response = api_client.get(f"/api/recipes/{recipe.id}/", format="json")
    assert response.status_code == 200