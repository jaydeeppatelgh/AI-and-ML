import os
import json
import uvicorn
import requests
import logging
import hmac
import psycopg2
import secrets
import html as html_module
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from db import get_conn
from openai import OpenAI
from pathlib import Path
from uuid import UUID

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "tiny-helper.log"

logger = logging.getLogger("tiny-helper")
logger.setLevel(logging.DEBUG)  # use DEBUG to see everything; change to INFO in prod

# Avoid adding handlers twice (FastAPI/uvicorn reloads can re-import the file)
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

INGEST_TOKEN = os.environ.get("INGEST_TOKEN", "")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

app = FastAPI(title="Tiny Helper - MVP")

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Tiny Helper API",
        "docs": "http://localhost:8000/docs",
    }

class EventIn(BaseModel):
    """
    Simplified event model for error ingestion.
    Only essential fields are required.
    """
    # REQUIRED fields
    client_id: str = Field(..., description="Client UUID")
    flow: str = Field(..., description="Human-readable flow name, e.g., 'WooCommerce → Zoho'")
    entity_type: str = Field(..., description="e.g., order, product, customer")
    entity_id: str = Field(..., description="External ID like order number, e.g., 'SO-12811'")
    status: str = Field(..., description="'fail' or 'success'")
    occurred_at: str = Field(..., description="ISO datetime of when the error occurred")

    # OPTIONAL fields
    severity: Optional[str] = Field(None, description="Error severity, e.g., 'critical', 'warning'")
    message: Optional[str] = Field(None, description="Error message, e.g., 'SKU not found for item ABC-123'")
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context for debugging (not used for notifications)")

    @validator("status")
    def status_must_be_known(cls, v):
        allowed = {"fail", "success"}
        if v not in allowed:
            raise ValueError("status must be 'fail' or 'success'")
        return v

    @validator("occurred_at")
    def occurred_at_must_be_valid(cls, v):
        parsed = parse_datetime(v)
        if not parsed:
            raise ValueError("occurred_at must be a valid ISO datetime (e.g., '2025-12-09T09:10:27.378925')")
        return v

class DigestRunRequest(BaseModel):
    window_days: int = Field(
        1,
        ge=1,
        description="Look back this many days if window_minutes is not provided"
    )
    window_minutes: Optional[int] = Field(
        None,
        ge=1,
        description="If set, ignore window_days and use this many minutes instead"
    )
    schedule_label: Optional[str] = Field(
        None,
        description="Optional label like 'daily@08:00IST' or 'manual_run'"
    )

class ClientCreateIn(BaseModel):
    name: str = Field(..., min_length=2, description="Client display name")
    contacts: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional contacts JSON (e.g. emails)"
    )

def parse_datetime(s: Optional[str]):
    if not s:
        return None
    # Try a few common formats
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in fmts:
        try:
            if "T" in s and fmt.startswith("%Y-%m-%dT"):
                # ISO with optional zone
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    pass
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def require_bearer(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="missing auth")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid auth header")
    token = parts[1]
    if not hmac.compare_digest(token, INGEST_TOKEN):
        raise HTTPException(status_code=401, detail="You do not have permission to create this client")

def require_client_api_key(
    authorization: Optional[str],
    expected_client_id: Optional[str] = None
):
    """
    Validates client API key and optionally enforces client_id match.
    Returns (client_id, client_name)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="missing auth")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid auth header")

    token = parts[1]

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM clients WHERE api_key = %s",
                (token,)
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="You do not have access to this client")

        client_id, client_name = row

        # 🔒 Enforce client_id match if provided
        if expected_client_id and str(client_id) != str(expected_client_id):
            raise HTTPException(status_code=401, detail="You do not have access to this client")

        return client_id, client_name

    finally:
        conn.close()

def require_admin_or_client(
    authorization: Optional[str],
    expected_client_id: str
):
    """
    Allows either:
    - Admin token (INGEST_TOKEN), OR
    - Client API key that matches expected_client_id
    """

    # 1️⃣ Try admin auth first
    try:
        require_bearer(authorization)
        return "admin"
    except HTTPException:
        pass

    # 2️⃣ Try client auth
    try:
        require_client_api_key(authorization, expected_client_id)
        return "client"
    except HTTPException:
        raise HTTPException(
            status_code=401,
            detail="You do not have access to this client"
        )

def send_slack(text: str):
    """
    Returns (ok: bool, info: str)
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set; skipping Slack")
        return (False, "no webhook set")
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        ok = (resp.status_code == 200)
        info = f"{resp.status_code} {resp.text}"
        if ok:
            logger.info(f"Slack sent ok: {info}")
        else:
            logger.error(f"Slack send failed: {info}")
        return (ok, info)
    except Exception as e:
        logger.exception("Slack send raised exception")
        return (False, f"exception: {e}")

