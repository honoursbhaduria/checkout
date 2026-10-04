import logging
from opentelemetry import trace
from opentelemetry.trace import Tracer

logger = logging.getLogger(__name__)


def setup_telemetry() -> Tracer:
    """Configures OpenTelemetry tracer provider."""
    tracer = trace.get_tracer("checkout.backend", "1.0.0")
    logger.info("OpenTelemetry tracing initialized for service: checkout")
    return tracer


tracer = setup_telemetry()
