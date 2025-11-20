from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from app.services.import_service import ImportService
from app.tasks.csv_import import process_csv_import

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/products/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not ImportService.is_valid_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed'}), 400
    
    try:
        job = ImportService.create_import_job(file.filename)
        
        filepath = ImportService.save_upload_file(file, current_app.config['UPLOAD_FOLDER'])
        
        process_csv_import.delay(job.id, filepath)
        
        return jsonify({
            'job_id': job.id,
            'filename': file.filename,
            'status': 'PENDING'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@upload_bp.route('/uploads/recent', methods=['GET'])
def get_recent_uploads():
    """Get recent upload jobs with their progress."""
    try:
        # Get last 10 import jobs
        jobs = ImportService.get_recent_jobs(limit=10)
        
        return jsonify([{
            'id': job.id,
            'filename': job.filename,
            'status': job.status,
            'total_rows': job.total_rows,
            'processed_rows': job.processed_rows,
            'success_count': job.success_count,
            'error_count': job.error_count,
            'progress': int((job.processed_rows / job.total_rows * 100)) if job.total_rows > 0 else 0,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        } for job in jobs]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
