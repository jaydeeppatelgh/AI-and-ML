import os
import requests
import json
TRANSPILE_URL = os.getenv("TRANSPILE_URL", "https://bruno.ngrok.pro/api/v1/transpiler/")

def transpile(request_text: str, base_pattern_spec: str, context_chat_history=None, timeout=15):
    payload = {
        "request": request_text,
        "knowledge": {"base_pattern": base_pattern_spec},
        "context": {"chat_history": context_chat_history or []}
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "bruno-client/1.0"}
    resp = requests.post(TRANSPILE_URL, json=payload, headers=headers, timeout=timeout)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # raise a clearer exception to be converted to HTTP 502 by FastAPI caller
        raise Exception(f"transpiler HTTP {resp.status_code}: {resp.text}") from e
    try:
        return resp.json()
    except ValueError as e:
        raise Exception(f"transpiler returned non-json response: {resp.text}") from e
