
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 12:
            flash("Please provide valid details and a password of at least 12 characters.")

        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.")

        else:
            user = User(name=name, email=email)
            user.set_password(password)

            db.session.add(user)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Unable to register. Please check your details.")
            else:
                flash("Account created successfully!")
                return redirect(url_for("auth.register"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!")
            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.")
    return redirect(url_for("auth.login"))


# ==========================================
# SECURITY: DISABLE PUBLIC REGISTRATION
# ==========================================

from flask import abort, request


@auth_bp.before_request
def block_public_registration():

    # Block both GET and POST requests to /register
    if request.endpoint == "auth.register":
        abort(404)
