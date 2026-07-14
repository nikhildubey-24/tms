from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import Mine
from app.utils import log_audit

mines_bp = Blueprint("mines", __name__, url_prefix="/mines")


@mines_bp.route("/")
@login_required
def list():
    mines = Mine.query.order_by(Mine.name).all()
    return render_template("mines/list.html", mines=mines)


@mines_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            if not name:
                flash("Mine name is required", "danger")
                return render_template("mines/form.html", mine=None)
            if Mine.query.filter_by(name=name).first():
                flash("Mine with this name already exists", "danger")
                return render_template("mines/form.html", mine=None)
            m = Mine(name=name)
            db.session.add(m)
            db.session.commit()
            log_audit("create", "mine", m.id, f"Created mine: {m.name}")
            flash("Mine added successfully", "success")
            return redirect(url_for("mines.list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("mines/form.html", mine=None)


@mines_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    m = Mine.query.get_or_404(id)
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            if not name:
                flash("Mine name is required", "danger")
                return render_template("mines/form.html", mine=m)
            existing = Mine.query.filter(Mine.name == name, Mine.id != id).first()
            if existing:
                flash("Mine with this name already exists", "danger")
                return render_template("mines/form.html", mine=m)
            m.name = name
            db.session.commit()
            log_audit("update", "mine", m.id, f"Updated mine: {m.name}")
            flash("Mine updated successfully", "success")
            return redirect(url_for("mines.list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("mines/form.html", mine=m)


@mines_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    m = Mine.query.get_or_404(id)
    try:
        db.session.delete(m)
        db.session.commit()
        log_audit("delete", "mine", id, f"Deleted mine: {m.name}")
        flash("Mine deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Cannot delete: {str(e)}", "danger")
    return redirect(url_for("mines.list"))


@mines_bp.route("/api")
@login_required
def api():
    mines = Mine.query.order_by(Mine.name).all()
    return jsonify([m.to_dict() for m in mines])
