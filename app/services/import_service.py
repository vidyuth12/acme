import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.import_job import ImportJob

class ImportService:
    
    ALLOWED_EXTENSIONS = {'csv'}
    
    @staticmethod
    def is_valid_file(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ImportService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def create_import_job(filename: str) -> ImportJob:
        job_id = str(uuid.uuid4())
        job = ImportJob(
            id=job_id,
            filename=filename,
            status='PENDING',
            total_rows=0,
            processed_rows=0,
            success_count=0,
            error_count=0
        )
        db.session.add(job)
        db.session.commit()
        return job
    
    @staticmethod
    def save_upload_file(file, upload_folder: str) -> str:
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        return filepath
    
    @staticmethod
    def update_job_status(job_id: str, status: str, **kwargs):
        job = db.session.query(ImportJob).filter_by(id=job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            if status in ['SUCCESS', 'FAILURE']:
                job.completed_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def get_recent_jobs(limit: int = 10):
        """Get recent import jobs ordered by creation date."""
        return db.session.query(ImportJob).order_by(
            ImportJob.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_job(job_id: str) -> ImportJob:
        return db.session.query(ImportJob).filter_by(id=job_id).first()
