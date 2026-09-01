# Steptember

A mobile-first web app for running a workplace step-count challenge: teams,
daily step tracking, personal/team progress dashboards, a leaderboard, and a
message board.

Built with **Python (Flask)**, **SQLAlchemy** + **SQLite**, server-rendered
Jinja templates, vanilla JS, and Chart.js. All competition maths (totals,
averages, rankings) is calculated server-side - the frontend never supplies
or trusts a total.

## Features

- Email/password authentication (Flask-Login) with persistent sessions -
  users stay logged in for **35 days** unless they explicitly log out.
- **Record Steps**: monthly calendar, one step-record per user/day, edit
  existing entries, future dates and pre-challenge dates blocked both in the
  UI and on the server.
- **My Progress**: total/avg-per-day/week/month, a daily chart, and
  weekly/monthly breakdown tables with improving/declining trend indicators.
- **My Team**: team overview, ranking, per-member stats table, team charts,
  and in-place editing of the team name/logo (image is auto square-cropped
  and resized).
- **Leaderboard**: Teams vs Individuals toggle; each team card shows its
  members (first name + last initial) inline, no expand/click required.
- **Message Board**: posts + replies, newest-first, users can delete their
  own posts/replies, admins can delete any.
- Security: CSRF protection on all forms, bcrypt-strength password hashing
  (Werkzeug `pbkdf2:sha256`), per-route rate limiting on login/register,
  security response headers + a strict CSP, validated/re-encoded image
  uploads, and access control on every mutating endpoint.

## Requirements

- Python 3.11+ (tested on 3.13/3.14)

## Setup

```bash
cd StepChallengeApp
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set a real SECRET_KEY, e.g.:
python -c "import secrets; print(secrets.token_hex(32))"
```

## Seed demo data

Creates 4 teams, 15 users + 1 admin, ~45 days of step history, and some
message board posts/replies. **This wipes any existing data.**

```bash
python seed.py
```

All seeded accounts use the password `demo1234`. Try:
`sarah.jenkins@example.com` (regular user) or `admin@example.com` (admin,
no team, can delete any message board post).

## Run

```bash
python run.py
```

Visit http://localhost:3000

For production, run behind a real WSGI server, e.g.:

```bash
gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app
```

...and put it behind HTTPS (the app automatically marks cookies `Secure`
when `FLASK_ENV=production`).

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Session/cookie signing key - must be random and secret |
| `DATABASE_URL` | Optional; defaults to `instance/step_challenge.db` |
| `CHALLENGE_NAME` | Shown in the nav bar and page titles |
| `CHALLENGE_START_DATE` | Steps can't be recorded before this date |
| `CHALLENGE_END_DATE` | Optional end date for "days elapsed" calculations |
| `MAX_PLAUSIBLE_DAILY_STEPS` | Upper bound for a single day's step entry |
| `REMEMBER_COOKIE_DAYS` | Login persistence length (requirement: ≥ 35) |
| `MAX_UPLOAD_MB` | Max team image upload size |

## Project structure

```
app/
  __init__.py          # App factory, extension wiring, security headers
  config.py            # Env-driven configuration
  models.py            # User, Team, StepRecord, Post, Reply
  services/
    stats.py           # All step/team/ranking calculations (server-side only)
    images.py           # Team logo validation, crop, resize
  auth/ steps/ progress/ team/ leaderboard/ messages/ main/
                        # One blueprint per feature area
  templates/            # Jinja templates (mobile-first, one dir per section)
  static/                # CSS, vanilla JS, Chart.js (vendored), uploads
seed.py                  # Demo data generator
run.py / wsgi.py         # Dev / production entry points
```

## Key design notes

- **Duplicate step prevention**: `step_records` has a unique constraint on
  `(user_id, date)`; `POST /api/steps` looks up an existing record for that
  date and updates it in place rather than inserting a second row.
- **Averages**: "per active day/week/month" only divides by periods the user
  actually logged steps (gaps are never silently treated as zero). A
  secondary "per calendar day" figure (gaps counted as zero) is shown on the
  Progress page for reference, clearly labelled.
- **Leaderboard tie-break**: total steps desc → average steps per active day
  desc (rewards consistency) → earliest joined/created → id. Applied
  identically for both team and individual rankings.
- **Rankings update automatically**: they're computed fresh from the
  database on every page load - there's no cached/stale leaderboard state to
  recalculate.
- **Public names**: `User.display_name` always renders as "First L." -
  templates never expose email addresses or full surnames.

## Manual test checklist

- [x] Register a new account, log in, log out
- [x] Session persists for 35 days (`Set-Cookie ... Expires=...`)
- [x] Record steps for today; edit an existing day's steps (no duplicate row)
- [x] Future dates and pre-challenge-start dates are not selectable/saveable
- [x] Validation: negative, non-integer, and implausibly large step counts rejected
- [x] Daily/weekly/monthly stats and charts match recorded data
- [x] Team stats, ranking, member list, and name/image editing
- [x] Individual + team leaderboards, tie-break behaviour, "you"/"your team" highlight
- [x] Message posting, replying, deleting own post, admin deleting any post
- [x] CSRF rejected without a token; non-owner blocked from deleting others' posts (403)
- [x] Mobile viewport (390px) layout: bottom tab bar, no horizontal scroll
