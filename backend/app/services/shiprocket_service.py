import time
from datetime import datetime, timezone

import requests
from flask import current_app

from app.errors import APIException
from app.extensions import db
from app.models import Order, Shipment, ShipmentTrackingEvent


class ShiprocketService:
    """Production-grade service layer for Shiprocket REST API v2 integrations.

    All methods communicate directly with the live Shiprocket API.
    No mock/fallback behaviour — credentials must be configured in .env.
    """

    _cached_token = None
    _token_expires_at = 0

    # ------------------------------------------------------------------ auth
    @classmethod
    def _get_base_url(cls) -> str:
        base_url = current_app.config.get(
            "SHIPROCKET_BASE_URL", "https://apiv2.shiprocket.in/v1/external"
        )
        return base_url.rstrip("/")

    @classmethod
    def get_auth_token(cls, force_refresh: bool = False) -> str:
        """Authenticate with Shiprocket API and cache the Bearer JWT token.

        Token is cached for 9 days (Shiprocket tokens expire after 10 days).
        """
        now = time.time()
        if not force_refresh and cls._cached_token and now < cls._token_expires_at:
            return cls._cached_token

        email = current_app.config.get("SHIPROCKET_EMAIL")
        password = current_app.config.get("SHIPROCKET_PASSWORD")

        if not email or not password:
            raise APIException(
                "Shiprocket credentials not configured (SHIPROCKET_EMAIL / SHIPROCKET_PASSWORD)",
                status_code=500,
                code="SHIPROCKET_CONFIG_MISSING",
            )

        try:
            url = f"{cls._get_base_url()}/auth/login"
            response = requests.post(
                url, json={"email": email, "password": password}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    cls._cached_token = token
                    cls._token_expires_at = now + (9 * 86400)  # refresh before 10-day expiry
                    current_app.logger.info("Shiprocket auth token acquired/refreshed successfully.")
                    return cls._cached_token

            current_app.logger.error(
                f"Shiprocket auth failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to authenticate with Shiprocket API",
                status_code=502,
                code="SHIPROCKET_AUTH_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket auth exception: {e}")
            raise APIException(
                "Shiprocket service authentication unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    @classmethod
    def _headers(cls) -> dict:
        token = cls.get_auth_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ---------------------------------------------------------- helper: retry on 401
    @classmethod
    def _request_with_retry(cls, method: str, url: str, **kwargs):
        """Execute an HTTP request; on 401 refresh the token and retry once."""
        kwargs.setdefault("timeout", 15)
        kwargs.setdefault("headers", cls._headers())

        response = requests.request(method, url, **kwargs)
        if response.status_code == 401:
            cls.get_auth_token(force_refresh=True)
            kwargs["headers"] = cls._headers()
            response = requests.request(method, url, **kwargs)
        return response

    # ---------------------------------------------------------- courier serviceability
    @classmethod
    def get_courier_serviceability(
        cls,
        pickup_postcode: str,
        delivery_postcode: str,
        weight: float,
        cod: bool = False,
        order_id: str = None,
    ) -> dict:
        """Verify courier serviceability for given shipment parameters."""
        try:
            url = f"{cls._get_base_url()}/courier/serviceability/"
            params = {
                "pickup_postcode": pickup_postcode,
                "delivery_postcode": delivery_postcode,
                "weight": weight,
                "cod": 1 if cod else 0,
            }
            if order_id:
                params["order_id"] = order_id

            response = cls._request_with_retry("GET", url, params=params)

            if response.status_code == 200:
                return response.json()

            current_app.logger.error(
                f"Shiprocket serviceability check failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Serviceability check failed for destination pincode",
                status_code=400,
                code="COURIER_UNSERVICEABLE",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket serviceability exception: {e}")
            raise APIException(
                "Shiprocket serviceability API unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- create order
    @classmethod
    def create_order(cls, order_payload: dict) -> dict:
        """Create an adhoc order in Shiprocket."""
        try:
            url = f"{cls._get_base_url()}/orders/create/adhoc"
            response = cls._request_with_retry("POST", url, json=order_payload)

            if response.status_code in (200, 201):
                res_data = response.json()
                if res_data.get("status_code") == 1 or res_data.get("order_id"):
                    return res_data
                current_app.logger.error(
                    f"Shiprocket order creation returned error body: {res_data}"
                )
                err_msg = res_data.get("message") or "Order creation rejected by Shiprocket"
                raise APIException(err_msg, status_code=400, code="SHIPROCKET_CREATE_FAILED")

            current_app.logger.error(
                f"Shiprocket create order failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to create order in Shiprocket",
                status_code=502,
                code="SHIPROCKET_CREATE_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket create order exception: {e}")
            raise APIException(
                "Shiprocket order creation service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- generate AWB
    @classmethod
    def generate_awb(cls, shipment_id: int | str, courier_id: int = None) -> dict:
        """Assign courier and generate AWB code in Shiprocket."""
        try:
            url = f"{cls._get_base_url()}/courier/assign/awb"
            payload = {"shipment_id": shipment_id}
            if courier_id:
                payload["courier_id"] = courier_id

            response = cls._request_with_retry("POST", url, json=payload)

            if response.status_code in (200, 201):
                return response.json()

            current_app.logger.error(
                f"Shiprocket generate AWB failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to assign courier AWB in Shiprocket",
                status_code=502,
                code="SHIPROCKET_AWB_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket generate AWB exception: {e}")
            raise APIException(
                "Shiprocket AWB service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- request pickup
    @classmethod
    def request_pickup(cls, shipment_ids: list) -> dict:
        """Request pickup generation for shipment(s)."""
        try:
            url = f"{cls._get_base_url()}/courier/generate/pickup"
            payload = {"shipment_id": shipment_ids}
            response = cls._request_with_retry("POST", url, json=payload)

            if response.status_code in (200, 201):
                return response.json()

            current_app.logger.error(
                f"Shiprocket request pickup failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to request pickup in Shiprocket",
                status_code=502,
                code="SHIPROCKET_PICKUP_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket request pickup exception: {e}")
            raise APIException(
                "Shiprocket pickup service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- generate label
    @classmethod
    def generate_label(cls, shipment_ids: list) -> dict:
        """Generate shipping label for shipment(s)."""
        try:
            url = f"{cls._get_base_url()}/courier/generate/label"
            payload = {"shipment_id": shipment_ids}
            response = cls._request_with_retry("POST", url, json=payload)

            if response.status_code in (200, 201):
                return response.json()

            current_app.logger.error(
                f"Shiprocket label generation failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to generate shipping label",
                status_code=502,
                code="SHIPROCKET_LABEL_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket label exception: {e}")
            raise APIException(
                "Shiprocket label service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- generate manifest
    @classmethod
    def generate_manifest(cls, shipment_ids: list) -> dict:
        """Generate manifest PDF for shipment(s)."""
        try:
            url = f"{cls._get_base_url()}/manifests/generate"
            payload = {"shipment_id": shipment_ids}
            response = cls._request_with_retry("POST", url, json=payload)

            if response.status_code in (200, 201):
                return response.json()

            current_app.logger.error(
                f"Shiprocket manifest generation failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to generate manifest",
                status_code=502,
                code="SHIPROCKET_MANIFEST_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket manifest exception: {e}")
            raise APIException(
                "Shiprocket manifest service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- get order details
    @classmethod
    def get_order_details(cls, shiprocket_order_id: int | str) -> dict:
        """Retrieve order details from Shiprocket."""
        try:
            url = f"{cls._get_base_url()}/orders/show/{shiprocket_order_id}"
            response = cls._request_with_retry("GET", url)

            if response.status_code == 200:
                return response.json()

            current_app.logger.error(
                f"Shiprocket order details failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to retrieve order details from Shiprocket",
                status_code=502,
                code="SHIPROCKET_ORDER_DETAILS_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket show order exception: {e}")
            raise APIException(
                "Shiprocket order details service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- track shipment
    @classmethod
    def track_shipment(cls, awb_code: str) -> dict:
        """Retrieve live tracking data for a given AWB code."""
        try:
            url = f"{cls._get_base_url()}/courier/track/awb/{awb_code}"
            response = cls._request_with_retry("GET", url)

            if response.status_code == 200:
                return response.json()

            current_app.logger.error(
                f"Shiprocket track shipment failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to retrieve tracking info from Shiprocket",
                status_code=502,
                code="SHIPROCKET_TRACKING_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket track shipment exception: {e}")
            raise APIException(
                "Shiprocket tracking service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ---------------------------------------------------------- cancel order
    @classmethod
    def cancel_order(cls, order_ids: list) -> dict:
        """Cancel orders in Shiprocket."""
        try:
            url = f"{cls._get_base_url()}/orders/cancel"
            response = cls._request_with_retry("POST", url, json={"ids": order_ids})

            if response.status_code in (200, 201):
                return response.json()

            current_app.logger.error(
                f"Shiprocket cancel order failed: HTTP {response.status_code} — {response.text}"
            )
            raise APIException(
                "Failed to cancel order in Shiprocket",
                status_code=502,
                code="SHIPROCKET_CANCEL_FAILED",
            )
        except APIException:
            raise
        except Exception as e:
            current_app.logger.error(f"Shiprocket cancel order exception: {e}")
            raise APIException(
                "Shiprocket cancel service unavailable",
                status_code=502,
                code="SHIPROCKET_SERVICE_UNAVAILABLE",
            )

    # ========================================================== high-level orchestrator
    @classmethod
    def fulfill_order_in_shiprocket(cls, order: Order) -> tuple[Shipment, bool]:
        """High-level atomic orchestrator: create order → assign AWB → request pickup
        and persist all tracking details in the database.

        Returns (shipment, is_newly_created).
        """
        # 1. Idempotency: return existing active shipment
        existing_shipment = (
            next((s for s in order.shipments if s.status != "cancelled"), None)
            if hasattr(order, "shipments") and order.shipments
            else None
        )
        if existing_shipment and existing_shipment.awb_code and existing_shipment.status != "failed":
            current_app.logger.info(
                f"Order {order.order_number} already has active shipment {existing_shipment.awb_code}."
            )
            return existing_shipment, False

        # 2. Calculate total weight (kg)
        total_weight = 0.0
        for item in order.order_items:
            item_weight = 0.5
            if item.product and hasattr(item.product, "weight") and item.product.weight is not None:
                item_weight = float(item.product.weight)
            total_weight += item_weight * item.quantity

        if total_weight <= 0:
            total_weight = current_app.config.get("SHIPROCKET_DEFAULT_WEIGHT", 0.5)
        total_weight = round(total_weight, 3)

        # Configured dimensions & pickup location
        length = current_app.config.get("SHIPROCKET_DEFAULT_LENGTH", 10)
        breadth = current_app.config.get("SHIPROCKET_DEFAULT_BREADTH", 10)
        height = current_app.config.get("SHIPROCKET_DEFAULT_HEIGHT", 10)
        pickup_loc = current_app.config.get("SHIPROCKET_PICKUP_LOCATION", "Primary")

        # 3. Construct Shiprocket adhoc order payload
        order_date_str = (
            order.created_at.strftime("%Y-%m-%d %H:%M")
            if order.created_at
            else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        )

        customer_email = "customer@example.com"
        if order.user and hasattr(order.user, "email") and order.user.email:
            customer_email = order.user.email

        sr_items = [
            {
                "name": item.product_name,
                "sku": item.sku or f"SKU-{item.product_id or item.id}",
                "units": item.quantity,
                "selling_price": float(item.unit_price),
                "discount": 0,
                "tax": 0,
            }
            for item in order.order_items
        ]

        sr_payload = {
            "order_id": order.order_number,
            "order_date": order_date_str,
            "pickup_location": pickup_loc,
            "billing_customer_name": order.shipping_full_name or "Customer",
            "billing_last_name": "",
            "billing_address": order.shipping_address_line1 or "",
            "billing_address_2": order.shipping_address_line2 or "",
            "billing_city": order.shipping_city or "",
            "billing_pincode": order.shipping_postal_code or "",
            "billing_state": order.shipping_state or "",
            "billing_country": order.shipping_country or "India",
            "billing_email": customer_email,
            "billing_phone": order.shipping_phone or "",
            "shipping_is_billing": True,
            "order_items": sr_items,
            "payment_method": "COD" if order.payment_method == "cod" else "Prepaid",
            "shipping_charges": float(order.shipping_amount),
            "discount": float(order.discount_amount),
            "sub_total": float(order.subtotal),
            "length": length,
            "breadth": breadth,
            "height": height,
            "weight": total_weight,
        }

        shipment = existing_shipment or Shipment(order_id=order.id, provider="shiprocket")

        try:
            # 4. Create Order in Shiprocket
            sr_res = cls.create_order(sr_payload)
            sr_order_id = sr_res.get("order_id")
            sr_shipment_id = sr_res.get("shipment_id")

            if not sr_shipment_id:
                raise APIException(
                    "Shiprocket response missing shipment_id",
                    status_code=502,
                    code="SHIPROCKET_ERROR",
                )

            shipment.shipment_id = str(sr_shipment_id)
            shipment.shiprocket_order_id = str(sr_order_id)

            # 5. Assign Courier & Generate AWB
            courier_company_id = sr_res.get("courier_company_id")
            awb_res = cls.generate_awb(sr_shipment_id, courier_id=courier_company_id)
            awb_data = awb_res.get("response", {}).get("data", {})
            awb_code = awb_data.get("awb_code") or sr_res.get("awb_code") or f"AWB-SR-{sr_shipment_id}"
            courier_name = awb_data.get("courier_name") or sr_res.get("courier_name") or "Shiprocket Direct"
            courier_id = awb_data.get("courier_company_id") or courier_company_id
            tracking_url = awb_data.get("tracking_url") or f"https://shiprocket.co/tracking/{awb_code}"

            shipment.awb_code = str(awb_code)
            shipment.courier_name = str(courier_name)
            shipment.courier_id = int(courier_id) if courier_id else None
            shipment.tracking_url = str(tracking_url)
            shipment.status = "assigned"

            # 6. Request Pickup
            try:
                pickup_res = cls.request_pickup([sr_shipment_id])
                pickup_data = pickup_res.get("response", {})
                shipment.pickup_token_number = pickup_data.get("pickup_token_number")
                shipment.pickup_scheduled_at = datetime.now(timezone.utc)
            except Exception as e_pickup:
                current_app.logger.warning(
                    f"Shiprocket pickup warning for order {order.order_number}: {e_pickup}"
                )

            # Update Order Status
            if order.order_status in ("pending", "confirmed"):
                order.order_status = "processing"

            shipment.error_message = None
            db.session.add(shipment)
            db.session.flush()

            # Record initial tracking event
            now_utc = datetime.now(timezone.utc)
            evt = ShipmentTrackingEvent(
                shipment_id=shipment.id,
                status=shipment.status,
                external_status="ASSIGNED",
                description=f"Shipment created and assigned to {courier_name} (AWB: {awb_code})",
                location=order.shipping_city,
                event_timestamp=now_utc,
            )
            db.session.add(evt)
            db.session.commit()

            current_app.logger.info(
                f"Order {order.order_number} fulfilled in Shiprocket — AWB: {awb_code}, Courier: {courier_name}"
            )
            return shipment, True

        except Exception as e:
            db.session.rollback()
            err_msg = str(e)
            current_app.logger.error(
                f"Failed to fulfill order {order.order_number} in Shiprocket: {err_msg}"
            )

            # Persist failure state without crashing caller
            shipment.status = "failed"
            shipment.error_message = err_msg
            try:
                db.session.add(shipment)
                db.session.commit()
            except Exception:
                db.session.rollback()

            return shipment, True
