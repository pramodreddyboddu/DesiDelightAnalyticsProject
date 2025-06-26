from . import db
from datetime import datetime

class DataSourceConfig(db.Model):
    __tablename__ = 'data_source_config'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), nullable=True)  # NULL for global, or set for per-tenant
    data_type = db.Column(db.String(32), nullable=False)  # 'sales' or 'inventory'
    source = db.Column(db.String(32), nullable=False)     # 'clover' or 'local'
    updated_by = db.Column(db.String(64), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'data_type': self.data_type,
            'source': self.source,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 