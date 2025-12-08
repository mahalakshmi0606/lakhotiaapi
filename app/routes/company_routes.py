from flask import Blueprint, request, jsonify
from app import db
from app.models.company import Company

company_bp = Blueprint("company_bp", __name__)

# ======================================================
#                 ADD COMPANY
# ======================================================
@company_bp.route("/company", methods=["POST"])
def add_company():
    data = request.json

    try:
        new_company = Company(
            company_name=data.get("companyName"),
            company_address=data.get("companyAddress"),
            pin_code=data.get("pinCode"),
            industry_segment=data.get("industrySegment"),
            customer_name=data.get("customerName"),
            customer_mobile=data.get("customerMobile"),
            customer_email=data.get("customerEmail"),
            department=data.get("department"),
            personal_mobile=data.get("personalMobile"),
            personal_email=data.get("personalEmail")
        )

        db.session.add(new_company)
        db.session.commit()

        return jsonify({"message": "Company added successfully!"}), 201

    except Exception as e:
        print("Error:", e)
        db.session.rollback()
        return jsonify({"message": "Error adding company"}), 500


# ======================================================
#                 GET ALL COMPANIES
# ======================================================
@company_bp.route("/company", methods=["GET"])
def get_companies():
    companies = Company.query.all()
    return jsonify([c.to_dict() for c in companies]), 200


# ======================================================
#                 GET COMPANY BY ID
# ======================================================
@company_bp.route("/company/<int:id>", methods=["GET"])
def get_company(id):
    company = Company.query.get(id)

    if not company:
        return jsonify({"message": "Company not found"}), 404

    return jsonify(company.to_dict()), 200


# ======================================================
# ⭐ GET COMPANY BY MOBILE — RETURN NAME + CUSTOMER NAME
# ======================================================
@company_bp.route("/company/mobile/<string:mobile>", methods=["GET"])
def get_company_by_mobile(mobile):

    # Ensure clean 10-digit mobile (optional but safer)
    mobile = ''.join(filter(str.isdigit, mobile))[-10:]

    company = Company.query.filter_by(customer_mobile=mobile).first()

    if not company:
        return jsonify({"message": "Company not found"}), 404

    return jsonify({
        "company_name": company.company_name,
        "customer_name": company.customer_name
    }), 200


# ======================================================
#                 GET COMPANY BY NAME
# ======================================================
@company_bp.route("/company/name/<string:name>", methods=["GET"])
def get_company_by_name(name):
    company = Company.query.filter(
        Company.company_name.ilike(f"%{name}%")
    ).first()

    if not company:
        return jsonify({"message": "Company not found"}), 404

    return jsonify(company.to_dict()), 200


# ======================================================
#                 UPDATE COMPANY
# ======================================================
@company_bp.route("/company/<int:id>", methods=["PUT"])
def update_company(id):
    company = Company.query.get(id)

    if not company:
        return jsonify({"message": "Company not found"}), 404

    data = request.json

    try:
        company.company_name = data.get("companyName")
        company.company_address = data.get("companyAddress")
        company.pin_code = data.get("pinCode")
        company.industry_segment = data.get("industrySegment")
        company.customer_name = data.get("customerName")
        company.customer_mobile = data.get("customerMobile")
        company.customer_email = data.get("customerEmail")
        company.department = data.get("department")
        company.personal_mobile = data.get("personalMobile")
        company.personal_email = data.get("personalEmail")

        db.session.commit()

        return jsonify({"message": "Company updated successfully!"}), 200

    except Exception as e:
        print("Error:", e)
        db.session.rollback()
        return jsonify({"message": "Error updating company"}), 500


# ======================================================
#                 DELETE COMPANY
# ======================================================
@company_bp.route("/company/<int:id>", methods=["DELETE"])
def delete_company(id):
    company = Company.query.get(id)

    if not company:
        return jsonify({"message": "Company not found"}), 404

    try:
        db.session.delete(company)
        db.session.commit()
        return jsonify({"message": "Company deleted!"}), 200

    except Exception as e:
        print("Error:", e)
        db.session.rollback()
        return jsonify({"message": "Error deleting company"}), 500
