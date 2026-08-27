"""Record Steps page: monthly calendar + create/update step records."""
import calendar as pycal
from datetime import date

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from ..extensions import db
from ..models import StepRecord
from ..services.stats import effective_start_date, effective_end_date, compute_user_stats
from ..utils.validation import parse_step_count

steps_bp = Blueprint("steps", __name__)


def _build_month_grid(user, year, month):
    """Return a list of weeks (each a list of 7 day-info dicts) for the given month."""
    today = date.today()
    start_limit = effective_start_date(user)

    # Fetch just the records that could fall in this month's visible grid.
    cal = pycal.Calendar(firstweekday=0)  # Monday first
    month_dates = [d for d in cal.itermonthdates(year, month)]
    range_start, range_end = month_dates[0], month_dates[-1]
    recs = StepRecord.query.filter(
        StepRecord.user_id == user.id,
        StepRecord.date >= range_start,
        StepRecord.date <= range_end,
    ).all()
    records = {r.date: r.step_count for r in recs}


    weeks = []
    week = []
    for d in month_dates:
        is_future = d > today
        is_before_start = d < start_limit
        info = {
            "date": d,
            "iso": d.isoformat(),
            "day": d.day,
            "in_month": d.month == month,
            "is_today": d == today,
            "is_future": is_future,
            "is_before_start": is_before_start,
            "has_record": d in records,
            "steps": records.get(d),
            "editable": (d.month == month) and not is_future and not is_before_start,
        }
        week.append(info)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week)
    return weeks


@steps_bp.route("/steps")
@login_required
def index():
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month
    if month < 1 or month > 12:
        year, month = today.year, today.month

    weeks = _build_month_grid(current_user, year, month)

    # Clamp month navigation so users can't browse to a month entirely
    # before the challenge started or... they may still browse history freely,
    # but never past the current month.
    first_of_this_month = date(year, month, 1)
    if month == 12:
        next_year, next_m = year + 1, 1
    else:
        next_year, next_m = year, month + 1
    if month == 1:
        prev_year, prev_m = year - 1, 12
    else:
        prev_year, prev_m = year, month - 1

    current_month_start = date(today.year, today.month, 1)
    can_go_next = date(next_year, next_m, 1) <= current_month_start

    stats = compute_user_stats(current_user)

    return render_template(
        "steps/index.html",
        weeks=weeks,
        month_label=first_of_this_month.strftime("%B %Y"),
        year=year,
        month=month,
        prev_year=prev_year,
        prev_month=prev_m,
        next_year=next_year,
        next_month=next_m,
        can_go_next=can_go_next,
        stats=stats,
        max_steps=current_app.config["MAX_PLAUSIBLE_DAILY_STEPS"],
    )


@steps_bp.route("/api/steps", methods=["POST"])
@login_required
def save_step():
    payload = request.get_json(silent=True) or request.form
    raw_date = payload.get("date")
    raw_steps = payload.get("steps")

    try:
        entry_date = date.fromisoformat(str(raw_date))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid date."}), 400

    today = date.today()
    start_limit = effective_start_date(current_user)
    if entry_date > today:
        return jsonify({"success": False, "error": "You can't record steps for a future date."}), 400
    if entry_date < start_limit:
        return jsonify(
            {"success": False, "error": f"Steps can only be recorded from {start_limit.strftime('%d %b %Y')} onwards."}
        ), 400

    step_count, error = parse_step_count(raw_steps)
    if error:
        return jsonify({"success": False, "error": error}), 400

    record = StepRecord.query.filter_by(user_id=current_user.id, date=entry_date).first()
    created = False
    if record:
        record.step_count = step_count
    else:
        record = StepRecord(user_id=current_user.id, date=entry_date, step_count=step_count)
        db.session.add(record)
        created = True
    db.session.commit()

    stats = compute_user_stats(current_user)

    return jsonify(
        {
            "success": True,
            "created": created,
            "date": entry_date.isoformat(),
            "steps": step_count,
            "message": f"Saved {step_count:,} steps for {entry_date.strftime('%A %d %B')}.",
            "totals": {
                "total_steps": stats["total_steps"],
                "avg_per_active_day": round(stats["avg_per_active_day"]),
                "avg_per_active_week": round(stats["avg_per_active_week"]),
                "avg_per_active_month": round(stats["avg_per_active_month"]),
                "active_days": stats["active_days"],
            },
        }
    )
