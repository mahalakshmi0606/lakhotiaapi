# routes/stock_sold_routes.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.stocksold import StockSold

stock_sold_bp = Blueprint("stock_sold_bp", __name__, url_prefix="/api/stock_sold")

@stock_sold_bp.route("/save", methods=["POST"])
def save_stock_sold():
    try:
        data = request.get_json()
        s = StockSold(
            item_name=data.get("item_name", ""),
            sold_qty=float(data.get("sold_qty", 0) or 0),
            date=data.get("date", ""),
            customer_name=data.get("customer_name", ""),
            remarks=data.get("remarks", "")
        )
        db.session.add(s)
        db.session.commit()
        return jsonify({"success": True, "message": "Saved"}), 201
    except Exception as e:
        print("ERROR save_stock_sold:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500

@stock_sold_bp.route("/all", methods=["GET"])
def get_all_sold():
    try:
        rows = StockSold.query.order_by(StockSold.id.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "item_name": r.item_name,
                "sold_qty": r.sold_qty,
                "date": r.date,
                "customer_name": r.customer_name,
                "remarks": r.remarks,
                "created_on": r.created_on.isoformat()
            })
        return jsonify({"success": True, "data": out})
    except Exception as e:
        print("ERROR get_all_sold:", e)
        return jsonify({"success": False, "message": "Server error"}), 500
