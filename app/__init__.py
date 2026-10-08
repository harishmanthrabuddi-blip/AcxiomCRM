from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.crm import crm_bp
    from app.admin import admin_bp
    from app.api import api_bp
    from app.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reports_bp)

    return app
