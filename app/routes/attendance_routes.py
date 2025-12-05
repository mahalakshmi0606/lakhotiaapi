# routes/attendance_routes.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.attendance import Attendance
from datetime import datetime

attendance_bp = Blueprint("attendance", __name__)

# ✅ Create new record (check-in)
@attendance_bp.route("/attendance/checkin", methods=["POST"])
def check_in():
    data = request.get_json()
    email = data.get("email")
    username = data.get("username")
    date = data.get("date")

    if not email or not username or not date:
        return jsonify({"message": "Missing email, username, or date"}), 400

    # Prevent multiple check-ins per day (by email)
    existing = Attendance.query.filter_by(email=email, date=date).first()
    if existing:
        return jsonify({"message": "Already checked in today"}), 400

    new_record = Attendance(
        email=email,
        username=username,
        date=date,
        check_in=data.get("checkIn"),
        status="checked-in",
        device_in=data.get("device"),
        location_in=data.get("location"),
    )
    db.session.add(new_record)
    db.session.commit()

    return jsonify({
        "message": "Checked in successfully",
        "record": new_record.to_dict()
    }), 201


# ✅ Update record (check-out)
@attendance_bp.route("/attendance/checkout", methods=["PUT"])
def check_out():
    data = request.get_json()
    email = data.get("email")
    date = data.get("date")

    if not email or not date:
        return jsonify({"message": "Missing email or date"}), 400

    record = Attendance.query.filter_by(email=email, date=date).first()
    if not record or not record.check_in:
        return jsonify({"message": "No active check-in found"}), 404

    record.check_out = data.get("checkOut")
    record.status = "checked-out"
    record.device_out = data.get("deviceOut")
    record.location_out = data.get("locationOut")

    # ✅ Calculate duration (HHh MMm)
    try:
        fmt = "%I:%M:%S %p" if "AM" in record.check_in or "PM" in record.check_in else "%H:%M:%S"
        t1 = datetime.strptime(record.check_in, fmt)
        t2 = datetime.strptime(record.check_out, fmt)
        delta = t2 - t1
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        record.duration = f"{hours}h {minutes}m"
    except Exception as e:
        print("Duration calculation error:", e)
        record.duration = "-"

    db.session.commit()
    return jsonify({
        "message": "Checked out successfully",
        "record": record.to_dict()
    })


# ✅ Fetch attendance by email
@attendance_bp.route("/attendance/email/<email>", methods=["GET"])
def get_attendance_by_email(email):
    records = Attendance.query.filter_by(email=email).order_by(Attendance.id.desc()).all()
    return jsonify([r.to_dict() for r in records])


# ✅ Fetch all attendance records (Admin view)
@attendance_bp.route("/attendance", methods=["GET"])
def get_all_attendance():
    records = Attendance.query.order_by(Attendance.id.desc()).all()
    return jsonify([r.to_dict() for r in records])
