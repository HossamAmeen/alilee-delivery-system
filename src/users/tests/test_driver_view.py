import pytest
from django.urls import reverse
from rest_framework import status
from users.models import Driver

@pytest.mark.django_db
class TestDriverViewSet:
    def test_list_drivers(self, admin_client, driver):
        """Test listing drivers as admin."""
        url = reverse("drivers-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        assert response.data["results"][0]["email"] == driver.email

    def test_retrieve_driver(self, admin_client, driver):
        """Test retrieving a specific driver as admin."""
        url = reverse("drivers-detail", args=[driver.id])
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == driver.email

    def test_create_driver(self, admin_client):
        """Test creating a new driver as admin."""
        url = reverse("drivers-list")
        data = {
            "email": "new_driver@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "full_name": "New Driver",
            "phone_number": "01234567890",
            "vehicle_number": "ABC-123",
            "license_number": "LIC-12345",
        }
        response = admin_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Driver.objects.filter(email="new_driver@example.com").exists()

    def test_update_driver(self, admin_client, driver):
        """Test updating a driver as admin."""
        url = reverse("drivers-detail", args=[driver.id])
        data = {"full_name": "Updated Driver Name"}
        response = admin_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        driver.refresh_from_db()
        assert driver.full_name == "Updated Driver Name"

    def test_delete_driver(self, admin_client, driver):
        """Test deleting a driver as admin."""
        url = reverse("drivers-detail", args=[driver.id])
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Driver.objects.filter(id=driver.id).exists()

    def test_driver_profile(self, api_client, driver):
        """Test retrieving own profile as driver."""
        api_client.force_authenticate(user=driver)
        url = reverse("driver-profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == driver.email

    def test_driver_update_profile(self, api_client, driver):
        """Test updating own profile as driver."""
        api_client.force_authenticate(user=driver)
        url = reverse("driver-profile")
        data = {"full_name": "Self Updated Name"}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        driver.refresh_from_db()
        assert driver.full_name == "Self Updated Name"
