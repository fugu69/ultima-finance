from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .forms import RegistrationForm, LoginForm
from . import db

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    # 1. Instantiate the form
    form = LoginForm()

    # 2. Check if the request is a POST and if the form passes validation
    if form.validate_on_submit():
        # The form data is already available via form.<field_name>.data
        email = form.email.data
        password = form.password.data
        remember = form.remember.data

        # Retrieve user from the database
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password, password):
            # Display error message on the same page
            flash("Please check your login details and try again", "danger")
            # When validation fails or login fails, you re-render the template
            # The form object will automatically contain the user's previously submitted data
            return render_template("login.html", form=form)

        # Successful login
        login_user(user, remember=remember)

        # Redirect the user to a protected page (e.g., profile)
        next_page = request.args.get('next')
        return redirect(next_page or url_for("main.index"))

    # 3. Handle GET request or failed POST (re-render with errors)
    # For a GET request, form is empty. For a failed POST, form has errors attached.
    return render_template("login.html", form=form)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email address already registrered, log in", "info")
            return redirect(url_for("auth.login"))

        new_user = User(
            name=name, email=email, password=generate_password_hash(password)
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Your account created! Log In now", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error when create account: {e}", "danger")

    return render_template("signup.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
