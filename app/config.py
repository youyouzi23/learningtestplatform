import os

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0",
)

REPORT_CACHE_TTL_SECONDS = int(os.getenv("REPORT_CACHE_TTL_SECONDS", "300"))

# Development-only defaults make the sample runnable after cloning. Production
# deployments must override both values with secrets from the environment.
API_ADMIN_KEY = os.getenv("API_ADMIN_KEY", "dev-admin-key")
API_VIEWER_KEY = os.getenv("API_VIEWER_KEY", "dev-viewer-key")
