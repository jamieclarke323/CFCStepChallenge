"""Database models."""
from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    multiplier = db.Column(db.Float, default=1.0, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    members = db.relationship("User", back_populates="team", order_by="User.first_name")

    def image_url(self):
        if self.image_filename:
            return f"/static/uploads/teams/{self.image_filename}"
        return "/static/img/default-team.svg"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    account_status = db.Column(db.String(20), default="active", nullable=False)  # active | disabled
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    team = db.relationship("Team", back_populates="members")
    step_records = db.relationship(
        "StepRecord", back_populates="user", cascade="all, delete-orphan"
    )
    posts = db.relationship("Post", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def display_name(self):
        """Public-facing name: first name + last initial (never expose full surname)."""
        last_initial = f"{self.last_name[0].upper()}." if self.last_name else ""
        return f"{self.first_name} {last_initial}".strip()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active_account(self):
        return self.account_status == "active"

    @property
    def is_active(self):  # UserMixin override, used by Flask-Login
        return self.account_status == "active"


class StepRecord(db.Model):
    __tablename__ = "step_records"
    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_step_record_user_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    step_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="step_records")


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="posts")
    replies = db.relationship(
        "Reply", back_populates="post", cascade="all, delete-orphan", order_by="Reply.created_at"
    )

    @property
    def is_edited(self):
        # created_at/updated_at defaults are evaluated independently at insert
        # time, so allow a small tolerance before treating a post as "edited".
        return (self.updated_at - self.created_at).total_seconds() > 2


class Reply(db.Model):
    __tablename__ = "replies"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    post = db.relationship("Post", back_populates="replies")
    user = db.relationship("User")

    @property
    def is_edited(self):
        return (self.updated_at - self.created_at).total_seconds() > 2
