"""Test classification functionality."""
import pytest
from app.document_grouper import document_grouper


class TestClassification:
    """Test multi-label classification and tag generation."""
    
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
    
    def test_tag_structure(self):
        """Test that tags have correct structure."""
        content = """
        QUARTERLY REPORT
        
        Financial analysis for Q1 2024.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Q1_Report.pdf",
            mime_type="application/pdf",
        )
        
        # Check each tag has required fields
        for tag in result['tags']:
            assert 'name' in tag, "Tag missing 'name' field"
            assert 'category' in tag, "Tag missing 'category' field"
            assert 'confidence' in tag, "Tag missing 'confidence' field"
            
            # Check category is valid
            valid_categories = ['type', 'topic', 'department', 'sensitivity', 'time_period', 'status', 'custom']
            assert tag['category'] in valid_categories, f"Invalid category: {tag['category']}"
    
    def test_no_duplicate_tags(self):
        """Test that no duplicate tags are generated."""
        content = """
        CONTRACT CONTRACT AGREEMENT AGREEMENT
        
        This is a legal legal contract contract.
        """
        
        result = document_grouper.analyze_document(
            content=content,
            filename="Contract.pdf",
            mime_type="application/pdf",
        )
        
        # Check for duplicate tags
        tag_keys = [(t['name'], t['category']) for t in result['tags']]
        assert len(tag_keys) == len(set(tag_keys)), "Duplicate tags found"
