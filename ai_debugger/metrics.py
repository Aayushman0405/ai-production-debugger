from prometheus_client import Counter, Histogram

# -------------------------
# Request counters
# -------------------------

ANALYZE_REQUESTS_TOTAL = Counter(
    "ai_debugger_analyze_requests_total",
    "Total number of analyze requests",
    ["status"]  # success | error
)

HEALTH_REQUESTS_TOTAL = Counter(
    "ai_debugger_health_requests_total",
    "Total number of health check requests"
)

# -------------------------
# Latency histograms
# -------------------------

ANALYZE_LATENCY = Histogram(
    "ai_debugger_analyze_latency_seconds",
    "Latency of analyze endpoint",
    buckets=(0.1, 0.3, 0.5, 1, 2, 3, 5)
)
