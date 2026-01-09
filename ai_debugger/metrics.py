from prometheus_client import Counter, Histogram

# Total analyze requests (success / error)
ANALYZE_REQUESTS_TOTAL = Counter(
    "ai_debugger_analyze_requests_total",
    "Total number of analyze requests",
    ["status"]
)

# Analyze latency histogram
ANALYZE_LATENCY = Histogram(
    "ai_debugger_analyze_latency_seconds",
    "Latency of analyze endpoint",
    buckets=(0.1, 0.3, 0.5, 1, 2, 3, 5)
)
