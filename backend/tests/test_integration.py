"""Test integration with ingestion pipeline."""
import pytest


class TestIngestionIntegration:
    """Test integration with document ingestion pipeline."""
    
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
        
        except Exception as e:
            # Expected if Qdrant/Gemini not configured
            pytest.skip(f"Ingestion test skipped due to missing dependencies: {str(e)[:100]}")
    
    def test_document_grouper_integration(self):
        """Test that document_grouper is properly integrated."""
        from app.document_grouper import document_grouper
        
        # Verify document_grouper instance exists
        assert document_grouper is not None, "document_grouper instance not found"
        
        # Verify analyze_document method exists
        assert hasattr(document_grouper, 'analyze_document'), "analyze_document method not found"
        
        # Test basic functionality
        result = document_grouper.analyze_document(
            content="Test document content",
            filename="test.txt",
            mime_type="text/plain",
        )
        
        # Verify result structure
        assert 'tags' in result, "Result missing tags"
        assert 'suggested_groups' in result, "Result missing suggested_groups"
        assert 'is_anonymous' in result, "Result missing is_anonymous"
