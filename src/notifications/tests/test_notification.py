import pytest
from rest_framework.test import APIClient

from notifications.models import Notification
from users.models import UserAccount


@pytest.fixture
def driver_user(db):
    user = UserAccount.objects.create_user(
        email="driver@gmail.com", password="driverpassword", role="driver"
    )
    return user


@pytest.fixture
def admin_user(db):
    user = UserAccount.objects.create_user(
        email="admin@gmail.com", password="adminpassword", role="admin"
    )
    return user


@pytest.fixture
def authenticated_driver_client(driver_user):
    client = APIClient()

    response = client.post(
        "/api/users/login/",
        {"email": driver_user.email, "password": "driverpassword"},
        format="json",
    )

    access_token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    return client, driver_user


def test_driver_can_get_notifications_list(authenticated_driver_client, admin_user):
    client, user = authenticated_driver_client

    Notification.objects.create(
        title="N1", description="D1", user_account=user, created_by=user, is_read=False
    )

    Notification.objects.create(
        title="N2", description="D2", user_account=user, created_by=user, is_read=True
    )

    Notification.objects.create(
        title="N3", description="D3", user_account=admin_user, created_by=admin_user
    )

    response = client.get("/api/notifications/notifications/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["unread_count"] == 1
