
from flask import Flask, jsonify, render_template
from config import Config
from app.extensions import db, migrate, login_manager, csrf
from app.models import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 2. Load user from database
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # 3. Homepage
    @app.get("/")
    def home():
        return render_template("index.html")

    # 4. Health check
    @app.get("/api/health")
    def health_check():
        return jsonify({
            "application": "SmartOps Management System",
            "status": "running"
        })
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.inventory import inventory_bp
    app.register_blueprint(inventory_bp)

    return app