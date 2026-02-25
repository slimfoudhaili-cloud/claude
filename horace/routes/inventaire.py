from flask import Blueprint, render_template
from ..models import Produit

inventaire_bp = Blueprint("inventaire", __name__)

CATEGORIES_ORDER = ["Visage", "Yeux", "Barbe", "Cheveux"]


@inventaire_bp.route("/inventaire")
def inventaire():
    produits = Produit.query.filter_by(actif=True).order_by(Produit.nom).all()

    # Group by category, respecting preferred order
    grouped = {}
    for p in produits:
        grouped.setdefault(p.categorie, []).append(p)

    categories = []
    seen = set()
    for cat in CATEGORIES_ORDER:
        if cat in grouped:
            categories.append((cat, grouped[cat]))
            seen.add(cat)
    # Any extra categories not in the preferred order
    for cat, items in grouped.items():
        if cat not in seen:
            categories.append((cat, items))

    return render_template("inventaire.html", categories=categories)
