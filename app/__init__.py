import os
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, cors, celery

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))
    
    initialize_extensions(app)
    register_blueprints(app)
    configure_celery(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app

def initialize_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    
    with app.app_context():
        from app.models import Product, Webhook, ImportJob

def register_blueprints(app):
    from app.api.product_api import product_bp
    from app.api.upload_api import upload_bp
    from app.api.webhook_api import webhook_bp
    from app.api.job_api import job_bp
    
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(webhook_bp, url_prefix='/api/webhooks')
    app.register_blueprint(job_bp, url_prefix='/api/jobs')
    
    from app.main import main_bp
    app.register_blueprint(main_bp)

def configure_celery(app):
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_track_started=app.config['CELERY_TASK_TRACK_STARTED'],
        task_time_limit=app.config['CELERY_TASK_TIME_LIMIT'],
        result_expires=app.config['CELERY_RESULT_EXPIRES'],
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
