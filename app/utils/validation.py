"""Shared server-side validation helpers (never trust the browser)."""
from flask import current_app


def parse_step_count(raw_value):
    """Validate a submitted step count.

    Returns (value, error_message). value is None if invalid.
    Rules: required, whole numbers only, no negatives, sensible upper bound.
    """
    if raw_value is None or str(raw_value).strip() == "":
        return None, "Please enter a step count."

    text = str(raw_value).strip()
    try:
        # Reject decimals/floats explicitly - only whole numbers allowed.
        if "." in text or "," in text:
            raise ValueError()
        value = int(text)
    except ValueError:
        return None, "Step count must be a whole number."

    if value < 0:
        return None, "Step count cannot be negative."

    max_steps = current_app.config.get("MAX_PLAUSIBLE_DAILY_STEPS", 100000)
    if value > max_steps:
        return None, f"That's more than {max_steps:,} steps in a day - please check the value."

    return value, None
