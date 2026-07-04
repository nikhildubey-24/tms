from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transporter(db.Model):
    __tablename__ = "transporters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    pan_card = db.Column(db.String(20), nullable=True)
    bank_account = db.Column(db.String(50), nullable=True)
    ifsc_code = db.Column(db.String(20), nullable=True)
    contact = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trips = db.relationship("Trip", backref="transporter", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pan_card": self.pan_card,
            "bank_account": self.bank_account,
            "ifsc_code": self.ifsc_code,
            "contact": self.contact,
        }


class Trip(db.Model):
    __tablename__ = "trips"
    __table_args__ = (
        db.UniqueConstraint("date", "lorry_number", name="uq_trip_date_lorry"),
        db.Index("ix_trip_date", "date"),
        db.Index("ix_trip_transporter", "transporter_id"),
        db.Index("ix_trip_plant", "plant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    lorry_number = db.Column(db.String(50), nullable=False)
    transporter_id = db.Column(db.Integer, db.ForeignKey("transporters.id"), nullable=False, index=True)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True, index=True)
    total_freight = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    tds_percent = db.Column(db.Numeric(5, 2), nullable=False, default=1.00)
    tds_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_expense = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expenses = db.relationship("Expense", backref="trip", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="trip", lazy=True, cascade="all, delete-orphan")

    def recalculate(self):
        self.tds_amount = round(float(self.total_freight) * float(self.tds_percent) / 100, 2)
        self.total_expense = sum(float(e.amount) for e in self.expenses) if self.expenses else 0
        self.total_paid = sum(float(p.amount) for p in self.payments) if self.payments else 0
        self.balance = round(
            float(self.total_freight) - float(self.total_paid) - float(self.total_expense) - float(self.tds_amount),
            2,
        )
        self.status = "Completed" if self.balance <= 0 else "Pending"

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "lorry_number": self.lorry_number,
            "transporter_id": self.transporter_id,
            "transporter_name": self.transporter.name if self.transporter else "",
            "plant_id": self.plant_id,
            "plant_name": self.plant.name if self.plant else "",
            "total_freight": float(self.total_freight),
            "tds_percent": float(self.tds_percent),
            "tds_amount": float(self.tds_amount),
            "total_expense": float(self.total_expense),
            "total_paid": float(self.total_paid),
            "balance": float(self.balance),
            "status": self.status,
            "remarks": self.remarks,
        }


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    description = db.Column(db.String(300), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "description": self.description,
            "amount": float(self.amount),
        }


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    payment_method = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    execution_date = db.Column(db.Date, nullable=False)
    beneficiary_name = db.Column(db.String(200), nullable=True)
    account_number = db.Column(db.String(50), nullable=True)
    ifsc_code = db.Column(db.String(20), nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "payment_method": self.payment_method,
            "amount": float(self.amount),
            "execution_date": self.execution_date.isoformat() if self.execution_date else None,
            "beneficiary_name": self.beneficiary_name,
            "account_number": self.account_number,
            "ifsc_code": self.ifsc_code,
            "reference_number": self.reference_number,
        }


class Plant(db.Model):
    __tablename__ = "plants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship("Trip", backref="plant", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
