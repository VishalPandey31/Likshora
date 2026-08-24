from datetime import datetime, timezone
from flask import jsonify, request, g
from app.api import api_v1
from app.auth.supabase_client import supabase_auth
from app.auth.utils import (
    validate_email_format,
    validate_password_strength,
    validate_phone_format,
)
from app.auth.decorators import require_auth
from app.models import User, CustomerLoginLog
from app.extensions import db, limiter
from app.errors import APIException


@api_v1.route("/auth/signup", methods=["POST"])
@limiter.limit("10 per minute")
def signup():
    """Customer signup endpoint via Supabase Auth."""
    data = request.get_json() or {}
    email = validate_email_format(data.get("email"))
    password = validate_password_strength(data.get("password"))
    name = (data.get("name") or "").strip()
    phone = validate_phone_format(data.get("phone"))

    if not name:
        raise APIException("Name is required", status_code=400, code="VALIDATION_ERROR")

    # Check if user email or phone already exists locally
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        raise APIException("User with this email already exists", status_code=400, code="EMAIL_EXISTS")

    if phone:
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            raise APIException("User with this phone number already exists", status_code=400, code="PHONE_EXISTS")

    # Call Supabase Auth Signup
    supabase_response = supabase_auth.signup(
        email=email,
        password=password,
        user_metadata={"name": name, "phone": phone},
    )

    supabase_user = supabase_response.get("user")
    if not supabase_user or not isinstance(supabase_user, dict):
        supabase_user = supabase_response if isinstance(supabase_response, dict) and "id" in supabase_response else {}

    supabase_uid = supabase_user.get("id")
    is_confirmed = bool(supabase_user.get("confirmed_at") or supabase_user.get("email_confirmed_at"))

    if not supabase_uid:
        raise APIException("Failed to obtain Auth User UUID from Supabase", status_code=500, code="SUPABASE_ERROR")

    # Create or update local user profile record cleanly
    user = User.query.filter((User.id == supabase_uid) | (User.supabase_uid == supabase_uid)).first()
    if not user:
        user = User(
            id=supabase_uid,
            supabase_uid=supabase_uid,
            name=name,
            email=email,
            phone=phone,
            role="customer",
            is_active=True,
            email_verified=is_confirmed,
        )
        db.session.add(user)
    else:
        user.name = name
        user.email = email
        user.phone = phone
        user.email_verified = is_confirmed

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise APIException("Failed to save customer profile: " + str(exc), status_code=500, code="DATABASE_ERROR")

    return jsonify({
        "success": True,
        "message": "Account created successfully. Please verify your email before logging in.",
        "data": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified,
        }
    }), 201


@api_v1.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """User authentication endpoint via Supabase Auth."""
    data = request.get_json() or {}
    email = validate_email_format(data.get("email"))
    password = data.get("password")

    if not password:
        raise APIException("Password is required", status_code=400, code="VALIDATION_ERROR")

    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    user = User.query.filter_by(email=email).first()

    if user and not user.is_active:
        try:
            log_entry = CustomerLoginLog(
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                day_of_week=datetime.now(timezone.utc).strftime("%A"),
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        raise APIException("Your account has been deactivated", status_code=403, code="ACCOUNT_DISABLED")

    try:
        auth_data = supabase_auth.login(email=email, password=password)
    except APIException as exc:
        if user:
            try:
                log_entry = CustomerLoginLog(
                    user_id=user.id,
                    user_name=user.name,
                    user_email=user.email,
                    day_of_week=datetime.now(timezone.utc).strftime("%A"),
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception:
                db.session.rollback()
        raise exc

    access_token = auth_data.get("access_token")
    refresh_token = auth_data.get("refresh_token")
    expires_in = auth_data.get("expires_in")
    supabase_user_info = auth_data.get("user")
    if not supabase_user_info or not isinstance(supabase_user_info, dict):
        supabase_user_info = auth_data if isinstance(auth_data, dict) and "id" in auth_data else {}

    supabase_uid = supabase_user_info.get("id")
    is_confirmed = bool(
        supabase_user_info.get("confirmed_at") or supabase_user_info.get("email_confirmed_at")
    )

    if not user and supabase_uid:
        user = User.query.filter((User.supabase_uid == supabase_uid) | (User.id == supabase_uid)).first()

    if not user:
        user_metadata = supabase_user_info.get("user_metadata") or {}
        user = User(
            id=supabase_uid,
            supabase_uid=supabase_uid,
            email=email,
            name=user_metadata.get("name") or email.split("@")[0],
            phone=user_metadata.get("phone"),
            role="customer",
            is_active=True,
            email_verified=is_confirmed,
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Sync supabase_uid and verification status
        if not user.supabase_uid and supabase_uid:
            user.supabase_uid = supabase_uid
        user.email_verified = is_confirmed
        db.session.commit()

    if not user.is_active:
        try:
            log_entry = CustomerLoginLog(
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                day_of_week=datetime.now(timezone.utc).strftime("%A"),
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        raise APIException("Your account has been deactivated", status_code=403, code="ACCOUNT_DISABLED")

    # Record successful login log
    try:
        log_entry = CustomerLoginLog(
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            day_of_week=datetime.now(timezone.utc).strftime("%A"),
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "role": user.role,
                "email_verified": user.email_verified,
            }
        }
    }), 200


@api_v1.route("/auth/logout", methods=["POST"])
@require_auth
def logout():
    """Logout session endpoint via Supabase Auth."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split()[1] if " " in auth_header else ""
    supabase_auth.logout(token)
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200


@api_v1.route("/auth/reset-password", methods=["POST"])
@limiter.limit("5 per minute")
def reset_password():
    """Trigger password recovery email via Supabase Auth."""
    data = request.get_json() or {}
    email = validate_email_format(data.get("email"))
    supabase_auth.recover_password(email)
    return jsonify({
        "success": True,
        "message": "Password recovery email sent"
    }), 200


@api_v1.route("/auth/resend-verification", methods=["POST"])
@limiter.limit("5 per minute")
def resend_verification():
    """Resend email verification link via Supabase Auth."""
    data = request.get_json() or {}
    email = validate_email_format(data.get("email"))
    res = supabase_auth.resend_verification(email)
    return jsonify({
        "success": True,
        "message": res.get("message") or f"Verification email has been sent again to {email}."
    }), 200


@api_v1.route("/auth/update-password", methods=["POST"])
@limiter.limit("5 per minute")
def update_password():
    """Update password using access token from password recovery link."""
    data = request.get_json() or {}
    access_token = data.get("access_token")
    new_password = validate_password_strength(data.get("password"))
    if not access_token:
        raise APIException("Access token is required to update password", status_code=400, code="VALIDATION_ERROR")
    supabase_auth.update_password_with_token(access_token, new_password)
    return jsonify({
        "success": True,
        "message": "Password updated successfully. You can now log in."
    }), 200


@api_v1.route("/auth/me", methods=["GET"])
@require_auth
def me():
    """Retrieve authenticated user details."""
    user = g.current_user
    return jsonify({
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }), 200

