
from prometheus_client import Counter, Histogram

http_requests = Counter(
    "http_requests_total", "Total HTTP requests", ["path", "status"]
)

webhook_requests = Counter(
    "webhook_requests_total", "Webhook outcomes", ["result"]
)

latency = Histogram(
    "request_latency_ms", "Request latency",
    buckets=[100, 300, 500, 1000, 2000]
)
