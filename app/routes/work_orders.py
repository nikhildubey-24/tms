from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import WorkOrder, Plant
from app.utils import log_audit

work_orders_bp = Blueprint("work_orders", __name__, url_prefix="/work-orders")


@work_orders_bp.route("/")
@login_required
def list():
    plant_id = request.args.get("plant_id", "", type=str)
    plants = Plant.query.order_by(Plant.name).all()
    query = WorkOrder.query
    if plant_id:
        query = query.filter_by(plant_id=int(plant_id))
    work_orders = query.order_by(WorkOrder.plant_id, WorkOrder.name).all()

    plant_groups = []
    if plant_id:
        p = Plant.query.get(int(plant_id))
        if p:
            wos = WorkOrder.query.filter_by(plant_id=p.id).order_by(WorkOrder.name).all()
            plant_groups.append({"plant": p, "work_orders": wos})
    else:
        for p in plants:
            wos = WorkOrder.query.filter_by(plant_id=p.id).order_by(WorkOrder.name).all()
            plant_groups.append({"plant": p, "work_orders": wos})

    return render_template("work_orders/list.html", work_orders=work_orders, plants=plants, plant_id=plant_id, plant_groups=plant_groups)


@work_orders_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    plants = Plant.query.order_by(Plant.name).all()
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            plant_id = request.form.get("plant_id")
            if not name or not plant_id:
                flash("Work order name and plant are required", "danger")
                return render_template("work_orders/form.html", work_order=None, plants=plants)
            if WorkOrder.query.filter_by(name=name, plant_id=int(plant_id)).first():
                flash("Work order with this name already exists for this plant", "danger")
                return render_template("work_orders/form.html", work_order=None, plants=plants)
            w = WorkOrder(name=name, plant_id=int(plant_id))
            db.session.add(w)
            db.session.commit()
            log_audit("create", "work_order", w.id, f"Created work order: {w.name} for {w.plant.name}")
            flash("Work order added successfully", "success")
            return redirect(url_for("work_orders.list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("work_orders/form.html", work_order=None, plants=plants)


@work_orders_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    w = WorkOrder.query.get_or_404(id)
    plants = Plant.query.order_by(Plant.name).all()
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            plant_id = request.form.get("plant_id")
            if not name or not plant_id:
                flash("Work order name and plant are required", "danger")
                return render_template("work_orders/form.html", work_order=w, plants=plants)
            existing = WorkOrder.query.filter(
                WorkOrder.name == name, WorkOrder.plant_id == int(plant_id), WorkOrder.id != id
            ).first()
            if existing:
                flash("Work order with this name already exists for this plant", "danger")
                return render_template("work_orders/form.html", work_order=w, plants=plants)
            w.name = name
            w.plant_id = int(plant_id)
            db.session.commit()
            log_audit("update", "work_order", w.id, f"Updated work order: {w.name}")
            flash("Work order updated successfully", "success")
            return redirect(url_for("work_orders.list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("work_orders/form.html", work_order=w, plants=plants)


@work_orders_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    w = WorkOrder.query.get_or_404(id)
    try:
        db.session.delete(w)
        db.session.commit()
        log_audit("delete", "work_order", id, f"Deleted work order: {w.name}")
        flash("Work order deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Cannot delete: {str(e)}", "danger")
    return redirect(url_for("work_orders.list"))


@work_orders_bp.route("/by-plant")
@login_required
def by_plant():
    plants = Plant.query.order_by(Plant.name).all()
    plant_groups = []
    for p in plants:
        wos = WorkOrder.query.filter_by(plant_id=p.id).order_by(WorkOrder.name).all()
        plant_groups.append({"plant": p, "work_orders": wos})
    return render_template("work_orders/by_plant.html", plant_groups=plant_groups)


@work_orders_bp.route("/api")
@login_required
def api():
    plant_id = request.args.get("plant_id", "", type=str)
    query = WorkOrder.query
    if plant_id:
        query = query.filter_by(plant_id=int(plant_id))
    work_orders = query.order_by(WorkOrder.name).all()
    return jsonify([w.to_dict() for w in work_orders])


@work_orders_bp.route("/api/by-plant")
@login_required
def api_by_plant():
    plants = Plant.query.order_by(Plant.name).all()
    result = []
    for p in plants:
        wos = WorkOrder.query.filter_by(plant_id=p.id).order_by(WorkOrder.name).all()
        result.append({"plant": p.to_dict(), "work_orders": [w.to_dict() for w in wos]})
    return jsonify(result)
