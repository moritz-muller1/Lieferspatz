"""Application factory."""
from flask import Flask

from config import Config
from app import db, storage


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    storage.init_app(app)

    from app.blueprints.main import bp as main_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.customer import bp as customer_bp
    from app.blueprints.restaurant import bp as restaurant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(restaurant_bp)

    return app
