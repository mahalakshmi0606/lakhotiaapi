from app import db

class Advance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    deduct_month = db.Column(db.String(50))  # NEW FIELD
    status = db.Column(db.String(20), default="Pending")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "department": self.department,
            "amount": self.amount,
            "reason": self.reason,
            "date": self.date,
            "time": self.time,
            "deduct_month": self.deduct_month,  # NEW
            "status": self.status,
        }
