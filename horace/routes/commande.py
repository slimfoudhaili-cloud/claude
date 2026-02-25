from datetime import datetime
from flask import Blueprint, render_template
from ..models import Produit

commande_bp = Blueprint("commande", __name__)

CATEGORIES_ORDER = ["Visage", "Yeux", "Barbe", "Cheveux"]


@commande_bp.route("/commande")
def commande():
    produits = Produit.query.filter_by(actif=True).order_by(Produit.nom).all()
    a_commander = [p for p in produits if p.statut in ("rupture", "alerte")]

    grouped = {}
    for p in a_commander:
        grouped.setdefault(p.categorie, []).append(p)

    categories = []
    seen = set()
    for cat in CATEGORIES_ORDER:
        if cat in grouped:
            categories.append((cat, grouped[cat]))
            seen.add(cat)
    for cat, items in grouped.items():
        if cat not in seen:
            categories.append((cat, items))

    now = datetime.now().strftime("%d %B %Y")
    return render_template("commande.html", categories=categories,
                           total=len(a_commander), now=now)
