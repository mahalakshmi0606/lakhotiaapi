from flask import Blueprint, request, jsonify
from app import db
from app.models.mrpchange import Product
from app.models.stock import Stock  # <-- IMPORTANT: using stock table here
import pandas as pd
import os

mrp_bp = Blueprint("mrp_bp", __name__, url_prefix="/api/mrp")

# -------------------------------------------------------------------
# 📌 POST: Upload Excel & Save Brands + MRP
# -------------------------------------------------------------------
@mrp_bp.route("/update", methods=["POST"])
def update_mrp():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file or file.filename.strip() == "":
            return jsonify({"error": "Invalid or empty file uploaded"}), 400

        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)

        # Read Excel
        try:
            df = pd.read_excel(filepath, dtype=str)
        except Exception as e:
            return jsonify({"error": f"Cannot read Excel file: {str(e)}"}), 400

        df.columns = df.columns.str.lower().str.replace(" ", "_")

        if "brand" not in df.columns or "mrp" not in df.columns:
            return jsonify({"error": "Excel must contain 'brand' and 'mrp' columns"}), 400

        inserted_records = []

        for _, row in df.iterrows():
            brand = str(row.get("brand", "")).strip()
            mrp_raw = str(row.get("mrp", "")).strip()

            if not brand or brand.lower() == "nan":
                continue

            try:
                mrp_value = float(mrp_raw)
            except:
                continue

            new_item = Product(brand=brand, mrp=mrp_value)
            db.session.add(new_item)

            inserted_records.append({
                "brand": brand,
                "mrp": mrp_value
            })

        db.session.commit()

        return jsonify({
            "message": "Data inserted successfully from Excel.",
            "inserted_count": len(inserted_records),
            "inserted": inserted_records
        }), 200

    except Exception as e:
        print("MRP Insert Error:", e)
        db.session.rollback()
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


# -------------------------------------------------------------------
# 📌 GET: View all saved MRP records
# -------------------------------------------------------------------
@mrp_bp.route("/all", methods=["GET"])
def get_all_mrp():
    try:
        products = Product.query.all()

        data = []
        for p in products:
            data.append({
                "id": p.id,
                "brand": p.brand,
                "mrp": p.mrp
            })

        return jsonify({
            "total": len(data),
            "data": data
        }), 200

    except Exception as e:
        print("MRP Fetch Error:", e)
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


# -------------------------------------------------------------------
# ❌ DELETE: Remove MRP Record by ID
# -------------------------------------------------------------------
@mrp_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_mrp(id):
    try:
        product = Product.query.get(id)

        if not product:
            return jsonify({"error": "Record not found"}), 404

        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": "Record deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print("MRP Delete Error:", e)
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


# -------------------------------------------------------------------
# ✏ PUT: Edit MRP Record
# -------------------------------------------------------------------
@mrp_bp.route("/edit/<int:id>", methods=["PUT"])
def edit_mrp(id):
    data = request.json
    brand = data.get("brand")
    mrp = data.get("mrp")

    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Not found"}), 404

    product.brand = brand
    product.mrp = mrp
    db.session.commit()

    return jsonify({"message": "Updated successfully"})


# -------------------------------------------------------------------
# ⭐ NEW API: GET Unmatched Stock Brands (Not in MRP Table)
# -------------------------------------------------------------------
@mrp_bp.route("/unmatched", methods=["GET"])
def get_unmatched_brands():
    try:
        # Fetch unique stock brands
        stock_brands = db.session.query(Stock.brand).all()
        stock_brands = {str(b[0]).strip().lower() for b in stock_brands if b[0]}

        # Fetch unique MRP brands
        mrp_brands = db.session.query(Product.brand).all()
        mrp_brands = {str(b[0]).strip().lower() for b in mrp_brands if b[0]}

        # Find brands missing in MRP
        unmatched = list(stock_brands - mrp_brands)

        return jsonify({
            "unmatched_count": len(unmatched),
            "unmatched": unmatched
        })

    except Exception as e:
        print("Unmatched Fetch Error:", e)
        return jsonify({"error": f"Server Error: {str(e)}"}), 500
