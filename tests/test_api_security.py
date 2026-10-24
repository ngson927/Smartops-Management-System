
import pytest

from app import create_app


# ==========================================
# 1. CREATE FLASK TEST CLIENT
# ==========================================

@pytest.fixture
def client():

    app = create_app()

    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


# ==========================================
# 2. PROTECTED API AND DASHBOARD ROUTES
# ==========================================

protected_routes = [
    "/api/inventory",
    "/api/analytics/inventory-by-category",
    "/api/forecast/1",
    "/api/ml-evaluation",
    "/analytics",
    "/forecast/1",
    "/ml-evaluation",
    "/inventory/add",
    "/inventory/1/edit",
    "/inventory/transactions",
    "/api/inventory/1/daily-usage",
    "/api/reorder/1",
    "/insights",
    "/api/forecast/real/1",
]


# ==========================================
# 3. TEST UNAUTHORIZED ACCESS
# ==========================================

@pytest.mark.parametrize("route", protected_routes)
def test_route_requires_login(client, route):

    response = client.get(route)

    assert response.status_code == 401, (
        f"Route {route} should require authentication, "
        f"but returned {response.status_code}"
    )
