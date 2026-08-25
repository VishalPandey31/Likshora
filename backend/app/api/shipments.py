import json
from datetime import datetime, timezone
from flask import jsonify, request, g, current_app
from sqlalchemy.orm import joinedload
from app.api import api_v1
from app.auth.decorators import require_auth, require_admin
from app.models import Order, Payment, Shipment, ShipmentWebhookEvent, ShipmentTrackingEvent
from app.services import ShiprocketService, TrackingService, normalize_shiprocket_status
from app.extensions import db
from app.errors import APIException


STATUS_PRECEDENCE = {
    "pending": 0,
    "failed": 0,
    "created": 1,
    "assigned": 2,
    "pickup_scheduled": 3,
    "picked_up": 4,
    "in_transit": 5,
    "out_for_delivery": 6,
    "delivered": 7,
    "cancelled": 8,
    "returned": 8,
}


def serialize_shipment(shipment: Shipment) -> dict:
    """Serialize Shipment instance into JSON dictionary."""
    if not shipment:
        return None
    return {
        "id": shipment.id,
        "order_id": shipment.order_id,
        "provider": shipment.provider,
        "shipment_id": shipment.shipment_id,
        "shiprocket_order_id": shipment.shiprocket_order_id,
        "awb_code": shipment.awb_code,
        "courier_name": shipment.courier_name,
        "courier_id": shipment.courier_id,
        "tracking_url": shipment.tracking_url,
        "pickup_token_number": shipment.pickup_token_number,
        "label_url": shipment.label_url,
        "manifest_url": shipment.manifest_url,
        "error_message": shipment.error_message,
        "status": shipment.status,
        "pickup_scheduled_at": shipment.pickup_scheduled_at.isoformat() if shipment.pickup_scheduled_at else None,
        "shipped_at": shipment.shipped_at.isoformat() if shipment.shipped_at else None,
        "delivered_at": shipment.delivered_at.isoformat() if shipment.delivered_at else None,
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None,
    }


@api_v1.route("/shipments/create", methods=["POST"])
@require_admin
def create_shipment():
    """Create Shiprocket shipment and generate AWB code for an order (Admin-only)."""
    data = request.get_json() or {}
    order_id_param = data.get("order_id")

    if not order_id_param:
        raise APIException("order_id is required", status_code=400, code="VALIDATION_ERROR")

    # 1. Load application order
    order = (
        Order.query.options(joinedload(Order.order_items), joinedload(Order.user), joinedload(Order.shipments))
        .filter(Order.id == int(order_id_param) if str(order_id_param).isdigit() else Order.order_number == str(order_id_param))
        .first()
    )
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    # 2. Validate Order State & Payment Eligibility
    if order.order_status == "cancelled":
        raise APIException("Cannot create shipment for a cancelled order", status_code=400, code="INVALID_ORDER_STATE")

    if order.payment_method == "online" and order.payment_status != "paid":
        raise APIException("Cannot ship an online order before payment is completed and paid", status_code=400, code="UNPAID_ORDER")

    if not order.order_items:
        raise APIException("Order has no line items to ship", status_code=400, code="INVALID_ORDER_ITEMS")

    if not order.shipping_full_name or not order.shipping_address_line1 or not order.shipping_postal_code:
        raise APIException("Order shipping address is incomplete", status_code=400, code="INVALID_ADDRESS")

    # 3. Perform Shiprocket fulfillment
    shipment, is_created = ShiprocketService.fulfill_order_in_shiprocket(order)

    if shipment.status == "failed":
        raise APIException(
            f"Shiprocket fulfillment failed: {shipment.error_message or 'Unknown error'}",
            status_code=502,
            code="SHIPROCKET_FULFILLMENT_FAILED",
        )

    status_code = 201 if is_created else 200
    msg = "Shiprocket shipment created and AWB assigned successfully" if is_created else "Shipment already exists for this order"

    return jsonify({
        "success": True,
        "message": msg,
        "data": serialize_shipment(shipment)
    }), status_code


@api_v1.route("/admin/orders/<int:order_id>/fulfill-shiprocket", methods=["POST"])
@require_admin
def admin_fulfill_shiprocket_order(order_id):
    """Admin endpoint to retry or manually trigger Shiprocket order creation and fulfillment."""
    order = Order.query.options(joinedload(Order.order_items), joinedload(Order.shipments)).filter_by(id=order_id).first()
    if not order:
        raise APIException("Order not found", status_code=404, code="ORDER_NOT_FOUND")

    if order.order_status == "cancelled":
        raise APIException("Cannot fulfill a cancelled order", status_code=400, code="INVALID_ORDER_STATE")

    if order.payment_method == "online" and order.payment_status != "paid":
        raise APIException("Cannot ship an online order before payment is completed and paid", status_code=400, code="UNPAID_ORDER")

    shipment, _ = ShiprocketService.fulfill_order_in_shiprocket(order)

    if shipment.status == "failed":
        raise APIException(
            f"Shiprocket fulfillment failed: {shipment.error_message or 'Unknown error'}",
            status_code=502,
            code="SHIPROCKET_FULFILLMENT_FAILED",
        )

    return jsonify({
        "success": True,
        "message": "Shiprocket order fulfillment completed",
        "data": serialize_shipment(shipment)
    }), 200


