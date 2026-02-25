from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Produit(db.Model):
    __tablename__ = "produit"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    categorie = db.Column(db.String(60), nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    seuil_alerte = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stock = db.relationship("Stock", back_populates="produit", uselist=False,
                            cascade="all, delete-orphan")
    logs = db.relationship("ConsommationLog", back_populates="produit",
                           order_by="ConsommationLog.created_at.desc()",
                           cascade="all, delete-orphan")

    @property
    def statut(self):
        s = self.stock
        if s is None or (s.quantite == 0 and s.en_cours == 0):
            return "rupture"
        if s.quantite <= self.seuil_alerte and s.en_cours == 0:
            return "alerte"
        return "ok"

    @property
    def reserve(self):
        if self.stock is None:
            return 0
        return max(0, self.stock.quantite - self.stock.en_cours)


class Stock(db.Model):
    __tablename__ = "stock"

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey("produit.id"),
                           nullable=False, unique=True)
    quantite = db.Column(db.Integer, default=0, nullable=False)
    en_cours = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    produit = db.relationship("Produit", back_populates="stock")


class ConsommationLog(db.Model):
    __tablename__ = "consommation_log"

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey("produit.id"), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    # action values: "ouvert", "termine", "restock", "correction"
    delta_quantite = db.Column(db.Integer, default=0)
    delta_en_cours = db.Column(db.Integer, default=0)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produit = db.relationship("Produit", back_populates="logs")
