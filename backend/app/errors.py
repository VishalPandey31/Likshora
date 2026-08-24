from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException


class APIException(Exception):
    """Custom base exception class for operational API errors."""

    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST", payload: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.payload = payload

    def __str__(self):
        return self.message

    def to_dict(self):
        rv = {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.payload:
            rv["error"]["details"] = self.payload
        return rv


def register_error_handlers(app):
    """Register centralized JSON error handlers on the Flask app instance."""

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def handle_bad_request(error):
        message = getattr(error, "description", "Bad request")
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": message
            }
        }), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        message = getattr(error, "description", "The requested resource was not found")
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": message
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        message = getattr(error, "description", "Method not allowed for the requested endpoint")
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": message
            }
        }), 405

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        code_str = error.name.upper().replace(" ", "_") if error.name else "HTTP_ERROR"
        return jsonify({
            "success": False,
            "error": {
                "code": code_str,
                "message": error.description or "An HTTP error occurred"
            }
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        # Log unhandled error internally without exposing details to client
        current_app.logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred"
            }
        }), 500
