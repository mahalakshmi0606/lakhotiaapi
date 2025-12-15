from app import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    priority = db.Column(db.String(20))
    dueDate = db.Column(db.String(50))
    assignedTo = db.Column(db.String(100))
    assignedBy = db.Column(db.String(100))
    assignedByEmail = db.Column(db.String(100))
    
    # ✅ Quotation-related fields
    quotation_id = db.Column(db.Integer)
    quotation_number = db.Column(db.String(50))
    company_name = db.Column(db.String(100))
    item_id = db.Column(db.Integer)
    item_name = db.Column(db.String(100))
    
    # ✅ Item details from quotation
    supplier_part_no = db.Column(db.String(100))
    hsn_sac = db.Column(db.String(50))
    cut_width = db.Column(db.String(50))
    length = db.Column(db.String(50))
    quantity = db.Column(db.String(50))
    unit = db.Column(db.String(20), default="pcs")
    mrp = db.Column(db.String(50))
    material_type = db.Column(db.String(100))
    thickness = db.Column(db.String(50))
    
    # ✅ Task tracking
    status = db.Column(db.String(20), default="Pending")
    status_check = db.Column(db.String(20))
    note = db.Column(db.Text)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ✅ Invoice details (new)
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.DateTime)
    invoice_amount = db.Column(db.Float)
    invoice_remarks = db.Column(db.Text)
    invoice_created_at = db.Column(db.DateTime)
    
    # ✅ Manufacturing details
    production_start_date = db.Column(db.DateTime)
    production_end_date = db.Column(db.DateTime)
    production_status = db.Column(db.String(50))
    quality_check = db.Column(db.String(50))

    def to_dict(self):
        """Convert model to dictionary for JSON responses"""
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if isinstance(value, datetime):
                result[c.name] = value.isoformat() if value else None
            else:
                result[c.name] = value
        return result