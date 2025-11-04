import os
import requests
import time
import pytest

BASE = os.getenv("BASE_URL", "http://localhost:8000")

def test_health_and_create_component():
    # Wait briefly for service
    time.sleep(1)
    # Ensure transpiler mock is reachable
    r = requests.post("http://localhost:8001/api/v1/transpiler/", json={"request":"ping"})
    assert r.status_code == 200
    # Create knowledge base directly via DB is expected before running; for quick test we assume KB exists
    # This test is illustrative; in CI you could pre-seed the DB or call a KB creation endpoint.
    assert r.json().get("code") is not None
