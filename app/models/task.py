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
    product_code = db.Column(db.String(50))
    length = db.Column(db.String(50))
    width = db.Column(db.String(50))
    qty = db.Column(db.String(50))
    batch_code = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Pending")
    status_check = db.Column(db.String(20))  # 🟢 NEW — store status check value
    note = db.Column(db.Text)  # 🟢 stores rework or extra notes
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary for JSON responses"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
