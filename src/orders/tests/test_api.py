import json
from decimal import Decimal

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework import status

from geo.models import DeliveryZone
from orders.models import Customer, Order
from users.models import Driver, Trader, UserAccount, UserRole


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def trader_user():
    return Trader.objects.create_user(
        email='trader@example.com',
        password='testpass123',
        full_name='Trader User',
        role=UserRole.TRADER
    )


@pytest.fixture
def driver_user():
    return Driver.objects.create_user(
        email='driver@example.com',
        password='testpass123',
        full_name='Driver User',
        role=UserRole.DRIVER
    )


@pytest.fixture
def admin_user():
    return UserAccount.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
        full_name='Admin User'
    )


@pytest.fixture
def delivery_zone():
    return DeliveryZone.objects.create(
        name='Downtown',
        cost=Decimal('10.00'),
        polygon=Point(31.2357, 30.0444).buffer(0.1)  # Cairo coordinates
    )


@pytest.fixture
def customer():
    return Customer.objects.create(
        name='John Doe',
        address='123 Main St',
        phone='+201234567890',
        location='https://maps.google.com/...'
    )


@pytest.fixture
def order_data(delivery_zone, trader_user):
    return {
        'reference_code': 'REF12345',
        'product_cost': '100.00',
        'delivery_zone': delivery_zone.id,
        'trader': trader_user.id,
        'status': 'created',
        'payment_method': 'cod',
        'product_payment_status': 'cod',
        'note': 'Test order',
        'longitude': '31.2357',
        'latitude': '30.0444',
        'customer': {
            'name': 'John Doe',
            'address': '123 Main St',
            'phone': '+201234567890',
            'location': 'https://maps.google.com/...'
        }
    }

@pytest.mark.django_db
def test_create_order_authenticated(api_client, trader_user, order_data):
    """Test creating a new order with authentication"""
    api_client.force_authenticate(user=trader_user)
    list_url = reverse('order-list')
    
    response = api_client.post(
        list_url,
        data=json.dumps(order_data),
        content_type='application/json'
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert Order.objects.count() == 1
    assert Order.objects.get().reference_code == 'REF12345'
    assert Order.objects.get().trader == trader_user

@pytest.mark.django_db
def test_create_order_unauthenticated(api_client, order_data):
    """Test that unauthenticated users cannot create orders"""
    list_url = reverse('order-list')
    response = api_client.post(
        list_url,
        data=json.dumps(order_data),
        content_type='application/json'
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_list_orders_as_trader(api_client, trader_user, customer, delivery_zone):
    """Test that a trader can only see their own orders"""
    # Create orders for different traders
    order1 = Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    # Create another trader and their order
    trader2 = Trader.objects.create_user(
        email='trader2@example.com',
        password='testpass123',
        full_name='Trader 2',
        role=UserRole.TRADER
    )
    Order.objects.create(
        reference_code='ORDER2',
        product_cost=Decimal('200.00'),
        delivery_cost=Decimal('15.00'),
        trader=trader2,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=trader_user)
    list_url = reverse('order-list')
    response = api_client.get(list_url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['reference_code'] == 'ORDER1'

@pytest.mark.django_db
def test_list_orders_as_driver(api_client, trader_user, driver_user, customer, delivery_zone):
    """Test that a driver can only see their assigned orders"""
    # Create orders with different drivers
    Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        driver=driver_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    # Create another driver and assign an order to them
    driver2 = Driver.objects.create_user(
        email='driver2@example.com',
        password='testpass123',
        full_name='Driver 2',
        role=UserRole.DRIVER
    )
    Order.objects.create(
        reference_code='ORDER2',
        product_cost=Decimal('200.00'),
        delivery_cost=Decimal('15.00'),
        trader=trader_user,
        driver=driver2,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=driver_user)
    list_url = reverse('order-list')
    response = api_client.get(list_url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['reference_code'] == 'ORDER1'

@pytest.mark.django_db
def test_retrieve_order(api_client, trader_user, customer, delivery_zone):
    """Test retrieving a single order"""
    order = Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=trader_user)
    url = reverse('order-detail', kwargs={'pk': order.id})
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['reference_code'] == 'ORDER1'
    assert response.data['status'] == 'created'

@pytest.mark.django_db
def test_update_order(api_client, trader_user, customer, delivery_zone):
    """Test updating an order"""
    order = Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    update_data = {
        'reference_code': 'ORDER1-UPDATED',
        'product_cost': '150.00',
        'note': 'Updated note',
        'delivery_zone': delivery_zone.id,
        'trader': trader_user.id,
        'customer': {
            'id': customer.id,
            'name': 'John Doe Updated',
            'address': '456 New St',
            'phone': '+201234567891',
            'location': 'https://maps.google.com/updated'
        }
    }
    
    api_client.force_authenticate(user=trader_user)
    url = reverse('order-detail', kwargs={'pk': order.id})
    response = api_client.put(
        url,
        data=json.dumps(update_data),
        content_type='application/json'
    )
    
    assert response.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.reference_code == 'ORDER1-UPDATED'
    assert order.product_cost == Decimal('150.00')
    assert order.customer.name == 'John Doe Updated'

@pytest.mark.django_db
def test_delete_order(api_client, admin_user, trader_user, customer, delivery_zone):
    """Test deleting an order"""
    order = Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=admin_user)
    url = reverse('order-detail', kwargs={'pk': order.id})
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Order.objects.count() == 0

@pytest.mark.django_db
def test_filter_orders_by_status(api_client, trader_user, customer, delivery_zone):
    """Test filtering orders by status"""
    # Create orders with different statuses
    Order.objects.create(
        reference_code='ORDER1',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        status='created',
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    Order.objects.create(
        reference_code='ORDER2',
        product_cost=Decimal('200.00'),
        delivery_cost=Decimal('15.00'),
        status='delivered',
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=trader_user)
    list_url = reverse('order-list')
    response = api_client.get(list_url, {'status': 'delivered'})
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['reference_code'] == 'ORDER2'
    assert response.data['results'][0]['status'] == 'delivered'

@pytest.mark.django_db
def test_search_orders(api_client, trader_user, customer, delivery_zone):
    """Test searching orders by reference code"""
    Order.objects.create(
        reference_code='ORDER123',
        product_cost=Decimal('100.00'),
        delivery_cost=Decimal('10.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    Order.objects.create(
        reference_code='ORDER456',
        product_cost=Decimal('200.00'),
        delivery_cost=Decimal('15.00'),
        trader=trader_user,
        customer=customer,
        delivery_zone=delivery_zone
    )
    
    api_client.force_authenticate(user=trader_user)
    list_url = reverse('order-list')
    response = api_client.get(list_url, {'search': 'ORDER123'})
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['reference_code'] == 'ORDER123'
