import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

load_dotenv()  # <-- Load variables from .env file FIRST


# Initialize SQLAlchemy instance (outside create_app for import access)
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # --- START DATABASE URI LOGIC ---
    # 2. Get environment variables for PostgreSQL connection
    # We use .get() to safely check if the variable exists.
    postgres_user = os.environ.get("POSTGRES_USER")
    postgres_password = os.environ.get("POSTGRES_PASSWORD")
    postgres_db = os.environ.get("POSTGRES_DB")
    db_host = os.environ.get("DB_HOST")

    # 3. Determine the final SQLAlchemy URI
    if postgres_user and postgres_password and postgres_db and db_host:
        db_uri = f"postgresql://{postgres_user}:{postgres_password}@{db_host}:5432/{postgres_db}"
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    else:
        # 🚨 NEW: Raise an error if connection details are missing (no SQLite fallback)
        raise EnvironmentError(
            "CRITICAL: PostgreSQL environment variables are not set. Cannot run in production mode."
        )

    # Configuration
    ## Generate a secure random key using secrets.token_hex(32)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # User loader function for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .main import main_blueprint

    app.register_blueprint(main_blueprint)

    return app
