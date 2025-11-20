# Acme Product Importer

Flask-based web application for importing large CSV files (up to 500,000 products) into PostgreSQL with real-time progress tracking.

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Docker, Docker Compose

## Project Structure

```
acme/
├── app/
│   ├── api/              # API blueprints
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   ├── templates/        # HTML templates
│   ├── static/           # CSS, JS, images
│   ├── __init__.py       # App factory
│   ├── config.py         # Configuration
│   ├── extensions.py     # Flask extensions
│   └── main.py           # Main routes
├── migrations/           # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── celery_worker.py
```

## Quick Start

### Using Docker (Recommended)

```bash
./run.sh
```

Or manually:

```bash
docker-compose up --build
```

### Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export FLASK_ENV=development
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/acme
export CELERY_BROKER_URL=redis://localhost:6379/0

flask db upgrade
flask run
```

Run Celery worker:

```bash
celery -A celery_worker.celery worker --loglevel=info
```

## API Endpoints

- `GET /` - Upload page
- `GET /products` - Product management page
- `GET /webhooks` - Webhook configuration page
- `GET /health` - Health check

## Environment Variables

See `.env.example` for configuration options.

## Features

- CSV upload with real-time progress (SSE)
- Product CRUD operations
- Webhook management
- Bulk delete functionality
- Async processing with Celery
- Docker deployment ready


# Link to deployed website: https://acme-crimson-smoke-3946.fly.dev
