from flask import Blueprint, render_template
from flask_login import login_required
from app import db
from app.models import Trip, Plant

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    trips = Trip.query.all()
    total_freight = sum(float(t.total_freight) for t in trips)
    total_paid = sum(float(t.total_paid) for t in trips)
    total_balance = sum(float(t.balance) for t in trips)
    pending_trips = Trip.query.filter(Trip.status == "Pending").count()
    completed_trips = Trip.query.filter(Trip.status == "Completed").count()
    total_trips = len(trips)

    plants = Plant.query.order_by(Plant.name).all()
    plant_data = []
    for p in plants:
        pt = Trip.query.filter_by(plant_id=p.id).all()
        if pt:
            plant_data.append({
                "name": p.name,
                "count": len(pt),
                "freight": sum(float(x.total_freight) for x in pt),
                "tds": sum(float(x.tds_amount) for x in pt),
                "expense": sum(float(x.total_expense) for x in pt),
                "paid": sum(float(x.total_paid) for x in pt),
                "balance": sum(float(x.balance) for x in pt),
                "pending": sum(1 for x in pt if x.status == "Pending"),
                "completed": sum(1 for x in pt if x.status == "Completed"),
                "work_orders": sum(1 for x in pt if x.work_order_number),
                "mines_qty": sum(float(x.mines_qty or 0) for x in pt),
            })

    return render_template(
        "dashboard.html",
        total_freight=total_freight,
        total_paid=total_paid,
        total_balance=total_balance,
        pending_trips=pending_trips,
        completed_trips=completed_trips,
        total_trips=total_trips,
        recent_trips=Trip.query.order_by(Trip.date.desc()).limit(5).all(),
        plants=plants,
        plant_data=plant_data,
    )
