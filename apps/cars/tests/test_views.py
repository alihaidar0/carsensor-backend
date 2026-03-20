import pytest
from apps.cars.factories import CarFactory


@pytest.mark.django_db
class TestCarListView:
    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/cars/")
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        response = auth_client.get("/api/v1/cars/")
        assert response.status_code == 200

    def test_returns_paginated_response(self, auth_client):
        CarFactory.create_batch(5)
        response = auth_client.get("/api/v1/cars/")
        assert response.status_code == 200
        assert "count" in response.data
        assert "results" in response.data
        assert response.data["count"] == 5

    def test_filter_by_brand(self, auth_client):
        CarFactory.create(brand="Toyota")
        CarFactory.create(brand="Honda")
        response = auth_client.get("/api/v1/cars/?brand=Toyota")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["brand"] == "Toyota"

    def test_ordering_by_price(self, auth_client):
        CarFactory.create(brand="Toyota", price=1000000)
        CarFactory.create(brand="Honda", price=500000)
        response = auth_client.get("/api/v1/cars/?ordering=price")
        assert response.status_code == 200
        results = response.data["results"]
        assert float(results[0]["price"]) <= float(results[1]["price"])


@pytest.mark.django_db
class TestCarDetailView:
    def test_unauthenticated_returns_401(self, api_client):
        car = CarFactory.create()
        response = api_client.get(f"/api/v1/cars/{car.id}/")
        assert response.status_code == 401

    def test_authenticated_returns_200(self, auth_client):
        car = CarFactory.create()
        response = auth_client.get(f"/api/v1/cars/{car.id}/")
        assert response.status_code == 200
        assert response.data["id"] == car.id
        assert response.data["brand"] == car.brand

    def test_returns_404_for_missing_car(self, auth_client):
        response = auth_client.get("/api/v1/cars/99999/")
        assert response.status_code == 404
