from datetime import datetime
from . import db

class Expense(db.Model):
    __tablename__ = 'expense'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))  # Made optional
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(100))  # Added vendor field
    date = db.Column(db.DateTime, nullable=False)
    invoice = db.Column(db.String(50))  # Added invoice field
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'category': self.category,
            'vendor': self.vendor,
            'invoice': self.invoice,
            'date': self.date.isoformat() if self.date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Expense {self.id}>' 