"""Custom Jinja filters/globals."""
from datetime import date


def format_number(value):
    if value is None:
        return "-"
    return f"{round(value):,}"


def format_avg(value):
    if value is None:
        return "-"
    return f"{value:,.0f}"


def date_range_label(start, end):
    if start.month == end.month:
        return f"{start.strftime('%-d')} - {end.strftime('%-d %b %Y')}"
    return f"{start.strftime('%-d %b')} - {end.strftime('%-d %b %Y')}"


def friendly_datetime(value):
    if value is None:
        return "-"
    return value.strftime("%d %b %Y, %H:%M")


def register_template_filters(app):
    app.jinja_env.filters["num"] = format_number
    app.jinja_env.filters["avg"] = format_avg
    app.jinja_env.filters["daterange"] = date_range_label
    app.jinja_env.filters["friendly_dt"] = friendly_datetime
    app.jinja_env.globals["today"] = date.today
    app.jinja_env.globals["challenge_name"] = lambda: app.config["CHALLENGE_NAME"]
