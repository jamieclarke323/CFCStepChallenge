"""Tests for the step backfill window.

Users get a rolling 45-day backfill window so people who join the challenge
late can still enter steps they have already walked, while future dates and
dates older than the window remain blocked. Long-standing members keep their
existing window back to the day before they joined.
"""
from datetime import date, datetime, timedelta

from flask import current_app

from app.models import User
from app.services.stats import (
    compute_user_stats,
    earliest_recordable_date,
    effective_start_date,
)
from tests.conftest import TEST_PASSWORD, make_user


def _login(client, email):
    return client.post(
        "/login",
        data={"email": email, "password": TEST_PASSWORD},
        follow_redirects=True,
    )


def test_effective_start_date_allows_one_day_before_join(app):
    with app.app_context():
        join_date = date(2024, 9, 2)
        user = make_user(email="unit@example.com", date_joined=datetime.combine(join_date, datetime.min.time()))
        assert effective_start_date(user) == join_date - timedelta(days=1)


def test_earliest_recordable_date_is_45_days_for_a_new_joiner(app):
    with app.app_context():
        today = date.today()
        user = make_user(email="newjoiner@example.com", date_joined=datetime.now())
        backfill_days = current_app.config["STEP_BACKFILL_DAYS"]
        assert backfill_days == 45
        assert earliest_recordable_date(user, today) == today - timedelta(days=backfill_days)


def test_earliest_recordable_date_keeps_older_window_for_long_standing_member(app):
    with app.app_context():
        today = date.today()
        join_date = today - timedelta(days=200)
        user = make_user(email="veteran@example.com", date_joined=datetime.combine(join_date, datetime.min.time()))
        assert earliest_recordable_date(user, today) == join_date - timedelta(days=1)


def test_earliest_recordable_date_never_precedes_challenge_start(app):
    with app.app_context():
        today = date.today()
        challenge_start = today - timedelta(days=10)
        current_app.config["CHALLENGE_START_DATE"] = challenge_start
        try:
            user = make_user(email="clamped@example.com", date_joined=datetime.now())
            assert earliest_recordable_date(user, today) == challenge_start
        finally:
            current_app.config["CHALLENGE_START_DATE"] = None


def test_can_submit_steps_exactly_45_days_ago(app, client):
    with app.app_context():
        make_user(email="fortyfive@example.com", date_joined=datetime.now())
    _login(client, "fortyfive@example.com")

    entry_date = date.today() - timedelta(days=45)
    resp = client.post("/api/steps", json={"date": entry_date.isoformat(), "steps": "6000"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["date"] == entry_date.isoformat()


def test_can_submit_steps_for_a_recent_past_date(app, client):
    with app.app_context():
        make_user(email="recent@example.com", date_joined=datetime.now())
    _login(client, "recent@example.com")

    entry_date = date.today() - timedelta(days=10)
    resp = client.post("/api/steps", json={"date": entry_date.isoformat(), "steps": "6000"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_can_submit_steps_for_today(app, client):
    with app.app_context():
        make_user(email="today@example.com", date_joined=datetime.now())
    _login(client, "today@example.com")

    resp = client.post("/api/steps", json={"date": date.today().isoformat(), "steps": "6000"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_cannot_submit_steps_older_than_45_days(app, client):
    with app.app_context():
        make_user(email="tooold@example.com", date_joined=datetime.now())
    _login(client, "tooold@example.com")

    entry_date = date.today() - timedelta(days=46)
    resp = client.post("/api/steps", json={"date": entry_date.isoformat(), "steps": "6000"})
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False


def test_backfilled_days_are_included_in_stats_range(app, client):
    with app.app_context():
        make_user(email="statsrange@example.com", date_joined=datetime.now())
    _login(client, "statsrange@example.com")

    entry_date = date.today() - timedelta(days=45)
    client.post("/api/steps", json={"date": entry_date.isoformat(), "steps": "6000"})

    with app.app_context():
        user = User.query.filter_by(email="statsrange@example.com").first()
        stats = compute_user_stats(user)
        assert stats["effective_start"] <= entry_date
        assert stats["total_steps"] == 6000
        assert any(day["date"] == entry_date for day in stats["daily_breakdown"])


def test_can_submit_steps_for_day_before_join_date(app, client):
    join_date = date(2024, 9, 2)
    with app.app_context():
        user = make_user(email="joiner@example.com", date_joined=datetime.combine(join_date, datetime.min.time()))
        email = user.email
    _login(client, email)

    backfill_date = join_date - timedelta(days=1)
    resp = client.post(
        "/api/steps",
        json={"date": backfill_date.isoformat(), "steps": "5000"},
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["date"] == backfill_date.isoformat()


def test_same_day_submission_still_works(app, client):
    join_date = date(2024, 9, 2)
    with app.app_context():
        user = make_user(email="sameday@example.com", date_joined=datetime.combine(join_date, datetime.min.time()))
        email = user.email
    _login(client, email)

    resp = client.post(
        "/api/steps",
        json={"date": join_date.isoformat(), "steps": "7500"},
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["success"] is True
    assert data["date"] == join_date.isoformat()


def test_cannot_submit_more_than_one_day_before_join_date(app, client):
    join_date = date(2024, 9, 2)
    with app.app_context():
        user = make_user(email="toosoon@example.com", date_joined=datetime.combine(join_date, datetime.min.time()))
        email = user.email
    _login(client, email)

    too_early = join_date - timedelta(days=2)
    resp = client.post(
        "/api/steps",
        json={"date": too_early.isoformat(), "steps": "1000"},
    )
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False


def test_cannot_submit_future_date(app, client):
    with app.app_context():
        user = make_user(email="future@example.com")
        email = user.email
    _login(client, email)

    future_date = date.today() + timedelta(days=1)
    resp = client.post(
        "/api/steps",
        json={"date": future_date.isoformat(), "steps": "1000"},
    )
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["success"] is False
