import json
from flask import jsonify, request
from app.api import api_v1
from app.auth.decorators import require_admin
from app.models import Banner, RotatingModel, SiteContent
from app.extensions import db
from app.errors import APIException

DEFAULT_SITE_CONTENT = {
    "heroTitle": "Kurtas, coloured for everyday wear.",
    "heroSubtitle": "Handcrafted cotton kurtas, tunic sets, and breezy co-ords designed for effortless modern lifestyle.",
    "heroCtaText": "Explore Collection",
    "announcementText": "Complimentary shipping on prepaid orders, across India",
    "announcementActive": True,
    "contactEmail": "care@LIKSHORA.com",
    "contactPhone": "+91 9876543210",
    "studioAddress": "LIKSHORA Design Studio, Indiranagar 100ft Road, Bengaluru, KA 560038",
    "footerBrandBio": "Kurtas, coloured for everyday wear.",
    "copyrightText": "© 2026 Likshora. All rights reserved.",
}

DEFAULT_HERO_SLIDES = [
    {"title": "Slide 1", "caption": "LIKSHORA model wearing kurta with embroidered stole", "image_url": "../../assets/images/products/model-photo-1.jpg", "display_order": 0},
    {"title": "Slide 2", "caption": "LIKSHORA model in courtyard wearing kurta with embroidered stole", "image_url": "../../assets/images/products/model-photo-2.jpg", "display_order": 1},
    {"title": "Slide 3", "caption": "LIKSHORA model leaning against pillar wearing kurta with stole", "image_url": "../../assets/images/products/model-photo-4.jpg", "display_order": 2},
    {"title": "Slide 4", "caption": "LIKSHORA model wearing white kurta outdoors", "image_url": "../../assets/images/products/model-photo-7.jpg", "display_order": 3},
]

DEFAULT_ROTATING_MODELS = [
    {"name": "Model photo 1", "image_url": "../../assets/images/products/model-photo-1.jpg", "display_order": 0},
    {"name": "Model photo 2", "image_url": "../../assets/images/products/model-photo-2.jpg", "display_order": 1},
    {"name": "Model photo 3", "image_url": "../../assets/images/products/model-photo-3.jpg", "display_order": 2},
    {"name": "Model photo 4", "image_url": "../../assets/images/products/model-photo-4.jpg", "display_order": 3},
    {"name": "Model photo 6", "image_url": "../../assets/images/products/model-photo-6.jpg", "display_order": 4},
    {"name": "Model photo 7", "image_url": "../../assets/images/products/model-photo-7.jpg", "display_order": 5},
]


def seed_default_content_if_empty():
    """Ensure default site content, banners, and rotating models exist in DB."""
    for key, val in DEFAULT_SITE_CONTENT.items():
        existing = SiteContent.query.filter_by(key=key).first()
        if not existing:
            str_val = json.dumps(val) if isinstance(val, (dict, list, bool)) else str(val)
            db.session.add(SiteContent(key=key, value=str_val))

    if Banner.query.count() == 0:
        for slide in DEFAULT_HERO_SLIDES:
            db.session.add(Banner(
                title=slide.get("title"),
                subtitle=slide.get("caption"),
                tagline="Hero Banner",
                image_url=slide["image_url"],
                display_order=slide["display_order"],
                is_active=True,
            ))

    if RotatingModel.query.count() == 0:
        for mod in DEFAULT_ROTATING_MODELS:
            db.session.add(RotatingModel(
                name=mod["name"],
                image_url=mod["image_url"],
                display_order=mod["display_order"],
                is_active=True,
            ))

    db.session.commit()


