from datetime import datetime, timezone
from flask import current_app
from sqlalchemy.orm import joinedload
from app.models import Order, Shipment, ShipmentTrackingEvent, Payment
from app.services.shiprocket_service import ShiprocketService
from app.extensions import db


STATUS_STAGE_ORDER = {
    "order_placed": 0,
    "confirmed": 1,
    "processing": 2,
    "shipped": 3,
    "out_for_delivery": 4,
    "delivered": 5,
    "cancelled": 99,
    "returned": 99,
}

STATUS_PRECEDENCE = {
    "pending": 0,
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


def normalize_shiprocket_status(raw_status: str) -> str:
    """Normalize raw Shiprocket status into internal status enum."""
    if not raw_status:
        return "processing"
    upper = str(raw_status).strip().upper()
    if "DELIVERED" in upper:
        return "delivered"
    elif "OUT FOR DELIVERY" in upper:
        return "out_for_delivery"
    elif "RETURN" in upper or "RTO" in upper:
        return "returned"
    elif "CANCEL" in upper:
        return "cancelled"
    elif "PICKED" in upper or "OUT FOR PICKUP" in upper:
        return "picked_up"
    elif "IN TRANSIT" in upper or "SHIPPED" in upper or "DISPATCH" in upper:
        return "in_transit"
    elif "READY TO SHIP" in upper or "ASSIGN" in upper:
        return "processing"
    elif "NEW" in upper:
        return "confirmed"
    return "processing"


class TrackingService:
    """Service handling tracking normalization, database event logging, and timeline generation."""

    @classmethod
    def sync_shipment_tracking(cls, shipment: Shipment) -> dict:
        """Sync live tracking data from Shiprocket and update local database events transactionally."""
        if not shipment or not shipment.awb_code:
            return cls.generate_order_timeline(shipment.order if shipment else None, shipment)

        try:
            # 1. Fetch live tracking data from Shiprocket API
            res = ShiprocketService.track_shipment(shipment.awb_code)
            tracking_data = res.get("tracking_data", {})
            shipment_track = tracking_data.get("shipment_track", [])

            now_utc = datetime.now(timezone.utc)

            for event_info in shipment_track:
                ext_status = str(event_info.get("current_status") or event_info.get("status") or "").strip()
                if not ext_status:
                    continue

                norm_status = normalize_shiprocket_status(ext_status)

                # Parse event timestamp if available, fallback to UTC now
                date_str = event_info.get("pickup_date") or event_info.get("delivered_date") or event_info.get("date")
                event_ts = now_utc
                if date_str:
                    try:
                        event_ts = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                location = event_info.get("location") or event_info.get("destination")
                description = event_info.get("activity") or f"Shipment status updated to {ext_status}"

                # Deduplicate tracking event insertion
                existing_evt = ShipmentTrackingEvent.query.filter_by(
                    shipment_id=shipment.id,
                    external_status=ext_status,
                    event_timestamp=event_ts
                ).first()

                if not existing_evt:
                    evt = ShipmentTrackingEvent(
                        shipment_id=shipment.id,
                        status=norm_status,
                        external_status=ext_status,
                        description=description,
                        location=location,
                        event_timestamp=event_ts,
                    )
                    db.session.add(evt)

                # Update Shipment & Order status (with Status Regression Protection)
                curr_prec = STATUS_PRECEDENCE.get(shipment.status, 0)
                new_prec = STATUS_PRECEDENCE.get(norm_status, 0)

                if curr_prec < 7 or new_prec >= 7:
                    shipment.status = norm_status

                    if norm_status in ["picked_up", "in_transit", "out_for_delivery"]:
                        if not shipment.shipped_at:
                            shipment.shipped_at = event_ts
                        if shipment.order and shipment.order.order_status != "cancelled":
                            shipment.order.order_status = "shipped"

                    elif norm_status == "delivered":
                        shipment.delivered_at = event_ts
                        if shipment.order and shipment.order.order_status != "cancelled":
                            shipment.order.order_status = "delivered"

                            # COD Payment confirmation upon delivery
                            if shipment.order.payment_method == "cod" and shipment.order.payment_status != "paid":
                                shipment.order.payment_status = "paid"
                                payment = Payment.query.filter_by(order_id=shipment.order.id, payment_method="cod").first()
                                if payment:
                                    payment.status = "captured"
                                    payment.paid_at = event_ts

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(f"Live tracking sync exception for shipment {shipment.id}: {str(e)}")

        return cls.generate_order_timeline(shipment.order, shipment)

    @classmethod
    def generate_order_timeline(cls, order: Order, shipment: Shipment = None) -> dict:
        """Generate a clean, normalized, frontend-ready tracking timeline array."""
        if not order:
            return {"timeline": [], "current_status": "unknown"}

        active_shipment = shipment
        if not active_shipment and hasattr(order, "shipments") and order.shipments:
            active_shipment = next((s for s in order.shipments if s.status != "cancelled"), None)

        order_status = order.order_status
        shipment_status = active_shipment.status if active_shipment else "pending"

        # Determine current timeline stage
        if order_status == "cancelled":
            curr_stage = "cancelled"
        elif order_status == "delivered" or shipment_status == "delivered":
            curr_stage = "delivered"
        elif shipment_status == "out_for_delivery":
            curr_stage = "out_for_delivery"
        elif order_status == "shipped" or shipment_status in ["picked_up", "in_transit"]:
            curr_stage = "shipped"
        elif order_status == "processing" or shipment_status in ["assigned", "created"]:
            curr_stage = "processing"
        elif order_status in ["confirmed", "pending"]:
            curr_stage = "confirmed" if order_status == "confirmed" else "order_placed"
        else:
            curr_stage = "order_placed"

        curr_stage_idx = STATUS_STAGE_ORDER.get(curr_stage, 0)

        # Collect event timestamps
        event_timestamps = {
            "order_placed": order.created_at.isoformat() if order.created_at else None,
            "confirmed": order.created_at.isoformat() if order.created_at else None,
            "processing": None,
            "shipped": None,
            "out_for_delivery": None,
            "delivered": None,
        }

        if active_shipment:
            if active_shipment.created_at:
                event_timestamps["processing"] = active_shipment.created_at.isoformat()
            if active_shipment.shipped_at:
                event_timestamps["shipped"] = active_shipment.shipped_at.isoformat()
            if active_shipment.delivered_at:
                event_timestamps["delivered"] = active_shipment.delivered_at.isoformat()

            # Inspect stored historical tracking events
            if hasattr(active_shipment, "tracking_events") and active_shipment.tracking_events:
                for evt in active_shipment.tracking_events:
                    ts_str = evt.event_timestamp.isoformat() if evt.event_timestamp else None
                    if evt.status == "out_for_delivery" and not event_timestamps["out_for_delivery"]:
                        event_timestamps["out_for_delivery"] = ts_str
                    elif evt.status in ["shipped", "in_transit", "picked_up"] and not event_timestamps["shipped"]:
                        event_timestamps["shipped"] = ts_str
                    elif evt.status == "delivered" and not event_timestamps["delivered"]:
                        event_timestamps["delivered"] = ts_str

        # Standard 6-step customer-facing tracking timeline
        stages = [
            ("order_placed", "Order Placed"),
            ("confirmed", "Confirmed"),
            ("processing", "Processing"),
            ("shipped", "Shipped"),
            ("out_for_delivery", "Out for Delivery"),
            ("delivered", "Delivered"),
        ]

        timeline = []
        if order_status == "cancelled":
            for stage_code, label in stages:
                is_completed = (stage_code == "order_placed")
                timeline.append({
                    "status": stage_code,
                    "label": label,
                    "completed": is_completed,
                    "current": False,
                    "timestamp": event_timestamps.get(stage_code) if is_completed else None,
                })
            timeline.append({
                "status": "cancelled",
                "label": "Order Cancelled",
                "completed": True,
                "current": True,
                "timestamp": order.updated_at.isoformat() if order.updated_at else None,
            })
        else:
            for stage_code, label in stages:
                stage_idx = STATUS_STAGE_ORDER.get(stage_code, 0)
                is_completed = stage_idx <= curr_stage_idx
                is_current = stage_code == curr_stage

                # Only include timestamp if stage is completed and timestamp exists
                ts = event_timestamps.get(stage_code) if is_completed else None

                timeline.append({
                    "status": stage_code,
                    "label": label,
                    "completed": is_completed,
                    "current": is_current,
                    "timestamp": ts,
                })

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "current_stage": curr_stage,
            "shipment": {
                "id": active_shipment.id if active_shipment else None,
                "status": active_shipment.status if active_shipment else None,
                "awb_code": active_shipment.awb_code if active_shipment else None,
                "courier_name": active_shipment.courier_name if active_shipment else None,
                "tracking_url": active_shipment.tracking_url if active_shipment else None,
            } if active_shipment else None,
            "timeline": timeline,
        }
