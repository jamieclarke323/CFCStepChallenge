"""Global error handlers."""
from flask import render_template, request, jsonify


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/error.html", code=404, message="Page not found"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/error.html", code=403, message="You don't have access to that."), 403

    @app.errorhandler(413)
    def too_large(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "File is too large."}), 413
        return render_template("errors/error.html", code=413, message="That file is too large."), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/error.html", code=500, message="Something went wrong on our end."), 500
