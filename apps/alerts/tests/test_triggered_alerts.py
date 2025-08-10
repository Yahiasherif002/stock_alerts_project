# apps/alerts/tests/test_triggered_alerts.py
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from apps.alerts.models import Alert, TriggeredAlert
from apps.stocks.models import Stock


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        password="testpass123"
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.login(username=user.username, password="testpass123")
    return api_client


@pytest.fixture
def stock():
    return Stock.objects.create(
        symbol="AAPL",
        name="Apple Inc.",
        current_price=150
    )


@pytest.fixture
def alert(user, stock):
    return Alert.objects.create(
        user=user,
        stock=stock,
        alert_type="THRESHOLD",
        condition=">",
        threshold_price=100,
        is_active=True
    )


@pytest.mark.django_db
def test_triggered_alerts_endpoint(authenticated_client, alert):
    
    TriggeredAlert.objects.create(
        alert=alert,
        triggered_at="2023-10-01T12:00:00Z",
        stock_price=120,
        notification_sent=False
    )

    url = reverse('alerts:triggeredalert-list')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert isinstance(response.data['results'], list)
    assert len(response.data['results']) > 0


@pytest.mark.django_db
def test_triggered_alerts_no_alerts(authenticated_client):
    url = reverse('alerts:triggeredalert-list')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert isinstance(response.data['results'], list)
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_triggered_alerts_unauthenticated(api_client):
    url = reverse('alerts:triggeredalert-list')
    response = api_client.get(url)

    
    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    assert 'detail' in response.data


@pytest.mark.django_db
def test_triggered_alerts_invalid_user(api_client):
    url = reverse('alerts:triggeredalert-list')
    response = api_client.get(url)

    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    assert 'detail' in response.data
