import os
import time
from urllib.parse import urlparse

import psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres"
)

def wait_for_db(max_retries: int = 30, delay: float = 2.0):
    parsed = urlparse(DATABASE_URL)
    dbname = parsed.path.lstrip("/") or "postgres"
    user = parsed.username or "postgres"
    password = parsed.password or "postgres"
    host = parsed.hostname or "db"
    port = parsed.port or 5432

    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=3,
            )
            conn.close()
            print("Postgres is available")
            return
        except Exception as e:
            print(f"[{attempt}/{max_retries}] Postgres not ready: {e}")
            time.sleep(delay)
    raise SystemExit("Postgres did not become available in time")

if __name__ == "__main__":
    wait_for_db()