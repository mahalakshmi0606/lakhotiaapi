from flask import Blueprint, request, jsonify
from app import db
from app.models.company import Company

company_bp = Blueprint("company_bp", __name__)

# -------------------- Add Company --------------------
@company_bp.route("/company", methods=["POST"])
def add_company():
    data = request.json
    new_company = Company(
        company_name=data["companyName"],
        company_address=data["companyAddress"],
        pin_code=data["pinCode"],
        industry_segment=data["industrySegment"],
        customer_name=data["customerName"],
        customer_mobile=data["customerMobile"],
        customer_email=data["customerEmail"],
        department=data["department"],
        personal_mobile=data["personalMobile"],
        personal_email=data["personalEmail"]
    )
    db.session.add(new_company)
    db.session.commit()
    return jsonify({"message": "Company added successfully!"}), 201


# -------------------- Get All Companies --------------------
@company_bp.route("/company", methods=["GET"])
def get_companies():
    companies = Company.query.all()
    return jsonify([c.to_dict() for c in companies]), 200


# -------------------- Get Company by ID --------------------
@company_bp.route("/company/<int:id>", methods=["GET"])
def get_company(id):
    company = Company.query.get(id)
    if not company:
        return jsonify({"message": "Company not found"}), 404
    return jsonify(company.to_dict()), 200


# 🆕 -------------------- Get Company by Mobile --------------------
@company_bp.route("/company/mobile/<string:mobile>", methods=["GET"])
def get_company_by_mobile(mobile):
    company = Company.query.filter_by(customer_mobile=mobile).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404
    return jsonify(company.to_dict()), 200


# 🆕 -------------------- Get Company by Name --------------------
@company_bp.route("/company/name/<string:name>", methods=["GET"])
def get_company_by_name(name):
    company = Company.query.filter(Company.company_name.ilike(f"%{name}%")).first()
    if not company:
        return jsonify({"message": "Company not found"}), 404
    return jsonify(company.to_dict()), 200


# -------------------- Update Company --------------------
@company_bp.route("/company/<int:id>", methods=["PUT"])
def update_company(id):
    company = Company.query.get(id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    data = request.json
    company.company_name = data["companyName"]
    company.company_address = data["companyAddress"]
    company.pin_code = data["pinCode"]
    company.industry_segment = data["industrySegment"]
    company.customer_name = data["customerName"]
    company.customer_mobile = data["customerMobile"]
    company.customer_email = data["customerEmail"]
    company.department = data["department"]
    company.personal_mobile = data["personalMobile"]
    company.personal_email = data["personalEmail"]

    db.session.commit()
    return jsonify({"message": "Company updated successfully!"}), 200


# -------------------- Delete Company --------------------
@company_bp.route("/company/<int:id>", methods=["DELETE"])
def delete_company(id):
    company = Company.query.get(id)
    if not company:
        return jsonify({"message": "Company not found"}), 404

    db.session.delete(company)
    db.session.commit()
    return jsonify({"message": "Company deleted!"}), 200
