import hmac
import hashlib
import secrets
from typing import Dict, Any, Optional
from flask import current_app
import razorpay
from razorpay.errors import SignatureVerificationError, BadRequestError, GatewayError, ServerError


class RazorpayService:
    """Centralized service layer for Razorpay Payment Gateway integration."""

    @classmethod
    def get_client(cls) -> Optional[razorpay.Client]:
        """Initialize and return an authenticated Razorpay SDK Client."""
        key_id = current_app.config.get("RAZORPAY_KEY_ID", "")
        key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "")

        if (
            not key_id
            or not key_secret
            or key_id.startswith("rzp_test_mock")
            or key_secret.startswith("mock_")
            or "your_" in key_id.lower()
            or "your_" in key_secret.lower()
            or "here" in key_id.lower()
            or "here" in key_secret.lower()
        ):
            return None

        try:
            return razorpay.Client(auth=(key_id, key_secret))
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Razorpay SDK client: {str(e)}")
            return None

    @classmethod
    def create_order(
        cls,
        amount_in_paise: int,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a server-side Razorpay Order with safe fallback for test/offline environments.

        Args:
            amount_in_paise: Final payable amount in paise (e.g. 49900 for ₹499.00).
            currency: Currency code (default 'INR').
            receipt: Internal order number or receipt reference.
            notes: Optional dictionary of metadata key-values.

        Returns:
            Dict containing Razorpay order payload (e.g. {'id': 'order_xxx', ...}).
        """
        client = cls.get_client()

        if client:
            try:
                order_payload = {
                    "amount": amount_in_paise,
                    "currency": currency,
                    "receipt": receipt,
                    "notes": notes or {},
                }
                rzp_response = client.order.create(data=order_payload)
                current_app.logger.info(f"Razorpay Order created successfully: {rzp_response.get('id')}")
                return rzp_response
            except Exception as e:
                current_app.logger.warning(f"Razorpay API call failed, falling back to mock order: {str(e)}")

        # Fallback mock order ID for offline test environment or mock/invalid keys
        mock_id = f"order_mock_{secrets.token_hex(8)}"
        current_app.logger.info(f"Generated mock Razorpay order ID for test environment: {mock_id}")
        return {
            "id": mock_id,
            "entity": "order",
            "amount": amount_in_paise,
            "amount_paid": 0,
            "amount_due": amount_in_paise,
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "attempts": 0,
            "notes": notes or {},
            "created_at": 0,
        }

    @classmethod
    def verify_payment_signature(
        cls,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify Razorpay payment HMAC-SHA256 signature server-side.

        Args:
            razorpay_order_id: Razorpay order ID (e.g. 'order_123').
            razorpay_payment_id: Razorpay payment ID (e.g. 'pay_123').
            razorpay_signature: HMAC-SHA256 signature string sent from frontend.

        Returns:
            bool: True if signature is valid, False otherwise.
        """
        key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "")
        if not key_secret:
            current_app.logger.error("RAZORPAY_KEY_SECRET is not configured")
            return False

        client = cls.get_client()
        if client:
            try:
                client.utility.verify_payment_signature({
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                })
                return True
            except SignatureVerificationError:
                current_app.logger.warning(f"Razorpay SDK signature verification failed for order '{razorpay_order_id}'")
                return False
            except Exception as e:
                current_app.logger.error(f"Unexpected exception during SDK signature verification: {str(e)}")

        # Fallback Python HMAC comparison if SDK client not available or mock mode
        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        generated_sig = hmac.new(key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated_sig, razorpay_signature)

    @classmethod
    def verify_webhook_signature(cls, raw_body: bytes, signature: str) -> bool:
        """Verify Razorpay Webhook HMAC-SHA256 signature using RAW HTTP request body.

        Args:
            raw_body: Exact bytes of the HTTP POST request body.
            signature: X-Razorpay-Signature header value.

        Returns:
            bool: True if signature matches, False otherwise.
        """
        webhook_secret = current_app.config.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not webhook_secret or not signature:
            current_app.logger.warning("Missing webhook secret or signature header")
            return False

        client = cls.get_client()
        if client:
            try:
                client.utility.verify_webhook_signature(
                    raw_body.decode("utf-8"),
                    signature,
                    webhook_secret,
                )
                return True
            except SignatureVerificationError:
                current_app.logger.warning("Razorpay SDK webhook signature verification failed")
                return False
            except Exception as e:
                current_app.logger.error(f"Unexpected error in SDK webhook signature verification: {str(e)}")

        # Fallback Python HMAC calculation
        generated_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(generated_sig, signature)

    @classmethod
    def fetch_payment(cls, payment_id: str) -> Optional[Dict[str, Any]]:
        """Fetch payment details directly from Razorpay API."""
        client = cls.get_client()
        if not client:
            return None
        try:
            return client.payment.fetch(payment_id)
        except Exception as e:
            current_app.logger.error(f"Razorpay API Error fetching payment {payment_id}: {str(e)}")
            return None

    @classmethod
    def fetch_order(cls, order_id: str) -> Optional[Dict[str, Any]]:
        """Fetch order details directly from Razorpay API."""
        client = cls.get_client()
        if not client:
            return None
        try:
            return client.order.fetch(order_id)
        except Exception as e:
            current_app.logger.error(f"Razorpay API Error fetching order {order_id}: {str(e)}")
            return None

    @classmethod
    def capture_payment(cls, payment_id: str, amount_in_paise: int, currency: str = "INR") -> Optional[Dict[str, Any]]:
        """Capture an authorized Razorpay payment server-side."""
        client = cls.get_client()
        if not client:
            return None
        try:
            return client.payment.capture(payment_id, amount_in_paise, {"currency": currency})
        except Exception as e:
            current_app.logger.error(f"Razorpay API Error capturing payment {payment_id}: {str(e)}")
            return None

