import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "sqlite"
    assert data["comps_in_db"] > 0

def test_get_comps():
    response = client.get("/comps")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0

def test_evaluate_post():
    payload = {
        "emirate": "Dubai",
        "code": "AA",
        "number": "333"
    }
    response = client.post("/v1/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["plate_display"] == "DUBAI AA 333"
    assert data["digit_count"] == 3
    assert data["fair_market_value_aed"] > 0
    assert data["liquidation_value_aed"] < data["fair_market_value_aed"]
    assert data["dealer_ask_aed"] > data["fair_market_value_aed"]
    assert len(data["comps"]) > 0

def test_valuate_get_backwards_compatible():
    response = client.get("/valuate?code=A&plate=77777&emirate=dubai")
    assert response.status_code == 200
    data = response.json()
    assert data["fair_market_value_aed"] > 0
    assert data["estimated_value"] == data["fair_market_value_aed"]
    assert "Super Solid" in data["patterns"][0]

def test_invalid_plate_validation():
    # Negative / 6 digits
    response = client.post("/v1/evaluate", json={"emirate": "Dubai", "code": "A", "number": "123456"})
    assert response.status_code == 400

    # Non-numeric
    response = client.post("/v1/evaluate", json={"emirate": "Dubai", "code": "A", "number": "ABC"})
    assert response.status_code == 400
