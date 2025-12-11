# backend/models/quotation.py
from app import db
from datetime import datetime

class Quotation(db.Model):
    __tablename__ = 'quotations'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    
    # Company details
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    company_name = db.Column(db.String(200), nullable=False)
    company_address = db.Column(db.Text, nullable=True)
    company_gstin = db.Column(db.String(20), nullable=True)
    
    # Contact details
    contact_person = db.Column(db.String(100), nullable=True)
    contact_mobile = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    
    # Issuer details (stored as JSON)
    issuer_details = db.Column(db.JSON, nullable=True)
    
    # Totals
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    total_discount = db.Column(db.Numeric(12, 2), default=0)
    total_tax = db.Column(db.Numeric(12, 2), default=0)
    grand_total = db.Column(db.Numeric(12, 2), default=0)
    
    # Additional info
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, sent, accepted, rejected, paid, cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('QuotationItem', backref='quotation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'date': self.date,
            'time': self.time,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_gstin': self.company_gstin,
            'contact_person': self.contact_person,
            'contact_mobile': self.contact_mobile,
            'contact_email': self.contact_email,
            'issuer_details': self.issuer_details or {},
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'total_discount': float(self.total_discount) if self.total_discount else 0,
            'total_tax': float(self.total_tax) if self.total_tax else 0,
            'grand_total': float(self.grand_total) if self.grand_total else 0,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class QuotationItem(db.Model):
    __tablename__ = 'quotation_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    
    # Item details
    item_name = db.Column(db.String(200), nullable=False)
    hsn_sac = db.Column(db.String(20), nullable=True)
    supplier_part_no = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Dimensions
    cut_width = db.Column(db.Numeric(10, 2), default=0)
    length = db.Column(db.Numeric(10, 2), default=0)
    
    # Batch info
    batch_no = db.Column(db.String(50), nullable=True)
    
    # Pricing
    mrp = db.Column(db.Numeric(12, 2), default=0)
    quantity = db.Column(db.Numeric(10, 2), default=1)
    unit = db.Column(db.String(20), default='pcs')
    
    # Discount
    discount = db.Column(db.Numeric(10, 2), default=0)
    discount_type = db.Column(db.String(20), default='amount')  # amount or percentage
    
    # Tax
    tax_rate = db.Column(db.Numeric(5, 2), default=18.0)
    
    # Calculated fields
    price_per_unit = db.Column(db.Numeric(12, 2), default=0)
    amount_before_discount = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    amount_after_discount = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    item_total = db.Column(db.Numeric(12, 2), default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'quotation_id': self.quotation_id,
            'item_name': self.item_name,
            'hsn_sac': self.hsn_sac,
            'supplier_part_no': self.supplier_part_no,
            'description': self.description,
            'cut_width': float(self.cut_width) if self.cut_width else 0,
            'length': float(self.length) if self.length else 0,
            'batch_no': self.batch_no,
            'mrp': float(self.mrp) if self.mrp else 0,
            'quantity': float(self.quantity) if self.quantity else 1,
            'unit': self.unit,
            'discount': float(self.discount) if self.discount else 0,
            'discount_type': self.discount_type,
            'tax_rate': float(self.tax_rate) if self.tax_rate else 18.0,
            'price_per_unit': float(self.price_per_unit) if self.price_per_unit else 0,
            'amount_before_discount': float(self.amount_before_discount) if self.amount_before_discount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'amount_after_discount': float(self.amount_after_discount) if self.amount_after_discount else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'item_total': float(self.item_total) if self.item_total else 0
        }