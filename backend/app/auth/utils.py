import re
from app.errors import APIException


def validate_email_format(email: str | None) -> str:
    """Validate email format."""
    if not email or not email.strip():
        raise APIException("Email is required", status_code=400, code="VALIDATION_ERROR")
    email = email.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        raise APIException("Invalid email format", status_code=400, code="INVALID_EMAIL")
    return email


def validate_password_strength(password: str | None) -> str:
    """Validate password strength (minimum 8 characters, containing numbers and letters)."""
    if not password:
        raise APIException("Password is required", status_code=400, code="VALIDATION_ERROR")
    if len(password) < 8:
        raise APIException(
            "Password must be at least 8 characters long",
            status_code=400,
            code="WEAK_PASSWORD",
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        raise APIException(
            "Password must contain both letters and numbers",
            status_code=400,
            code="WEAK_PASSWORD",
        )
    return password


def validate_phone_format(phone: str | None) -> str | None:
    """Validate optional phone format."""
    if not phone or not phone.strip():
        return None
    phone = phone.strip()
    # Simple international/domestic phone regex
    pattern = r"^\+?[0-9]{7,15}$"
    if not re.match(pattern, phone):
        raise APIException("Invalid phone number format", status_code=400, code="INVALID_PHONE")
    return phone
