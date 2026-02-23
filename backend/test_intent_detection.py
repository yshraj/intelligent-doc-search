"""Quick test script for intent detection."""
import sys
sys.path.insert(0, '.')

from app.intent_detection import detect_intent, get_document_scope

# Test cases
test_cases = [
    # (query, doc_scope, expected_intent)
    ("Create a comprehensive summary", "multi", "comprehensive"),
    ("Summarize this document", "single", "summarize_single"),
    ("Summarize all documents", "multi", "summarize_multi"),
    ("Compare these documents", "multi", "compare"),
    ("What is the main topic?", "single", "qa_single"),
    ("What are the key differences?", "multi", "compare"),  # "differences" triggers compare
    ("Extract all dates", "multi", "extract"),
    ("Analyze the trends", "multi", "analysis"),
    ("Give me a detailed overview", "multi", "comprehensive"),
    ("List all employees", "single", "extract"),
]

print("Testing Intent Detection\n" + "="*50)

passed = 0
failed = 0

for query, scope, expected in test_cases:
    detected = detect_intent(query, scope)
    status = "✓" if detected == expected else "✗"
    
    if detected == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} Query: '{query}'")
    print(f"  Scope: {scope} | Expected: {expected} | Got: {detected}")
    if detected != expected:
        print(f"  ⚠️  MISMATCH!")
    print()

print("="*50)
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("✅ All tests passed!")
    sys.exit(0)
else:
    print("❌ Some tests failed")
    sys.exit(1)
