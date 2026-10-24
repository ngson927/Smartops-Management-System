
import pytest

from app import create_app


@pytest.fixture
def client():

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_public_registration_disabled(client):

    response = client.get("/register")

    assert response.status_code == 404


def test_login_still_accessible(client):

    response = client.get("/login")

    assert response.status_code == 200
