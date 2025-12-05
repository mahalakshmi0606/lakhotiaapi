from flask import Blueprint, request, jsonify
from app import db
from app.models.advance import Advance

advance_bp = Blueprint("advance_bp", __name__, url_prefix="/api")

# 🟢 Get all advances
@advance_bp.route("/advance", methods=["GET"])
def get_all_advances():
    advances = Advance.query.all()
    return jsonify([a.to_dict() for a in advances])

# 🟢 Add new advance
@advance_bp.route("/advance", methods=["POST"])
def add_advance():
    data = request.json
    new_advance = Advance(
        email=data["email"],
        name=data["name"],
        department=data.get("department"),
        amount=data["amount"],
        reason=data.get("reason"),
        date=data.get("date"),
        time=data.get("time"),
        status=data.get("status", "Pending"),
    )
    db.session.add(new_advance)
    db.session.commit()
    return jsonify({"message": "Advance added successfully"}), 201

# 🟡 Update existing advance
@advance_bp.route("/advance/<int:id>", methods=["PUT"])
def update_advance(id):
    data = request.json
    advance = Advance.query.get_or_404(id)
    advance.email = data.get("email", advance.email)
    advance.name = data.get("name", advance.name)
    advance.department = data.get("department", advance.department)
    advance.amount = data.get("amount", advance.amount)
    advance.reason = data.get("reason", advance.reason)
    advance.date = data.get("date", advance.date)
    advance.time = data.get("time", advance.time)
    advance.status = data.get("status", advance.status)
    db.session.commit()
    return jsonify({"message": "Advance updated successfully"})

# 🔴 Delete advance
@advance_bp.route("/advance/<int:id>", methods=["DELETE"])
def delete_advance(id):
    advance = Advance.query.get_or_404(id)
    db.session.delete(advance)
    db.session.commit()
    return jsonify({"message": "Advance deleted successfully"})
