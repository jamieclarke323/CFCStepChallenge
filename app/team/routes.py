"""My Team page: overview, member stats, and editing team name/image."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Team
from ..services.stats import compute_team_stats, get_team_rankings
from ..services.images import save_team_image, InvalidImageError

team_bp = Blueprint("team", __name__)


def _team_chart_payload(stats):
    return {
        "daily": [{"date": d["date"].isoformat(), "steps": d["steps"]} for d in stats["daily_breakdown"]],
        "weekly": [
            {
                "label": f"{w['week_start'].strftime('%d %b')} - {w['week_end'].strftime('%d %b')}",
                "total": w["total"],
            }
            for w in stats["weekly_breakdown"]
        ],
        "monthly": [{"label": m["label"], "total": m["total"]} for m in stats["monthly_breakdown"]],
    }


@team_bp.route("/team")
@login_required
def index():
    if not current_user.team_id:
        return render_template("team/no_team.html")

    team = db.session.get(Team, current_user.team_id)
    stats = compute_team_stats(team)

    rankings = get_team_rankings()
    team_rank = next((r["rank"] for r in rankings if r["team"].id == team.id), None)

    return render_template(
        "team/index.html",
        team=team,
        stats=stats,
        team_rank=team_rank,
        total_teams=len(rankings),
        chart_data=_team_chart_payload(stats),
    )


@team_bp.route("/team/update-name", methods=["POST"])
@login_required
def update_name():
    if not current_user.team_id:
        abort(403)
    team = db.session.get(Team, current_user.team_id)
    new_name = (request.form.get("name") or "").strip()

    if not new_name:
        flash("Team name can't be empty.", "error")
    elif len(new_name) > 80:
        flash("Team name is too long (max 80 characters).", "error")
    elif Team.query.filter(Team.name.ilike(new_name), Team.id != team.id).first():
        flash("Another team already has that name.", "error")
    else:
        team.name = new_name
        db.session.commit()
        flash("Team name updated.", "success")

    return redirect(url_for("team.index"))


@team_bp.route("/team/update-image", methods=["POST"])
@login_required
def update_image():
    if not current_user.team_id:
        abort(403)
    team = db.session.get(Team, current_user.team_id)

    file_storage = request.files.get("image")
    try:
        new_filename = save_team_image(file_storage, old_filename=team.image_filename)
    except InvalidImageError as e:
        flash(str(e), "error")
        return redirect(url_for("team.index"))

    team.image_filename = new_filename
    db.session.commit()
    flash("Team image updated.", "success")
    return redirect(url_for("team.index"))
