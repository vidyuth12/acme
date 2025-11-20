import os
import csv
import chardet
from celery import current_task
from celery.exceptions import MaxRetriesExceededError
from app.extensions import celery, db
from app.services.import_service import ImportService
from app.utils.db_helper import DatabaseHelper
from app.utils.progress_tracker import ProgressTracker
from app.utils.csv_validator import CSVValidator

def detect_encoding(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_csv_import(self, job_id: str, filepath: str):
    tracker = ProgressTracker()
    
    try:
        tracker.publish_progress(job_id, 'STARTED', 0, 'Starting CSV import')
        ImportService.update_job_status(job_id, 'STARTED')
        
        total_rows = count_csv_rows(filepath)
        tracker.publish_progress(job_id, 'PROGRESS', 0, f'Found {total_rows} rows', total_rows=total_rows)
        ImportService.update_job_status(job_id, 'PROGRESS', total_rows=total_rows)
        
        tracker.publish_progress(job_id, 'PROGRESS', 5, 'Parsing CSV')
        
        result = process_csv_file(filepath, job_id, total_rows, tracker)
        
        tracker.publish_progress(job_id, 'SUCCESS', 100, 'Import Complete', **result)
        ImportService.update_job_status(
            job_id,
            'SUCCESS',
            processed_rows=result['processed'],
            success_count=result['success'],
            error_count=result['errors']
        )
        
        # Trigger webhooks for upload.completed
        from app.services.webhook_service import WebhookService
        from app.models.import_job import ImportJob
        from datetime import datetime
        
        job = db.session.query(ImportJob).filter_by(id=job_id).first()
        if job:
            webhook_payload = {
                'event': 'upload.completed',
                'upload_id': job_id,
                'filename': job.filename,
                'status': 'completed',
                'imported_count': result['success'],
                'total_rows': result['processed'],
                'error_count': result['errors'],
                'timestamp': datetime.utcnow().isoformat()
            }
            WebhookService.trigger_webhooks('upload.completed', webhook_payload)
        
        cleanup_file(filepath)
        
        return {
            'status': 'SUCCESS',
            'job_id': job_id,
            **result
        }
        
    except Exception as e:
        error_message = str(e)
        
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            tracker.publish_progress(job_id, 'FAILURE', 0, f'Failed: {error_message}')
            ImportService.update_job_status(job_id, 'FAILURE', error_message=error_message)
            
            # Trigger webhooks for upload.failed
            from app.services.webhook_service import WebhookService
            from app.models.import_job import ImportJob
            from datetime import datetime
            
            job = db.session.query(ImportJob).filter_by(id=job_id).first()
            if job:
                webhook_payload = {
                    'event': 'upload.failed',
                    'upload_id': job_id,
                    'filename': job.filename,
                    'status': 'failed',
                    'error_message': error_message,
                    'timestamp': datetime.utcnow().isoformat()
                }
                WebhookService.trigger_webhooks('upload.failed', webhook_payload)
            
            cleanup_file(filepath)
            raise

def count_csv_rows(filepath: str) -> int:
    encoding = detect_encoding(filepath)
    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        return sum(1 for _ in csv.DictReader(f))

def process_csv_file(filepath: str, job_id: str, total_rows: int, tracker: ProgressTracker) -> dict:
    processed = 0
    success = 0
    errors = 0
    batch = []
    batch_size = 1000
    
    encoding = detect_encoding(filepath)
    print(f"DEBUG: Detected encoding: {encoding} for file {filepath}")
    print(f"DEBUG: Total rows passed to process_csv_file: {total_rows}")
    
    # Read first line to get headers and normalize them
    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        header_line = f.readline()
        # Handle potential BOM if not handled by encoding
        if header_line.startswith('\ufeff'):
            header_line = header_line[1:]
            
        # Parse headers using csv reader to handle quoting correctly
        header_reader = csv.reader([header_line])
        headers = next(header_reader)
        normalized_headers = [h.strip().lower() for h in headers]
        
    print(f"DEBUG: Normalized headers: {normalized_headers}")

    with open(filepath, 'r', encoding=encoding, errors='replace') as f:
        # Skip the header line since we already read it
        # We use DictReader with our normalized headers
        # But we need to skip the first line of the file
        f.readline() 
        
        reader = csv.DictReader(f, fieldnames=normalized_headers)
        
        for row_num, row in enumerate(reader, start=1):
            if row_num == 1:
                print(f"DEBUG: First row data: {row}")

            processed += 1
            
            is_valid, error_msg = CSVValidator.validate_row(row, row_num)
            
            if not is_valid:
                errors += 1
                if errors <= 10:
                    print(f"DEBUG: Validation error: {error_msg}")
                    tracker.publish_progress(
                        job_id, 'PROGRESS',
                        int((processed / total_rows) * 100),
                        f'Validation error: {error_msg}'
                    )
                continue
            
            normalized = CSVValidator.normalize_row(row)
            batch.append(normalized)
            
            if len(batch) >= batch_size:
                batch_result = DatabaseHelper.batch_upsert_products(batch, batch_size)
                success += batch_result['processed']
                batch = []
                
                progress = int((processed / total_rows) * 100)
                tracker.publish_progress(
                    job_id, 'PROGRESS', progress,
                    'Validating' if progress < 50 else 'Importing products',
                    processed=processed,
                    total=total_rows
                )
                ImportService.update_job_status(job_id, 'PROGRESS', processed_rows=processed)
        
        if batch:
            batch_result = DatabaseHelper.batch_upsert_products(batch, batch_size)
            success += batch_result['processed']
    
    return {
        'processed': processed,
        'success': success,
        'errors': errors
    }

def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
