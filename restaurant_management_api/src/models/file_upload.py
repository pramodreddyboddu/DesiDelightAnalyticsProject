from datetime import datetime
from . import db

class FileUpload(db.Model):
    __tablename__ = 'file_upload'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'sales', 'inventory', 'chef_mapping', 'expenses'
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processing')  # 'processing', 'completed', 'failed'
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed_records': self.processed_records,
            'failed_records': self.failed_records,
            'status': self.status,
            'error_message': self.error_message
        } 