#!/usr/bin/env python
from app import create_app
from app.extensions import db
from app.models import Product, Webhook, ImportJob

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database initialized successfully!")
