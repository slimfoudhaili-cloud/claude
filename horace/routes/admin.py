from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Produit, Stock

admin_bp = Blueprint("admin", __name__)

CATEGORIES_DEFAUT = ["Visage", "Yeux", "Barbe", "Cheveux"]


@admin_bp.route("/produits")
def produits():
    actifs = (Produit.query.filter_by(actif=True)
              .order_by(Produit.categorie, Produit.nom).all())
    archives = (Produit.query.filter_by(actif=False)
                .order_by(Produit.categorie, Produit.nom).all())
    # Build list of existing categories for the add form datalist
    cats = sorted({p.categorie for p in actifs + archives})
    return render_template("produits.html",
                           actifs=actifs, archives=archives, categories=cats,
                           categories_defaut=CATEGORIES_DEFAUT)


@admin_bp.route("/produits/ajouter", methods=["POST"])
def ajouter_produit():
    nom = request.form.get("nom", "").strip()
    categorie = request.form.get("categorie", "").strip()
    try:
        seuil = int(request.form.get("seuil_alerte", 1))
        if seuil < 0:
            raise ValueError
    except (ValueError, TypeError):
        seuil = 1

    if not nom or not categorie:
        flash("Le nom et la catégorie sont obligatoires.", "danger")
        return redirect(url_for("admin.produits"))

    # Prevent exact duplicates (same nom + categorie, active)
    existing = Produit.query.filter_by(nom=nom, categorie=categorie, actif=True).first()
    if existing:
        flash(f"Le produit « {nom} » existe déjà dans la catégorie {categorie}.", "warning")
        return redirect(url_for("admin.produits"))

    p = Produit(nom=nom, categorie=categorie, seuil_alerte=seuil, actif=True)
    db.session.add(p)
    db.session.flush()
    db.session.add(Stock(produit_id=p.id))
    db.session.commit()
    flash(f"Produit « {nom} » ajouté avec succès.", "success")
    return redirect(url_for("admin.produits"))


@admin_bp.route("/produits/<int:produit_id>/archiver", methods=["POST"])
def archiver_produit(produit_id):
    p = Produit.query.get_or_404(produit_id)
    p.actif = False
    db.session.commit()
    flash(f"« {p.nom} » archivé. Il n'apparaît plus dans l'inventaire.", "info")
    return redirect(url_for("admin.produits"))


@admin_bp.route("/produits/<int:produit_id>/restaurer", methods=["POST"])
def restaurer_produit(produit_id):
    p = Produit.query.get_or_404(produit_id)
    p.actif = True
    db.session.commit()
    flash(f"« {p.nom} » restauré et de nouveau suivi.", "success")
    return redirect(url_for("admin.produits"))


@admin_bp.route("/produits/<int:produit_id>/seuil", methods=["POST"])
def modifier_seuil(produit_id):
    p = Produit.query.get_or_404(produit_id)
    try:
        seuil = int(request.form.get("seuil_alerte", 1))
        if seuil < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Seuil invalide.", "danger")
        return redirect(url_for("admin.produits"))
    p.seuil_alerte = seuil
    db.session.commit()
    flash(f"Seuil d'alerte de « {p.nom} » mis à jour : {seuil}.", "info")
    return redirect(url_for("admin.produits"))
