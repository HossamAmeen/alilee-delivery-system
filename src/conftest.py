import pytest
from rest_framework.test import APIClient

from users.models import UserAccount, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return UserAccount.objects.create_user(
        email="admin@example.com",
        password="testpass123",
        role=UserRole.ADMIN,
        full_name="Admin User",
        is_active=True,
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client
