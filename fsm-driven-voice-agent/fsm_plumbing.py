from enum import Enum
import json
import os
import uuid
from datetime import datetime

# =====================================================
# PATH SETUP
# =====================================================
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "configs")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "transcripts")
INTAKE_DIR = os.path.join(BASE_DIR, "intakes")

for d in [LOG_DIR, TRANSCRIPT_DIR, INTAKE_DIR]:
    os.makedirs(d, exist_ok=True)

# =====================================================
# CONFIG LOADING
# =====================================================
def load_config(name):
    with open(os.path.join(CONFIG_DIR, name)) as f:
        return json.load(f)

base_config = load_config("base_agent_config.json")
vertical_config = load_config("vertical_plumbing_config.json")
business_config = load_config("business_config.json")
intake_schema = load_config("intake_object.json")

# =====================================================
# SCHEMA VALIDATION
# =====================================================
def validate_intake_schema(intake, schema):
    errors = []

    for field in schema["required_fields"]:
        if field not in intake or intake[field] in [None, ""]:
            errors.append(f"Missing required field: {field}")

    if intake["terminal_state"] not in schema["termination_states"]:
        errors.append("Invalid terminal_state")

    if intake["terminal_state"] != "SUCCESS" and intake["safe_to_execute"] is True:
        errors.append("safe_to_execute cannot be true when terminal_state is not SUCCESS")

    return errors

# =====================================================
# FSM STATES
# =====================================================
class State(Enum):
    GREETING = "GREETING"
    COLLECT_PROBLEM = "COLLECT_PROBLEM"
    DETERMINE_INTENT = "DETERMINE_INTENT"
    DETERMINE_URGENCY = "DETERMINE_URGENCY"
    COLLECT_ADDRESS = "COLLECT_ADDRESS"
    COLLECT_PHONE = "COLLECT_PHONE"
    COLLECT_NAME = "COLLECT_NAME"
    CONFIRM = "CONFIRM"
    SUCCESS = "SUCCESS"
    FAIL_CLOSED = "FAIL_CLOSED"

