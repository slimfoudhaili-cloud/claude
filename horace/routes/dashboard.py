from flask import Blueprint, render_template
from ..models import Produit, ConsommationLog

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    produits = Produit.query.filter_by(actif=True).all()
    rupture = sum(1 for p in produits if p.statut == "rupture")
    alerte = sum(1 for p in produits if p.statut == "alerte")
    ok = sum(1 for p in produits if p.statut == "ok")
    logs = (ConsommationLog.query
            .order_by(ConsommationLog.created_at.desc())
            .limit(10)
            .all())
    return render_template("index.html",
                           rupture=rupture, alerte=alerte, ok=ok, logs=logs)
