"""Test pattern matching functionality."""
import pytest
from app.document_grouper import document_grouper


class TestPatternMatching:
    """Test document type and topic detection using pattern matching."""
    
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
    
    def test_meeting_notes_detection(self):
        """Test meeting notes detection."""
        content = """
        TEAM MEETING MINUTES
        Date: March 15, 2024
        
        ATTENDEES:
        - John Smith (Engineering)
        - Jane Doe (Product)
        
        AGENDA:
        1. Project status update
        2. Q2 roadmap planning
        
        DISCUSSION:
        The team discussed the current sprint progress.
        
        ACTION ITEMS:
        - John: Complete API integration by March 20
        - Jane: Finalize product requirements by March 18
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Team_Meeting_2024-03-15.txt",
            mime_type="text/plain",
        )
        
        # Check for meeting_notes type
        type_tags = [t for t in result['tags'] if t['category'] == 'type']
        assert any(t['name'] == 'meeting_notes' for t in type_tags), "Meeting notes type not detected"
    
    def test_confidential_detection(self):
        """Test confidential document detection."""
        content = """
        CONFIDENTIAL - INTERNAL USE ONLY
        
        Company Strategy Document
        
        This document contains proprietary information and should not be
        distributed outside the organization.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Strategy_2024_CONFIDENTIAL.pdf",
            mime_type="application/pdf",
        )
        
        # Check for confidential sensitivity
        sensitivity_tags = [t for t in result['tags'] if t['category'] == 'sensitivity']
        assert any(t['name'] == 'confidential' for t in sensitivity_tags), "Confidential not detected"
    
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
