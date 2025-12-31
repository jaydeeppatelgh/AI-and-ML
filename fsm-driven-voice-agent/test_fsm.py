#!/usr/bin/env python3
"""
FSM TEST SCRIPT
===============
Tests the FSM locally to verify all states work correctly
and produce SUCCESS with proper data extraction.

Run: python test_fsm.py
"""

import json
from fsm_plumbing import PlumbingFSM

def test_successful_call():
    """Test a complete successful call flow"""
    print("\n" + "="*60)
    print("TEST: SUCCESSFUL CALL FLOW")
    print("="*60)
    
    fsm = PlumbingFSM()
    test_inputs = [
        ("", "GREETING - Ask about problem"),
        ("I have a water leak in my kitchen", "COLLECT_PROBLEM → DETERMINE_INTENT"),
        ("leak", "DETERMINE_INTENT → Detect intent = 'leak'"),
        ("yes", "DETERMINE_URGENCY → Set urgency = 'high'"),
        ("123 Main Street, Minneapolis", "COLLECT_ADDRESS → Parse address & city"),
        ("929-265-6565", "COLLECT_PHONE → Parse phone"),
        ("John Smith", "COLLECT_NAME → Parse name"),
        ("yes", "CONFIRM → Move to SUCCESS"),
    ]
    
    for i, (user_input, description) in enumerate(test_inputs, 1):
        print(f"\n--- Step {i}: {description} ---")
        print(f"User Input: '{user_input}'")
        
        response = fsm.handle(user_input)
        print(f"Agent Response: {response}")
        print(f"Current State: {fsm.state.value}")
        print(f"Data Collected: {fsm.data}")
        print(f"Active: {fsm.active}")
        
        if not fsm.active:
            break
    
    # Finalize and check results
    print("\n" + "-"*60)
    intake = fsm.finalize()
    
    print("\n✅ FINAL INTAKE OBJECT:")
    print(json.dumps(intake, indent=2))
    
    # Validate
    if intake["terminal_state"] == "SUCCESS" and intake["safe_to_execute"]:
        print("\n✅ SUCCESS: Call completed with all required fields!")
        return True
    else:
        print("\n❌ FAILED: Call did not complete successfully")
        if intake.get("schema_errors"):
            print("Errors:", intake["schema_errors"])
        return False


def test_vague_language():
    """Test fail_closed on vague language"""
    print("\n" + "="*60)
    print("TEST: VAGUE LANGUAGE REJECTION")
    print("="*60)
    
    fsm = PlumbingFSM()
    test_inputs = [
        ("", "GREETING"),
        ("maybe there's a leak", "Vague language 'maybe' detected"),
    ]
    
    for user_input, description in test_inputs:
        print(f"\nInput: '{user_input}' ({description})")
        response = fsm.handle(user_input)
        print(f"Response: {response}")
        print(f"State: {fsm.state.value}, Active: {fsm.active}")
    
    intake = fsm.finalize()
    if intake["terminal_state"] == "FAIL_CLOSED":
        print("\n✅ CORRECT: Rejected vague language")
        return True
    else:
        print("\n❌ FAILED: Should have rejected vague language")
        return False


def test_intent_detection():
    """Test intent detection from various keywords"""
    print("\n" + "="*60)
    print("TEST: INTENT DETECTION")
    print("="*60)
    
    test_cases = [
        ("I have a burst pipe", "leak"),
        ("My drain is backed up", "clog"),
        ("No hot water in my house", "water_heater"),
        ("I need a repair estimate", "estimate"),
    ]
    
    for problem, expected_intent in test_cases:
        fsm = PlumbingFSM()
        print(f"\nProblem: '{problem}'")
        print(f"Expected Intent: {expected_intent}")
        
        fsm.handle("")  # GREETING
        fsm.handle(problem)  # COLLECT_PROBLEM
        response = fsm.handle(problem)  # DETERMINE_INTENT
        
        actual_intent = fsm.data.get("intent")
        print(f"Detected Intent: {actual_intent}")
        
        if actual_intent == expected_intent:
            print("✅ Correct")
        else:
            print(f"❌ Failed - got '{actual_intent}' instead of '{expected_intent}'")


def test_service_city_validation():
    """Test service city validation"""
    print("\n" + "="*60)
    print("TEST: SERVICE CITY VALIDATION")
    print("="*60)
    
    fsm = PlumbingFSM()
    test_inputs = [
        ("", "GREETING"),
        ("leak in my pipe", "COLLECT_PROBLEM"),
        ("leak", "DETERMINE_INTENT"),
        ("yes", "DETERMINE_URGENCY"),
        ("123 Main Street, Denver", "Try city outside service area"),
    ]
    
    for user_input, description in test_inputs:
        print(f"\nInput: '{user_input}' ({description})")
        response = fsm.handle(user_input)
        print(f"Response: {response}")
    
    if fsm.state.value == "FAIL_CLOSED":
        print("\n✅ CORRECT: Rejected out-of-service city")
        return True
    else:
        print("\n❌ FAILED: Should reject out-of-service city")
        return False


def test_phone_parsing():
    """Test phone number parsing"""
    print("\n" + "="*60)
    print("TEST: PHONE NUMBER PARSING")
    print("="*60)
    
    test_cases = [
        ("9292656565", "XXX-XXX-XXXX", "10 digit string"),
        ("929-265-6565", "XXX-XXX-XXXX", "Already formatted"),
        ("(929) 265-6565", "XXX-XXX-XXXX", "With parentheses"),
        ("929 265 6565", "XXX-XXX-XXXX", "With spaces"),
    ]
    
    for phone_input, expected_format, description in test_cases:
        fsm = PlumbingFSM()
        
        # Get to phone collection state
        fsm.handle("")  # GREETING
        fsm.handle("leak")  # COLLECT_PROBLEM
        fsm.handle("leak")  # DETERMINE_INTENT
        fsm.handle("yes")  # DETERMINE_URGENCY
        fsm.handle("123 Main, Minneapolis")  # COLLECT_ADDRESS
        
        print(f"\nPhone Input: '{phone_input}' ({description})")
        response = fsm.handle(phone_input)
        extracted = fsm.data.get("caller_phone")
        print(f"Extracted: '{extracted}'")
        
        if extracted == "929-265-6565":
            print("✅ Correctly formatted")
        else:
            print(f"❌ Failed - got '{extracted}'")


if __name__ == "__main__":
    results = []
    
    try:
        results.append(("Successful Call", test_successful_call()))
    except Exception as e:
        print(f"\n❌ Exception in successful call test: {e}")
        results.append(("Successful Call", False))
    
    try:
        results.append(("Vague Language", test_vague_language()))
    except Exception as e:
        print(f"\n❌ Exception in vague language test: {e}")
        results.append(("Vague Language", False))
    
    try:
        test_intent_detection()
    except Exception as e:
        print(f"\n❌ Exception in intent detection: {e}")
    
    try:
        results.append(("Service City Validation", test_service_city_validation()))
    except Exception as e:
        print(f"\n❌ Exception in city validation: {e}")
        results.append(("Service City Validation", False))
    
    try:
        test_phone_parsing()
    except Exception as e:
        print(f"\n❌ Exception in phone parsing: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
