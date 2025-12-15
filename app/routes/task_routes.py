from flask import Blueprint, request, jsonify
from app import db
from app.models.task import Task
from datetime import datetime

task_bp = Blueprint("task", __name__)

# ✅ CREATE TASK
@task_bp.route("/api/tasks", methods=["POST"])
def create_task():
    try:
        data = request.get_json()
        print("📥 Received task data:", data)
        
        item_details = data.get("item_details", {})
        
        task = Task(
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=data.get("priority", "Medium"),
            dueDate=data.get("dueDate", ""),
            assignedTo=data.get("assignedTo", ""),
            assignedBy=data.get("assignedBy", ""),
            assignedByEmail=data.get("assignedByEmail", ""),
            
            quotation_id=data.get("quotation_id") or item_details.get("quotation_id"),
            quotation_number=data.get("quotation_number") or item_details.get("quote_number"),
            company_name=data.get("company_name") or item_details.get("company_name"),
            item_id=data.get("item_id") or item_details.get("id"),
            item_name=data.get("item_name") or item_details.get("item_name"),
            
            supplier_part_no=data.get("supplier_part_no") or item_details.get("supplier_part_no", ""),
            hsn_sac=data.get("hsn_sac") or item_details.get("hsn_sac", ""),
            cut_width=data.get("cut_width") or item_details.get("cut_width", ""),
            length=data.get("length") or item_details.get("length", ""),
            quantity=data.get("quantity") or item_details.get("quantity", ""),
            unit=data.get("unit") or item_details.get("unit", "pcs"),
            mrp=data.get("mrp") or item_details.get("mrp", ""),
            material_type=data.get("material_type") or item_details.get("material_type", ""),
            thickness=data.get("thickness") or item_details.get("thickness", ""),
            
            status=data.get("status", "Pending"),
            status_check=data.get("status_check"),
            note=data.get("note", ""),
            createdAt=datetime.utcnow(),
        )
        
        db.session.add(task)
        db.session.commit()
        
        print("✅ Task saved:", task.id, task.title)
        return jsonify({
            "success": True,
            "message": "✅ Task created successfully",
            "task": task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("❌ Error creating task:", str(e))
        return jsonify({
            "success": False,
            "error": "Failed to create task",
            "message": str(e)
        }), 500


# ✅ GET ALL TASKS WITH FILTERS
@task_bp.route("/api/tasks", methods=["GET"])
def get_tasks():
    try:
        # Get query parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        show_completed = request.args.get('show_completed', 'true').lower() == 'true'
        
        query = Task.query
        
        # Apply filters
        if status and status != 'all':
            query = query.filter_by(status=status)
        
        if priority and priority != 'all':
            query = query.filter_by(priority=priority)
            
        if assigned_to and assigned_to != 'all':
            query = query.filter_by(assignedTo=assigned_to)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Task.title.ilike(search_term)) |
                (Task.description.ilike(search_term)) |
                (Task.item_name.ilike(search_term)) |
                (Task.company_name.ilike(search_term)) |
                (Task.quotation_number.ilike(search_term)) |
                (Task.supplier_part_no.ilike(search_term))
            )
        
        # Filter out completed tasks if needed
        if not show_completed:
            query = query.filter(Task.status != 'Completed')
        
        tasks = query.order_by(
            db.case(
                (Task.priority == 'High', 1),
                (Task.priority == 'Medium', 2),
                (Task.priority == 'Low', 3),
                else_=4
            )
        ).order_by(Task.dueDate).order_by(Task.createdAt.desc()).all()
        
        return jsonify([task.to_dict() for task in tasks]), 200
    except Exception as e:
        print("❌ Error fetching tasks:", str(e))
        return jsonify({
            "success": False,
            "error": "Failed to fetch tasks",
            "message": str(e)
        }), 500


# ✅ GET TASKS BY ASSIGNER EMAIL
@task_bp.route("/api/tasks/assigned-by/<string:email>", methods=["GET"])
def get_tasks_by_assigner(email):
    try:
        tasks = Task.query.filter_by(assignedByEmail=email).order_by(Task.createdAt.desc()).all()
        return jsonify([task.to_dict() for task in tasks]), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch tasks",
            "message": str(e)
        }), 500


# ✅ UPDATE TASK
@task_bp.route("/api/tasks/<int:id>", methods=["PUT"])
def update_task(id):
    try:
        data = request.get_json()
        task = Task.query.get_or_404(id)

        update_fields = [
            'title', 'description', 'priority', 'dueDate',
            'assignedTo', 'assignedBy', 'assignedByEmail',
            'quotation_id', 'quotation_number', 'company_name',
            'item_id', 'item_name', 'supplier_part_no', 'hsn_sac',
            'cut_width', 'length', 'quantity', 'unit', 'mrp',
            'material_type', 'thickness', 'status', 'status_check', 
            'note', 'production_start_date', 'production_end_date',
            'production_status', 'quality_check'
        ]
        
        for field in update_fields:
            if field in data:
                value = data[field]
                if field in ['production_start_date', 'production_end_date'] and value:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                setattr(task, field, value)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "✅ Task updated successfully",
            "task": task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Failed to update task",
            "message": str(e)
        }), 500


