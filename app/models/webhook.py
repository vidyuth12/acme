from datetime import datetime
from app.extensions import db

class Webhook(db.Model):
    __tablename__ = 'webhooks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    event_types = db.Column(db.JSON, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_test_status = db.Column(db.String(50))
    last_test_response_code = db.Column(db.Integer)
    last_test_response_time = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'event_types': self.event_types,
            'enabled': self.enabled,
            'last_test_status': self.last_test_status,
            'last_test_response_code': self.last_test_response_code,
            'last_test_response_time': self.last_test_response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get('name'),
            url=data.get('url'),
            event_types=data.get('event_types', []),
            enabled=data.get('enabled', True)
        )
    
    def update_from_dict(self, data):
        if 'name' in data:
            self.name = data['name']
        if 'url' in data:
            self.url = data['url']
        if 'event_types' in data:
            self.event_types = data['event_types']
        if 'enabled' in data:
            self.enabled = data['enabled']
        self.updated_at = datetime.utcnow()
    
    def update_test_result(self, status: str, response_code: int = None, response_time: float = None):
        self.last_test_status = status
        self.last_test_response_code = response_code
        self.last_test_response_time = response_time
        self.updated_at = datetime.utcnow()