# =====================================================
# FSM CORE
# =====================================================
class PlumbingFSM:
    def __init__(self):
        self.call_id = str(uuid.uuid4())
        self.state = State.GREETING
        self.data = {}
        self.active = True
        self.transcript = []

        self.vague_terms = base_config["failure_rules"]["fail_on_vague_language"]
        self.intent_keywords = vertical_config["supported_intents"]
        self.allowed_cities = business_config["service_cities"]
        self.required_fields = base_config["required_fields"]

        self.log_event(f"CALL STARTED | call_id={self.call_id}")

    # -----------------------------
    # LOGGING
    # -----------------------------
    def log_event(self, message):
        ts = datetime.utcnow().isoformat()
        with open(os.path.join(LOG_DIR, "fsm.log"), "a") as f:
            f.write(f"{ts} | {message}\n")

    # -----------------------------
    # TRANSCRIPT
    # -----------------------------
    def record(self, speaker, text):
        self.transcript.append(f"{speaker}: {text}")

    # -----------------------------
    # FAIL CLOSED
    # -----------------------------
    def fail_closed(self, reason):
        self.log_event(f"FAIL_CLOSED | reason={reason}")
        self.record("Agent", reason)
        self.state = State.FAIL_CLOSED
        self.active = False
        return reason

    # -----------------------------
    # FSM HANDLER
    # -----------------------------
    def handle(self, user_input: str):
        user_input = user_input.lower().strip()
        self.record("Caller", user_input)

        if user_input in self.vague_terms:
            return self.fail_closed("I don’t have enough clear information to proceed safely.")

        if self.state == State.GREETING:
            self.state = State.COLLECT_PROBLEM
            msg = "Thanks for calling. Can you briefly describe what’s going on?"
            self.record("Agent", msg)
            return msg

        if self.state == State.COLLECT_PROBLEM:
            self.data["problem_summary"] = user_input
            self.state = State.DETERMINE_INTENT
            msg = (
                "Are you calling about a leak, a clog or backup, "
                "a water heater issue, or a general repair or estimate?"
            )
            self.record("Agent", msg)
            return msg

        if self.state == State.DETERMINE_INTENT:
            detected = None
            for intent, keywords in self.intent_keywords.items():
                if any(k in user_input for k in keywords):
                    detected = intent
                    break

            if not detected:
                return self.fail_closed("I’m not able to clearly identify the issue.")

            self.data["intent"] = detected
            self.state = State.DETERMINE_URGENCY
            msg = "Is there active water leaking right now?"
            self.record("Agent", msg)
            return msg

        if self.state == State.DETERMINE_URGENCY:
            if user_input == "yes":
                self.data["urgency"] = "high"
            elif user_input == "no":
                self.data["urgency"] = "medium"
            else:
                return self.fail_closed("I need a clear yes or no to proceed.")

            self.state = State.COLLECT_ADDRESS
            msg = "May I please have your FULL street address and city? For example: 123 Main Street, Minneapolis"
            self.record("Agent", msg)
            return msg

        if self.state == State.COLLECT_ADDRESS:
            parts = user_input.split(',')
            
            # Check if we have both address and city (separated by comma)
            if len(parts) < 2:
                return "I need both the street address and city. For example: 123 Main Street, Minneapolis"
            
            address = parts[0].strip().title()
            city = parts[1].strip().title()
            
            # Validate address has enough content (street number + street name)
            address_words = address.split()
            if len(address_words) < 2:
                return "Please provide a complete street address with both number and street name. For example: 123 Main Street"
            
            if city not in self.allowed_cities:
                return self.fail_closed(f"That city is outside our service area. We serve: {', '.join(self.allowed_cities)}")
            
            self.data["address"] = address
            self.data["service_city"] = city
            self.state = State.COLLECT_PHONE
            msg = "What's the best phone number to reach you? Please include the area code."
            self.record("Agent", msg)
            return msg

        if self.state == State.COLLECT_PHONE:
            # Extract only digits
            phone_digits = user_input.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            if not phone_digits.isdigit():
                return "That doesn't seem like a valid phone number. Please provide digits only."
            
            # Check for area code (should have 10 digits, not 7)
            if len(phone_digits) == 7:
                # Store what we have so far and ask for area code
                self.data['caller_phone'] = phone_digits
                return "Thank you. What's the area code for that number?"
            elif len(phone_digits) == 10:
                # Format as XXX-XXX-XXXX
                formatted = f"{phone_digits[0:3]}-{phone_digits[3:6]}-{phone_digits[6:10]}"
                self.data['caller_phone'] = formatted
                self.state = State.COLLECT_NAME
                msg = "Perfect. And what is your name, please?"
                self.record("Agent", msg)
                return msg
            elif len(phone_digits) == 3:
                # Assume this is area code being added to previous 7 digits
                if 'caller_phone' in self.data and len(self.data['caller_phone']) == 7:
                    full_phone = f"{phone_digits}-{self.data['caller_phone']}"
                    self.data['caller_phone'] = full_phone
                    self.state = State.COLLECT_NAME
                    msg = "Perfect. And what is your name, please?"
                    self.record("Agent", msg)
                    return msg
                else:
                    return "I need the full 10-digit phone number with area code."
            else:
                return f"That phone number has {len(phone_digits)} digits. Please provide a 10-digit number with area code."
        if self.state == State.COLLECT_NAME:
            name = user_input.strip().title()
            
            # Validate that we have a real name (at least 2 characters)
            if len(name) < 2:
                return "I'm sorry, could you please provide your name?"
            
            self.data['caller_name'] = name
            self.state = State.CONFIRM
            return self._handle_confirm()
        if self.state == State.CONFIRM:
            if user_input == "yes":
                self.state = State.SUCCESS
                self.active = False
                msg = "Your request has been recorded safely."
                self.record("Agent", msg)
                self.log_event("CALL SUCCESS")
                return msg
            else:
                return self.fail_closed("Okay, I won’t proceed.")
    def _handle_confirm(self):
        """Generate confirmation message with all collected data"""
        address = self.data.get("address", "Unknown")
        city = self.data.get("service_city", "Unknown")
        phone = self.data.get("caller_phone", "Unknown")
        name = self.data.get("caller_name", "Unknown")
        
        msg = f"To confirm: {address}, {city}, {phone}, {name}. Is that correct?"
        self.record("Agent", msg)
        return msg
    # -----------------------------
    # FINALIZATION
    # -----------------------------
    def finalize(self):
        intake = {
            "call_id": self.call_id,
            "terminal_state": "SUCCESS" if self.state == State.SUCCESS else "FAIL_CLOSED",
            "safe_to_execute": self.state == State.SUCCESS,
            "intent": self.data.get("intent"),
            "urgency": self.data.get("urgency"),
            "address": self.data.get("address"),
            "service_city": self.data.get("service_city"),
            "caller_phone": self.data.get("caller_phone"),
            "caller_name": self.data.get("caller_name")
        }

        errors = validate_intake_schema(intake, intake_schema)

        if errors:
            intake["terminal_state"] = "FAIL_CLOSED"
            intake["safe_to_execute"] = False
            intake["schema_errors"] = errors
            self.log_event(f"SCHEMA VALIDATION FAILED | errors={errors}")

        with open(os.path.join(INTAKE_DIR, f"{self.call_id}.json"), "w") as f:
            json.dump(intake, f, indent=2)

        with open(os.path.join(TRANSCRIPT_DIR, f"{self.call_id}.txt"), "w") as f:
            f.write("\n".join(self.transcript))

        self.log_event(f"CALL ENDED | terminal_state={intake['terminal_state']}")
        return intake

# =====================================================
# CLI RUNNER
# =====================================================
def run():
    fsm = PlumbingFSM()
    print("\n--- Plumbing FSM (Full Production Demo) ---\n")

    print("Agent:", fsm.handle(""))

    while fsm.active:
        user_input = input("Caller: ")
        print("Agent:", fsm.handle(user_input))

    intake = fsm.finalize()
    print("\n--- FINAL INTAKE OBJECT ---")
    print(json.dumps(intake, indent=2))
    print(f"\nSaved call artifacts for call_id={fsm.call_id}")

if __name__ == "__main__":
    run()
