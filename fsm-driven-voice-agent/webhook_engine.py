"""
RETELL WEBHOOK RESPONSE ENGINE (CUSTOM LLM MODE)
===============================================

IMPORTANT:
- NO conversational responses here
- NO FSM.handle() here
- WebSocket handles ALL speech
- This file is lifecycle + auditing ONLY
"""

import json
import logging

logger = logging.getLogger(__name__)


def route_webhook(payload: dict) -> dict:
    """
    Route Retell webhook lifecycle events.

    In Custom LLM mode:
    - HTTP webhooks must NOT return speech
    - All speech happens over WebSocket
    """
    event = payload.get("event", "unknown")
    logger.info(f"Webhook event: {event}")

    if event == "call_started":
        return handle_call_started(payload)

    if event == "call_ended":
        return handle_call_ended(payload)

    if event == "call_analyzed":
        return handle_call_analyzed(payload)

    logger.warning(f"Unknown event type: {event}")
    return {"success": True}


def handle_call_started(payload: dict) -> dict:
    """
    Call started lifecycle event.

    DO NOT return speech here.
    WebSocket will handle greeting.
    """
    call_id = payload.get("call", {}).get("call_id")
    logger.info(f"[{call_id}] Call started")
    return {"success": True}


def handle_call_ended(payload: dict) -> dict:
    """
    Call ended lifecycle event.

    FSM finalization happens in server.py (WebSocket).
    """
    call_id = payload.get("call", {}).get("call_id")
    logger.info(f"[{call_id}] Call ended by Retell")
    return {"success": True}


def handle_call_analyzed(payload: dict) -> dict:
    """
    Post-call analysis from Retell (optional).
    """
    call_id = payload.get("call", {}).get("call_id")
    analysis = payload.get("call", {}).get("call_analysis", {})

    logger.info(f"[{call_id}] Call analysis received:")
    logger.info(f"  - Summary: {analysis.get('call_summary', 'N/A')}")
    logger.info(f"  - Sentiment: {analysis.get('user_sentiment', 'N/A')}")
    logger.info(f"  - Success: {analysis.get('call_successful', 'N/A')}")

    return {"success": True}
