import os
import requests
import jwt
from flask import current_app
from app.errors import APIException


class SupabaseAuthClient:
    """Wrapper client for Supabase Auth REST endpoints."""

    def __init__(self):
        pass

    @property
    def supabase_url(self) -> str | None:
        return current_app.config.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")

    @property
    def supabase_anon_key(self) -> str | None:
        return current_app.config.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY")

    @property
    def supabase_service_role_key(self) -> str | None:
        return current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def verify_ssl(self) -> bool:
        val = current_app.config.get("SUPABASE_VERIFY_SSL") or os.environ.get("SUPABASE_VERIFY_SSL", "true")
        return str(val).lower() != "false"

    def _get_headers(self, access_token: str | None = None) -> dict:
        anon_key = self.supabase_anon_key or ""
        headers = {
            "apikey": anon_key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    def signup(self, email: str, password: str, user_metadata: dict | None = None) -> dict:
        """Register a new user via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException(
                "Supabase Auth credentials are unconfigured on server",
                status_code=500,
                code="SUPABASE_CONFIG_ERROR",
            )

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/signup"
        payload = {
            "email": email,
            "password": password,
            "data": user_metadata or {},
        }

        try:
            res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10, verify=self.verify_ssl)
            data = res.json()
            if res.status_code >= 400:
                msg = data.get("error_description") or data.get("msg") or data.get("message") or "Signup failed"
                err_code_str = str(data.get("error_code") or data.get("code") or "").lower()

                if res.status_code == 429 or "rate_limit" in err_code_str or "rate limit" in msg.lower() or "over_email_send_rate_limit" in err_code_str:
                    current_app.logger.error("Supabase public signup email rate limited.")
                    raise APIException(
                        "Supabase email delivery rate limit exceeded. Please configure a Custom SMTP Provider in Supabase Dashboard (Authentication -> Email Settings -> Custom SMTP) or wait before trying again.",
                        status_code=429,
                        code="RATE_LIMITED"
                    )

                if "already" in msg.lower() or "exists" in msg.lower() or "registered" in msg.lower():
                    raise APIException("User with this email already exists", status_code=400, code="EMAIL_EXISTS")

                raise APIException(msg, status_code=res.status_code, code="SUPABASE_SIGNUP_ERROR")
            return data
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase signup network failure: {str(exc)}")
            raise APIException("Authentication server connection failed", status_code=503, code="SERVICE_UNAVAILABLE")

    def login(self, email: str, password: str) -> dict:
        """Authenticate user credentials via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException(
                "Supabase Auth credentials are unconfigured on server",
                status_code=500,
                code="SUPABASE_CONFIG_ERROR",
            )

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
        payload = {
            "email": email,
            "password": password,
        }

        try:
            res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10, verify=self.verify_ssl)
            data = res.json()
            if res.status_code >= 400:
                msg = data.get("error_description") or data.get("msg") or data.get("message") or "Invalid credentials"
                err_code_str = str(data.get("error_code") or data.get("error") or "").lower()

                if "confirm" in msg.lower() or "unconfirmed" in msg.lower() or "email_not_confirmed" in err_code_str:
                    raise APIException("Please verify your email before logging in", status_code=401, code="EMAIL_NOT_VERIFIED")
                elif "invalid" in msg.lower() or "credentials" in msg.lower() or "grant" in err_code_str:
                    raise APIException("Invalid email address or password", status_code=401, code="INVALID_CREDENTIALS")
                raise APIException(msg, status_code=401, code="INVALID_CREDENTIALS")
            return data
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase login network failure: {str(exc)}")
            raise APIException("Authentication server connection failed", status_code=503, code="SERVICE_UNAVAILABLE")

    def logout(self, access_token: str) -> bool:
        """Revoke session via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            return True

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/logout"
        try:
            res = requests.post(url, headers=self._get_headers(access_token), timeout=10, verify=self.verify_ssl)
            return res.status_code < 400
        except requests.RequestException:
            return False

    def verify_token(self, access_token: str) -> dict:
        """Verify Supabase JWT access token by querying /auth/v1/user."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException(
                "Supabase Auth credentials are unconfigured on server",
                status_code=500,
                code="SUPABASE_CONFIG_ERROR",
            )

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/user"
        try:
            res = requests.get(url, headers=self._get_headers(access_token), timeout=10, verify=self.verify_ssl)
            if res.status_code >= 400:
                raise APIException("Invalid or expired access token", status_code=401, code="UNAUTHORIZED")
            return res.json()
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase verify token network failure: {str(exc)}")
            raise APIException("Authentication verification server unavailable", status_code=503, code="SERVICE_UNAVAILABLE")

    def recover_password(self, email: str) -> dict:
        """Send password recovery email via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException(
                "Supabase Auth credentials are unconfigured on server",
                status_code=500,
                code="SUPABASE_CONFIG_ERROR",
            )

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/recover"
        payload = {"email": email}

        try:
            res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10, verify=self.verify_ssl)
            if res.status_code >= 400:
                data = res.json()
                msg = data.get("error_description") or data.get("msg") or "Password recovery request failed"
                raise APIException(msg, status_code=res.status_code, code="RECOVERY_ERROR")
            return res.json() if res.content else {"message": "Recovery email sent"}
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase password recovery network failure: {str(exc)}")
            raise APIException("Authentication server connection failed", status_code=503, code="SERVICE_UNAVAILABLE")

    def resend_verification(self, email: str) -> dict:
        """Resend email confirmation link via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException(
                "Supabase Auth credentials are unconfigured on server",
                status_code=500,
                code="SUPABASE_CONFIG_ERROR",
            )

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/resend"
        payload = {
            "type": "signup",
            "email": email,
        }

        try:
            res = requests.post(url, json=payload, headers=self._get_headers(), timeout=10, verify=self.verify_ssl)
            data = res.json() if res.content else {}
            if res.status_code >= 400:
                msg = data.get("error_description") or data.get("msg") or data.get("message") or "Failed to resend verification email"
                err_code_str = str(data.get("error_code") or data.get("code") or "").lower()

                if "already" in msg.lower() or "confirmed" in msg.lower() or "verified" in msg.lower() or "registered" in err_code_str:
                    raise APIException("Your email is already verified. You can log in.", status_code=400, code="EMAIL_ALREADY_VERIFIED")
                if res.status_code == 429 or "rate_limit" in err_code_str or "rate limit" in msg.lower():
                    raise APIException("Too many requests. Please wait a moment before requesting another email.", status_code=429, code="RATE_LIMITED")

                raise APIException(msg, status_code=res.status_code, code="SUPABASE_RESEND_ERROR")
            return {"message": f"Verification email has been sent again to {email}."}
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase resend verification network failure: {str(exc)}")
            raise APIException("Authentication server connection failed", status_code=503, code="SERVICE_UNAVAILABLE")

    def update_password_with_token(self, access_token: str, new_password: str) -> dict:
        """Update user password using reset token via Supabase Auth API."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise APIException("Supabase Auth credentials unconfigured", status_code=500, code="SUPABASE_CONFIG_ERROR")

        url = f"{self.supabase_url.rstrip('/')}/auth/v1/user"
        headers = self._get_headers(access_token)
        payload = {"password": new_password}

        try:
            res = requests.put(url, json=payload, headers=headers, timeout=10, verify=self.verify_ssl)
            data = res.json() if res.content else {}
            if res.status_code >= 400:
                msg = data.get("error_description") or data.get("msg") or "Password update failed"
                raise APIException(msg, status_code=res.status_code, code="PASSWORD_UPDATE_ERROR")
            return data
        except requests.RequestException as exc:
            current_app.logger.error(f"Supabase password update network failure: {str(exc)}")
            raise APIException("Authentication server connection failed", status_code=503, code="SERVICE_UNAVAILABLE")


supabase_auth = SupabaseAuthClient()

