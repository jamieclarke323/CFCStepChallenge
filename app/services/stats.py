"""Server-side step, team and ranking calculations.

All competition math lives here so the frontend never has to be trusted with
totals, averages or rankings. Two flavours of "average" are calculated
throughout, and both are always labelled clearly wherever they are shown:

* "per active day" - total steps / number of days the user actually logged a
  step count. This is the headline figure because it never pretends a day
  with no record was a zero-step day.
* "per calendar day" - total steps / number of calendar days that have
  elapsed since the challenge (or the user's membership) began. This shows
  how someone is doing across the whole challenge, including gaps.

Competition rule: missing days are NEVER treated as zero when computing
"per active day" averages - they are simply excluded from that average's
denominator. They *do* count as zero implicitly for "per calendar day"
averages, and that is called out in the label everywhere it is displayed.
"""
from collections import OrderedDict
from datetime import date, timedelta

from flask import current_app

from ..extensions import db
from ..models import StepRecord, User, Team


def effective_start_date(user):
    """The earliest date this user may have steps counted towards stats."""
    challenge_start = current_app.config.get("CHALLENGE_START_DATE")
    join_date = user.date_joined.date() if user.date_joined else date.today()
    if challenge_start:
        return max(challenge_start, join_date)
    return join_date


def effective_end_date():
    challenge_end = current_app.config.get("CHALLENGE_END_DATE")
    today = date.today()
    if challenge_end and challenge_end < today:
        return challenge_end
    return today


