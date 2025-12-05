# models/stock_sold.py
from app import db
from datetime import datetime

class StockSold(db.Model):
    __tablename__ = "stock_sold"

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200))
    sold_qty = db.Column(db.Float)
    date = db.Column(db.String(30))          # storing date as string (YYYY-MM-DD)
    customer_name = db.Column(db.String(200))
    remarks = db.Column(db.String(500))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
