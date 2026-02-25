from flask import Blueprint, request, redirect, url_for, flash
from ..models import db, Produit, Stock, ConsommationLog

stock_bp = Blueprint("stock", __name__)


def _get_or_create_stock(produit_id):
    s = Stock.query.filter_by(produit_id=produit_id).first()
    if s is None:
        s = Stock(produit_id=produit_id, quantite=0, en_cours=0)
        db.session.add(s)
        db.session.flush()
    return s


@stock_bp.route("/stock/<int:produit_id>/ouvrir", methods=["POST"])
def ouvrir(produit_id):
    p = Produit.query.get_or_404(produit_id)
    s = _get_or_create_stock(produit_id)

    if p.reserve <= 0:
        flash(f"Impossible : il n'y a pas de {p.nom} en réserve.", "warning")
        return redirect(url_for("inventaire.inventaire"))

    s.en_cours += 1
    log = ConsommationLog(produit_id=produit_id, action="ouvert",
                          delta_quantite=0, delta_en_cours=1,
                          note=None)
    db.session.add(log)
    db.session.commit()
    flash(f"{p.nom} — flacon ouvert. En cours : {s.en_cours}.", "success")
    return redirect(url_for("inventaire.inventaire"))


@stock_bp.route("/stock/<int:produit_id>/terminer", methods=["POST"])
def terminer(produit_id):
    p = Produit.query.get_or_404(produit_id)
    s = _get_or_create_stock(produit_id)

    if s.en_cours <= 0:
        flash(f"Impossible : aucun flacon de {p.nom} n'est en cours.", "warning")
        return redirect(url_for("inventaire.inventaire"))

    s.quantite = max(0, s.quantite - 1)
    s.en_cours = max(0, s.en_cours - 1)
    log = ConsommationLog(produit_id=produit_id, action="termine",
                          delta_quantite=-1, delta_en_cours=-1,
                          note=None)
    db.session.add(log)
    db.session.commit()

    msg = f"{p.nom} — flacon terminé."
    if p.statut in ("rupture", "alerte"):
        msg += " Pensez à commander !"
    flash(msg, "success" if p.statut == "ok" else "warning")
    return redirect(url_for("inventaire.inventaire"))


@stock_bp.route("/stock/<int:produit_id>/restock", methods=["POST"])
def restock(produit_id):
    p = Produit.query.get_or_404(produit_id)
    s = _get_or_create_stock(produit_id)

    try:
        n = int(request.form.get("quantite", 1))
        if n < 1:
            raise ValueError
    except (ValueError, TypeError):
        flash("Quantité invalide.", "danger")
        return redirect(url_for("inventaire.inventaire"))

    s.quantite += n
    log = ConsommationLog(produit_id=produit_id, action="restock",
                          delta_quantite=n, delta_en_cours=0,
                          note=f"+{n} unité(s)")
    db.session.add(log)
    db.session.commit()
    flash(f"{p.nom} — {n} unité(s) ajoutée(s). Stock total : {s.quantite}.", "success")
    return redirect(url_for("inventaire.inventaire"))


@stock_bp.route("/stock/<int:produit_id>/corriger", methods=["POST"])
def corriger(produit_id):
    p = Produit.query.get_or_404(produit_id)
    s = _get_or_create_stock(produit_id)

    try:
        new_quantite = int(request.form.get("quantite", 0))
        new_en_cours = int(request.form.get("en_cours", 0))
        if new_quantite < 0 or new_en_cours < 0:
            raise ValueError
        if new_en_cours > new_quantite:
            raise ValueError
    except (ValueError, TypeError):
        flash("Valeurs invalides (en cours ne peut pas dépasser le total).", "danger")
        return redirect(url_for("inventaire.inventaire"))

    note = request.form.get("note", "").strip()
    if not note:
        flash("Une note est requise pour une correction manuelle.", "danger")
        return redirect(url_for("inventaire.inventaire"))

    dq = new_quantite - s.quantite
    de = new_en_cours - s.en_cours
    s.quantite = new_quantite
    s.en_cours = new_en_cours
    log = ConsommationLog(produit_id=produit_id, action="correction",
                          delta_quantite=dq, delta_en_cours=de,
                          note=note)
    db.session.add(log)
    db.session.commit()
    flash(f"{p.nom} — stock corrigé : {new_quantite} total, {new_en_cours} en cours.", "info")
    return redirect(url_for("inventaire.inventaire"))