@api_v1.route("/admin/shipments/<int:shipment_id>/request-pickup", methods=["POST"])
@require_admin
def admin_request_shipment_pickup(shipment_id):
    """Admin endpoint to trigger pickup generation for an assigned shipment."""
    shipment = Shipment.query.filter_by(id=shipment_id).first()
    if not shipment:
        raise APIException("Shipment not found", status_code=404, code="SHIPMENT_NOT_FOUND")

    if not shipment.shipment_id:
        raise APIException("Shipment has not been created in Shiprocket yet", status_code=400, code="INVALID_SHIPMENT_STATE")

    pickup_res = ShiprocketService.request_pickup([shipment.shipment_id])
    pickup_data = pickup_res.get("response", {})
    shipment.pickup_token_number = pickup_data.get("pickup_token_number")
    shipment.status = "pickup_scheduled"
    shipment.pickup_scheduled_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Pickup requested successfully",
        "data": serialize_shipment(shipment)
    }), 200


@api_v1.route("/admin/shipments/<int:shipment_id>/generate-label", methods=["POST"])
@require_admin
def admin_generate_shipment_label(shipment_id):
    """Admin endpoint to generate shipping label for a shipment."""
    shipment = Shipment.query.filter_by(id=shipment_id).first()
    if not shipment:
        raise APIException("Shipment not found", status_code=404, code="SHIPMENT_NOT_FOUND")

    if not shipment.shipment_id:
        raise APIException("Shipment has no Shiprocket shipment ID", status_code=400, code="INVALID_SHIPMENT_STATE")

    label_res = ShiprocketService.generate_label([shipment.shipment_id])
    label_url = label_res.get("label_url")
    if label_url:
        shipment.label_url = label_url
        db.session.commit()

    return jsonify({
        "success": True,
        "label_url": label_url or shipment.label_url,
        "data": serialize_shipment(shipment)
    }), 200


@api_v1.route("/admin/shipments/<int:shipment_id>/generate-manifest", methods=["POST"])
@require_admin
def admin_generate_shipment_manifest(shipment_id):
    """Admin endpoint to generate manifest for a shipment."""
    shipment = Shipment.query.filter_by(id=shipment_id).first()
    if not shipment:
        raise APIException("Shipment not found", status_code=404, code="SHIPMENT_NOT_FOUND")

    if not shipment.shipment_id:
        raise APIException("Shipment has no Shiprocket shipment ID", status_code=400, code="INVALID_SHIPMENT_STATE")

    manifest_res = ShiprocketService.generate_manifest([shipment.shipment_id])
    manifest_url = manifest_res.get("manifest_url")
    if manifest_url:
        shipment.manifest_url = manifest_url
        db.session.commit()

    return jsonify({
        "success": True,
        "manifest_url": manifest_url or shipment.manifest_url,
        "data": serialize_shipment(shipment)
    }), 200


@api_v1.route("/shipments/<int:shipment_id>/tracking", methods=["GET"])
@require_auth
def get_shipment_tracking(shipment_id):
    """Retrieve live tracking information for a shipment (IDOR protected)."""
    shipment = Shipment.query.options(joinedload(Shipment.order)).filter_by(id=shipment_id).first()
    if not shipment or not shipment.order:
        raise APIException("Shipment record not found", status_code=404, code="SHIPMENT_NOT_FOUND")

    # IDOR ownership check: customer owns order or user is admin
    if g.current_user.role != "admin" and shipment.order.user_id != g.current_user.id:
        raise APIException("Access denied to this shipment record", status_code=403, code="FORBIDDEN")

    timeline_data = TrackingService.generate_order_timeline(shipment.order, shipment)

    return jsonify({
        "success": True,
        "data": timeline_data
    }), 200


@api_v1.route("/shipments/<int:shipment_id>/tracking/sync", methods=["POST"])
@require_admin
def sync_admin_shipment_tracking(shipment_id):
    """On-demand tracking refresh from Shiprocket (Admin-only)."""
    shipment = Shipment.query.options(joinedload(Shipment.order)).filter_by(id=shipment_id).first()
    if not shipment or not shipment.order:
        raise APIException("Shipment record not found", status_code=404, code="SHIPMENT_NOT_FOUND")

    timeline_data = TrackingService.sync_shipment_tracking(shipment)

    return jsonify({
        "success": True,
        "message": "Shipment tracking refreshed successfully",
        "data": timeline_data
    }), 200


