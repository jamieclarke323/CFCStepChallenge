"""Tests for the pre-join step backfill window.

Users should be able to log steps for the single calendar day before they
joined (e.g. joining on 2 September still allows an entry for 1 September),
while future dates and dates further in the past remain blocked.
"""
from datetime import date, datetime, timedelta

from flask import current_app

from app.services.stats import effective_start_date
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
