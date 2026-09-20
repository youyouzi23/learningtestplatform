import os

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0",
)

REPORT_CACHE_TTL_SECONDS = int(os.getenv("REPORT_CACHE_TTL_SECONDS", "300"))
