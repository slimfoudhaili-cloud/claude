from flask import Flask, g
from .models import db, Produit, Stock

CATALOGUE = [
    # (nom, categorie)
    ("Nettoyant visage",                "Visage"),
    ("Lotion tonique",                  "Visage"),
    ("Hydratant matifiant",             "Visage"),
    ("Hydratant matifiant SPF30",       "Visage"),
    ("Hydratant riche",                 "Visage"),
    ("Gel raffermissant visage",        "Visage"),
    ("Exfoliant / Gommage",            "Visage"),
    ("Masque",                          "Visage"),
    ("Solution exfoliante perfectrice", "Visage"),
    ("Sérum",                           "Visage"),
    ("Fluide bonne mine",               "Visage"),
    ("Hydratant contour des yeux",      "Yeux"),
    ("Patchs contour des yeux",         "Yeux"),
    ("Shampoing barbe",                 "Barbe"),
    ("Huile barbe",                     "Barbe"),
    ("Shampoing doux purifiant",        "Cheveux"),
    ("Shampoing hydratant doux",        "Cheveux"),
    ("Après-shampoing fortifiant",      "Cheveux"),
    ("Après-shampoing nourrissant",     "Cheveux"),
    ("Cire coiffante",                  "Cheveux"),
    ("Sérum anti-chute",                "Cheveux"),
]


def seed_if_empty():
    if Produit.query.count() == 0:
        for nom, categorie in CATALOGUE:
            p = Produit(nom=nom, categorie=categorie)
            db.session.add(p)
            db.session.flush()
            db.session.add(Stock(produit_id=p.id))
        db.session.commit()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///horace.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "horace-perso-2026"

    db.init_app(app)

    from .routes import register_blueprints
    register_blueprints(app)

    @app.before_request
    def inject_nb_a_commander():
        from .models import Produit, Stock
        count = 0
        for p in Produit.query.filter_by(actif=True).all():
            if p.statut in ("rupture", "alerte"):
                count += 1
        g.nb_a_commander = count

    with app.app_context():
        db.create_all()
        seed_if_empty()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