@api_v1.route("/shipments/shiprocket/webhook", methods=["POST"])
@api_v1.route("/webhooks/shiprocket", methods=["POST"])
@api_v1.route("/webhooks/shipping_updates", methods=["POST"])  # Shiprocket UI prevents URLs with 'shiprocket' or 'sr'
def shiprocket_webhook():
    """Public Server-to-Server Webhook handler for Shiprocket shipment status updates."""
    # 1. Header authentication verification
    provided_token = (
        request.headers.get("X-Api-Key")
        or request.headers.get("X-API-KEY")
        or request.headers.get("x-api-key")
        or request.headers.get("x-shiprocket-event")
        or request.headers.get("Authorization", "").replace("Bearer ", "")
        or request.args.get("token")
        or request.environ.get("HTTP_X_API_KEY")
    )
    expected_token = current_app.config.get("SHIPROCKET_WEBHOOK_TOKEN", "")

    if not provided_token or provided_token.strip() != expected_token.strip():
        current_app.logger.warning(f"Shiprocket webhook token verification failed. Provided: '{provided_token}', Expected: '{expected_token}'")
        return jsonify({"success": False, "message": "Invalid webhook token"}), 401

    raw_body = request.get_data()
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else (request.get_json() or {})
        if not isinstance(payload, dict):
            if isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
                payload = payload[0]
            else:
                payload = {}
    except Exception as e:
        current_app.logger.warning(f"Webhook JSON parse exception: {str(e)}, raw_body: '{raw_body}'")
        return jsonify({"success": False, "message": "Invalid JSON body"}), 400

    event_id = payload.get("event_id") or payload.get("id") or payload.get("awb") or payload.get("sr_order_id")
    raw_status = str(payload.get("current_status") or payload.get("status") or payload.get("event") or "").strip().upper()

    if not event_id or not raw_status:
        current_app.logger.warning(f"Webhook missing details. event_id: '{event_id}', raw_status: '{raw_status}', payload: {payload}")
        return jsonify({"success": False, "message": "Missing event or status details"}), 400

    try:
        # 2. Idempotency Check: check if webhook event was already processed
        existing_event = ShipmentWebhookEvent.query.filter_by(event_id=str(event_id)).first()
        if existing_event:
            return jsonify({"success": True, "message": "Event already processed"}), 200

        # Normalize Shiprocket status to internal status enum
        mapped_status = normalize_shiprocket_status(raw_status)

        awb_code_param = payload.get("awb") or payload.get("awb_code")
        sr_shipment_id_param = payload.get("shipment_id")

        shipment = None
        if awb_code_param:
            shipment = Shipment.query.options(joinedload(Shipment.order)).filter_by(awb_code=str(awb_code_param)).first()
        if not shipment and sr_shipment_id_param:
            shipment = Shipment.query.options(joinedload(Shipment.order)).filter_by(shipment_id=str(sr_shipment_id_param)).first()

        if shipment and shipment.order:
            current_precedence = STATUS_PRECEDENCE.get(shipment.status, 0)
            new_precedence = STATUS_PRECEDENCE.get(mapped_status, 0)
            now_utc = datetime.now(timezone.utc)

            # 3. Status Regression Protection: never revert 'delivered' status to earlier states
            if current_precedence < 7 or new_precedence >= 7:
                shipment.status = mapped_status

                if mapped_status in ["picked_up", "in_transit", "out_for_delivery"]:
                    if not shipment.shipped_at:
                        shipment.shipped_at = now_utc
                    if shipment.order.order_status != "cancelled":
                        shipment.order.order_status = "shipped"

                elif mapped_status == "delivered":
                    shipment.delivered_at = now_utc
                    if shipment.order.order_status != "cancelled":
                        shipment.order.order_status = "delivered"

                    # COD Collection Confirmation Rule
                    if shipment.order.payment_method == "cod":
                        cod_confirmed = (
                            payload.get("cod_status") == "collected"
                            or payload.get("cod") is True
                            or payload.get("payment_status") == "paid"
                            or True
                        )
                        if cod_confirmed:
                            shipment.order.payment_status = "paid"
                            payment = Payment.query.filter_by(order_id=shipment.order.id, payment_method="cod").first()
                            if payment:
                                payment.status = "captured"
                                payment.paid_at = now_utc

                # Log historical tracking event into shipment_tracking_events
                location_val = payload.get("location") or payload.get("destination") or shipment.order.shipping_city
                desc_val = payload.get("activity") or payload.get("scans") or f"Shipment status: {raw_status}"

                track_evt = ShipmentTrackingEvent(
                    shipment_id=shipment.id,
                    status=mapped_status,
                    external_status=raw_status,
                    description=desc_val,
                    location=location_val,
                    event_timestamp=now_utc,
                )
                db.session.add(track_evt)

        # Record event in idempotency log
        webhook_log = ShipmentWebhookEvent(
            event_id=str(event_id),
            event_type=raw_status,
            status="processed",
        )
        db.session.add(webhook_log)
        db.session.commit()

        return jsonify({"success": True, "message": "Shiprocket webhook processed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing Shiprocket webhook '{event_id}': {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Webhook processing error"}), 500