def get_ai_recommendation(messages: List[str]) -> List[str]:
    """
    Get AI-powered, non-technical recommendations based on individual error messages.

    Input:
        messages: list of raw message strings from events table
                  e.g. ["Line item ABC-123 missing", "SKU not found for order 12345"]

    Output:
        list of strings like:
        [
          "Line item ABC-123 missing → What this means: ... Next steps: 1) ... 2) ...",
          "SKU not found for order 12345 → What this means: ... Next steps: 1) ... 2) ..."
        ]
    """
    if not OPENAI_API_KEY or not OpenAI:
        return []

    # Remove duplicates and empty / None messages, keep stable order
    seen = set()
    clean_messages: List[str] = []
    for m in messages:
        m = (m or "").strip()
        if not m:
            continue
        if m in seen:
            continue
        seen.add(m)
        clean_messages.append(m)

    if not clean_messages:
        return []

    # Give each message an id so we can map responses back
    msgs_payload = [
        {"id": i + 1, "text": m}
        for i, m in enumerate(clean_messages)
    ]

    system_prompt = (
        "You are an expert e-commerce operations coach. "
        "Explain things in simple, friendly language for a non-technical store owner. "
        "Avoid technical jargon like 'API', 'database', 'HTTP', etc. "
        "Instead say things like 'your online shop system' or 'your stock system'. "
        "Return STRICT JSON that matches the schema below—no prose, no markdown, no extra keys."
    )

    user_prompt = {
        "task": (
            "For each error message, do two things:\n"
            "1) Explain in simple words what probably happened.\n"
            "2) Give 2–4 short, practical steps the store owner can take right now."
        ),
        "messages": msgs_payload,
        "style": {
            "tone": "friendly, calm, non-technical",
            "steps_max": 4,
            "steps_min": 2,
            "step_length": "one short sentence"
        },
        "output_schema": {
            "type": "object",
            "required": ["answers"],
            "properties": {
                "answers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "explanation_simple", "steps"],
                        "properties": {
                            "id": {"type": "number"},
                            "explanation_simple": {"type": "string"},
                            "steps": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "maxItems": 4
                            }
                        }
                    }
                }
            }
        },
        "format": "Return JSON only."
    }

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=800,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)}
            ]
        )

        content = (resp.choices[0].message.content or "").strip()
        recommendations: List[str] = []

        try:
            data = json.loads(content)
            answers = data.get("answers", [])

            # Map id -> original message text
            msg_by_id = {p["id"]: p["text"] for p in msgs_payload}

            for ans in answers:
                _id = ans.get("id")
                simple = (ans.get("explanation_simple") or "").strip()
                steps_raw = ans.get("steps") or []
                steps = [(s or "").strip() for s in steps_raw if (s or "").strip()]
                if _id in msg_by_id and (simple or steps):
                    original = msg_by_id[_id]

                    # Build a friendly one-line summary with numbered steps
                    steps_part = ""
                    if steps:
                        numbered = [f"{i+1}) {s}" for i, s in enumerate(steps)]
                        # Example: "Next steps: 1) Check X. 2) Update Y."
                        steps_part = " Next steps: " + " ".join(numbered)

                    combined = f"{original} → What this means: {simple}{steps_part}".strip()
                    recommendations.append(combined)

        except json.JSONDecodeError:
            # Fallback: if the model didn't return proper JSON
            if content:
                recommendations.append(content)

        # Safety net: if something went wrong, return a generic, merchant-friendly suggestion
        if not recommendations:
            for m in clean_messages:
                recommendations.append(
                    f"{m} → What this means: Something about this order or product "
                    f"doesn't match what your system expects. "
                    f"Next steps: 1) Check the order and product details in your shop. "
                    f"2) Make sure the product code exists and is active. "
                    f"3) If you use another system (like an ERP/warehouse tool), "
                    f"make sure the product is set up there as well."
                )

        return recommendations

    except Exception:
        try:
            logger.exception("Failed to get AI recommendations from messages")
        except Exception:
            pass
        return []

