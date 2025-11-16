from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    name = StringField(
        "Username",
        validators=[
            DataRequired(message="Username cannot be blank"),
            Length(min=2, max=20, message="Name should be 2 to 20 characters long"),
        ],
    )

    email = EmailField(
        "Email",
        validators=[
            DataRequired(message="Your email is needed"),
            Email(message="Provide a valid email address"),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Secure and memorable password"),
            Length(min=8, message="Minimum 8 characters long"),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Confirm your password"),
            EqualTo("password", message="Passwords must match"),
        ],
    )

    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(message="Your email is needed"),
            Email(message="Provide a valid email address"),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Secure and memorable password"),
            Length(min=8, message="Minimum 8 characters long"),
        ],
    )
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")
