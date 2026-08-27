"""Message board: posts, replies, and moderation (own-post + admin delete)."""
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Post, Reply

messages_bp = Blueprint("messages", __name__)

MAX_MESSAGE_LENGTH = 1000
POST_COOLDOWN_SECONDS = 5  # basic spam throttle


def _too_soon_since_last_post():
    last = (
        Post.query.filter_by(user_id=current_user.id)
        .order_by(Post.created_at.desc())
        .first()
    )
    if last and (datetime.utcnow() - last.created_at) < timedelta(seconds=POST_COOLDOWN_SECONDS):
        return True
    return False


@messages_bp.route("/messages")
@login_required
def index():
    posts = (
        Post.query.filter_by(is_deleted=False)
        .order_by(Post.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("messages/index.html", posts=posts)


@messages_bp.route("/messages", methods=["POST"])
@login_required
def create_post():
    message = (request.form.get("message") or "").strip()
    if not message:
        flash("Message can't be empty.", "error")
    elif len(message) > MAX_MESSAGE_LENGTH:
        flash(f"Message is too long (max {MAX_MESSAGE_LENGTH} characters).", "error")
    elif _too_soon_since_last_post():
        flash("You're posting a little too fast - please wait a few seconds.", "error")
    else:
        post = Post(user_id=current_user.id, message=message)
        db.session.add(post)
        db.session.commit()
        flash("Posted!", "success")
    return redirect(url_for("messages.index"))


@messages_bp.route("/messages/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    post.is_deleted = True
    post.deleted_at = datetime.utcnow()
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("messages.index"))


@messages_bp.route("/messages/<int:post_id>/reply", methods=["POST"])
@login_required
def create_reply(post_id):
    post = db.session.get(Post, post_id)
    if not post or post.is_deleted:
        abort(404)

    message = (request.form.get("message") or "").strip()
    if not message:
        flash("Reply can't be empty.", "error")
    elif len(message) > MAX_MESSAGE_LENGTH:
        flash(f"Reply is too long (max {MAX_MESSAGE_LENGTH} characters).", "error")
    else:
        reply = Reply(post_id=post.id, user_id=current_user.id, message=message)
        db.session.add(reply)
        db.session.commit()
        flash("Reply posted.", "success")
    return redirect(url_for("messages.index", _anchor=f"post-{post_id}"))


@messages_bp.route("/messages/reply/<int:reply_id>/delete", methods=["POST"])
@login_required
def delete_reply(reply_id):
    reply = db.session.get(Reply, reply_id)
    if not reply:
        abort(404)
    if reply.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    reply.is_deleted = True
    reply.deleted_at = datetime.utcnow()
    db.session.commit()
    flash("Reply deleted.", "info")
    return redirect(url_for("messages.index", _anchor=f"post-{reply.post_id}"))
