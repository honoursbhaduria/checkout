from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "checkout_http_requests_total",
    "Total HTTP requests handled by Checkout backend",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "checkout_http_request_duration_seconds",
    "HTTP request latency histogram in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_INTERVIEW_SESSIONS = Gauge(
    "checkout_active_interview_sessions",
    "Number of currently active candidate interview sessions"
)

AI_INFERENCE_DURATION_SECONDS = Histogram(
    "checkout_ai_inference_duration_seconds",
    "AI model inference latency in seconds",
    ["provider", "task"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 15.0]
)


def get_metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
