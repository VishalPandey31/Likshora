import os
import uuid
import requests
from werkzeug.utils import secure_filename
from flask import jsonify, request, current_app
from app.api import api_v1
from app.auth.decorators import require_admin
from app.errors import APIException

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB Limit


def is_allowed_file(filename: str, mimetype: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS and mimetype.lower() in ALLOWED_MIME_TYPES


@api_v1.route("/admin/upload", methods=["POST"])
@require_admin
def upload_file():
    """Secure image upload endpoint (Admin-only).
    Validates file extension, MIME type, file size, and filename safety.
    Uploads to Supabase Storage if configured; otherwise saves to local static uploads directory.
    """
    if "file" not in request.files:
        raise APIException("No file provided in request", status_code=400, code="VALIDATION_ERROR")

    file = request.files["file"]
    if not file or file.filename == "":
        raise APIException("Empty filename", status_code=400, code="VALIDATION_ERROR")

    filename = secure_filename(file.filename)
    mimetype = file.mimetype or ""

    if not is_allowed_file(filename, mimetype):
        raise APIException(
            "Invalid file type. Only JPG, PNG, WEBP, and GIF images are allowed.",
            status_code=400,
            code="INVALID_FILE_TYPE",
        )

    # Validate file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    if file_length > MAX_FILE_SIZE_BYTES:
        raise APIException(
            "File size exceeds 5MB limit",
            status_code=400,
            code="FILE_TOO_LARGE",
        )

    ext = filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    supabase_url = current_app.config.get("SUPABASE_URL")
    supabase_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or current_app.config.get("SUPABASE_ANON_KEY")

    # Attempt Supabase Storage Upload if credentials present
    if supabase_url and supabase_key:
        bucket_name = "products"
        storage_endpoint = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket_name}/{unique_filename}"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": mimetype,
        }
        try:
            file_data = file.read()
            res = requests.post(storage_endpoint, data=file_data, headers=headers, timeout=15)
            if res.status_code < 300:
                public_url = f"{supabase_url.rstrip('/')}/storage/v1/object/public/{bucket_name}/{unique_filename}"
                return jsonify({
                    "success": True,
                    "message": "Image uploaded successfully to Supabase Storage",
                    "data": {
                        "url": public_url,
                        "filename": unique_filename,
                        "storage": "supabase",
                    }
                }), 201
        except Exception as exc:
            current_app.logger.warning(f"Supabase Storage upload failed, falling back to local storage: {exc}")

    # Local file storage fallback
    # Save into frontend/assets/images/uploads directory
    root_dir = os.path.abspath(os.path.join(current_app.root_path, "..", ".."))
    uploads_dir = os.path.join(root_dir, "frontend", "assets", "images", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    target_path = os.path.join(uploads_dir, unique_filename)
    file.seek(0)
    file.save(target_path)

    relative_url = f"assets/images/uploads/{unique_filename}"
    return jsonify({
        "success": True,
        "message": "Image uploaded successfully to local storage",
        "data": {
            "url": relative_url,
            "filename": unique_filename,
            "storage": "local",
        }
    }), 201
