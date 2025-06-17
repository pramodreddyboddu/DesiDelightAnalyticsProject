from datetime import datetime
from . import db

class Sale(db.Model):
    __tablename__ = 'sale'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    clover_id = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    line_item_date = db.Column(db.DateTime, nullable=False)
    order_employee_id = db.Column(db.String(50))
    order_employee_name = db.Column(db.String(100))
    order_id = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    item_revenue = db.Column(db.Float, nullable=False)
    modifiers_revenue = db.Column(db.Float, default=0)
    total_revenue = db.Column(db.Float, nullable=False)
    discounts = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    item_total_with_tax = db.Column(db.Float, nullable=False)
    payment_state = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define relationship with Item
    item = db.relationship('Item', back_populates='sales')

    def to_dict(self):
        return {
            'id': self.id,
            'clover_id': self.clover_id,
            'item_id': self.item_id,
            'line_item_date': self.line_item_date.isoformat() if self.line_item_date else None,
            'order_employee_id': self.order_employee_id,
            'order_employee_name': self.order_employee_name,
            'order_id': self.order_id,
            'quantity': self.quantity,
            'item_revenue': self.item_revenue,
            'modifiers_revenue': self.modifiers_revenue,
            'total_revenue': self.total_revenue,
            'discounts': self.discounts,
            'tax_amount': self.tax_amount,
            'item_total_with_tax': self.item_total_with_tax,
            'payment_state': self.payment_state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 