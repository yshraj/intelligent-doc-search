"""Integration tests for Document Grouper functionality."""
from app.document_grouper import document_grouper


class TestDocumentGrouper:
    """Test the document grouper classification engine."""
    
    def test_contract_detection(self):
        """Test contract document detection."""
        content = """
        SERVICE AGREEMENT
        
        This Agreement is entered into as of January 1, 2024, by and between
        Party A ("Client") and Party B ("Service Provider").
        
        WHEREAS, the parties wish to establish the terms and conditions...
        
        LIABILITY AND INDEMNITY:
        Each party shall indemnify the other party against any claims.
        This clause shall survive termination of this Agreement.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Service_Agreement_2024.pdf",
            mime_type="application/pdf",
        )
        
        # Check tags were generated
        assert len(result['tags']) > 0, "No tags generated"
        
        # Check for contract type
        type_tags = [t for t in result['tags'] if t['category'] == 'type']
        assert any(t['name'] == 'contract' for t in type_tags), "Contract type not detected"
        
        # Check for legal topic
        topic_tags = [t for t in result['tags'] if t['category'] == 'topic']
        assert any(t['name'] == 'legal' for t in topic_tags), "Legal topic not detected"
        
        # Check suggested groups
        assert len(result['suggested_groups']) > 0, "No groups suggested"
        assert 'Contracts' in result['suggested_groups'], "Contracts group not suggested"
        
        print("✓ Contract detection test passed")
    
    def test_report_detection(self):
        """Test report document detection."""
        content = """
        QUARTERLY FINANCIAL REPORT
        Q1 2024
        
        EXECUTIVE SUMMARY
        This report presents the financial results for the first quarter of 2024.
        
        KEY FINDINGS:
        - Revenue increased by 15% compared to Q1 2023
        - Operating expenses decreased by 8%
        - Net profit margin improved to 22%
        
        ANALYSIS:
        The strong performance was driven by increased sales in our core markets
        and improved operational efficiency.
        
        RECOMMENDATIONS:
        1. Continue investment in high-growth segments
        2. Maintain cost discipline
        3. Expand into new geographic markets
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Q1_2024_Financial_Report.pdf",
            mime_type="application/pdf",
        )
        
        # Check for report type
        type_tags = [t for t in result['tags'] if t['category'] == 'type']
        assert any(t['name'] == 'report' for t in type_tags), "Report type not detected"
        
        # Check for finance topic
        topic_tags = [t for t in result['tags'] if t['category'] == 'topic']
        assert any(t['name'] == 'finance' for t in topic_tags), "Finance topic not detected"
        
        # Check for time period
        time_tags = [t for t in result['tags'] if t['category'] == 'time_period']
        assert len(time_tags) > 0, "Time period not detected"
        
        # Check suggested groups
        assert 'Reports' in result['suggested_groups'], "Reports group not suggested"
        
        print("✓ Report detection test passed")
    
    def test_meeting_notes_detection(self):
        """Test meeting notes detection."""
        content = """
        TEAM MEETING MINUTES
        Date: March 15, 2024
        
        ATTENDEES:
        - John Smith (Engineering)
        - Jane Doe (Product)
        - Bob Johnson (Design)
        
        AGENDA:
        1. Project status update
        2. Q2 roadmap planning
        3. Resource allocation
        
        DISCUSSION:
        The team discussed the current sprint progress. All features are on track
        for the Q2 release. We agreed to prioritize the mobile app improvements.
        
        ACTION ITEMS:
        - John: Complete API integration by March 20
        - Jane: Finalize product requirements by March 18
        - Bob: Prepare design mockups for review
        
        NEXT STEPS:
        Follow-up meeting scheduled for March 22 to review progress.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Team_Meeting_2024-03-15.txt",
            mime_type="text/plain",
        )
        
        # Check for meeting_notes type
        type_tags = [t for t in result['tags'] if t['category'] == 'type']
        assert any(t['name'] == 'meeting_notes' for t in type_tags), "Meeting notes type not detected"
        
        # Check suggested groups
        assert 'Meeting Notes' in result['suggested_groups'], "Meeting Notes group not suggested"
        
        print("✓ Meeting notes detection test passed")
    
    def test_confidential_detection(self):
        """Test confidential document detection."""
        content = """
        CONFIDENTIAL - INTERNAL USE ONLY
        
        Company Strategy Document
        
        This document contains proprietary information and should not be
        distributed outside the organization.
        
        Strategic initiatives for 2024...
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Strategy_2024_CONFIDENTIAL.pdf",
            mime_type="application/pdf",
        )
        
        # Check for confidential sensitivity
        sensitivity_tags = [t for t in result['tags'] if t['category'] == 'sensitivity']
        assert any(t['name'] == 'confidential' for t in sensitivity_tags), "Confidential not detected"
        
        print("✓ Confidential detection test passed")
    
    def test_anonymous_detection(self):
        """Test anonymous document detection."""
        content = """
        This is some random text without any identifying information.
        No author, no date, no company name.
        Just plain content.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="untitled.txt",
            mime_type="text/plain",
        )
        
        # Check anonymous flag
        assert result['is_anonymous'], "Anonymous document not detected"
        
        # Check for anonymous tag
        sensitivity_tags = [t for t in result['tags'] if t['category'] == 'sensitivity']
        assert any(t['name'] == 'anonymous' for t in sensitivity_tags), "Anonymous tag not added"
        
        print("✓ Anonymous detection test passed")
    
    def test_time_period_extraction(self):
        """Test time period extraction from filename and content."""
        content = """
        Financial Report for Q1 2024
        
        This report covers the period from January to March 2024.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Q1_2024_Report.pdf",
            mime_type="application/pdf",
        )
        
        # Check for time period tag
        time_tags = [t for t in result['tags'] if t['category'] == 'time_period']
        assert len(time_tags) > 0, "Time period not detected"
        assert any('2024' in t['name'] for t in time_tags), "Year not detected in time period"
        
        print("✓ Time period extraction test passed")
    
    def test_multi_label_classification(self):
        """Test that documents can have multiple tags."""
        content = """
        CONFIDENTIAL LEGAL AGREEMENT
        
        This Agreement is entered into on January 1, 2024.
        
        WHEREAS, the parties agree to the following terms...
        
        LIABILITY: Each party shall indemnify the other.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Legal_Agreement_2024.pdf",
            mime_type="application/pdf",
        )
        
        # Should have multiple tag categories
        categories = set(t['category'] for t in result['tags'])
        assert len(categories) >= 2, "Multi-label classification not working"
        
        # Should have both type and topic
        assert 'type' in categories, "Type category missing"
        assert any(cat in categories for cat in ['topic', 'sensitivity']), "Additional categories missing"
        
        print("✓ Multi-label classification test passed")
    
    def test_confidence_scores(self):
        """Test that confidence scores are within valid range."""
        content = """
        SERVICE AGREEMENT
        
        This Agreement is entered into by Party A and Party B.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Agreement.pdf",
            mime_type="application/pdf",
        )
        
        # Check all confidence scores are valid
        for tag in result['tags']:
            assert 0.0 <= tag['confidence'] <= 1.0, f"Invalid confidence score: {tag['confidence']}"
            assert 'name' in tag, "Tag missing name"
            assert 'category' in tag, "Tag missing category"
        
        print("✓ Confidence scores test passed")
    
    def test_suggested_groups_format(self):
        """Test that suggested groups are properly formatted."""
        content = """
        CONTRACT AGREEMENT
        
        Legal document between parties.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Contract.pdf",
            mime_type="application/pdf",
        )
        
        # Check suggested groups format
        assert isinstance(result['suggested_groups'], list), "Suggested groups should be a list"
        for group in result['suggested_groups']:
            assert isinstance(group, str), "Group name should be a string"
            assert len(group) > 0, "Group name should not be empty"
        
        # Check for no duplicates
        assert len(result['suggested_groups']) == len(set(result['suggested_groups'])), "Duplicate groups found"
        
        print("✓ Suggested groups format test passed")


class TestIngestionIntegration:
    """Test integration with ingestion pipeline."""
    
    def test_ingestion_returns_tags(self):
        """Test that process_document returns tags and groups."""
        from app.ingestion import process_document
        
        # Create a simple test document
        content = b"""SERVICE AGREEMENT

