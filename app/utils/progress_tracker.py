import redis
import json
from flask import current_app

class ProgressTracker:
    
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            from app.config import Config
            redis_url = Config.CELERY_BROKER_URL
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    def publish_progress(self, job_id: str, state: str, progress: int = 0, message: str = None, **kwargs):
        data = {
            'job_id': job_id,
            'state': state,
            'progress': progress,
            'message': message,
            **kwargs
        }
        
        key = f"job:{job_id}:progress"
        self.redis_client.setex(key, 3600, json.dumps(data))
        
        channel = f"job:{job_id}:events"
        self.redis_client.publish(channel, json.dumps(data))
    
    def get_progress(self, job_id: str) -> dict:
        key = f"job:{job_id}:progress"
        data = self.redis_client.get(key)
        return json.loads(data) if data else None
