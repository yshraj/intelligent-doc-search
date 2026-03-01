"""Simple standalone test for document grouper pattern matching."""
import re


# Simplified version of pattern matching logic
TYPE_PATTERNS = {
    "contract": [
        r"\b(agreement|contract|terms and conditions|service agreement)\b",
        r"\b(party|parties|whereas|hereby)\b",
        r"\b(effective date|termination|renewal)\b",
    ],
    "report": [
        r"\b(executive summary|findings|recommendations|conclusion)\b",
        r"\b(analysis|results|data|metrics)\b",
        r"\b(quarterly|annual|monthly) report\b",
    ],
    "meeting_notes": [
        r"\b(meeting|minutes|attendees|agenda)\b",
        r"\b(action items|next steps|follow.?up)\b",
        r"\b(discussed|decided|agreed)\b",
    ],
}

TOPIC_PATTERNS = {
    "legal": [
        r"\b(legal|law|attorney|counsel|litigation)\b",
        r"\b(clause|liability|indemnity|jurisdiction)\b",
    ],
    "finance": [
        r"\b(financial|budget|revenue|expense|profit)\b",
        r"\b(accounting|fiscal|investment|cost)\b",
    ],
}


def detect_type(content: str) -> str | None:
    """Detect document type."""
    content_lower = content.lower()
    scores = {}
    
    for doc_type, patterns in TYPE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
            score += matches
        if score > 0:
            scores[doc_type] = score
    
    if not scores:
        return None
    
    return max(scores, key=scores.get)


def detect_topics(content: str) -> list[str]:
    """Detect topics."""
    content_lower = content.lower()
    topics = []
    
    for topic, patterns in TOPIC_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
            score += matches
        if score > 0:
            topics.append(topic)
    
    return topics


def test_contract():
    """Test contract detection."""
    content = """
    SERVICE AGREEMENT
    
    This Agreement is entered into as of January 1, 2024, by and between
    Party A ("Client") and Party B ("Service Provider").
    
    WHEREAS, the parties wish to establish the terms and conditions...
    
    LIABILITY AND INDEMNITY:
    Each party shall indemnify the other party against any claims.
    This clause shall survive termination of this Agreement.
    """
    
    doc_type = detect_type(content)
    topics = detect_topics(content)
    
    print("Contract Test:")
    print(f"  Type: {doc_type}")
    print(f"  Topics: {topics}")
    
    assert doc_type == "contract", f"Expected 'contract', got '{doc_type}'"
    assert "legal" in topics, f"Expected 'legal' in topics, got {topics}"
    print("  ✓ Passed")


def test_report():
    """Test report detection."""
    content = """
    QUARTERLY FINANCIAL REPORT
    
    EXECUTIVE SUMMARY
    This report presents the financial results for Q1 2024.
    
    KEY FINDINGS:
    - Revenue increased by 15%
    - Operating expenses decreased by 8%
    
    ANALYSIS:
    The strong performance was driven by increased sales.
    
    RECOMMENDATIONS:
    Continue investment in high-growth segments.
    """
    
    doc_type = detect_type(content)
    topics = detect_topics(content)
    
    print("\nReport Test:")
    print(f"  Type: {doc_type}")
    print(f"  Topics: {topics}")
    
    assert doc_type == "report", f"Expected 'report', got '{doc_type}'"
    assert "finance" in topics, f"Expected 'finance' in topics, got {topics}"
    print("  ✓ Passed")


def test_meeting_notes():
    """Test meeting notes detection."""
    content = """
    TEAM MEETING MINUTES
    
    ATTENDEES:
    - John Smith
    - Jane Doe
    
    AGENDA:
    1. Project status update
    2. Q2 roadmap planning
    
    DISCUSSION:
    The team discussed the current sprint progress.
    
    ACTION ITEMS:
    - John: Complete API integration
    - Jane: Finalize requirements
    
    NEXT STEPS:
    Follow-up meeting scheduled for next week.
    """
    
    doc_type = detect_type(content)
    
    print("\nMeeting Notes Test:")
    print(f"  Type: {doc_type}")
    
    assert doc_type == "meeting_notes", f"Expected 'meeting_notes', got '{doc_type}'"
    print("  ✓ Passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Document Grouper Pattern Matching Tests")
    print("=" * 60)
    
    try:
        test_contract()
        test_report()
        test_meeting_notes()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
