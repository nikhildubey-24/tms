from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app import db
from app.models import Trip, Transporter, Plant
from app.utils import generate_csv

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    return render_template("reports/index.html")


@reports_bp.route("/trip-wise")
@login_required
def trip_wise():
    query = Trip.query
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    if date_from:
        query = query.filter(Trip.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = query.filter(Trip.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
    trips = query.order_by(Trip.date.desc()).all()

    if request.args.get("export") == "csv":
        headers = ["Date", "Truck", "Work Order", "Mines Name", "Mines Qty", "Plant", "Transporter", "Freight", "TDS%", "TDS Amt", "Expense", "Paid", "Balance", "Status"]
        rows = [
            [
                t.date,
                t.lorry_number,
                t.work_order.name if t.work_order else "",
                t.mine.name if t.mine else "",
                float(t.mines_qty) if t.mines_qty else "",
                t.plant.name if t.plant else "",
                t.transporter.name if t.transporter else "",
                float(t.total_freight),
                float(t.tds_percent),
                float(t.tds_amount),
                float(t.total_expense),
                float(t.total_paid),
                float(t.balance),
                t.status,
            ]
            for t in trips
        ]
        return generate_csv(headers, rows)

    return render_template("reports/trip_wise.html", trips=trips, date_from=date_from, date_to=date_to)


@reports_bp.route("/transporter-wise")
@login_required
def transporter_wise():
    transporters = Transporter.query.order_by(Transporter.name).all()
    data = []
    for t in transporters:
        trips = Trip.query.filter_by(transporter_id=t.id).all()
        if trips:
            total_freight = sum(float(x.total_freight) for x in trips)
            total_paid = sum(float(x.total_paid) for x in trips)
            total_expense = sum(float(x.total_expense) for x in trips)
            total_tds = sum(float(x.tds_amount) for x in trips)
            total_balance = sum(float(x.balance) for x in trips)
            data.append({
                "transporter": t.name,
                "trip_count": len(trips),
                "total_freight": total_freight,
                "total_paid": total_paid,
                "total_expense": total_expense,
                "total_tds": total_tds,
                "total_balance": total_balance,
            })

    if request.args.get("export") == "csv":
        headers = ["Transporter", "Trips", "Freight", "Paid", "Expense", "TDS", "Balance"]
        rows = [
            [d["transporter"], d["trip_count"], d["total_freight"], d["total_paid"], d["total_expense"], d["total_tds"], d["total_balance"]]
            for d in data
        ]
        return generate_csv(headers, rows)

    return render_template("reports/transporter_wise.html", data=data)


@reports_bp.route("/date-wise")
@login_required
def date_wise():
    query = Trip.query
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    if date_from:
        query = query.filter(Trip.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = query.filter(Trip.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
    trips = query.order_by(Trip.date.desc()).all()

    date_groups = {}
    for t in trips:
        d = t.date.isoformat()
        if d not in date_groups:
            date_groups[d] = []
        date_groups[d].append(t)

    summary = []
    for d, ts in sorted(date_groups.items(), reverse=True):
        summary.append({
            "date": d,
            "trip_count": len(ts),
            "total_freight": sum(float(x.total_freight) for x in ts),
            "total_paid": sum(float(x.total_paid) for x in ts),
            "total_expense": sum(float(x.total_expense) for x in ts),
            "total_tds": sum(float(x.tds_amount) for x in ts),
            "total_balance": sum(float(x.balance) for x in ts),
        })

    if request.args.get("export") == "csv":
        headers = ["Date", "Trips", "Freight", "Paid", "Expense", "TDS", "Balance"]
        rows = [
            [s["date"], s["trip_count"], s["total_freight"], s["total_paid"], s["total_expense"], s["total_tds"], s["total_balance"]]
            for s in summary
        ]
        return generate_csv(headers, rows)

    return render_template("reports/date_wise.html", summary=summary, date_from=date_from, date_to=date_to)


@reports_bp.route("/plant-wise")
@login_required
def plant_wise():
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    plants = Plant.query.order_by(Plant.name).all()
    hierarchy = []

    for p in plants:
        query = Trip.query.filter_by(plant_id=p.id)
        if date_from:
            query = query.filter(Trip.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            query = query.filter(Trip.date <= datetime.strptime(date_to, "%Y-%m-%d").date())

        trips = query.order_by(Trip.date.desc()).all()
        if not trips:
            continue

        lorry_groups = {}
        for t in trips:
            key = t.lorry_number
            if key not in lorry_groups:
                lorry_groups[key] = []
            lorry_groups[key].append(t)

        lorry_data = []
        plant_freight = plant_paid = plant_expense = plant_tds = plant_balance = 0
        for lorry, lt in sorted(lorry_groups.items()):
            lorry_freight = sum(float(x.total_freight) for x in lt)
            lorry_paid = sum(float(x.total_paid) for x in lt)
            lorry_expense = sum(float(x.total_expense) for x in lt)
            lorry_tds = sum(float(x.tds_amount) for x in lt)
            lorry_balance = sum(float(x.balance) for x in lt)
            lorry_data.append({
                "lorry": lorry,
                "trips": lt,
                "trip_count": len(lt),
                "freight": lorry_freight,
                "paid": lorry_paid,
                "expense": lorry_expense,
                "tds": lorry_tds,
                "balance": lorry_balance,
            })
            plant_freight += lorry_freight
            plant_paid += lorry_paid
            plant_expense += lorry_expense
            plant_tds += lorry_tds
            plant_balance += lorry_balance

        hierarchy.append({
            "plant": p,
            "trip_count": len(trips),
            "freight": plant_freight,
            "paid": plant_paid,
            "expense": plant_expense,
            "tds": plant_tds,
            "balance": plant_balance,
            "lorries": lorry_data,
        })

    if request.args.get("export") == "csv":
        headers = ["Plant", "Truck", "Work Order", "Mines Name", "Mines Qty", "Date", "Transporter", "Freight", "TDS%", "TDS Amt", "Expense", "Paid", "Balance", "Status"]
        rows = []
        for h in hierarchy:
            for l in h["lorries"]:
                for t in l["trips"]:
                    rows.append([
                        h["plant"].name,
                        l["lorry"],
                        t.work_order.name if t.work_order else "",
                        t.mine.name if t.mine else "",
                        float(t.mines_qty) if t.mines_qty else "",
                        t.date,
                        t.transporter.name if t.transporter else "",
                        float(t.total_freight),
                        float(t.tds_percent),
                        float(t.tds_amount),
                        float(t.total_expense),
                        float(t.total_paid),
                        float(t.balance),
                        t.status,
                    ])
        return generate_csv(headers, rows)

    return render_template("reports/plant_wise.html", hierarchy=hierarchy, date_from=date_from, date_to=date_to)