@api_v1.route("/content", methods=["GET"])
def get_site_content():
    """Retrieve full dynamic site content, banners, and rotating models."""
    seed_default_content_if_empty()

    contents = {sc.key: sc.value for sc in SiteContent.query.all()}
    res = {}
    for key, default_val in DEFAULT_SITE_CONTENT.items():
        val = contents.get(key)
        if val is None:
            res[key] = default_val
        elif key == "announcementActive":
            res[key] = val.lower() == "true" if isinstance(val, str) else bool(val)
        else:
            try:
                res[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                res[key] = val

    banners = Banner.query.filter_by(is_active=True).order_by(Banner.display_order.asc(), Banner.id.asc()).all()
    res["heroSlides"] = [
        {
            "id": b.id,
            "title": b.title or "",
            "caption": b.subtitle or b.title or "",
            "image": b.image_url,
            "ctaText": b.cta_text or "",
            "ctaLink": b.cta_link or "",
            "displayOrder": b.display_order,
        }
        for b in banners
    ]

    models = RotatingModel.query.filter_by(is_active=True).order_by(RotatingModel.display_order.asc(), RotatingModel.id.asc()).all()
    res["rotatingModels"] = [
        {
            "id": m.id,
            "name": m.name,
            "title": m.title or "",
            "tagline": m.tagline or "",
            "description": m.description or "",
            "image": m.image_url,
            "linkUrl": m.link_url or "",
            "displayOrder": m.display_order,
        }
        for m in models
    ]

    return jsonify({
        "success": True,
        "data": res
    }), 200


@api_v1.route("/admin/content", methods=["PUT"])
@require_admin
def update_site_content():
    """Update dynamic site content, banners, and rotating models (Admin-only)."""
    data = request.get_json() or {}

    # Update Key-Value SiteContent entries
    for key in DEFAULT_SITE_CONTENT.keys():
        if key in data:
            val = data[key]
            str_val = json.dumps(val) if isinstance(val, (dict, list, bool)) else str(val)
            item = SiteContent.query.filter_by(key=key).first()
            if item:
                item.value = str_val
            else:
                db.session.add(SiteContent(key=key, value=str_val))

    # Sync hero slides if provided in payload
    if "heroSlides" in data and isinstance(data["heroSlides"], list):
        # Deactivate or remove existing banners and re-sync
        Banner.query.delete()
        for idx, slide in enumerate(data["heroSlides"]):
            img_url = slide.get("image") or slide.get("image_url") or ""
            if img_url:
                db.session.add(Banner(
                    title=slide.get("title") or f"Slide {idx + 1}",
                    subtitle=slide.get("caption") or slide.get("subtitle"),
                    image_url=img_url,
                    cta_text=slide.get("ctaText") or slide.get("cta_text"),
                    cta_link=slide.get("ctaLink") or slide.get("cta_link"),
                    display_order=idx,
                    is_active=True,
                ))

    # Sync rotating model slider if provided in payload
    if "rotatingModels" in data and isinstance(data["rotatingModels"], list):
        RotatingModel.query.delete()
        for idx, mod in enumerate(data["rotatingModels"]):
            img_url = mod.get("image") or mod.get("image_url") or ""
            if img_url:
                db.session.add(RotatingModel(
                    name=mod.get("name") or f"Model {idx + 1}",
                    title=mod.get("title"),
                    tagline=mod.get("tagline"),
                    description=mod.get("description"),
                    image_url=img_url,
                    link_url=mod.get("linkUrl") or mod.get("link_url"),
                    display_order=idx,
                    is_active=True,
                ))

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Website content configuration updated successfully"
    }), 200


@api_v1.route("/banners", methods=["GET"])
def get_banners():
    """Retrieve active promotional banners."""
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.display_order.asc()).all()
    return jsonify({
        "success": True,
        "data": [
            {
                "id": b.id,
                "title": b.title,
                "subtitle": b.subtitle,
                "tagline": b.tagline,
                "image_url": b.image_url,
                "cta_text": b.cta_text,
                "cta_link": b.cta_link,
                "display_order": b.display_order,
                "is_active": b.is_active,
            }
            for b in banners
        ]
    }), 200


@api_v1.route("/banners", methods=["POST"])
@require_admin
def create_banner():
    """Create new banner slide (Admin-only)."""
    data = request.get_json() or {}
    image_url = (data.get("image_url") or data.get("image") or "").strip()
    if not image_url:
        raise APIException("image_url is required", status_code=400, code="VALIDATION_ERROR")

    banner = Banner(
        title=data.get("title"),
        subtitle=data.get("subtitle") or data.get("caption"),
        tagline=data.get("tagline"),
        image_url=image_url,
        cta_text=data.get("cta_text") or data.get("ctaText"),
        cta_link=data.get("cta_link") or data.get("ctaLink"),
        display_order=int(data.get("display_order", 0)),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(banner)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Banner created successfully",
        "data": {"id": banner.id, "image_url": banner.image_url}
    }), 201


@api_v1.route("/banners/<int:banner_id>", methods=["PUT"])
@require_admin
def update_banner(banner_id):
    """Update existing banner (Admin-only)."""
    banner = db.session.get(Banner, banner_id)
    if not banner:
        raise APIException("Banner not found", status_code=404, code="BANNER_NOT_FOUND")

    data = request.get_json() or {}
    if "title" in data: banner.title = data["title"]
    if "subtitle" in data: banner.subtitle = data["subtitle"]
    if "tagline" in data: banner.tagline = data["tagline"]
    if "image_url" in data: banner.image_url = data["image_url"]
    if "cta_text" in data: banner.cta_text = data["cta_text"]
    if "cta_link" in data: banner.cta_link = data["cta_link"]
    if "display_order" in data: banner.display_order = int(data["display_order"])
    if "is_active" in data: banner.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify({"success": True, "message": "Banner updated successfully"}), 200


@api_v1.route("/banners/<int:banner_id>", methods=["DELETE"])
@require_admin
def delete_banner(banner_id):
    """Delete banner (Admin-only)."""
    banner = db.session.get(Banner, banner_id)
    if not banner:
        raise APIException("Banner not found", status_code=404, code="BANNER_NOT_FOUND")

    db.session.delete(banner)
    db.session.commit()
    return jsonify({"success": True, "message": "Banner deleted successfully"}), 200
