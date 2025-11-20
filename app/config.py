import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Render provides DATABASE_URL with postgres:// but SQLAlchemy needs postgresql://
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/acme')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    CELERY_BROKER_URL = os.getenv(
    'REDIS_URL',  # <- use REDIS_URL secret set on Fly
    'redis://localhost:6379/0'  # fallback only if local Redis exists
)
    CELERY_RESULT_BACKEND = os.getenv(
    'REDIS_URL',
    'redis://localhost:6379/0'
    )
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 1800
    CELERY_RESULT_EXPIRES = timedelta(hours=24)
    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
