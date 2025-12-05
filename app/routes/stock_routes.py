from flask import Blueprint, request, jsonify
from app import db
from app.models.stock import Stock

stock_bp = Blueprint("stock_bp", __name__, url_prefix="/api/stock")

# -------------------------------------------------------
# BULK SAVE STOCK (POST)
# -------------------------------------------------------
@stock_bp.route("/bulk-save", methods=["POST"])
def bulk_save_stock():
    try:
        data = request.get_json()
        records = data.get("records", [])

        if not records:
            return jsonify({"success": False, "message": "No records found"}), 400

        for r in records:

            # Remove internal React ID if sent
            r.pop("_id", None)

            stock = Stock(
                item_name=r.get("Item Name", "").strip(),
                brand=r.get("Brand", "").strip(),
                brand_code=r.get("Brand Code", "").strip(),
                brand_description=r.get("Brand Description", "").strip(),
                hsn=r.get("HSN", "").strip(),
                batch_code=r.get("Batch Code", "").strip(),
                mrp=float(r.get("MRP", 0) or 0),
                buy_price=float(r.get("Buy Price", 0) or 0),
                width=r.get("Width", ""),
                length=r.get("Length", ""),
                unit=r.get("Unit", ""),
                gst=float(r.get("GST", 0) or 0),
            )

            db.session.add(stock)

        db.session.commit()
        return jsonify({"success": True, "message": "Stock saved successfully!"})

    except Exception as e:
        print("ERROR (Bulk Save):", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# GET ALL STOCK (GET)
# -------------------------------------------------------
@stock_bp.route("/all", methods=["GET"])
def get_all_stock():
    try:
        items = Stock.query.order_by(Stock.id.desc()).all()
        output = []

        for s in items:
            output.append({
                "id": s.id,
                "Item Name": s.item_name,
                "Brand": s.brand,
                "Brand Code": s.brand_code,
                "Brand Description": s.brand_description,
                "HSN": s.hsn,
                "Batch Code": s.batch_code,
                "MRP": s.mrp,
                "Buy Price": s.buy_price,
                "Width": s.width,
                "Length": s.length,
                "Unit": s.unit,
                "GST": s.gst,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({"success": True, "data": output})

    except Exception as e:
        print("ERROR (Get All):", e)
        return jsonify({"success": False, "message": "Server error"}), 500
