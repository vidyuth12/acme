import time
import redis
import json
from flask import Blueprint, jsonify
from app.services.import_service import ImportService
from app.utils.sse import SSEHelper
from app.utils.progress_tracker import ProgressTracker

job_bp = Blueprint('jobs', __name__)

@job_bp.route('/<job_id>/events')
def job_events(job_id: str):
    def event_stream():
        tracker = ProgressTracker()
        redis_client = tracker.redis_client
        pubsub = redis_client.pubsub()
        channel = f"job:{job_id}:events"
        
        pubsub.subscribe(channel)
        
        initial_progress = tracker.get_progress(job_id)
        if initial_progress:
            yield SSEHelper.format_sse(initial_progress)
        
        timeout = 300
        start_time = time.time()
        
        try:
            for message in pubsub.listen():
                if time.time() - start_time > timeout:
                    break
                
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    yield SSEHelper.format_sse(data)
                    
                    if data.get('state') in ['SUCCESS', 'FAILURE']:
                        break
                
                time.sleep(0.1)
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
    
    return SSEHelper.create_stream(event_stream())

@job_bp.route('/<job_id>')
def get_job(job_id: str):
    job = ImportService.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    tracker = ProgressTracker()
    progress_data = tracker.get_progress(job_id)
    
    response = job.to_dict()
    
    if progress_data:
        response['live_progress'] = progress_data
    
    return jsonify(response), 200
