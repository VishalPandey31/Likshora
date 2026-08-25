import json
from datetime import datetime, timezone
from decimal import Decimal
from flask import jsonify, request, g, current_app
from sqlalchemy.orm import joinedload
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import Order, Payment, PaymentWebhookEvent
from app.services import RazorpayService, ShiprocketService
from app.extensions import db
from app.errors import APIException


def serialize_payment(payment: Payment) -> dict:
    """Serialize Payment instance into JSON dict."""
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "payment_method": payment.payment_method,
        "provider": payment.provider,
        "provider_order_id": payment.provider_order_id,
        "provider_payment_id": payment.provider_payment_id,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
    }


def verify_razorpay_hmac_signature(order_id: str, payment_id: str, signature: str, secret: str = None) -> bool:
    """Compute and verify Razorpay HMAC-SHA256 signature for payment verification."""
    return RazorpayService.verify_payment_signature(order_id, payment_id, signature)


def verify_razorpay_webhook_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
    """Compute and verify Razorpay Webhook HMAC-SHA256 signature using RAW request body."""
    return RazorpayService.verify_webhook_signature(raw_body, signature)


@api_v1.route("/payments/create-order", methods=["POST"])
@api_v1.route("/payments/razorpay/create-order", methods=["POST"])
@api_v1.route("/../payments/create-order", methods=["POST"])
@api_v1.route("/../payments/razorpay/create-order", methods=["POST"])
@require_auth
def create_razorpay_order():
    """Create server-side Razorpay Order for an application order."""
    data = request.get_json() or {}
    order_id_param = data.get("order_id")

    if not order_id_param:
        raise APIException("order_id is required", status_code=400, code="VALIDATION_ERROR")

    # 1. Load application order with ownership verification (IDOR protection)
    query = Order.query.filter(Order.user_id == g.current_user.id)
    if isinstance(order_id_param, int) or (isinstance(order_id_param, str) and str(order_id_param).isdigit()):
        order = query.filter(Order.id == int(order_id_param)).first()
    else:
        order = query.filter(Order.order_number == str(order_id_param)).first()

    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    # 2. Validate order state and eligibility
    if order.order_status in ["cancelled", "delivered"]:
        raise APIException(f"Cannot process payment for order in '{order.order_status}' status", status_code=400, code="INVALID_ORDER_STATE")

    if order.payment_method != "online":
        raise APIException("Razorpay payment is only supported for online payment method", status_code=400, code="INVALID_PAYMENT_METHOD")

    if order.payment_status == "paid":
        raise APIException("Order has already been paid", status_code=409, code="ALREADY_PAID")

    # 3. Server-side amount calculation: convert total amount to paise (Decimal safe)
    total_dec = Decimal(str(order.total_amount))
    amount_in_paise = int(total_dec * Decimal("100"))

    key_id = current_app.config.get("RAZORPAY_KEY_ID", "")
    currency = current_app.config.get("RAZORPAY_CURRENCY", "INR")

    # 4. Create Razorpay Order via central RazorpayService
    try:
        rzp_order_resp = RazorpayService.create_order(
            amount_in_paise=amount_in_paise,
            currency=currency,
            receipt=order.order_number,
            notes={"order_id": order.id, "order_number": order.order_number},
        )
        rzp_order_id = rzp_order_resp.get("id")
    except Exception as e:
        current_app.logger.error(f"Error creating Razorpay Order via service: {str(e)}")
        raise APIException("Failed to create Razorpay Order", status_code=500, code="RAZORPAY_ERROR")

    # 5. Create or update Payment record in local DB
    payment = Payment.query.filter_by(order_id=order.id, provider="razorpay").first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            payment_method="online",
            provider="razorpay",
            amount=total_dec,
            currency=currency,
            status="created",
            provider_order_id=rzp_order_id,
        )
        db.session.add(payment)
    else:
        payment.provider_order_id = rzp_order_id
        payment.amount = total_dec
        payment.currency = currency
        payment.status = "created"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Razorpay order created successfully",
        "order_id": order.id,
        "razorpay_order_id": rzp_order_id,
        "amount": amount_in_paise,
        "currency": currency,
        "key_id": key_id,
        "data": {
            "application_order_id": order.id,
            "order_number": order.order_number,
            "razorpay_order_id": rzp_order_id,
            "razorpay_key_id": key_id,
            "amount": amount_in_paise,
            "currency": currency,
        }
    }), 200


