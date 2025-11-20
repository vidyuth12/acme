from datetime import datetime
from app.extensions import db

class ImportJob(db.Model):
    __tablename__ = 'import_jobs'
    
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='PENDING', nullable=False)
    total_rows = db.Column(db.Integer, default=0)
    processed_rows = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'status': self.status,
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'error_message': self.error_message,
            'progress': self.get_progress(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_progress(self):
        if self.total_rows == 0:
            return 0
        return int((self.processed_rows / self.total_rows) * 100)
