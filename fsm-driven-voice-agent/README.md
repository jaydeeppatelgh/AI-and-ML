# FSM-Driven Plumbing Voice Intake Agent

A production-grade AI voice agent for plumbing intake calls built with **Retell Custom LLM mode**. Uses deterministic finite state machine (FSM) logic to ensure safe, structured data capture from real inbound phone calls.

## Overview

This system implements a **fail-closed** architecture that:

- ✅ Handles real-time inbound phone calls via Retell telephony
- ✅ Uses a deterministic FSM for complete conversation control
- ✅ Generates all conversational output from FSM logic (LLM is transport only)
- ✅ Produces structured, validated intake data safe for downstream automation
- ✅ Fails safely on ambiguity—never guesses or infers

## Quick Start

### Prerequisites

- Python 3.8+
- `uvicorn` and dependencies (see `requirements.txt`)
- Active Retell Custom LLM agent deployment
- Assigned demo phone number

### Installation

```bash
pip install -r requirements.txt
```

### Running the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** Ensure Ngrok (or equivalent) is running and your Retell agent is configured to point to your server's public URL.

## Testing the Agent

1. **Call the demo phone number** (assigned in Retell dashboard)
2. **Describe your plumbing issue**, e.g., "water leaking under my sink"
3. **Follow the agent's guided questions** for intent, urgency, location, contact info
4. **End the call or let the agent complete intake**

The agent will deterministically guide the conversation and terminate once the FSM reaches a terminal state (SUCCESS or FAIL_CLOSED).

## How It Works

```
Inbound Call
    ↓
Retell Telephony + STT
    ↓
Custom LLM WebSocket
    ↓
FSM (Authoritative Decision Logic)
    ↓
Structured Intake Output
```

### Architecture Details

| Component | Role |
|-----------|------|
| **Retell** | Handles phone connectivity, audio streaming, speech-to-text, and text-to-speech |
| **FSM** | Owns all conversational logic, state transitions, and data validation |
| **LLM** | Acts purely as a transport layer; all output is FSM-generated |
| **Intake Object** | Structured JSON output consumed by downstream systems |

## Output Artifacts

Each completed call produces three artifacts:

### 1. Intake Object (JSON)

**Location:** `/intakes/{call_id}.json`

**Structure:**
```json
{
  "call_id": "0bee234a-74c4-45c8-b870-e5c132b9fa32",
  "terminal_state": "SUCCESS",
  "safe_to_execute": true,
  "intent": "leak",
  "urgency": "high",
  "service_city": "Minneapolis",
  "caller_phone": "9292929292",
  "caller_name": "John",
  "missing_fields": []
}
```

**If incomplete or ambiguous:**
```json
{
  "call_id": "47fbc25e-6996-4d18-a8b6-7df6e7c1b37b",
  "terminal_state": "FAIL_CLOSED",
  "safe_to_execute": false,
  "missing_fields": ["urgency", "service_city"],
  "termination_reason": "insufficient data"
}
```

### 2. Call Transcript (Text)

**Location:** `/transcripts/{call_id}.txt`

Contains:
- Turn-by-turn agent and caller messages
- Exact wording used during the call
- Timestamps and state transitions (for debugging)

### 3. Application Logs (Optional)

**Location:** `/logs/fsm.log`

Contains:
- FSM state transitions
- Call lifecycle events
- Validation results
- Error and failure-closed reasons

## Configuration

### Core Configs

- **`configs/base_agent_config.json`** — Base FSM configuration, prompts, and system parameters
- **`configs/business_config.json`** — Business rules, escalation logic, and plumbing categories
- **`configs/intake_object.json`** — Intake object schema and required fields
- **`configs/vertical_plumbing_config.json`** — Plumbing-specific intents and urgency mapping

### Environment Variables

Create a `.env` file in the root directory:

```
RETELL_API_KEY=your_api_key_here
RETELL_AGENT_ID=your_agent_id_here
LOG_LEVEL=INFO
```

## Project Structure

```
.
├── server.py              # FastAPI app, WebSocket handler
├── fsm_plumbing.py        # FSM state machine logic
├── webhook_engine.py      # Intake artifact generation
├── test_fsm.py            # FSM unit tests
├── requirements.txt       # Python dependencies
├── configs/               # Configuration files
├── intakes/               # Generated intake objects (JSON)
├── transcripts/           # Generated call transcripts (TXT)
└── logs/                  # Application logs
```

## Key Design Principles

### 1. FSM is Authoritative
All conversation decisions come from the FSM. No context inference, no LLM hallucinations.

### 2. Fail Closed
If required information is ambiguous or missing, the call terminates with `FAIL_CLOSED` status and `safe_to_execute: false`.

### 3. Structured Output
Every intake object is validated against the schema. Invalid calls never produce intake records.

### 4. No Inferred Values
Fields are only populated if explicitly confirmed by the caller. Partial or unclear data triggers safe shutdown.

## Testing & Validation

Run unit tests on the FSM:

```bash
python test_fsm.py
```

This validates:
- State transitions
- Intent classification
- Urgency detection
- Address validation
- Field completeness checks

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **WebSocket timeouts** | Increase FSM response timeout in `base_agent_config.json` |
| **"Invalid state" errors** | Check FSM configuration for missing transitions |
| **Transcripts not generated** | Verify `/transcripts/` directory exists and is writable |
| **Intake objects empty** | Check FSM validation rules in `vertical_plumbing_config.json` |
| **Phone number not ringing** | Confirm Retell agent is published and webhook URL is accessible |

## Example Call Flow

1. **Caller:** "Hi, my sink is leaking"
2. **Agent:** "Thanks for calling. Let me help with that. How urgent is this—is it actively flooding, or is it a slow leak?"
3. **Caller:** "It's pretty bad—water under the cabinet"
4. **Agent:** "Understood. What city or neighborhood are you in?"
5. **Caller:** "Minneapolis"
6. **Agent:** "Got it. I'm capturing your information now... [validates] Great! We'll dispatch a plumber. Can I confirm your name and callback number?"
7. **Caller:** "John, 929-292-9292"
8. **Agent:** "Perfect. Your intake is complete. A plumber will contact you shortly."

**Output:**
- ✅ Intake Object: `SUCCESS`, `safe_to_execute: true`
- ✅ Transcript saved
- ✅ Logs recorded

## Deployment

### Local Testing

```bash
uvicorn server:app --reload
# Server runs at http://localhost:8000
```

### Production Deployment

1. Build Docker image (if applicable):
   ```bash
   docker build -t plumbing-agent .
   docker run -p 8000:8000 plumbing-agent
   ```

2. Use Ngrok for public URL:
   ```bash
   ngrok http 8000
   ```

3. Configure Retell:
   - Set webhook URL to: `https://<your-ngrok-url>/webhook`
   - Publish the Custom LLM agent
   - Assign phone number

## Contributing

1. Update FSM logic in `fsm_plumbing.py`
2. Update configuration in `configs/`
3. Add tests to `test_fsm.py`
4. Run tests before commit
5. Document new state transitions

## License

Proprietary - Plumbing Service

## Support

For issues, feature requests, or questions:
- Review logs in `/logs/fsm.log`
- Check call transcripts in `/transcripts/`
- Validate intake schema against `configs/intake_object.json`

---

**Last Updated:** December 31, 2025
