# routes/usertype_routes.py
from flask import Blueprint, jsonify, request
from app.models.usertype import db, UserType
from app.models.access_control import AccessControl
from app.models.permission import Permission


user_type_bp = Blueprint('user_type_bp', __name__)

# ✅ Create a user type
@user_type_bp.route('/usertype', methods=['POST'])
def create_user_type():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"success": False, "message": "User type name is required"}), 400

    # check duplicate
    if UserType.query.filter_by(name=name).first():
        return jsonify({"success": False, "message": "User type already exists"}), 400

    new_type = UserType(name=name)
    db.session.add(new_type)
    db.session.commit()
    return jsonify({"success": True, "data": new_type.to_dict(), "message": "User type added successfully!"}), 201


# ✅ Get all user types
@user_type_bp.route('/usertype', methods=['GET'])
def get_all_user_types():
    user_types = UserType.query.all()
    return jsonify({"success": True, "data": [ut.to_dict() for ut in user_types]}), 200


# ✅ Get one user type by ID
@user_type_bp.route('/usertype/<int:id>', methods=['GET'])
def get_user_type(id):
    user_type = UserType.query.get(id)
    if not user_type:
        return jsonify({"success": False, "message": "User type not found"}), 404
    return jsonify({"success": True, "data": user_type.to_dict()}), 200


# ✅ Update user type
@user_type_bp.route('/usertype/<int:id>', methods=['PUT'])
def update_user_type(id):
    data = request.get_json()
    name = data.get('name')

    user_type = UserType.query.get(id)
    if not user_type:
        return jsonify({"success": False, "message": "User type not found"}), 404

    user_type.name = name
    db.session.commit()
    return jsonify({"success": True, "data": user_type.to_dict(), "message": "User type updated successfully"}), 200


# ✅ Delete user type
# ✅ Delete user type
@user_type_bp.route('/usertype/<int:id>', methods=['DELETE'])
def delete_user_type(id):
    user_type = UserType.query.get(id)
    if not user_type:
        return jsonify({
            "success": False,
            "message": "User type not found"
        }), 404

    # 1️⃣ Delete related access control rows
    AccessControl.query.filter_by(user_type_id=id).delete()

    # 2️⃣ Delete related user permissions rows
    Permission.query.filter_by(user_type_id=id).delete()

    # 3️⃣ Now safely delete user type
    db.session.delete(user_type)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "User type deleted successfully"
    })

