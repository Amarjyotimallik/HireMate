"""
Celery Application Configuration

Configures Celery with Redis as broker and result backend.
Handles rate-limited resume processing tasks.
"""

import os
from celery import Celery
from dotenv import load_dotenv

# Load .env from backend root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'hiremate',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Concurrency — upped to 4 workers for faster processing
    worker_concurrency=4,
    worker_prefetch_multiplier=1,

    # Rate limiting — max 30 resume tasks per minute (Optimized Mode)
    task_default_rate_limit='30/m',

    # Task time limits
    task_soft_time_limit=120,  # 2 min soft limit per task
    task_time_limit=180,       # 3 min hard limit per task

    # Result expiration
    result_expires=3600,  # 1 hour

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Queue configuration
    task_default_queue='hiremate_bulk',
    task_routes={
        'app.celery_tasks.process_single_resume': {'queue': 'hiremate_bulk'},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app'])

# Explicitly import tasks to ensure they are registered
from app import celery_tasks
