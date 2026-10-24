
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    return app.test_client()


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_health_api(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_inventory_requires_login(client):
    response = client.get("/api/inventory")
    assert response.status_code == 401
