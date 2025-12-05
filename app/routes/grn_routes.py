from flask import Blueprint, request, jsonify
from app import db
from app.models.grn import GRN

grn_bp = Blueprint("grn_bp", __name__, url_prefix="/api/grn")


# -------------------------------------------------------------------
# SAVE **SINGLE** GRN ENTRY
# -------------------------------------------------------------------
@grn_bp.route("/save", methods=["POST"])
def save_grn():
    try:
        data = request.get_json()

        new_grn = GRN(
            invoice_number=data.get("invoice_number"),
            invoice_date=data.get("invoice_date"),
            customer_name=data.get("customer_name"),
            customer_part_no=data.get("customer_part_no"),
            customer_description=data.get("customer_description"),

            item_name=data.get("item_name"),
            brand=data.get("brand"),
            length=data.get("length"),
            width=data.get("width"),
            buy_price=data.get("buy_price"),
            batch_code=data.get("batch_code")
        )

        db.session.add(new_grn)
        db.session.commit()

        return jsonify({"success": True, "message": "GRN saved successfully!"})

    except Exception as e:
        print("Error saving GRN:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# SAVE **MULTIPLE** GRN ITEMS (same invoice)
# -------------------------------------------------------------------
@grn_bp.route("/save-multiple", methods=["POST"])
def save_multiple_grn():
    try:
        data = request.get_json()
        items = data.get("items", [])

        if not items:
            return jsonify({"success": False, "message": "No items provided"}), 400

        for item in items:
            new_grn = GRN(
                invoice_number=data.get("invoice_number"),
                invoice_date=data.get("invoice_date"),
                customer_name=data.get("customer_name"),
                customer_part_no=data.get("customer_part_no"),
                customer_description=data.get("customer_description"),

                item_name=item.get("item_name"),
                brand=item.get("brand"),
                length=item.get("length"),
                width=item.get("width"),
                buy_price=item.get("buy_price"),
                batch_code=item.get("batch_code")
            )

            db.session.add(new_grn)

        db.session.commit()

        return jsonify({"success": True, "message": "Multiple GRN items saved!"})

    except Exception as e:
        print("Error saving multiple GRN:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------------------
# GET ALL GRN RECORDS
# -------------------------------------------------------------------
@grn_bp.route("/all", methods=["GET"])
def get_all_grn():
    try:
        grn_list = GRN.query.order_by(GRN.id.desc()).all()

        result = []
        for g in grn_list:
            result.append({
                "id": g.id,
                "invoice_number": g.invoice_number,
                "invoice_date": g.invoice_date,
                "customer_name": g.customer_name,
                "customer_part_no": g.customer_part_no,
                "customer_description": g.customer_description,

                "item_name": g.item_name,
                "brand": g.brand,
                "length": g.length,
                "width": g.width,
                "buy_price": g.buy_price,
                "batch_code": g.batch_code,

                "created_on": g.created_on.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({"success": True, "data": result})

    except Exception as e:
        print("Error loading GRN list:", e)
        return jsonify({"success": False, "error": str(e)}), 500
