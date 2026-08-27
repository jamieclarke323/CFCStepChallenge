"""Authentication routes: register, login, logout."""
from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db, limiter
from ..models import User, Team
from .forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("steps.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form)
        if not user.is_active_account:
            flash("This account has been disabled. Contact an administrator.", "error")
            return render_template("auth/login.html", form=form)

        # Always persist the login for the configured "remember me" duration
        # (see requirement: stay logged in >= 35 days unless explicitly logged out).
        login_user(user, remember=True)

        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("steps.index")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("steps.index"))

    form = RegisterForm()
    form.team_id.choices = [(0, "-- select a team --")] + [
        (t.id, t.name) for t in Team.query.order_by(Team.name).all()
    ]

    if form.validate_on_submit():
        team = None
        new_team_name = form.new_team_name.data.strip()
        if new_team_name:
            team = Team(name=new_team_name)
            db.session.add(team)
            db.session.flush()
        elif form.team_id.data:
            team = db.session.get(Team, form.team_id.data)

        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.lower().strip(),
            team=team,
            date_joined=datetime.utcnow(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)
        flash(f"Welcome aboard, {user.first_name}! Your account has been created.", "success")
        return redirect(url_for("steps.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
