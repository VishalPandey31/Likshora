def test_app_creation(app):
    """Test that the application factory initializes successfully."""
    assert app is not None
    assert app.name == "app"


def test_health_endpoint(client):
    """Test GET /api/v1/health returns 200 OK and expected JSON structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["message"] == "Likshora backend is running"
    assert data["service"] == "Likshora API"
    assert data["version"] == "v1"


def test_unknown_route_returns_json_404(client):
    """Test accessing non-existent route returns standard JSON 404 response."""
    response = client.get("/api/v1/unknown-endpoint-xyz")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]


def test_method_not_allowed_returns_json_405(client):
    """Test POST request to GET-only route returns standard JSON 405 response."""
    response = client.post("/api/v1/health")
    assert response.status_code == 405
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert "message" in data["error"]


def test_db_health_check_without_connection(client, monkeypatch):
    """Test GET /api/v1/health/db handles missing or unconfigured connection gracefully."""
    monkeypatch.setenv("DATABASE_URL", "")
    response = client.get("/api/v1/health/db")
    assert response.status_code == 503
    data = response.get_json()
    assert data["success"] is False
    assert data["backend"] == "healthy"
    assert data["database"] == "disconnected"
    assert data["error"] == "DATABASE_URL environment variable is missing or unconfigured"
