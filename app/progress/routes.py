"""My Progress page."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

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
    stats = compute_user_stats(current_user)

    rankings = get_individual_rankings()
    my_rank = next((r["rank"] for r in rankings if r["user"].id == current_user.id), None)

    return render_template(
        "progress/index.html",
        stats=stats,
        my_rank=my_rank,
        total_participants=len(rankings),
        chart_data=_chart_payload(stats),
    )
