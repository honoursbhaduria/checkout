import pytest
import httpx
import re

@pytest.mark.asyncio
async def test_frontend_hand_drawn_loads():
    """Verify that the Hand-Drawn frontend on port 5173 loads and renders correctly."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get("http://localhost:5173")
        assert res.status_code == 200
        assert "<div id=\"root\">" in res.text


@pytest.mark.asyncio
async def test_prometheus_metrics_scrape():
    """Verify that the Prometheus metrics endpoint exposes metrics."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get("http://localhost:8000/metrics")
        assert res.status_code == 200
        assert "checkout_http_requests_total" in res.text or "python_gc_objects_collected_total" in res.text
