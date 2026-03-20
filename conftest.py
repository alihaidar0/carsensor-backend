import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="testadmin",
        email="testadmin@example.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(api_client, admin_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "testadmin", "password": "testpass123"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
