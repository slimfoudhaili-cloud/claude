from .dashboard import dashboard_bp
from .inventaire import inventaire_bp
from .stock import stock_bp
from .commande import commande_bp
from .admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventaire_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(commande_bp)
    app.register_blueprint(admin_bp)
