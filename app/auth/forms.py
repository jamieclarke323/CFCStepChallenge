"""WTForms definitions for authentication."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError

from ..models import User


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class RegisterForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=60)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    team_id = SelectField("Join an existing team", coerce=int, validators=[Optional()])
    new_team_name = StringField("...or create a new team", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")

    def validate_new_team_name(self, field):
        from ..models import Team

        name = (field.data or "").strip()
        if name and Team.query.filter(Team.name.ilike(name)).first():
            raise ValidationError("A team with this name already exists - please choose it from the list instead.")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if not self.new_team_name.data.strip() and not self.team_id.data:
            self.team_id.errors.append("Choose an existing team or enter a new team name.")
            return False
        return True
