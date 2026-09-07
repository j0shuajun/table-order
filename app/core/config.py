"""Application configuration loaded from environment with safe local defaults.

JWT secret and TTL are read from the environment so deployments can override
them; defaults exist only to make local/demo startup frictionless.
"""

import os

# Token lifetime: 16 hours (see requirements — admin/table sessions last one shift).
JWT_TTL_SECONDS = 16 * 60 * 60

# HS256 signing secret. Overridable via env; the default is for local demo only.
JWT_SECRET = os.environ.get(
    "TABLE_ORDER_JWT_SECRET", "dev-secret-change-me-please-32-bytes-min!!"
)
JWT_ALGORITHM = "HS256"

# SQLite database file (created on first run). Overridable for tests.
DATABASE_URL = os.environ.get("TABLE_ORDER_DATABASE_URL", "sqlite:///table_order.db")

# Single demo store fixed for this MVP.
DEFAULT_STORE_ID = "store001"

# Timezone used only to derive the human-facing order-number date/time.
ORDER_NUMBER_TZ = "Asia/Seoul"