@api_v1.route("/payments/verify", methods=["POST"])
@api_v1.route("/payments/razorpay/verify", methods=["POST"])
@api_v1.route("/../payments/verify", methods=["POST"])
@api_v1.route("/../payments/razorpay/verify", methods=["POST"])
@require_auth
def verify_razorpay_payment():
    """Verify Razorpay payment signature, amount, gateway status, and update order status."""
    data = request.get_json() or {}
    rzp_order_id = (data.get("razorpay_order_id") or "").strip()
    rzp_payment_id = (data.get("razorpay_payment_id") or "").strip()
    rzp_signature = (data.get("razorpay_signature") or "").strip()
    req_order_id = data.get("order_id")

    if not rzp_order_id or not rzp_payment_id or not rzp_signature:
        raise APIException("razorpay_order_id, razorpay_payment_id, and razorpay_signature are required", status_code=400, code="VALIDATION_ERROR")

    # 1. Load payment record with IDOR ownership check
    payment = (
        Payment.query.options(joinedload(Payment.order))
        .filter(Payment.provider_order_id == rzp_order_id)
        .first()
    )
    if not payment or not payment.order or payment.order.user_id != g.current_user.id:
        raise APIException("Payment record not found or access denied", status_code=404, code="PAYMENT_NOT_FOUND")

    # 2. Customer & Order ownership verification: verify requested order matches payment record
    if req_order_id:
        req_order_str = str(req_order_id).strip()
        if str(payment.order_id) != req_order_str and payment.order.order_number != req_order_str:
            raise APIException("Order ID mismatch for payment verification", status_code=400, code="ORDER_MISMATCH")

    # 3. Idempotency check: return success if already captured
    if payment.status == "captured" and payment.order.payment_status == "paid":
        return jsonify({
            "success": True,
            "message": "Payment already verified and captured",
            "data": serialize_payment(payment)
        }), 200

    # 4. Verify HMAC-SHA256 signature via RazorpayService
    is_valid = RazorpayService.verify_payment_signature(rzp_order_id, rzp_payment_id, rzp_signature)
    if not is_valid:
        payment.status = "failed"
        payment.failure_reason = "Signature verification failed"
        payment.order.payment_status = "failed"
        db.session.commit()
        raise APIException("Invalid Razorpay payment signature", status_code=400, code="INVALID_PAYMENT_SIGNATURE")

    # 5. Fetch & Verify actual Razorpay payment status & amount from API
    expected_paise = int(Decimal(str(payment.order.total_amount)) * Decimal("100"))
    rzp_payment_details = RazorpayService.fetch_payment(rzp_payment_id)

    if rzp_payment_details:
        # Amount Verification
        actual_paise = rzp_payment_details.get("amount")
        if actual_paise is not None and actual_paise != expected_paise:
            payment.status = "failed"
            payment.failure_reason = f"Amount mismatch: expected {expected_paise}, got {actual_paise}"
            payment.order.payment_status = "failed"
            db.session.commit()
            raise APIException("Payment amount mismatch", status_code=400, code="AMOUNT_MISMATCH")

        # Payment Status Check
        rzp_status = rzp_payment_details.get("status")
        if rzp_status == "failed":
            payment.status = "failed"
            payment.failure_reason = rzp_payment_details.get("error_description", "Payment failed at gateway")
            payment.order.payment_status = "failed"
            db.session.commit()
            raise APIException("Payment failed at payment gateway", status_code=400, code="PAYMENT_FAILED")

        # Manual Capture if status is authorized
        if rzp_status == "authorized":
            try:
                RazorpayService.capture_payment(rzp_payment_id, expected_paise, payment.currency)
            except Exception as e_cap:
                current_app.logger.warning(f"Payment capture attempt for {rzp_payment_id} was unsuccessful: {e_cap}")

    # 6. Update Payment and Order statuses cleanly
    payment.status = "captured"
    payment.provider_payment_id = rzp_payment_id
    payment.razorpay_signature = rzp_signature
    payment.paid_at = datetime.now(timezone.utc)
    payment.order.payment_status = "paid"

    # Transition order status from 'pending' to 'confirmed' upon successful payment
    if payment.order.order_status == "pending":
        payment.order.order_status = "confirmed"

    db.session.commit()

    # Automatic Shiprocket Order Creation & Fulfillment for verified Prepaid orders
    try:
        ShiprocketService.fulfill_order_in_shiprocket(payment.order)
    except Exception as e_sr:
        current_app.logger.error(f"Automatic Shiprocket Prepaid fulfillment failed for order {payment.order.order_number}: {str(e_sr)}")

    return jsonify({
        "success": True,
        "message": "Payment verified and order marked as paid",
        "data": serialize_payment(payment)
    }), 200