# ✅ UPDATE INVOICE DETAILS
@task_bp.route("/api/tasks/<int:id>/invoice", methods=["PUT"])
def update_task_invoice(id):
    try:
        data = request.get_json()
        task = Task.query.get_or_404(id)
        
        if task.status_check != "Completed":
            return jsonify({
                "success": False,
                "error": "Cannot add invoice to non-completed task"
            }), 400
        
        invoice_number = data.get("invoice_number")
        invoice_amount = data.get("invoice_amount")
        
        if not invoice_number:
            return jsonify({
                "success": False,
                "error": "Invoice number is required"
            }), 400
        
        task.invoice_number = invoice_number
        task.invoice_amount = invoice_amount
        task.invoice_date = datetime.utcnow()
        task.invoice_remarks = data.get("invoice_remarks", "")
        task.invoice_created_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "✅ Invoice details added successfully",
            "task": task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Failed to update invoice details",
            "message": str(e)
        }), 500


# ✅ PATCH TASK STATUS
@task_bp.route("/api/tasks/<int:id>/status", methods=["PATCH"])
def update_task_status(id):
    try:
        data = request.get_json()
        task = Task.query.get_or_404(id)
        
        new_status = data.get("status")
        if new_status:
            task.status = new_status
        
        new_status_check = data.get("status_check")
        if new_status_check:
            task.status_check = new_status_check
            if new_status_check == "Completed":
                task.status = "Completed"
                
        new_note = data.get("note")
        if new_note is not None:
            task.note = new_note
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "✅ Task status updated successfully",
            "task": task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Failed to update task status",
            "message": str(e)
        }), 500


# ✅ DELETE TASK
@task_bp.route("/api/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    try:
        task = Task.query.get_or_404(id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "🗑️ Task deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Failed to delete task",
            "message": str(e)
        }), 500


# ✅ GET TASKS BY QUOTATION ID
@task_bp.route("/api/tasks/quotation/<int:quotation_id>", methods=["GET"])
def get_tasks_by_quotation(quotation_id):
    try:
        tasks = Task.query.filter_by(quotation_id=quotation_id).order_by(Task.createdAt.desc()).all()
        return jsonify({
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "count": len(tasks)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch tasks for quotation",
            "message": str(e)
        }), 500


# ✅ SEARCH TASKS
@task_bp.route("/api/tasks/search", methods=["GET"])
def search_tasks():
    try:
        search_term = request.args.get('q', '').strip()
        if not search_term:
            return jsonify({
                "success": False,
                "error": "Search term required"
            }), 400
        
        tasks = Task.query.filter(
            (Task.title.ilike(f'%{search_term}%')) |
            (Task.description.ilike(f'%{search_term}%')) |
            (Task.item_name.ilike(f'%{search_term}%')) |
            (Task.company_name.ilike(f'%{search_term}%')) |
            (Task.quotation_number.ilike(f'%{search_term}%')) |
            (Task.supplier_part_no.ilike(f'%{search_term}%'))
        ).order_by(Task.createdAt.desc()).all()
        
        return jsonify({
            "success": True,
            "data": [task.to_dict() for task in tasks],
            "count": len(tasks)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to search tasks",
            "message": str(e)
        }), 500


# ✅ GET TASK STATISTICS
@task_bp.route("/api/tasks/statistics", methods=["GET"])
def get_task_statistics():
    try:
        email = request.args.get('email')
        query = Task.query
        
        if email:
            query = query.filter_by(assignedByEmail=email)
        
        total_tasks = query.count()
        
        status_counts = {}
        for status in ["Pending", "In Progress", "Completed"]:
            count = query.filter_by(status=status).count()
            status_counts[status] = count
        
        priority_counts = {}
        for priority in ["High", "Medium", "Low"]:
            count = query.filter_by(priority=priority).count()
            priority_counts[priority] = count
        
        overdue_tasks = query.filter(
            Task.dueDate < datetime.utcnow().date().isoformat(),
            Task.status != "Completed"
        ).count()
        
        return jsonify({
            "success": True,
            "data": {
                "total_tasks": total_tasks,
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "overdue_tasks": overdue_tasks
            }
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch task statistics",
            "message": str(e)
        }), 500


# ✅ GET TASK DETAILS
@task_bp.route("/api/tasks/<int:id>", methods=["GET"])
def get_task_details(id):
    try:
        task = Task.query.get_or_404(id)
        return jsonify({
            "success": True,
            "task": task.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to fetch task details",
            "message": str(e)
        }), 500