"""Seed the database with demo data for local development / testing.

Run with:  python seed.py
This wipes existing data and recreates a fresh demo dataset so every page
(record steps, progress, team, leaderboard, message board) has something
useful to show. All demo accounts use the password: demo1234
"""
import random
from datetime import date, datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, Team, StepRecord, Post, Reply

DEMO_PASSWORD = "demo1234"

TEAM_DEFS = ["The Striders", "Step Squad", "Marathon Mavericks", "Pace Setters"]

MEMBER_DEFS = {
    "The Striders": [("Sarah", "Jenkins"), ("David", "Patel"), ("Tom", "Wilson"), ("Emma", "Roberts")],
    "Step Squad": [("Priya", "Nair"), ("Liam", "O'Connor"), ("Grace", "Kim"), ("Noah", "Fischer")],
    "Marathon Mavericks": [("Olivia", "Bennett"), ("James", "Chen"), ("Mia", "Thompson")],
    "Pace Setters": [("Ethan", "Clarke"), ("Ava", "Morgan"), ("Lucas", "Silva"), ("Zoe", "Adams")],
}

SAMPLE_POSTS = [
    "Great start to the challenge everyone, let's keep it up! 🎉",
    "Hit 12,000 steps on my lunchtime walk today - who's joining tomorrow?",
    "Rainy days are no excuse, laps around the office it is ☔👟",
    "Shoutout to Marathon Mavericks for the strong week!",
    "Anyone fancy a walking meeting instead of sitting in the conference room?",
]

SAMPLE_REPLIES = [
    "Count me in!",
    "Nice work! 💪",
    "That's the spirit.",
    "Let's go team!",
]


def random_step_count(rng, base):
    variation = rng.randint(-3000, 4000)
    return max(0, base + variation)


def seed():
    app = create_app()
    with app.app_context():
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()

        rng = random.Random(42)

        print("Creating teams...")
        teams = {}
        for name in TEAM_DEFS:
            team = Team(name=name, date_created=datetime.utcnow() - timedelta(days=60))
            db.session.add(team)
            teams[name] = team
        db.session.flush()

        print("Creating users...")
        all_users = []
        for team_name, members in MEMBER_DEFS.items():
            for first, last in members:
                email = f"{first.lower()}.{last.lower().replace(chr(39), '')}@example.com"
                joined_days_ago = rng.randint(40, 55)
                user = User(
                    first_name=first,
                    last_name=last,
                    email=email,
                    team=teams[team_name],
                    date_joined=datetime.utcnow() - timedelta(days=joined_days_ago),
                )
                user.set_password(DEMO_PASSWORD)
                db.session.add(user)
                all_users.append(user)

        admin = User(
            first_name="Alex",
            last_name="Admin",
            email="admin@example.com",
            team=None,
            date_joined=datetime.utcnow() - timedelta(days=60),
            is_admin=True,
        )
        admin.set_password(DEMO_PASSWORD)
        db.session.add(admin)
        db.session.flush()

        print("Creating step records...")
        today = date.today()
        challenge_start = app.config.get("CHALLENGE_START_DATE") or (today - timedelta(days=45))
        for user in all_users:
            join_date = user.date_joined.date()
            start = max(challenge_start, join_date)
            base = rng.randint(5000, 11000)
            cursor = start
            while cursor < today:
                # Simulate real-life gaps: ~85% chance a day was logged.
                if rng.random() < 0.85:
                    steps = random_step_count(rng, base)
                    db.session.add(StepRecord(user_id=user.id, date=cursor, step_count=steps))
                cursor += timedelta(days=1)

        db.session.flush()

        print("Creating message board posts...")
        posters = rng.sample(all_users, k=min(len(SAMPLE_POSTS), len(all_users)))
        posts = []
        for i, text in enumerate(SAMPLE_POSTS):
            created = datetime.utcnow() - timedelta(hours=(len(SAMPLE_POSTS) - i) * 5)
            post = Post(
                user_id=posters[i % len(posters)].id,
                message=text,
                created_at=created,
                updated_at=created,
            )
            db.session.add(post)
            posts.append(post)
        db.session.flush()

        for post in posts[:3]:
            replier = rng.choice(all_users)
            reply_created = post.created_at + timedelta(minutes=30)
            db.session.add(
                Reply(
                    post_id=post.id,
                    user_id=replier.id,
                    message=rng.choice(SAMPLE_REPLIES),
                    created_at=reply_created,
                    updated_at=reply_created,
                )
            )

        db.session.commit()
        print(f"Done. Created {len(all_users)} users across {len(TEAM_DEFS)} teams, plus 1 admin.")
        print(f"All demo accounts use the password: {DEMO_PASSWORD}")
        print("Try logging in as: sarah.jenkins@example.com / admin@example.com")


if __name__ == "__main__":
    seed()