def iso_week_bounds(d):
    """Return (monday, sunday) for the ISO week containing date d."""
    monday = d - timedelta(days=d.isoweekday() - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_user_records(user_id, order="asc"):
    q = StepRecord.query.filter_by(user_id=user_id)
    q = q.order_by(StepRecord.date.asc() if order == "asc" else StepRecord.date.desc())
    return q.all()


def compute_user_stats(user):
    """Return a dict of all headline + breakdown stats for a single user."""
    records = get_user_records(user.id)
    total_steps = sum(r.step_count for r in records)
    active_days = len(records)

    start = effective_start_date(user)
    end = effective_end_date()
    calendar_days_elapsed = max((end - start).days + 1, 0) if end >= start else 0

    avg_per_active_day = (total_steps / active_days) if active_days else 0
    avg_per_calendar_day = (total_steps / calendar_days_elapsed) if calendar_days_elapsed else 0

    # --- Daily breakdown: every calendar day in range, None where no record ---
    by_date = {r.date: r.step_count for r in records}
    daily_breakdown = []
    cursor = start
    while cursor <= end:
        daily_breakdown.append({"date": cursor, "steps": by_date.get(cursor)})
        cursor += timedelta(days=1)

    # --- Weekly breakdown: group by ISO week ---
    weekly_map = OrderedDict()
    for r in records:
        wk_start, wk_end = iso_week_bounds(r.date)
        key = wk_start
        if key not in weekly_map:
            weekly_map[key] = {"week_start": wk_start, "week_end": wk_end, "total": 0, "active_days": 0}
        weekly_map[key]["total"] += r.step_count
        weekly_map[key]["active_days"] += 1
    weekly_breakdown = []
    for wk in sorted(weekly_map.values(), key=lambda w: w["week_start"]):
        wk["avg_daily"] = wk["total"] / wk["active_days"] if wk["active_days"] else 0
        weekly_breakdown.append(wk)

    # --- Monthly breakdown: group by calendar month ---
    monthly_map = OrderedDict()
    for r in records:
        key = (r.date.year, r.date.month)
        if key not in monthly_map:
            monthly_map[key] = {
                "year": r.date.year,
                "month": r.date.month,
                "label": r.date.strftime("%B %Y"),
                "total": 0,
                "active_days": 0,
            }
        monthly_map[key]["total"] += r.step_count
        monthly_map[key]["active_days"] += 1
    monthly_breakdown = []
    for m in sorted(monthly_map.values(), key=lambda m: (m["year"], m["month"])):
        m["avg_daily"] = m["total"] / m["active_days"] if m["active_days"] else 0
        monthly_breakdown.append(m)

    weeks_with_data = len(weekly_breakdown)
    months_with_data = len(monthly_breakdown)
    avg_per_active_week = (total_steps / weeks_with_data) if weeks_with_data else 0
    avg_per_active_month = (total_steps / months_with_data) if months_with_data else 0

    last_recorded = records[-1].date if records else None

    return {
        "user": user,
        "total_steps": total_steps,
        "active_days": active_days,
        "calendar_days_elapsed": calendar_days_elapsed,
        "avg_per_active_day": avg_per_active_day,
        "avg_per_calendar_day": avg_per_calendar_day,
        "avg_per_active_week": avg_per_active_week,
        "avg_per_active_month": avg_per_active_month,
        "daily_breakdown": daily_breakdown,
        "weekly_breakdown": weekly_breakdown,
        "monthly_breakdown": monthly_breakdown,
        "last_recorded": last_recorded,
        "effective_start": start,
        "effective_end": end,
    }


def compute_team_stats(team):
    """Aggregate stats for every member of a team."""
    member_stats = [compute_user_stats(m) for m in team.members]
    team_total = sum(s["total_steps"] for s in member_stats)
    active_member_stats = [s for s in member_stats if s["active_days"] > 0]
    # Team average = mean of each member's own "per active day" average, so
    # team size / tenure differences don't skew the figure.
    team_avg_per_active_day = (
        sum(s["avg_per_active_day"] for s in active_member_stats) / len(active_member_stats)
        if active_member_stats
        else 0
    )

    # Combine daily/weekly/monthly breakdowns across the whole team.
    daily_totals = OrderedDict()
    weekly_totals = OrderedDict()
    monthly_totals = OrderedDict()
    for s in member_stats:
        for day in s["daily_breakdown"]:
            if day["steps"] is None:
                continue
            daily_totals.setdefault(day["date"], 0)
            daily_totals[day["date"]] += day["steps"]
        for wk in s["weekly_breakdown"]:
            key = wk["week_start"]
            entry = weekly_totals.setdefault(
                key, {"week_start": wk["week_start"], "week_end": wk["week_end"], "total": 0}
            )
            entry["total"] += wk["total"]
        for m in s["monthly_breakdown"]:
            key = (m["year"], m["month"])
            entry = monthly_totals.setdefault(
                key, {"year": m["year"], "month": m["month"], "label": m["label"], "total": 0}
            )
            entry["total"] += m["total"]

    daily_breakdown = [{"date": d, "steps": v} for d, v in sorted(daily_totals.items())]
    weekly_breakdown = sorted(weekly_totals.values(), key=lambda w: w["week_start"])
    monthly_breakdown = sorted(monthly_totals.values(), key=lambda m: (m["year"], m["month"]))

    return {
        "team": team,
        "member_stats": member_stats,
        "member_count": len(member_stats),
        "team_total_steps": team_total,
        "team_avg_per_active_day": team_avg_per_active_day,
        "daily_breakdown": daily_breakdown,
        "weekly_breakdown": weekly_breakdown,
        "monthly_breakdown": monthly_breakdown,
    }


def _tie_break_key(total_steps, avg_per_active_day, joined_at, entity_id):
    """Deterministic sort key for leaderboard ties.

    Order: 1) total steps desc, 2) avg steps per active day desc (rewards
    consistency over one-off spikes), 3) earliest joined/created first,
    4) id ascending as a final deterministic fallback.
    """
    return (-total_steps, -avg_per_active_day, joined_at, entity_id)


def _apply_team_multiplier(row):
    """Apply the persisted team multiplier to its leaderboard score."""
    multiplier = row["team"].multiplier or 1.0
    row["team_total_steps"] *= multiplier
    row["team_avg_per_active_day"] *= multiplier
    row["multiplier_percent"] = round((multiplier - 1) * 100)
    return row


def get_individual_rankings(period=None, year=None, month=None):
    """Return users ranked by total steps, with the tie-break rule applied.

    If `period` == 'month' and `year`/`month` are provided, compute totals
    and averages only for that calendar month. Otherwise falls back to the
    full-history ranking (existing behaviour).
    """
    users = User.query.filter_by(account_status="active").all()
    rows = []

    # If monthly view requested compute stats for that month only
    if period == "month" and year and month:
        start = date(int(year), int(month), 1)
        if int(month) == 12:
            next_month = date(int(year) + 1, 1, 1)
        else:
            next_month = date(int(year), int(month) + 1, 1)
        end = next_month - timedelta(days=1)

        for u in users:
            q = StepRecord.query.filter(
                StepRecord.user_id == u.id,
                StepRecord.date >= start,
                StepRecord.date <= end,
            ).order_by(StepRecord.date.asc())
            records = q.all()
            total_steps = sum(r.step_count for r in records)
            active_days = len(records)
            avg_per_active_day = total_steps / active_days if active_days else 0
            rows.append({"user": u, "total_steps": total_steps, "avg_per_active_day": avg_per_active_day, "active_days": active_days})
    else:
        for u in users:
            stats = compute_user_stats(u)
            rows.append({**stats, "user": u})

    rows.sort(
        key=lambda r: _tie_break_key(
            r["total_steps"], r["avg_per_active_day"], r["user"].date_joined, r["user"].id
        )
    )
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def get_team_rankings(period=None, year=None, month=None):
    """Return teams ranked by total steps, with the tie-break rule applied.

    Supports monthly aggregation when `period=='month'` and `year`/`month`
    are supplied. Returns the same structure as before so templates need no
    changes beyond using the values which may be month-scoped.
    """
    teams = Team.query.all()
    rows = []

    # Monthly range if requested
    if period == "month" and year and month:
        start = date(int(year), int(month), 1)
        if int(month) == 12:
            next_month = date(int(year) + 1, 1, 1)
        else:
            next_month = date(int(year), int(month) + 1, 1)
        end = next_month - timedelta(days=1)

        for t in teams:
            # Build member stats scoped to range
            member_stats = []
            for m in t.members:
                q = StepRecord.query.filter(
                    StepRecord.user_id == m.id,
                    StepRecord.date >= start,
                    StepRecord.date <= end,
                ).order_by(StepRecord.date.asc())
                records = q.all()
                total_steps = sum(r.step_count for r in records)
                active_days = len(records)
                avg_per_active_day = total_steps / active_days if active_days else 0
                member_stats.append({"user": m, "total_steps": total_steps, "active_days": active_days, "avg_per_active_day": avg_per_active_day})

            team_total = sum(s["total_steps"] for s in member_stats)
            active_member_stats = [s for s in member_stats if s["active_days"] > 0]
            team_avg_per_active_day = (
                sum(s["avg_per_active_day"] for s in active_member_stats) / len(active_member_stats)
                if active_member_stats
                else 0
            )

            rows.append(_apply_team_multiplier({
                "team": t,
                "member_stats": member_stats,
                "member_count": len(member_stats),
                "team_total_steps": team_total,
                "team_avg_per_active_day": team_avg_per_active_day,
            }))
    else:
        for t in teams:
            stats = compute_team_stats(t)
            avg_of_active_days = (
                sum(s["avg_per_active_day"] for s in stats["member_stats"]) / len(stats["member_stats"]) 
                if stats["member_stats"]
                else 0
            )
            rows.append(_apply_team_multiplier({**stats, "team": t, "_tiebreak_avg": avg_of_active_days}))

    # Ensure deterministic ordering with same tie-break rule
    rows.sort(
        key=lambda r: _tie_break_key(
            r.get("team_total_steps", 0), r.get("team_avg_per_active_day", r.get("_tiebreak_avg", 0)), r["team"].date_created, r["team"].id
        )
    )
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows
