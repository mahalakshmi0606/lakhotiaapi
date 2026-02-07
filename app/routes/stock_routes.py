from flask import Blueprint, request, jsonify
from app import db
from app.models.stock import Stock
from flask_cors import CORS
from sqlalchemy import or_

stock_bp = Blueprint("stock_bp", __name__, url_prefix="/api/stock")
CORS(stock_bp)

# -------------------------------------------------------
# SEARCH STOCK (BY BRAND CODE, ITEM NAME, BRAND, HSN, ETC.)
# -------------------------------------------------------
@stock_bp.route("/search", methods=["GET"])
def search_stock():
    try:
        search_term = request.args.get("q", "").strip()
        
        if not search_term:
            return jsonify({"success": False, "message": "Search term required"}), 400
        
        # Search in multiple fields
        search_query = Stock.query.filter(
            or_(
                Stock.brand_code.ilike(f"%{search_term}%"),
                Stock.item_name.ilike(f"%{search_term}%"),
                Stock.brand.ilike(f"%{search_term}%"),
                Stock.hsn.ilike(f"%{search_term}%"),
                Stock.brand_description.ilike(f"%{search_term}%"),
                Stock.batch_code.ilike(f"%{search_term}%")
            )
        ).order_by(Stock.id.desc())
        
        items = search_query.limit(50).all()  # Limit to 50 results
        
        output = []
        for s in items:
            output.append({
                "id": s.id,
                "ID": s.stock_id,
                "Item Name": s.item_name,
                "Brand": s.brand,  # Added Brand field
                "Length": s.length,
                "Width": s.width,
                "Qty": s.quantity,
                "AutoCalculate Count": s.auto_calculate_count,
                "Buy Price": s.buy_price,
                "Batch Code": s.batch_code,
                "Brand Code": s.brand_code,
                "Brand Description": s.brand_description,
                "HSN": s.hsn,
                "MRP": s.mrp,
                "Unit": s.unit,
                "GST": s.gst,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return jsonify({
            "success": True, 
            "data": output,
            "count": len(output)
        }), 200
        
    except Exception as e:
        print("Search Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# GET BUY PRICE BY BRAND CODE (SPECIFIC ENDPOINT)
# -------------------------------------------------------
@stock_bp.route("/buy-price/<string:brand_code>", methods=["GET"])
def get_buy_price(brand_code):
    try:
        if not brand_code or brand_code.strip() == "":
            return jsonify({"success": False, "message": "Brand Code required"}), 400
        
        stock = Stock.query.filter_by(brand_code=brand_code.strip()).first()
        
        if not stock:
            return jsonify({
                "success": False, 
                "message": f"Stock item with Brand Code '{brand_code}' not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": {
                "stock_id": stock.stock_id,
                "brand_code": stock.brand_code,
                "item_name": stock.item_name,
                "buy_price": stock.buy_price,
                "mrp": stock.mrp,
                "brand": stock.brand,
                "hsn": stock.hsn,
                "unit": stock.unit
            }
        }), 200
        
    except Exception as e:
        print("Get Buy Price Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# GET MULTIPLE BUY PRICES (BULK LOOKUP)
# -------------------------------------------------------
@stock_bp.route("/bulk-buy-prices", methods=["POST"])
def get_bulk_buy_prices():
    try:
        data = request.get_json()
        brand_codes = data.get("brand_codes", [])
        
        if not brand_codes:
            return jsonify({"success": False, "message": "Brand codes list required"}), 400
        
        # Remove duplicates and empty strings
        unique_codes = list(set([code.strip() for code in brand_codes if code and str(code).strip()]))
        
        if not unique_codes:
            return jsonify({"success": False, "message": "No valid brand codes provided"}), 400
        
        # Query for all brand codes at once
        stocks = Stock.query.filter(Stock.brand_code.in_(unique_codes)).all()
        
        # Create a map for quick lookup
        stock_map = {stock.brand_code: stock for stock in stocks}
        
        results = []
        not_found = []
        
        for code in unique_codes:
            stock = stock_map.get(code)
            if stock:
                results.append({
                    "stock_id": stock.stock_id,
                    "brand_code": code,
                    "item_name": stock.item_name,
                    "buy_price": stock.buy_price,
                    "mrp": stock.mrp,
                    "brand": stock.brand,
                    "hsn": stock.hsn,
                    "unit": stock.unit
                })
            else:
                not_found.append(code)
        
        return jsonify({
            "success": True,
            "data": results,
            "not_found": not_found,
            "found_count": len(results),
            "not_found_count": len(not_found)
        }), 200
        
    except Exception as e:
        print("Bulk Buy Prices Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


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
            stock_id = str(r.get("ID", "")).strip()
            brand_code = str(r.get("Brand Code", "")).strip()
            
            # Check if record already exists by BOTH stock_id AND brand_code
            existing_stock = None
            if stock_id:
                existing_stock = Stock.query.filter_by(stock_id=stock_id).first()
            
            # If not found by stock_id, try brand_code
            if not existing_stock and brand_code:
                existing_stock = Stock.query.filter_by(brand_code=brand_code).first()
            
            if existing_stock:
                # Record exists, skip insertion to avoid duplicate
                duplicates.append(stock_id if stock_id else brand_code)
                continue
            
            # If no ID provided, generate one from brand code
            if not stock_id and brand_code:
                stock_id = f"ID_{brand_code}"
            elif not stock_id:
                # Skip records with no identifier
                continue

            # Parse numeric values with defaults
            try:
                length_val = float(r.get("Length", 0))
                width_val = float(r.get("Width", 0))
                qty_val = float(r.get("Qty", 0))
                auto_count = length_val * width_val * qty_val
            except:
                length_val = 0
                width_val = 0
                qty_val = 0
                auto_count = 0

            # CREATE NEW RECORD
            new_stock = Stock(
                stock_id=stock_id,
                item_name=r.get("Item Name", "").strip(),
                brand=r.get("Brand", "").strip(),  # Brand field
                length=length_val,
                width=width_val,
                quantity=qty_val,
                auto_calculate_count=auto_count,
                buy_price=float(r.get("Buy Price", 0)),
                batch_code=r.get("Batch Code", "").strip(),
                brand_code=brand_code,
                brand_description=r.get("Brand Description", "").strip(),
                hsn=r.get("HSN", "").strip(),
                mrp=float(r.get("MRP", 0)),
                unit=r.get("Unit", "").strip(),
                gst=float(r.get("GST", 0))
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
# BULK UPDATE ALL FIELDS (USING ID or BRAND CODE)
# -------------------------------------------------------
@stock_bp.route("/update", methods=["PUT", "OPTIONS"])
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
            # Remove React internal ID
            if '_id' in r:
                del r['_id']
            
            # Try ID first, then brand code
            stock_id = str(r.get("ID", "")).strip()
            brand_code = str(r.get("Brand Code", "")).strip()
            
            stock = None
            if stock_id:
                stock = Stock.query.filter_by(stock_id=stock_id).first()
            
            if not stock and brand_code:
                stock = Stock.query.filter_by(brand_code=brand_code).first()

            if not stock:
                not_found.append(stock_id if stock_id else brand_code)
                continue

            # Parse and calculate auto count
            try:
                length_val = float(r.get("Length", stock.length))
                width_val = float(r.get("Width", stock.width))
                qty_val = float(r.get("Qty", stock.quantity))
                auto_count = length_val * width_val * qty_val
            except:
                length_val = stock.length
                width_val = stock.width
                qty_val = stock.quantity
                auto_count = stock.auto_calculate_count
            
            # Update all fields
            stock.item_name = r.get("Item Name", stock.item_name).strip()
            stock.brand = r.get("Brand", stock.brand).strip()  # Brand field
            stock.length = length_val
            stock.width = width_val
            stock.quantity = qty_val
            stock.auto_calculate_count = auto_count
            stock.buy_price = float(r.get("Buy Price", stock.buy_price))
            stock.batch_code = r.get("Batch Code", stock.batch_code).strip()
            stock.brand_code = brand_code if brand_code else stock.brand_code
            stock.brand_description = r.get("Brand Description", stock.brand_description).strip()
            stock.hsn = r.get("HSN", stock.hsn).strip()
            stock.mrp = float(r.get("MRP", stock.mrp))
            stock.unit = r.get("Unit", stock.unit).strip()
            stock.gst = float(r.get("GST", stock.gst))

            updated_count += 1

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
# UPDATE QUANTITY SPECIFICALLY (PUT METHOD)
# -------------------------------------------------------
@stock_bp.route("/update-quantity", methods=["PUT", "OPTIONS"])
def update_quantity_bulk():
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
            stock_id = str(r.get("ID", "")).strip()
            brand_code = str(r.get("Brand Code", "")).strip()
            new_quantity = r.get("Qty", None)
            
            if new_quantity is None:
                continue

            stock = None
            if stock_id:
                stock = Stock.query.filter_by(stock_id=stock_id).first()
            
            if not stock and brand_code:
                stock = Stock.query.filter_by(brand_code=brand_code).first()

            if stock:
                try:
                    # Parse the new quantity
                    qty_val = float(new_quantity)
                    
                    # Update quantity and recalculate auto_calculate_count
                    stock.quantity = qty_val
                    stock.auto_calculate_count = stock.length * stock.width * qty_val
                    
                    updated += 1
                except ValueError:
                    not_found.append(f"{stock_id if stock_id else brand_code} (invalid quantity)")
            else:
                not_found.append(stock_id if stock_id else brand_code)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Quantity updated successfully",
            "updated": updated,
            "not_found": not_found
        }), 200

    except Exception as e:
        print("Bulk Quantity Update Error:", e)
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
            stock_id = str(r.get("ID", "")).strip()
            brand_code = str(r.get("Brand Code", "")).strip()
            mrp = r.get("MRP", None)

            stock = None
            if stock_id:
                stock = Stock.query.filter_by(stock_id=stock_id).first()
            
            if not stock and brand_code:
                stock = Stock.query.filter_by(brand_code=brand_code).first()

            if stock:
                if mrp is not None:
                    stock.mrp = float(mrp)
                updated += 1
            else:
                not_found.append(stock_id if stock_id else brand_code)

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
                "ID": s.stock_id,
                "Item Name": s.item_name,
                "Brand": s.brand,  # Added Brand field
                "Length": s.length,
                "Width": s.width,
                "Qty": s.quantity,
                "AutoCalculate Count": s.auto_calculate_count,
                "Buy Price": s.buy_price,
                "Batch Code": s.batch_code,
                "Brand Code": s.brand_code,
                "Brand Description": s.brand_description,
                "HSN": s.hsn,
                "MRP": s.mrp,
                "Unit": s.unit,
                "GST": s.gst,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({"success": True, "data": output}), 200

    except Exception as e:
        print("Get All Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------------------------------
# DELETE STOCK BY ID or BRAND CODE
# -------------------------------------------------------
@stock_bp.route("/delete", methods=["DELETE", "OPTIONS"])
def delete_stock():
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"}), 200

    try:
        data = request.get_json()
        stock_id = str(data.get("ID", "")).strip()
        brand_code = str(data.get("Brand Code", "")).strip()

        stock = None
        if stock_id:
            stock = Stock.query.filter_by(stock_id=stock_id).first()
        
        if not stock and brand_code:
            stock = Stock.query.filter_by(brand_code=brand_code).first()

        if not stock:
            return jsonify({
                "success": False,
                "message": "Stock item not found"
            }), 404

        db.session.delete(stock)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Stock deleted successfully"
        }), 200

    except Exception as e:
        print("Delete Error:", e)
        db.session.rollback()
        return jsonify({"success": False, "message": "Server error"}), 500