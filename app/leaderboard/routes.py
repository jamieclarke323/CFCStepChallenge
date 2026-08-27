"""Leaderboard page: teams vs individuals toggle, auto-updating rankings."""
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from ..services.stats import get_team_rankings, get_individual_rankings

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/leaderboard")
@login_required
def index():
    view = request.args.get("view", "teams")
    if view not in ("teams", "individuals"):
        view = "teams"

    team_rankings = get_team_rankings()
    individual_rankings = get_individual_rankings()

    return render_template(
        "leaderboard/index.html",
        view=view,
        team_rankings=team_rankings,
        individual_rankings=individual_rankings,
    )
