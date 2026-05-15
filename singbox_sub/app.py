from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .admin import admin_bp
from .subscription import subscription_bp


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(admin_bp)
    app.register_blueprint(subscription_bp)

    return app
