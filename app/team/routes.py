"""My Team page: overview, member stats, and editing team name/image."""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Team
from ..services.stats import compute_team_stats, get_team_rankings
from ..services.images import save_team_image, InvalidImageError

team_bp = Blueprint("team", __name__)


@team_bp.route("/admin/team-multipliers", methods=["GET", "POST"])
@login_required
def manage_multipliers():
    """Admin-only control for team-level scoring multipliers."""
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        team = db.session.get(Team, request.form.get("team_id", type=int))
        raw_multiplier = (request.form.get("multiplier") or "").strip()
        try:
            multiplier = Decimal(raw_multiplier)
        except InvalidOperation:
            multiplier = None

        if not team:
            flash("That team could not be found.", "error")
        elif multiplier is None or not multiplier.is_finite() or not Decimal("0") <= multiplier <= Decimal("10"):
            flash("Enter a multiplier between 0.00 and 10.00.", "error")
        else:
            team.multiplier = float(multiplier)
            db.session.commit()
            flash(f"{team.name} multiplier updated to {multiplier:.2f}.", "success")
        return redirect(url_for("team.manage_multipliers"))

    return render_template("team/manage_multipliers.html", teams=Team.query.order_by(Team.name).all())


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
