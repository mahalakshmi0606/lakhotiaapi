from flask import Blueprint, request, jsonify
from app import db
from app.models.task import Task
from datetime import datetime

task_bp = Blueprint("task", __name__)

# ✅ CREATE TASK
@task_bp.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    task = Task(
        title=data.get("title"),
        description=data.get("description"),
        priority=data.get("priority"),
        dueDate=data.get("dueDate"),
        assignedTo=data.get("assignedTo"),
        assignedBy=data.get("assignedBy"),
        assignedByEmail=data.get("assignedByEmail"),
        product_code=data.get("product_code"),
        length=data.get("length"),
        width=data.get("width"),
        qty=data.get("qty"),
        batch_code=data.get("batch_code"),
        status=data.get("status", "Pending"),
        status_check=data.get("status_check"),  # 🟢 NEW — store status check
        note=data.get("note"),  # 🟢 Save note when creating
        createdAt=datetime.utcnow(),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "✅ Task created successfully"}), 201


# ✅ GET ALL TASKS
@task_bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    tasks = Task.query.order_by(Task.createdAt.desc()).all()
    return jsonify([task.to_dict() for task in tasks]), 200


# ✅ UPDATE TASK (e.g., status, description, rework note, etc.)
@task_bp.route("/api/tasks/<int:id>", methods=["PUT"])
def update_task(id):
    data = request.get_json()
    task = Task.query.get_or_404(id)

    # Update all editable fields
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.priority = data.get("priority", task.priority)
    task.dueDate = data.get("dueDate", task.dueDate)
    task.assignedTo = data.get("assignedTo", task.assignedTo)
    task.assignedBy = data.get("assignedBy", task.assignedBy)
    task.assignedByEmail = data.get("assignedByEmail", task.assignedByEmail)
    task.product_code = data.get("product_code", task.product_code)
    task.length = data.get("length", task.length)
    task.width = data.get("width", task.width)
    task.qty = data.get("qty", task.qty)
    task.batch_code = data.get("batch_code", task.batch_code)
    task.status = data.get("status", task.status)
    task.status_check = data.get("status_check", task.status_check)  # 🟢 NEW — update status_check
    task.note = data.get("note", task.note)

    db.session.commit()
    return jsonify({"message": "✅ Task updated successfully"}), 200


# ✅ DELETE TASK
@task_bp.route("/api/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "🗑️ Task deleted successfully"}), 200
