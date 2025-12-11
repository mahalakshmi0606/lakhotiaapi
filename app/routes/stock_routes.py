from flask import Blueprint, request, jsonify
from app import db
from app.models.stock import Stock
from flask_cors import CORS

stock_bp = Blueprint("stock_bp", __name__, url_prefix="/api/stock")
CORS(stock_bp)

# -------------------------------------------------------
# BULK SAVE (INSERT NEW RECORDS)
# -------------------------------------------------------
@stock_bp.route("/bulk-save", methods=["POST", "OPTIONS"])
def bulk_save_stock():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        data = request.get_json()
        records = data.get("records", [])

        if not records:
            return jsonify({"success": False, "message": "No data provided"}), 400

        saved = 0
        duplicates = []

        for r in records:

            brand_code = str(r.get("Brand Code", "")).strip()

            if not brand_code:
                continue

            # Check if stock exists
            exists = Stock.query.filter_by(brand_code=brand_code).first()
            if exists:
                duplicates.append(brand_code)
                continue

            # CREATE NEW RECORD
            new_stock = Stock(
                item_name=r.get("Item Name", "").strip(),
                brand=r.get("Brand", "").strip(),
                brand_code=brand_code,
                brand_description=r.get("Brand Description", "").strip(),
                hsn=r.get("HSN", "").strip(),
                batch_code=r.get("Batch Code", "").strip(),
                mrp=float(r.get("MRP", 0)),
                buy_price=float(r.get("Buy Price", 0)),
                width=r.get("Width", 0),
                length=r.get("Length", 0),
                unit=r.get("Unit", ""),
                gst=float(r.get("GST", 0)),
            )

            db.session.add(new_stock)
            saved += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Bulk stock saved successfully",
            "saved": saved,
            "duplicates": duplicates
        }), 200

    except Exception as e:
        print("Bulk Save Error:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server Error"}), 500


# -------------------------------------------------------
# BULK UPDATE ALL FIELDS (USING BRAND CODE)
# -------------------------------------------------------
@stock_bp.route("/update", methods=["POST", "OPTIONS"])
def update_stock_bulk():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        data = request.get_json()
        records = data.get("records", [])

        if not records:
            return jsonify({"success": False, "message": "No data found"}), 400

        updated_count = 0
        not_found = []

        for r in records:

            r.pop("_id", None)  # Remove React internal ID
            brand_code = str(r.get("Brand Code", "")).strip()

            if not brand_code:
                continue

            stock = Stock.query.filter_by(brand_code=brand_code).first()

            if stock:
                stock.item_name = r.get("Item Name", stock.item_name).strip()
                stock.brand = r.get("Brand", stock.brand).strip()
                stock.brand_description = r.get(
                    "Brand Description", stock.brand_description
                ).strip()
                stock.hsn = r.get("HSN", stock.hsn).strip()
                stock.batch_code = r.get("Batch Code", stock.batch_code).strip()
                stock.mrp = float(r.get("MRP", stock.mrp))
                stock.buy_price = float(r.get("Buy Price", stock.buy_price))
                stock.width = r.get("Width", stock.width)
                stock.length = r.get("Length", stock.length)
                stock.unit = r.get("Unit", stock.unit)
                stock.gst = float(r.get("GST", stock.gst))

                updated_count += 1
            else:
                not_found.append(brand_code)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Stock updated successfully",
            "updated": updated_count,
            "not_found": not_found
        }), 200

    except Exception as e:
        print("Bulk Update Error:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# UPDATE ONLY MRP (USING PUT)
# -------------------------------------------------------
@stock_bp.route("/update-mrp", methods=["PUT", "OPTIONS"])
def update_mrp_bulk():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        data = request.get_json()
        records = data.get("records", [])

        if not records:
            return jsonify({"success": False, "message": "No data found"}), 400

        updated = 0
        not_found = []

        for r in records:
            brand_code = str(r.get("Brand Code", "")).strip()
            mrp = r.get("MRP", None)

            if not brand_code:
                continue

            stock = Stock.query.filter_by(brand_code=brand_code).first()

            if stock:
                if mrp is not None:
                    stock.mrp = float(mrp)
                updated += 1
            else:
                not_found.append(brand_code)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "MRP updated successfully",
            "updated": updated,
            "not_found": not_found
        }), 200

    except Exception as e:
        print("Bulk MRP Update Error:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# GET ALL STOCK
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

        return jsonify({"success": True, "data": output}), 200

    except Exception as e:
        print("Get All Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500
