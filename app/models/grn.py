from app import db
from datetime import datetime

class GRN(db.Model):
    __tablename__ = "grn"

    id = db.Column(db.Integer, primary_key=True)
    
    # Purchase Order reference
    po_number = db.Column(db.String(50), nullable=False)
    
    # Invoice details
    invoice_number = db.Column(db.String(100), nullable=False)
    invoice_date = db.Column(db.String(20), nullable=False)
    
    # Company Details (from Purchase Order)
    company_name = db.Column(db.String(200))
    company_address = db.Column(db.String(500))
    customer_name = db.Column(db.String(100))
    customer_mobile = db.Column(db.String(15))
    customer_email = db.Column(db.String(100))
    department = db.Column(db.String(100))
    gst_number = db.Column(db.String(20))
    supplier_part_no = db.Column(db.String(100))
    supplier_description = db.Column(db.String(500))
    
    # Item Details
    item_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    brand_code = db.Column(db.String(50))
    brand_description = db.Column(db.String(500))
    length = db.Column(db.String(50))
    width = db.Column(db.String(50))
    unit = db.Column(db.String(20), default="PCS")
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    buy_price = db.Column(db.Float, nullable=False)
    
    # Auto generated batch code
    batch_code = db.Column(db.String(100), nullable=False)
    
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, po_number, invoice_number, invoice_date, company_name, 
                 customer_name, item_name, brand, buy_price, batch_code, 
                 company_address=None, customer_mobile=None, customer_email=None,
                 department=None, gst_number=None, supplier_part_no=None, 
                 supplier_description=None, brand_code=None, brand_description=None,
                 length=None, width=None, unit="PCS", quantity=1.0):
        self.po_number = po_number
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        
        # Company details
        self.company_name = company_name
        self.company_address = company_address
        self.customer_name = customer_name
        self.customer_mobile = customer_mobile
        self.customer_email = customer_email
        self.department = department
        self.gst_number = gst_number
        self.supplier_part_no = supplier_part_no
        self.supplier_description = supplier_description
        
        # Item details
        self.item_name = item_name
        self.brand = brand
        self.brand_code = brand_code
        self.brand_description = brand_description
        self.length = length
        self.width = width
        self.unit = unit
        self.quantity = quantity
        self.buy_price = buy_price
        self.batch_code = batch_code
    
    def to_dict(self):
        return {
            "id": self.id,
            "po_number": self.po_number,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            
            # Company details
            "company_name": self.company_name,
            "company_address": self.company_address,
            "customer_name": self.customer_name,
            "customer_mobile": self.customer_mobile,
            "customer_email": self.customer_email,
            "department": self.department,
            "gst_number": self.gst_number,
            "supplier_part_no": self.supplier_part_no,
            "supplier_description": self.supplier_description,
            
            # Item details
            "item_name": self.item_name,
            "brand": self.brand,
            "brand_code": self.brand_code,
            "brand_description": self.brand_description,
            "length": self.length,
            "width": self.width,
            "unit": self.unit,
            "quantity": float(self.quantity) if self.quantity else 1.0,
            "buy_price": float(self.buy_price) if self.buy_price else 0.0,
            "batch_code": self.batch_code,
            
            "created_on": self.created_on.strftime("%Y-%m-%d %H:%M:%S") if self.created_on else None
        }