"""Tests for team leaderboard ordering.

Teams must be ranked by the average steps per active day that is actually
displayed on the leaderboard (highest first), with ties broken by team name
ascending so the order is never random.
"""
from datetime import date, timedelta

from app.extensions import db
from app.models import StepRecord, Team
from app.services.stats import get_team_rankings
from tests.conftest import make_user


def _make_team(name, multiplier=1.0):
    team = Team(name=name, multiplier=multiplier)
    db.session.add(team)
    db.session.commit()
    return team


def _add_member(team, email, daily_steps):
    user = make_user(first_name=email.split("@")[0], email=email)
    user.team_id = team.id
    for offset, steps in enumerate(daily_steps):
        db.session.add(
            StepRecord(user_id=user.id, date=date.today() - timedelta(days=offset), step_count=steps)
        )
    db.session.commit()
    return user


def test_teams_ranked_by_average_steps_descending(app):
    with app.app_context():
        low = _make_team("Alpha")
        high = _make_team("Bravo")
        mid = _make_team("Charlie")
        # Alpha has the most total steps but the lowest average per active day.
        _add_member(low, "low@example.com", [1000, 1000, 1000, 1000, 1000])
        _add_member(high, "high@example.com", [9000])
        _add_member(mid, "mid@example.com", [5000, 5000])

        rows = get_team_rankings()
        assert [r["team"].name for r in rows] == ["Bravo", "Charlie", "Alpha"]
        assert [r["rank"] for r in rows] == [1, 2, 3]
        averages = [r["team_avg_per_active_day"] for r in rows]
        assert averages == sorted(averages, reverse=True)


def test_ties_broken_by_team_name_ascending(app):
    with app.app_context():
        zulu = _make_team("Zulu")
        alpha = _make_team("alpha")
        mike = _make_team("Mike")
        _add_member(zulu, "z@example.com", [4000, 4000])
        _add_member(alpha, "a@example.com", [4000])
        _add_member(mike, "m@example.com", [4000, 4000, 4000])

        rows = get_team_rankings()
        assert [r["team"].name for r in rows] == ["alpha", "Mike", "Zulu"]


def test_multiplier_is_reflected_in_ordering(app):
    with app.app_context():
        boosted = _make_team("Boosted", multiplier=2.0)
        plain = _make_team("Plain")
        _add_member(boosted, "b@example.com", [3000])
        _add_member(plain, "p@example.com", [5000])

        rows = get_team_rankings()
        assert [r["team"].name for r in rows] == ["Boosted", "Plain"]


def test_monthly_view_ranked_by_average_steps_descending(app):
    with app.app_context():
        low = _make_team("Alpha")
        high = _make_team("Bravo")
        low_member = _add_member(low, "low@example.com", [])
        high_member = _add_member(high, "high@example.com", [])
        for day, steps in ((10, 1000), (11, 1000), (12, 1000)):
            db.session.add(StepRecord(user_id=low_member.id, date=date(2024, 5, day), step_count=steps))
        db.session.add(StepRecord(user_id=high_member.id, date=date(2024, 5, 10), step_count=8000))
        db.session.commit()

        rows = get_team_rankings(period="month", year=2024, month=5)
        averages = [r["team_avg_per_active_day"] for r in rows]
        assert averages == sorted(averages, reverse=True)
        assert rows[0]["team"].name == "Bravo"