def build_email_html(client_name: str, window_start, window_end, stats: Dict[str, int], 
                    recommendations: List[str], error_rate: float, total: int, fails: int) -> str:
    """
    Build a professional, friendly HTML email template with AI recommendations and pricing CTAs.
    
    Args:
        client_name: Client/tenant name
        window_start: Start datetime of the digest window
        window_end: End datetime of the digest window
        stats: Dict of {reason: count} for top errors
        recommendations: List of AI-powered recommendation strings
        error_rate: Error rate as a decimal (0.0–1.0)
        total: Total number of events
        fails: Number of failures
    
    Returns:
        HTML string ready to send via email
    """
    
    # Escape strings for safe HTML rendering
    safe_client = html_module.escape(str(client_name))
    safe_start = html_module.escape(str(window_start.date()))
    safe_end = html_module.escape(str(window_end.date()))
    error_rate_pct = round(error_rate * 100, 2)
    try:
        delta_days = (window_end - window_start).days
        days_count = max(1, int(delta_days))
    except Exception:
        days_count = 1
    
    # Build top reasons HTML
    reasons_html = ""
    if stats:
        sorted_stats = sorted(stats.items(), key=lambda kv: kv[1], reverse=True)[:5]
        for reason, count in sorted_stats:
            safe_reason = html_module.escape(str(reason or "unknown"))
            reasons_html += f"<li style='margin: 8px 0; color: #333;'><strong>{safe_reason}:</strong> {count} occurrence(s)</li>"
    else:
        reasons_html = "<li style='color: #666;'>No errors detected in this period.</li>"
    
    # Build recommendations HTML
    recs_html = ""
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            safe_rec = html_module.escape(str(rec))
            recs_html += f"<div style='margin: 12px 0; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #4CAF50; color: #333;'>{safe_rec}</div>"
    else:
        recs_html = "<p style='color: #666;'>Keep monitoring your flows. No immediate actions suggested.</p>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tiny Helper Digest</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .header p {{
                margin: 8px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
                margin: 25px 0;
            }}
            .stat-box {{
                background-color: #f0f4ff;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #e0e7ff;
            }}
            .stat-box .label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .stat-box .value {{
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-box.error {{
                background-color: #fff3e0;
                border-color: #ffe0b2;
            }}
            .stat-box.error .value {{
                color: #f57c00;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-bottom: 15px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            .reasons-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            .cta-section {{
                background-color: #f9f9f9;
                padding: 25px 20px;
                border-top: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                margin: 30px -20px;
            }}
            .cta-title {{
                font-size: 16px;
                font-weight: 600;
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }}
            .pricing-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
            }}
            .pricing-card {{
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s ease;
            }}
            .pricing-card:hover {{
                border-color: #667eea;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            }}
            .pricing-card.featured {{
                border-color: #667eea;
                background-color: #f0f4ff;
                transform: scale(1.05);
            }}
            .pricing-card .badge {{
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                margin-bottom: 10px;
                text-transform: uppercase;
            }}
            .pricing-card .name {{
                font-size: 16px;
                font-weight: 600;
                color: #333;
                margin: 10px 0;
            }}
            .pricing-card .price {{
                font-size: 22px;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .pricing-card .description {{
                font-size: 12px;
                color: #666;
                margin: 10px 0;
                line-height: 1.4;
            }}
            .pricing-card .cta-button {{
                display: inline-block;
                background-color: #667eea;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 13px;
                font-weight: 600;
                margin-top: 15px;
                transition: background-color 0.3s;
            }}
            .pricing-card .cta-button:hover {{
                background-color: #764ba2;
            }}
            .pricing-card.featured .cta-button {{
                background-color: #4CAF50;
            }}
            .pricing-card.featured .cta-button:hover {{
                background-color: #45a049;
            }}
            .footer {{
                background-color: #f5f5f5;
                padding: 20px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
                font-size: 12px;
                color: #666;
            }}
            .footer a {{
                color: #667eea;
                text-decoration: none;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
            @media only screen and (max-width: 600px) {{
                .stats-grid, .pricing-grid {{
                    grid-template-columns: 1fr;
                }}
                .pricing-card.featured {{
                    transform: scale(1);
                }}
                .header h1 {{
                    font-size: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>📊 Error Digest Report</h1>
                <p>{safe_client} • {safe_start} to {safe_end}</p>
            </div>

            <!-- Main Content -->
            <div class="content">
                <p style="margin-top: 0; font-size: 15px; color: #555;">
                    Hi there! Here's a summary of your system's health over the past {days_count} day(s). We've analyzed your errors and compiled actionable insights below.
                </p>

                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="label">Total Events</div>
                        <div class="value">{total}</div>
                    </div>
                    <div class="stat-box error">
                        <div class="label">Failures</div>
                        <div class="value">{fails}</div>
                    </div>
                    <div class="stat-box">
                        <div class="label">Error Rate</div>
                        <div class="value">{error_rate_pct}%</div>
                    </div>
                </div>

                <!-- Top Reasons Section -->
                <div class="section">
                    <div class="section-title">🔍 Top Issues Found</div>
                    <ul class="reasons-list">
                        {reasons_html}
                    </ul>
                </div>

                <!-- AI Recommendations Section -->
                <div class="section">
                    <div class="section-title">💡 AI Recommendations</div>
                    <p style="color: #666; font-size: 14px; margin: 0 0 15px 0;">Based on your error patterns, here's what we recommend:</p>
                    {recs_html}
                </div>

                <!-- Pricing & CTAs Section -->
                <div class="cta-section">
                    <div class="cta-title">Upgrade Your Monitoring & Support</div>
                    <div class="pricing-grid">
                        <!-- AI Reporting -->
                        <div class="pricing-card">
                            <div class="name">🤖 AI Reporting</div>
                            <div class="price">£99</div>
                            <div class="description">per month</div>
                            <div class="description" style="font-size: 11px;">Advanced AI insights and trend analysis</div>
                            <a href="mailto:sales@tiny-helper.io?subject=Interested%20in%20AI%20Reporting" class="cta-button">Learn More</a>
                        </div>

                        <!-- Monitoring (Featured) -->
                        <div class="pricing-card featured">
                            <div class="badge">Most Popular</div>
                            <div class="name">📈 Monitoring</div>
                            <div class="price">£199</div>
                            <div class="description">per month</div>
                            <div class="description" style="font-size: 11px;">Real-time alerts & detailed dashboards</div>
                            <a href="mailto:sales@tiny-helper.io?subject=Interested%20in%20Monitoring" class="cta-button">Start Now</a>
                        </div>

                        <!-- Proactive Support -->
                        <div class="pricing-card">
                            <div class="name">🛟 Proactive Support</div>
                            <div class="price">£399</div>
                            <div class="description">per month</div>
                            <div class="description" style="font-size: 11px;">Dedicated support & optimization</div>
                            <a href="mailto:sales@tiny-helper.io?subject=Interested%20in%20Proactive%20Support" class="cta-button">Contact Us</a>
                        </div>
                    </div>
                </div>

                <p style="text-align: center; margin: 25px 0 0 0; font-size: 13px; color: #888;">
                    Have questions? <a href="mailto:support@tiny-helper.io" style="color: #667eea; text-decoration: none;">Reply to this email</a> or visit our <a href="https://tiny-helper.io/docs" style="color: #667eea; text-decoration: none;">documentation</a>.
                </p>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p style="margin: 0 0 10px 0;">
                    Tiny Helper • Intelligent Error Monitoring
                </p>
                <p style="margin: 0;">
                    <a href="https://tiny-helper.io/unsubscribe">Unsubscribe from these emails</a> | 
                    <a href="https://tiny-helper.io/settings">Notification Settings</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_email_sendgrid(to_emails: List[str], subject: str, plain_text: str, html: Optional[str] = None) -> tuple[bool, str]:
    """Send email via SendGrid API with optional HTML content.
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject line
        plain_text: Plain text email body (fallback for clients that don't support HTML)
        html: Optional HTML email body (will be used if provided)
    
    Returns:
        (success: bool, info: str)
    """
    if not SENDGRID_API_KEY or not FROM_EMAIL or not to_emails:
        logger.warning("SendGrid email not sent; missing config")
        return False, "missing configuration"
    
    try:
        url = "https://api.sendgrid.com/v3/mail/send"
        
        # Build content array with both plain text and HTML (if provided)
        content = [{"type": "text/plain", "value": plain_text}]
        if html:
            content.append({"type": "text/html", "value": html})
        
        payload = {
            "personalizations": [
                {"to": [{"email": e} for e in to_emails]}
            ],
            "from": {"email": FROM_EMAIL},
            "subject": subject,
            "content": content
        }
        
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        ok = (resp.status_code == 202)  # SendGrid returns 202 Accepted on success
        info = f"{resp.status_code} {resp.text}"
        
        if ok:
            logger.info(f"Email sent successfully to {', '.join(to_emails)}: {resp.status_code}")
        else:
            logger.error(f"Email send failed: {info}")
        
        return ok, info
        
    except Exception as e:
        logger.exception("Email send raised exception")
        return False, f"exception: {e}"

def get_client_contacts(conn, client_id) -> Dict[str, Any]:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT contacts FROM clients WHERE id=%s", (client_id,))
            row = cur.fetchone()
    except Exception:
        # Log the full traceback so you can debug DB/connectivity issues
        logger.exception("Failed to fetch contacts for client_id=%s", client_id)
        return {}

    if not row:
        # No client found with that id
        logger.debug("No client found with id=%s", client_id)
        return {}

    contacts = row[0] or {}

    # Ensure result is a dict (jsonb could be something else if DB was populated oddly)
    if not isinstance(contacts, dict):
        logger.warning("Contacts for client_id=%s is not a dict (type=%s); returning empty dict",
                    client_id, type(contacts).__name__)
        return {}

    return contacts

def is_critical_event(event: EventIn) -> bool:
    """
    Decide if an event should trigger an immediate alert.
    Rule: status == 'fail' AND severity is critical.
    """
    if event.status != "fail":
        return False
    sev = (event.severity or "").strip().lower()
    return sev == "critical"

def ingest_event_core(
    conn,
    event: EventIn,
    client_id: str
) -> int:
    """
    Core event ingestion logic shared by /events and /events/bulk

    - Inserts event into DB
    - Sends Slack alert if critical
    - Returns inserted event_id
    """

    # 1️⃣ Parse occurred_at safely
    occurred_at = parse_datetime(event.occurred_at) or datetime.utcnow()

    # 2️⃣ Insert event into database
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO events (
                client_id,
                flow,
                entity_type,
                entity_id,
                status,
                severity,
                message,
                occurred_at,
                meta
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            client_id,
            event.flow,
            event.entity_type,
            event.entity_id,
            event.status,
            event.severity,
            event.message,
            occurred_at,
            json.dumps(event.meta or {})
        ))
        event_id = cur.fetchone()[0]

    # 3️⃣ Send Slack alert if event is critical
    if is_critical_event(event):
        severity_label = (event.severity or "").upper() or "CRITICAL"

        slack_text = (
            "🚨 *CRITICAL ERROR ALERT*\n"
            f"*Client ID*: {client_id}\n"
            f"*Flow*: `{event.flow}`\n"
            f"*Entity*: `{event.entity_type}` `{event.entity_id}`\n"
            f"*Status*: `{event.status}`\n"
            f"*Severity*: *{severity_label}*\n"
            f"*Message*: {event.message or '_no message provided_'}\n"
            f"*Occurred at*: `{occurred_at.isoformat()}`\n"
        )

        # Optional meta preview (debug only)
        if event.meta:
            try:
                meta_preview = json.dumps(event.meta, indent=2)
                if len(meta_preview) > 800:
                    meta_preview = meta_preview[:800] + "... (truncated)"
                slack_text += f"\n*Meta*: ```\n{meta_preview}\n```"
            except Exception:
                pass

        send_slack(slack_text)

    return event_id

def run_digests_job(
    payload: DigestRunRequest,
    client_id: Optional[str] = None
):
    """
    Background job to compute and send digests.

    - If client_id is None → runs for ALL clients
    - If client_id is provided → runs for ONE client
    """

    scope = "all clients" if client_id is None else f"client_id={client_id}"
    logger.info("Starting background digest job for %s", scope)

    now_utc = datetime.now(timezone.utc)

    # Determine time window
    if payload.window_minutes is not None:
        end = now_utc
        start = end - timedelta(minutes=payload.window_minutes)
        window_label = f"{payload.window_minutes}m"
    else:
        end = now_utc
        start = end - timedelta(days=payload.window_days)
        window_label = f"{payload.window_days}d"

    conn = get_conn()
    try:
        # 1️⃣ Fetch clients
        with conn.cursor() as cur:
            if client_id:
                cur.execute(
                    "SELECT id, name FROM clients WHERE id = %s",
                    (client_id,)
                )
            else:
                cur.execute(
                    "SELECT id, name FROM clients"
                )
            clients = cur.fetchall()

        if not clients:
            logger.warning("No clients found for digest job (%s)", scope)
            return

        for cid, cname in clients:
            try:
                # 2️⃣ Top error reasons (fails only)
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT message, COUNT(*) AS cnt
                        FROM events
                        WHERE client_id = %s
                          AND occurred_at >= %s AND occurred_at < %s
                          AND status = 'fail'
                        GROUP BY message
                        ORDER BY cnt DESC
                    """, (cid, start, end))
                    rows = cur.fetchall()

                stats = {(r[0] or "unknown"): int(r[1]) for r in rows}

                # 3️⃣ Totals & error rate
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            SUM(CASE WHEN status='fail' THEN 1 ELSE 0 END),
                            COUNT(*)
                        FROM events
                        WHERE client_id = %s
                          AND occurred_at >= %s AND occurred_at < %s
                    """, (cid, start, end))
                    fails, total = cur.fetchone()

                fails = int(fails or 0)
                total = int(total or 0)
                error_rate = (fails / total) if total else 0.0

                # 4️⃣ Repeat patterns (last 14 days)
                repeat_start = end - timedelta(days=14)

                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT message
                        FROM events
                        WHERE client_id = %s
                          AND status = 'fail'
                          AND occurred_at >= %s AND occurred_at < %s
                        GROUP BY message
                        HAVING COUNT(DISTINCT occurred_at::date) >= 3
                    """, (cid, repeat_start, end))
                    repeat_reasons = [r[0] or "unknown" for r in cur.fetchall()]

                # 5️⃣ AI recommendations
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT message
                        FROM events
                        WHERE client_id = %s
                          AND occurred_at >= %s AND occurred_at < %s
                          AND status = 'fail'
                          AND message IS NOT NULL
                        LIMIT 20
                    """, (cid, start, end))
                    messages_for_ai = [r[0] for r in cur.fetchall() if r[0]]

                recs: List[str] = []
                recs.extend(get_ai_recommendation(messages_for_ai))

                # Heuristics
                if error_rate >= 0.05 and fails >= 10:
                    recs.append("High error rate detected. Consider enabling Monitoring.")
                if repeat_reasons:
                    recs.append(
                        f"Repeat issues detected over multiple days: {', '.join(repeat_reasons)}"
                    )

                # 6️⃣ Persist digest
                digest_stats = {
                    "top_reasons": stats,
                    "fails": fails,
                    "total": total,
                    "error_rate": round(error_rate, 4),
                    "repeat_reasons": repeat_reasons,
                    "window_label": window_label,
                }

                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO digests (
                            client_id, window_start, window_end,
                            stats, recommendations, sent_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        cid,
                        start,
                        end,
                        json.dumps(digest_stats),
                        json.dumps(recs),
                        datetime.utcnow()
                    ))
                    digest_id = cur.fetchone()[0]
                    conn.commit()

                # 7️⃣ Notifications
                if fails > 0:
                    contacts = get_client_contacts(conn, cid)
                    to_emails: List[str] = []

                    if isinstance(contacts, dict):
                        if "emails" in contacts and isinstance(contacts["emails"], list):
                            to_emails = contacts["emails"]
                        elif "email" in contacts:
                            to_emails = [contacts["email"]]

                    subject = f"[Tiny Helper] {cname} — Digest ({window_label})"

                    body = (
                        f"Client: {cname}\n"
                        f"Window: {start.isoformat()} → {end.isoformat()} UTC\n"
                        f"Total events: {total}\n"
                        f"Failures: {fails}\n"
                        f"Error rate: {round(error_rate * 100, 2)}%\n"
                    )

                    html_body = build_email_html(
                        client_name=cname,
                        window_start=start,
                        window_end=end,
                        stats=stats,
                        recommendations=recs,
                        error_rate=error_rate,
                        total=total,
                        fails=fails
                    )

                    send_email_sendgrid(to_emails, subject, body, html=html_body)

                    send_slack(
                        f"📊 Digest created for *{cname}*\n"
                        f"Failures: {fails}\n"
                        f"Error rate: {error_rate * 100:.2f}%"
                    )

                logger.info(
                    "Digest completed client=%s digest_id=%s",
                    cname,
                    digest_id
                )

            except Exception:
                logger.exception("Digest failed for client=%s", cname)

    except Exception:
        logger.exception("Digest background job failed (%s)", scope)

    finally:
        conn.close()
        logger.info("Background digest job finished for %s", scope)

# -----------------------------
# Ingestion
# -----------------------------

@app.post("/events")    
def ingest(event: EventIn, authorization: Optional[str] = Header(None)):
    """
    Ingest a single error event.
    
    This endpoint receives error information and stores it in the database.
    If severity is 'critical', it also sends an immediate Slack alert.
    
    Args:
    event: EventIn object with client_id, flow, entity_type, entity_id, status, occurred_at
    plus optional fields: severity, message, meta
    authorization: Bearer token for authentication
    
    Returns:
        {"ok": True, "client_id": "uuid-here", "event_id": 12345}
    """
    # Log incoming event for debugging
    logger.debug(
        "Processing event: client_id=%r flow=%r entity_type=%r entity_id=%r status=%r severity=%r",
        event.client_id, event.flow, event.entity_type, event.entity_id, event.status, event.severity
    )
    
    # Validate UUID first (optional)
    try:
        UUID(event.client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="client_id must be a valid UUID")
    
    # 🔒 Authenticate and enforce client_id match
    client_id_from_token, _ = require_client_api_key(
    authorization,
    expected_client_id=event.client_id
)

    conn = get_conn()

    try:
        client_id = client_id_from_token

        event_id = ingest_event_core(conn, event, client_id)

        conn.commit()

        return {
            "ok": True,
            "client_id": str(client_id),
            "event_id": event_id
        }

    except HTTPException:
        raise

    except psycopg2.Error:
        conn.rollback()
        logger.exception("Database error while ingesting event")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "database_error",
                "message": "Failed to store event"
            }
        )

    except Exception:
        conn.rollback()
        logger.exception("Unexpected error while ingesting event for client_id=%s", event.client_id)
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "server_error",
                "message": "An unexpected error occurred"
            }
        )

    finally:
        conn.close()

@app.post("/events/bulk")
def ingest_bulk(
    events: List[EventIn],
    authorization: Optional[str] = Header(None)
):
    """
    Ingest multiple events in a single request.

    - Same behavior as /events
    - Authenticated once
    - Inserted in a single transaction
    - Partial failures are reported
    """

    # 1️⃣ Validate request body
    if not events:
        raise HTTPException(
            status_code=400,
            detail="No events provided"
        )
    
    MAX_BULK_EVENTS = 50

    if len(events) > MAX_BULK_EVENTS:
        raise HTTPException(
            status_code=413,
            detail=f"Bulk request exceeds maximum allowed events ({MAX_BULK_EVENTS})"
        )

    # 2️⃣ Validate client_id format (from first event)
    first_client_id = events[0].client_id
    try:
        UUID(first_client_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="client_id must be a valid UUID"
        )

    # 3️⃣ Authenticate ONCE and enforce client isolation
    client_id_from_token, _ = require_client_api_key(
        authorization,
        expected_client_id=first_client_id
    )

    conn = get_conn()

    inserted_event_ids: List[int] = []
    failed: List[Dict[str, Any]] = []

    try:
        # 4️⃣ Process each event
        for idx, event in enumerate(events):
            # Enforce same client_id for all events
            if event.client_id != first_client_id:
                failed.append({
                    "index": idx,
                    "error": "Mixed client_id in bulk request"
                })
                continue

            try:
                event_id = ingest_event_core(
                    conn=conn,
                    event=event,
                    client_id=client_id_from_token
                )
                inserted_event_ids.append(event_id)

            except Exception as e:
                logger.exception(
                    "Bulk event insert failed at index=%s",
                    idx
                )
                failed.append({
                    "index": idx,
                    "error": str(e)
                })

        # 5️⃣ Commit once for all successful inserts
        conn.commit()

        return {
            "ok": True,
            "client_id": str(client_id_from_token),
            "received": len(events),
            "inserted": len(inserted_event_ids),
            "event_ids": inserted_event_ids,
            "failed": failed
        }

    except psycopg2.Error:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Bulk event ingestion failed"
        )

    finally:
        conn.close()

@app.post("/digests/run/all")
def run_digests_all(
    payload: DigestRunRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Trigger digest generation for ALL clients (background).
    """

    # 🔒 Admin-only
    require_bearer(authorization)

    # 🧵 Run digest job asynchronously
    background_tasks.add_task(
        run_digests_job,
        payload
    )

    return {
        "ok": True,
        "message": "Digest job started for all clients",
        "status": "running_in_background"
    }

@app.post("/digests/run/{client_id}")
def run_digest_for_client(
    client_id: str,
    payload: DigestRunRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    Trigger digest generation for a SINGLE client (background).
    Safe for client usage.
    """
    
    try:
        UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="client_id must be a valid UUID")

    # 🔒 Admin OR owning client
    require_admin_or_client(authorization, client_id)

    # 🧵 Run digest job asynchronously (single client)
    background_tasks.add_task(
        run_digests_job,
        payload,
        client_id
    )

    return {
        "ok": True,
        "message": "Digest job started for client",
        "client_id": client_id,
        "status": "running_in_background"
    }

@app.post("/clients")
def create_client(
    payload: ClientCreateIn,
    authorization: Optional[str] = Header(None)
):
    """
    Explicitly create a new client.

    - Admin-only (Bearer token)
    - Prevents duplicate client names
    - Returns client_id (UUID)
    """
    require_bearer(authorization)

    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Client name is required")

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 1️⃣ Check for duplicate client name
            cur.execute(
                "SELECT id FROM clients WHERE name = %s",
                (name,)
            )
            existing = cur.fetchone()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Client with this name already exists"
                )

            # 2️⃣ Generate API key
            api_key = secrets.token_urlsafe(32)

            # 2️⃣ Insert new client
            cur.execute(
                """
                INSERT INTO clients (name, contacts, api_key)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    name,
                    json.dumps(payload.contacts or {}),
                    api_key
                )
            )

            client_id = cur.fetchone()[0]
            conn.commit()

        logger.info("Created new client: %s (%s)", name, client_id)

        return {
            "ok": True,
            "message": "Client created",
            "client_id": str(client_id),
            "api_key": api_key,
            "name": name
        }

    except HTTPException:
        conn.rollback()
        raise

    except psycopg2.Error:
        conn.rollback()
        logger.exception("Database error while creating client")
        raise HTTPException(
            status_code=500,
            detail="Failed to create client"
        )

    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))