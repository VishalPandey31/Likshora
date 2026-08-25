import hmac
import hashlib
from typing import Dict, Any, Optional

from flask import current_app
import razorpay
from razorpay.errors import SignatureVerificationError

from app.errors import APIException


class RazorpayService:
    """Production-grade service layer for Razorpay Payment Gateway integration.

    All methods strictly use the live Razorpay SDK — no mock/fallback behaviour.
    Credentials must be configured in .env (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET).
    """

    _client: Optional[razorpay.Client] = None

    # ------------------------------------------------------------------ client
    @classmethod
    def get_client(cls) -> razorpay.Client:
        """Initialize and return an authenticated Razorpay SDK Client.

        Raises APIException if credentials are missing or SDK initialization fails.
        """
        if cls._client is not None:
            return cls._client

        key_id = current_app.config.get("RAZORPAY_KEY_ID", "")
        key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "")

        if not key_id or not key_secret:
            raise APIException(
                "Razorpay credentials not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET)",
                status_code=500,
                code="RAZORPAY_CONFIG_MISSING",
            )

        try:
            cls._client = razorpay.Client(auth=(key_id, key_secret))
            current_app.logger.info("Razorpay SDK client initialized successfully.")
            return cls._client
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Razorpay SDK client: {e}")
            raise APIException(
                "Failed to initialize Razorpay payment gateway",
                status_code=502,
                code="RAZORPAY_INIT_FAILED",
            )

    # ------------------------------------------------------------------ create order
    @classmethod
    def create_order(
        cls,
        amount_in_paise: int,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a server-side Razorpay Order.

        Args:
            amount_in_paise: Final payable amount in paise (e.g. 49900 for ₹499.00).
            currency: Currency code (default 'INR').
            receipt: Internal order number or receipt reference.
            notes: Optional dictionary of metadata key-values.

        Returns:
            Dict containing Razorpay order payload (e.g. {'id': 'order_xxx', ...}).
        """
        client = cls.get_client()

        try:
            order_payload = {
                "amount": amount_in_paise,
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
            }
            rzp_response = client.order.create(data=order_payload)
            current_app.logger.info(f"Razorpay Order created: {rzp_response.get('id')}")
            return rzp_response
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Razorpay create order failed: {e}")
            raise APIException(
                "Failed to create Razorpay order",
                status_code=502,
                code="RAZORPAY_ORDER_FAILED",
            )

    # ------------------------------------------------------------------ verify payment
    @classmethod
    def verify_payment_signature(
        cls,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify Razorpay payment HMAC-SHA256 signature server-side.

        Returns True if valid, False otherwise.
        """
        key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "")
        if not key_secret:
            current_app.logger.error("RAZORPAY_KEY_SECRET is not configured")
            return False

        client = cls.get_client()
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except SignatureVerificationError:
            current_app.logger.warning(
                f"Razorpay payment signature verification failed for order '{razorpay_order_id}'"
            )
            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error during payment signature verification: {e}")
            # Fallback: manual HMAC comparison
            message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
            generated_sig = hmac.new(key_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated_sig, razorpay_signature)

    # ------------------------------------------------------------------ verify webhook
    @classmethod
    def verify_webhook_signature(cls, raw_body: bytes, signature: str) -> bool:
        """Verify Razorpay Webhook HMAC-SHA256 signature using raw HTTP request body.

        Returns True if valid, False otherwise.
        """
        webhook_secret = current_app.config.get("RAZORPAY_WEBHOOK_SECRET", "")
        if not webhook_secret or not signature:
            current_app.logger.warning("Missing RAZORPAY_WEBHOOK_SECRET or X-Razorpay-Signature header")
            return False

        client = cls.get_client()
        try:
            client.utility.verify_webhook_signature(
                raw_body.decode("utf-8"),
                signature,
                webhook_secret,
            )
            return True
        except SignatureVerificationError:
            current_app.logger.warning("Razorpay webhook signature verification failed")
            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error in webhook signature verification: {e}")
            # Fallback: manual HMAC calculation
            generated_sig = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            return hmac.compare_digest(generated_sig, signature)

    # ------------------------------------------------------------------ fetch payment
    @classmethod
    def fetch_payment(cls, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details directly from Razorpay API."""
        client = cls.get_client()
        try:
            return client.payment.fetch(payment_id)
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Razorpay fetch payment {payment_id} failed: {e}")
            raise APIException(
                f"Failed to fetch payment details from Razorpay",
                status_code=502,
                code="RAZORPAY_FETCH_FAILED",
            )

    # ------------------------------------------------------------------ fetch order
    @classmethod
    def fetch_order(cls, order_id: str) -> Dict[str, Any]:
        """Fetch order details directly from Razorpay API."""
        client = cls.get_client()
        try:
            return client.order.fetch(order_id)
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Razorpay fetch order {order_id} failed: {e}")
            raise APIException(
                f"Failed to fetch order details from Razorpay",
                status_code=502,
                code="RAZORPAY_FETCH_FAILED",
            )

    # ------------------------------------------------------------------ capture payment
    @classmethod
    def capture_payment(cls, payment_id: str, amount_in_paise: int, currency: str = "INR") -> Dict[str, Any]:
        """Capture an authorized Razorpay payment server-side."""
        client = cls.get_client()
        try:
            result = client.payment.capture(payment_id, amount_in_paise, {"currency": currency})
            current_app.logger.info(f"Razorpay payment captured: {payment_id}")
            return result
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Razorpay capture payment {payment_id} failed: {e}")
            raise APIException(
                f"Failed to capture payment in Razorpay",
                status_code=502,
                code="RAZORPAY_CAPTURE_FAILED",
            )
