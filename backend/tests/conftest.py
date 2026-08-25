import pytest
import sys
from pathlib import Path

# Add backend directory to python path for pytest execution
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Create and configure a Flask application instance for testing."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the application's CLI commands."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def mock_external_apis(monkeypatch):
    """Auto-mock external APIs for all tests to prevent hitting live endpoints."""
    from app.services.shiprocket_service import ShiprocketService
    from app.services.razorpay_service import RazorpayService

    # Shiprocket Mocks
    monkeypatch.setattr(ShiprocketService, "get_auth_token", lambda *a, **k: "mock_shiprocket_jwt_token")
    monkeypatch.setattr(ShiprocketService, "create_order", lambda *a, **k: {"order_id": 999123, "shipment_id": 888456, "status_code": 1})
    monkeypatch.setattr(ShiprocketService, "generate_awb", lambda *a, **k: {"awb_assign_status": 1, "response": {"data": {"awb_code": "AWB-SR-123", "courier_name": "Mock Courier", "courier_company_id": 1}}})
    monkeypatch.setattr(ShiprocketService, "request_pickup", lambda *a, **k: {"pickup_status": 1, "response": {"pickup_token_number": "mock-ptoken-123"}})
    monkeypatch.setattr(ShiprocketService, "track_shipment", lambda *a, **k: {"tracking_data": {"shipment_status": 7, "shipment_track": [{"current_status": "DELIVERED"}]}})
    monkeypatch.setattr(ShiprocketService, "cancel_order", lambda *a, **k: {"status_code": 200, "message": "Cancelled"})
    monkeypatch.setattr(ShiprocketService, "get_courier_serviceability", lambda *a, **k: {"status": 200, "data": {"available_courier_companies": [{"courier_company_id": 1, "courier_name": "Mock Courier"}]}})
    monkeypatch.setattr(ShiprocketService, "get_order_details", lambda *a, **k: {"data": {"status": "DELIVERED"}})
    monkeypatch.setattr(ShiprocketService, "generate_label", lambda *a, **k: {"status": 200, "label_url": "mock_url"})
    monkeypatch.setattr(ShiprocketService, "generate_manifest", lambda *a, **k: {"status": 200, "manifest_url": "mock_url"})

    # Razorpay Mocks
    def mock_fetch_payment(pid, *a, **k):
        # Infer amount based on payment ID specific test context
        amount = 250000 if "123456" in pid else 150000
        return {"id": pid, "amount": amount, "status": "captured"}

    monkeypatch.setattr(RazorpayService, "verify_webhook_signature", lambda body, sig: not (sig or "").startswith("invalid"))
    monkeypatch.setattr(RazorpayService, "verify_payment_signature", lambda *a, **k: not k.get("razorpay_signature", a[2] if len(a)>2 else "").startswith("invalid"))
    monkeypatch.setattr(RazorpayService, "fetch_payment", mock_fetch_payment)
    monkeypatch.setattr(RazorpayService, "create_order", lambda *a, **k: {"id": f"order_{k.get('receipt', 'mock')}"})
    monkeypatch.setattr(RazorpayService, "capture_payment", lambda *a, **k: {"status": "captured"})
