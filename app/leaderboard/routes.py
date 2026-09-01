"""Leaderboard page: teams vs individuals toggle, auto-updating rankings."""
from datetime import date

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

    # The competition is scored monthly; default to the current calendar month.
    period = request.args.get("period", "month")
    month_str = request.args.get("month") or date.today().strftime("%Y-%m")
    year = None
    month = None
    if period == "month" and month_str:
        try:
            parts = month_str.split("-")
            year = int(parts[0])
            month = int(parts[1])
        except (IndexError, ValueError):
            month_str = date.today().strftime("%Y-%m")
            year, month = date.today().year, date.today().month

    team_rankings = get_team_rankings(period=period, year=year, month=month)
    individual_rankings = get_individual_rankings(period=period, year=year, month=month)

    return render_template(
        "leaderboard/index.html",
        view=view,
        team_rankings=team_rankings,
        individual_rankings=individual_rankings,
        period=period,
        selected_month=month_str,
    )
