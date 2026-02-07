from flask import Blueprint, request, jsonify
from app import db
from app.models.stocksold import StockSold
from datetime import datetime

stock_sold_bp = Blueprint("stock_sold_bp", __name__, url_prefix="/api/stock_sold")

@stock_sold_bp.route("/save", methods=["POST"])
def save_stock_sold():
    try:
        data = request.get_json()
        
        # Create new stock sold record
        sold_record = StockSold(
            task_id=data.get("task_id"),
            item_name=data.get("item_name", ""),
            company_name=data.get("company_name", ""),
            quantity=float(data.get("quantity", 0) or 0),
            unit=data.get("unit", ""),
            sold_date=data.get("sold_date", datetime.now().strftime("%Y-%m-%d")),
            customer_name=data.get("customer_name", ""),
            sold_remarks=data.get("sold_remarks", ""),
            
            # Additional fields
            hsn_sac=data.get("hsn_sac", ""),
            invoice_remarks=data.get("invoice_remarks", ""),
            invoice_amount=float(data.get("invoice_amount", 0) or 0),
            mrp=float(data.get("mrp", 0) or 0),
            material_type=data.get("material_type", ""),
            production_end_date=data.get("production_end_date", ""),
            production_start_date=data.get("production_start_date", ""),
            production_status=data.get("production_status", ""),
            quality_check=data.get("quality_check", ""),
            thickness=data.get("thickness", ""),
            due_date=data.get("due_date", "")
        )
        
        db.session.add(sold_record)
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Stock sold record saved successfully",
            "id": sold_record.id
        }), 201
        
    except Exception as e:
        print("ERROR save_stock_sold:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error: " + str(e)}), 500

@stock_sold_bp.route("/all", methods=["GET"])
def get_all_sold():
    try:
        rows = StockSold.query.order_by(StockSold.id.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "task_id": r.task_id,
                "item_name": r.item_name,
                "company_name": r.company_name,
                "quantity": r.quantity,
                "unit": r.unit,
                "sold_date": r.sold_date,
                "customer_name": r.customer_name,
                "sold_remarks": r.sold_remarks,
                "created_on": r.created_on.isoformat() if r.created_on else None,
                
                # Additional fields
                "hsn_sac": r.hsn_sac,
                "invoice_remarks": r.invoice_remarks,
                "invoice_amount": r.invoice_amount,
                "mrp": r.mrp,
                "material_type": r.material_type,
                "production_end_date": r.production_end_date,
                "production_start_date": r.production_start_date,
                "production_status": r.production_status,
                "quality_check": r.quality_check,
                "thickness": r.thickness,
                "due_date": r.due_date
            })
        return jsonify({"success": True, "data": out})
    except Exception as e:
        print("ERROR get_all_sold:", e)
        return jsonify({"success": False, "message": "Server error: " + str(e)}), 500

@stock_sold_bp.route("/<int:id>", methods=["GET"])
def get_sold_by_id(id):
    try:
        record = StockSold.query.get(id)
        if not record:
            return jsonify({"success": False, "message": "Record not found"}), 404
            
        return jsonify({
            "success": True,
            "data": {
                "id": record.id,
                "task_id": record.task_id,
                "item_name": record.item_name,
                "company_name": record.company_name,
                "quantity": record.quantity,
                "unit": record.unit,
                "sold_date": record.sold_date,
                "customer_name": record.customer_name,
                "sold_remarks": record.sold_remarks,
                "created_on": record.created_on.isoformat() if record.created_on else None,
                
                # Additional fields
                "hsn_sac": record.hsn_sac,
                "invoice_remarks": record.invoice_remarks,
                "invoice_amount": record.invoice_amount,
                "mrp": record.mrp,
                "material_type": record.material_type,
                "production_end_date": record.production_end_date,
                "production_start_date": record.production_start_date,
                "production_status": record.production_status,
                "quality_check": record.quality_check,
                "thickness": record.thickness,
                "due_date": record.due_date
            }
        })
    except Exception as e:
        print("ERROR get_sold_by_id:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

@stock_sold_bp.route("/update/<int:id>", methods=["PUT"])
def update_sold_record(id):
    try:
        data = request.get_json()
        record = StockSold.query.get(id)
        
        if not record:
            return jsonify({"success": False, "message": "Record not found"}), 404
        
        # Update fields
        record.item_name = data.get("item_name", record.item_name)
        record.company_name = data.get("company_name", record.company_name)
        record.quantity = float(data.get("quantity", record.quantity) or 0)
        record.unit = data.get("unit", record.unit)
        record.sold_date = data.get("sold_date", record.sold_date)
        record.customer_name = data.get("customer_name", record.customer_name)
        record.sold_remarks = data.get("sold_remarks", record.sold_remarks)
        
        # Update additional fields
        record.hsn_sac = data.get("hsn_sac", record.hsn_sac)
        record.invoice_remarks = data.get("invoice_remarks", record.invoice_remarks)
        record.invoice_amount = float(data.get("invoice_amount", record.invoice_amount) or 0)
        record.mrp = float(data.get("mrp", record.mrp) or 0)
        record.material_type = data.get("material_type", record.material_type)
        record.production_end_date = data.get("production_end_date", record.production_end_date)
        record.production_start_date = data.get("production_start_date", record.production_start_date)
        record.production_status = data.get("production_status", record.production_status)
        record.quality_check = data.get("quality_check", record.quality_check)
        record.thickness = data.get("thickness", record.thickness)
        record.due_date = data.get("due_date", record.due_date)
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "Record updated successfully"})
        
    except Exception as e:
        print("ERROR update_sold_record:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500

@stock_sold_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_sold_record(id):
    try:
        record = StockSold.query.get(id)
        if not record:
            return jsonify({"success": False, "message": "Record not found"}), 404
            
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Record deleted successfully"})
        
    except Exception as e:
        print("ERROR delete_sold_record:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500

@stock_sold_bp.route("/search", methods=["GET"])
def search_sold_items():
    try:
        item_name = request.args.get("item_name", "")
        customer_name = request.args.get("customer_name", "")
        from_date = request.args.get("from_date", "")
        to_date = request.args.get("to_date", "")
        
        query = StockSold.query
        
        if item_name:
            query = query.filter(StockSold.item_name.ilike(f"%{item_name}%"))
        if customer_name:
            query = query.filter(StockSold.customer_name.ilike(f"%{customer_name}%"))
        if from_date:
            query = query.filter(StockSold.sold_date >= from_date)
        if to_date:
            query = query.filter(StockSold.sold_date <= to_date)
        
        rows = query.order_by(StockSold.id.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "item_name": r.item_name,
                "company_name": r.company_name,
                "quantity": r.quantity,
                "unit": r.unit,
                "sold_date": r.sold_date,
                "customer_name": r.customer_name,
                "sold_remarks": r.sold_remarks,
                "created_on": r.created_on.isoformat() if r.created_on else None
            })
            
        return jsonify({"success": True, "data": out})
        
    except Exception as e:
        print("ERROR search_sold_items:", e)
        return jsonify({"success": False, "message": "Server error"}), 500