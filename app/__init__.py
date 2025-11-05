from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize SQLAlchemy instance (outside create_app for import access)
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Configuration
    ## Generate a secure random key using secrets.token_hex(32)
    app.config["SECRET_KEY"] = "your-secret-key-change-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sales.sqlite"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # User loader function for Flask-Login
    from .models import User, Sale

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from .main import main_blueprint as main_blueprint

    app.register_blueprint(main_blueprint)

    # Create tables if don't exist

    from .models import (
        db as temp_db_import_for_creation,
    )  # Import db to use it in context

    return app
