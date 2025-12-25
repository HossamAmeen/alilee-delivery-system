import pytest
from django.urls import reverse
from rest_framework import status

from users.models import FirebaseDevice


@pytest.mark.django_db
class TestFirebaseDeviceRegisterAPIView:
    url = reverse("firebase-device-register")

    def test_register_new_device(self, user_client, admin):
        """Test that a user can register a new Firebase token."""
        payload = {"token": "new-token-123"}
        response = user_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created"] is True
        assert response.data["token"] == "new-token-123"

        assert FirebaseDevice.objects.filter(user=admin, token="new-token-123").exists()

    def test_register_existing_device_same_user(
        self, user_client, firebase_device, admin
    ):
        """Test registering an already registered token for the same user returns 200."""
        payload = {"token": firebase_device.token}
        response = user_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] is False
        assert response.data["token"] == firebase_device.token

        assert (
            FirebaseDevice.objects.filter(
                user=admin, token=firebase_device.token
            ).count()
            == 1
        )

    def test_register_existing_device_different_user(
        self, user_client, firebase_device, trader
    ):
        """Test registering a token already owned by another user updates the ownership."""
        # firebase_device is owned by admin (from fixture)
        # user_client is authenticated as admin (from fixture)
        # Let's use trader_client instead
        from rest_framework.test import APIClient

        trader_client = APIClient()
        trader_client.force_authenticate(user=trader)

        payload = {"token": firebase_device.token}
        response = trader_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["created"] is False

        firebase_device.refresh_from_db()
        assert firebase_device.user_id == trader.id

    def test_unregister_device(self, user_client, firebase_device, admin):
        """Test that a user can unregister a Firebase token."""
        payload = {"token": firebase_device.token}
        response = user_client.delete(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FirebaseDevice.objects.filter(token=firebase_device.token).exists()

    def test_unregister_nonexistent_device(self, user_client):
        """Test unregistering a nonexistent token returns 204."""
        payload = {"token": "nonexistent-token"}
        response = user_client.delete(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthorized_access(self, api_client):
        """Test unauthenticated requests are rejected."""
        payload = {"token": "some-token"}

        # POST
        response = api_client.post(self.url, data=payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # DELETE
        response = api_client.delete(self.url, data=payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
