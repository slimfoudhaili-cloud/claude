"""
Horace Product Inventory Tracker
Usage : python horace_inventory.py
Accès  : http://localhost:5000
"""

import json
import os
import uuid
from datetime import datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "horace-dev-secret-change-me")

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "inventory.json")

UNITS_SUGGESTIONS = ["flacon", "tube", "sachet", "boite", "stick", "spray", "pot"]


# ─── Helpers de persistance ────────────────────────────────────────────────────

def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        return {"products": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


# ─── Logique métier ────────────────────────────────────────────────────────────

def calculate_daily_rate(product: dict):
    """Retourne la consommation moyenne en unités/jour, ou None si données insuffisantes."""
    log = product.get("consumption_log", [])
    if len(log) < 2:
        return None
    events = sorted(log, key=lambda e: e["date"])
    total_qty = sum(e["quantity"] for e in events)
    first = datetime.fromisoformat(events[0]["date"])
    last = datetime.fromisoformat(events[-1]["date"])
    span_days = (last - first).total_seconds() / 86400
    if span_days < 1:
        return None
    return total_qty / span_days


def estimate_days_remaining(product: dict):
    """Retourne le nombre de jours de stock estimé, ou None si taux inconnu."""
    rate = calculate_daily_rate(product)
    if rate is None or rate == 0:
        return None
    stock = product.get("stock", 0)
    return int(stock / rate)


def urgency_score(product: dict) -> tuple:
    """Score de tri : plus bas = plus urgent."""
    stock = product.get("stock", 0)
    min_stk = product.get("min_stock", 1)
    days = estimate_days_remaining(product)
    days_sort = days if days is not None else 9999

    if stock == 0:
        return (0, 0)
    elif stock <= min_stk:
        return (1, days_sort)
    else:
        return (2, days_sort)


def enrich_product(product: dict) -> dict:
    """Ajoute les champs calculés à un produit pour l'affichage."""
    p = dict(product)
    p["daily_rate"] = calculate_daily_rate(product)
    p["days_remaining"] = estimate_days_remaining(product)
    rate = p["daily_rate"]
    if rate and rate > 0:
        # Consommation exprimée en jours par unité
        p["days_per_unit"] = round(1 / rate)
    else:
        p["days_per_unit"] = None
    p["is_out"] = p.get("stock", 0) == 0
    p["is_low"] = 0 < p.get("stock", 0) <= p.get("min_stock", 1)
    return p


def generate_order_list(products: dict) -> list:
    """Retourne les produits en alerte (rupture ou stock faible), triés par urgence."""
    low = [p for p in products.values() if p.get("stock", 0) <= p.get("min_stock", 1)]
    return [enrich_product(p) for p in sorted(low, key=urgency_score)]


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    data = load_data()
    products = data.get("products", {})
    enriched = [enrich_product(p) for p in sorted(products.values(), key=urgency_score)]
    alert_count = sum(1 for p in enriched if p["is_out"] or p["is_low"])
    return render_template("index.html", products=enriched, alert_count=alert_count)


@app.route("/product/add", methods=["GET", "POST"])
def product_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Le nom du produit est obligatoire.", "danger")
            return render_template("product_form.html", product=None, units=UNITS_SUGGESTIONS, action_label="Ajouter")

        data = load_data()
        product_id = str(uuid.uuid4())
        data["products"][product_id] = {
            "id": product_id,
            "name": name,
            "url": request.form.get("url", "").strip(),
            "unit": request.form.get("unit", "unité").strip() or "unité",
            "stock": max(0, int(request.form.get("stock", 0) or 0)),
            "min_stock": max(0, int(request.form.get("min_stock", 1) or 1)),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "consumption_log": [],
        }
        save_data(data)
        flash(f"Produit « {name} » ajouté avec succès.", "success")
        return redirect(url_for("dashboard"))

    return render_template("product_form.html", product=None, units=UNITS_SUGGESTIONS, action_label="Ajouter")


@app.route("/product/<product_id>/edit", methods=["GET", "POST"])
def product_edit(product_id):
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Le nom du produit est obligatoire.", "danger")
            return render_template("product_form.html", product=product, units=UNITS_SUGGESTIONS, action_label="Modifier")

        product["name"] = name
        product["url"] = request.form.get("url", "").strip()
        product["unit"] = request.form.get("unit", "unité").strip() or "unité"
        product["min_stock"] = max(0, int(request.form.get("min_stock", 1) or 1))
        save_data(data)
        flash(f"Produit « {name} » modifié.", "success")
        return redirect(url_for("product_detail", product_id=product_id))

    return render_template("product_form.html", product=product, units=UNITS_SUGGESTIONS, action_label="Modifier")


@app.route("/product/<product_id>/delete", methods=["POST"])
def product_delete(product_id):
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)
    name = product["name"]
    del data["products"][product_id]
    save_data(data)
    flash(f"Produit « {name} » supprimé.", "success")
    return redirect(url_for("dashboard"))


@app.route("/product/<product_id>")
def product_detail(product_id):
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)
    enriched = enrich_product(product)
    log = sorted(product.get("consumption_log", []), key=lambda e: e["date"], reverse=True)[:50]
    return render_template("product_detail.html", product=enriched, log=log)


@app.route("/product/<product_id>/consume", methods=["POST"])
def product_consume(product_id):
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)

    qty = max(1, int(request.form.get("quantity", 1) or 1))
    note = request.form.get("note", "").strip()
    product["stock"] = max(0, product["stock"] - qty)
    product["consumption_log"].append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "quantity": qty,
        "note": note,
    })
    save_data(data)
    flash(f"Utilisation enregistrée : {qty} {product['unit']}.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/product/<product_id>/restock", methods=["POST"])
def product_restock(product_id):
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)

    qty = max(1, int(request.form.get("quantity", 1) or 1))
    product["stock"] = product["stock"] + qty
    save_data(data)
    flash(f"Stock mis à jour : +{qty} {product['unit']}. Stock actuel : {product['stock']}.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/product/<product_id>/quick-consume", methods=["POST"])
def product_quick_consume(product_id):
    """Action rapide depuis le tableau de bord : consommer 1 unité."""
    data = load_data()
    product = data["products"].get(product_id)
    if not product:
        abort(404)
    product["stock"] = max(0, product["stock"] - 1)
    product["consumption_log"].append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "quantity": 1,
        "note": "Action rapide",
    })
    save_data(data)
    flash(f"1 {product['unit']} de « {product['name']} » utilisé(e).", "success")
    return redirect(url_for("dashboard"))


@app.route("/order")
def order_list():
    data = load_data()
    items = generate_order_list(data.get("products", {}))
    return render_template("order_list.html", items=items, today=datetime.now().strftime("%d/%m/%Y"))


@app.route("/order/print")
def order_print():
    data = load_data()
    items = generate_order_list(data.get("products", {}))
    return render_template("order_print.html", items=items, today=datetime.now().strftime("%d/%m/%Y"))


# ─── Filtres Jinja2 ────────────────────────────────────────────────────────────

@app.template_filter("format_date")
def format_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso_str


# ─── Point d'entrée ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