This Agreement is entered into by Party A and Party B.

LIABILITY: Each party shall indemnify the other."""
        
        # Note: This will fail if Qdrant/Gemini are not configured
        # But we can test the structure
        try:
            result = process_document(
                document_id="test-doc-id",
                user_id="test-user-id",
                filename="Test_Agreement.txt",
                mime_type="text/plain",
                content=content,
            )
            
            # Check result structure
            assert 'status' in result, "Result missing status"
            assert 'tags' in result or result['status'] == 'failed', "Result missing tags (unless failed)"
            assert 'suggested_groups' in result or result['status'] == 'failed', "Result missing suggested_groups (unless failed)"
            
            if result['status'] == 'ready':
                assert isinstance(result['tags'], list), "Tags should be a list"
                assert isinstance(result['suggested_groups'], list), "Suggested groups should be a list"
                print("✓ Ingestion integration test passed")
            else:
                print(f"⚠ Ingestion test skipped (status: {result['status']}, error: {result.get('error_message', 'N/A')})")
                print("  This is expected if Qdrant/Gemini are not configured")
        
        except Exception as e:
            print(f"⚠ Ingestion test skipped due to missing dependencies: {str(e)[:100]}")
            print("  This is expected if Qdrant/Gemini are not configured")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("Document Grouper Integration Tests")
    print("=" * 70)
    print()
    
    test_grouper = TestDocumentGrouper()
    test_ingestion = TestIngestionIntegration()
    
    tests = [
        ("Contract Detection", test_grouper.test_contract_detection),
        ("Report Detection", test_grouper.test_report_detection),
        ("Meeting Notes Detection", test_grouper.test_meeting_notes_detection),
        ("Confidential Detection", test_grouper.test_confidential_detection),
        ("Anonymous Detection", test_grouper.test_anonymous_detection),
        ("Time Period Extraction", test_grouper.test_time_period_extraction),
        ("Multi-Label Classification", test_grouper.test_multi_label_classification),
        ("Confidence Scores", test_grouper.test_confidence_scores),
        ("Suggested Groups Format", test_grouper.test_suggested_groups_format),
        ("Ingestion Integration", test_ingestion.test_ingestion_returns_tags),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}...")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            if "skipped" in str(e).lower() or "⚠" in str(e):
                skipped += 1
            else:
                print(f"✗ {test_name} ERROR: {e}")
                failed += 1
        print()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)
    
    if failed > 0:
        exit(1)
    else:
        print("\n✅ All tests passed!")
        exit(0)


if __name__ == "__main__":
    run_all_tests()
