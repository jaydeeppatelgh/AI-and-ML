from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
import logging
from dotenv import load_dotenv

from webhook_engine import route_webhook
from fsm_plumbing import PlumbingFSM

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI()

# Store active FSMs by call_id
active_calls: dict[str, PlumbingFSM] = {}

# =====================================================
# HELPER: SEND RETELL-COMPATIBLE OUTPUT
# =====================================================
def ws_say(text: str, end_call: bool = False) -> dict:
    """
    Retell Custom LLM requires responses in this format.
    """
    message = {
        "content": [
            {
                "type": "output_text",
                "text": text or ""
            }
        ]
    }
    if end_call:
        message["end_call"] = True
    return message


# =====================================================
# HTTP WEBHOOK (CALL LIFECYCLE EVENTS ONLY)
# =====================================================
@app.post("/retell/webhook")
async def retell_webhook(request: Request):
    """
    Handles Retell lifecycle events:
    - call_started
    - call_ended
    - call_analyzed

    IMPORTANT:
    In Custom LLM mode, this endpoint must NOT return speech.
    """
    try:
        payload = await request.json()
    except Exception:
        logger.error("Invalid JSON payload")
        return {"success": False}

    event = payload.get("event")
    logger.info(f"Received webhook event: {event}")

    return route_webhook(payload) or {"success": True}


# =====================================================
# WEBSOCKET (REAL-TIME CONVERSATION)
# =====================================================
@app.websocket("/retell/webhook/{call_id}")
async def retell_websocket(websocket: WebSocket, call_id: str):
    await websocket.accept()
    logger.info(f"[{call_id}] WebSocket connected")

    if call_id not in active_calls:
        active_calls[call_id] = PlumbingFSM()

    fsm = active_calls[call_id]

    # FSM speaks first
    first_message = fsm.handle("")
    logger.info(f"[{call_id}] FSM greeting: {first_message}")

    await websocket.send_json({
        "type": "response.create",
        "response": {
            "modalities": ["text", "audio"],
            "instructions": first_message
        }
    })

    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"[{call_id}] WS received: {data}")

            transcript_items = data.get("transcript", [])
            turntaking = data.get("turntaking")

            # Only react when user has finished speaking
            if turntaking != "user_turn":
                continue

            if not transcript_items:
                continue

            last_item = transcript_items[-1]
            user_text = last_item.get("content", "").strip()

            if not user_text:
                continue

            logger.info(f"[{call_id}] User said: {user_text}")

            response_text = fsm.handle(user_text)

            # FSM finished → end call
            if not fsm.active:
                fsm.finalize()
                logger.info(f"[{call_id}] FSM completed, ending call")

                await websocket.send_json(
                    ws_say(response_text or "", end_call=True)
                )

                active_calls.pop(call_id, None)
                break

            # Normal FSM response
            await websocket.send_json(ws_say(response_text))

    except WebSocketDisconnect:
        logger.info(f"[{call_id}] WebSocket disconnected")

        if call_id in active_calls:
            fsm = active_calls.pop(call_id)
            fsm.finalize()


# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/health")
def health():
    return {"status": "healthy"}
