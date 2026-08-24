from flask import jsonify, g
from app.api import api_v1
from app.auth.decorators import require_auth
from app.models import SearchHistory
from app.extensions import db


@api_v1.route("/search/history", methods=["GET"])
@require_auth
def get_search_history():
    """Retrieve search history for current authenticated user."""
    history = (
        SearchHistory.query.filter_by(user_id=g.current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(50)
        .all()
    )

    data = [
        {
            "id": h.id,
            "query": h.search_query,
            "results_count": h.results_count,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    }), 200


@api_v1.route("/search/history", methods=["DELETE"])
@require_auth
def clear_search_history():
    """Clear all search history for current authenticated user."""
    SearchHistory.query.filter_by(user_id=g.current_user.id).delete()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Search history cleared successfully",
    }), 200
