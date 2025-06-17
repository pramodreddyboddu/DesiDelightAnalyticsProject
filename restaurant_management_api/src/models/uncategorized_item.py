from datetime import datetime
from . import db

class UncategorizedItem(db.Model):
    __tablename__ = 'uncategorized_item'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    frequency = db.Column(db.Integer, default=1)
    suggested_category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # 'pending', 'categorized', 'ignored'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'frequency': self.frequency,
            'suggested_category': self.suggested_category,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 