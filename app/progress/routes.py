"""My Progress page."""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from ..models import User
from ..services.stats import compute_user_stats, get_individual_rankings

progress_bp = Blueprint("progress", __name__)


def _chart_payload(stats):
    """Convert date objects to plain strings/numbers so |tojson works safely."""
    return {
        "daily": [
            {"date": d["date"].isoformat(), "steps": d["steps"]} for d in stats["daily_breakdown"]
        ],
        "weekly": [
            {
                "label": f"{w['week_start'].strftime('%d %b')} - {w['week_end'].strftime('%d %b')}",
                "total": w["total"],
                "avg_daily": round(w["avg_daily"]),
            }
            for w in stats["weekly_breakdown"]
        ],
        "monthly": [
            {"label": m["label"], "total": m["total"], "avg_daily": round(m["avg_daily"])}
            for m in stats["monthly_breakdown"]
        ],
    }


@progress_bp.route("/progress")
@login_required
def index():
    return _render_progress(current_user)


@progress_bp.route("/progress/<int:user_id>")
@login_required
def view(user_id):
    user = User.query.filter_by(id=user_id, account_status="active").first()
    if user is None:
        abort(404)
    return _render_progress(user)


def _render_progress(user):
    stats = compute_user_stats(user)

    rankings = get_individual_rankings()
    rank = next((r["rank"] for r in rankings if r["user"].id == user.id), None)

    return render_template(
        "progress/index.html",
        viewed_user=user,
        is_own_progress=(user.id == current_user.id),
        stats=stats,
        my_rank=rank,
        total_participants=len(rankings),
        chart_data=_chart_payload(stats),
    )
