from celery import Celery
from app.core.config import settings

# Celery application instance
# Connects to Upstash Redis or local Redis
broker_url = settings.REDIS_URL
if broker_url.startswith("rediss://"):
    # Upstash Redis TLS configuration
    broker_use_ssl = {"ssl_cert_reqs": None}
else:
    broker_use_ssl = None

celery_app = Celery(
    "checkout_workers",
    broker=broker_url,
    backend=broker_url,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    broker_use_ssl=broker_use_ssl
)