def process_razorpay_webhook_logic():
    """Core transactional handler for Razorpay Webhooks using RAW HTTP request body."""
    raw_body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "").strip()

    # 1. Mandatory HMAC-SHA256 Signature Verification using RAW unparsed request body
    if not signature or not RazorpayService.verify_webhook_signature(raw_body, signature):
        current_app.logger.warning("Razorpay webhook signature verification failed")
        return jsonify({"success": False, "message": "Invalid webhook signature"}), 400

    # 2. Parse JSON ONLY AFTER signature verification succeeds
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    event_id = payload.get("event_id") or payload.get("id")
    event_type = payload.get("event")

    if not event_id or not event_type:
        return jsonify({"success": False, "message": "Missing event details"}), 400

    payment = None
    # 3. Transactional Webhook Processing & Idempotency
    try:
        # Check duplicate event in payment_webhook_events table
        existing_event = PaymentWebhookEvent.query.filter_by(event_id=str(event_id)).first()
        if existing_event:
            return jsonify({"success": True, "message": "Event already processed"}), 200

        # Handle supported event types
        if event_type in ["payment.captured", "payment.failed", "order.paid"]:
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            rzp_order_id = payment_data.get("order_id")
            rzp_payment_id = payment_data.get("id")

            if rzp_order_id or rzp_payment_id:
                payment = None
                if rzp_order_id:
                    payment = Payment.query.options(joinedload(Payment.order)).filter_by(provider_order_id=rzp_order_id).first()
                if not payment and rzp_payment_id:
                    payment = Payment.query.options(joinedload(Payment.order)).filter_by(provider_payment_id=rzp_payment_id).first()

                if payment and payment.order:
                    if event_type in ["payment.captured", "order.paid"]:
                        # State Protection: Never downgrade from 'captured'
                        if payment.status != "captured":
                            payment.status = "captured"
                            payment.provider_payment_id = rzp_payment_id or payment.provider_payment_id
                            payment.paid_at = datetime.now(timezone.utc)
                            payment.order.payment_status = "paid"
                            # Keep fulfillment order_status separate (do NOT change to shipped/delivered)
                            if payment.order.order_status == "pending":
                                payment.order.order_status = "confirmed"
                    elif event_type == "payment.failed":
                        # State Protection: Never downgrade captured payment
                        if payment.status != "captured":
                            payment.status = "failed"
                            payment.order.payment_status = "failed"
                            payment.failure_reason = payment_data.get("error_description", "Payment failed")
                else:
                    current_app.logger.info(f"Webhook event '{event_type}' received for unmapped order_id '{rzp_order_id}'")
        else:
            current_app.logger.info(f"Webhook received unsupported event_type '{event_type}', ignoring safely.")

        # Record event in idempotency table
        webhook_log = PaymentWebhookEvent(
            event_id=str(event_id),
            event_type=event_type,
            status="processed",
        )
        db.session.add(webhook_log)
        db.session.commit()

        if event_type in ["payment.captured", "order.paid"] and payment and payment.order:
            try:
                ShiprocketService.fulfill_order_in_shiprocket(payment.order)
            except Exception as e_sr:
                current_app.logger.error(f"Automatic Shiprocket Webhook fulfillment failed for order {payment.order.order_number}: {str(e_sr)}")

        return jsonify({"success": True}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing webhook event '{event_id}': {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Webhook processing error"}), 500


@api_v1.route("/payments/webhook", methods=["POST"])
@api_v1.route("/payments/razorpay/webhook", methods=["POST"])
@api_v1.route("/../payments/webhook", methods=["POST"])
@api_v1.route("/../payments/razorpay/webhook", methods=["POST"])
def razorpay_webhook():
    """Public Webhook endpoint for Razorpay payment notifications."""
    return process_razorpay_webhook_logic()


@api_v1.route("/payments/<int:payment_id>", methods=["GET"])
@require_auth
def get_payment_detail(payment_id):
    """Retrieve single payment transaction details (IDOR protected)."""
    payment = (
        Payment.query.options(joinedload(Payment.order))
        .filter(Payment.id == payment_id)
        .first()
    )
    if not payment or not payment.order or payment.order.user_id != g.current_user.id:
        raise APIException("Payment record not found", status_code=404, code="PAYMENT_NOT_FOUND")

    return jsonify({
        "success": True,
        "data": serialize_payment(payment)
    }), 200
