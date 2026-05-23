"""
Tests for Synthesizer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.synthesizer import Synthesizer


@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    with patch('src.core.synthesizer.OpenAI') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def synthesizer(mock_openai):
    """Create synthesizer with mocked OpenAI"""
    return Synthesizer(api_key="test-key")


@pytest.fixture
def sample_chunks():
    """Sample retrieved chunks"""
    return [
        {
            "filename": "auth.py",
            "start_line": 10,
            "end_line": 15,
            "content": "def authenticate(user): return validate(user)",
            "similarity": 0.9,
            "context": "authenticate"
        },
        {
            "filename": "user.py",
            "start_line": 20,
            "end_line": 25,
            "content": "class User: def __init__(self, name): self.name = name",
            "similarity": 0.85,
            "context": "User"
        }
    ]


def test_synthesizer_initialization(synthesizer):
    """Test synthesizer initializes"""
    assert synthesizer.client is not None
    assert synthesizer.model == "gpt-4"
    assert synthesizer.temperature == 0.3


def test_build_context_string(synthesizer, sample_chunks):
    """Test context building"""
    context = synthesizer._build_context_string(sample_chunks)
    
    assert "auth.py" in context
    assert "user.py" in context
    assert "authenticate" in context
    assert len(context) > 0


def test_build_context_empty(synthesizer):
    """Test context with no chunks"""
    context = synthesizer._build_context_string([])
    assert "No relevant code found" in context


def test_confidence_calculation(synthesizer, sample_chunks):
    """Test confidence score calculation"""
    answer = "The authentication is in auth.py and user data in user.py"
    
    confidence = synthesizer._calculate_confidence(sample_chunks, answer)
    
    assert 0 <= confidence <= 1
    assert confidence > 0


def test_extract_citations(synthesizer, sample_chunks):
    """Test citation extraction"""
    answer = "Authentication is handled in auth.py:10. User class is in user.py:20."
    
    citations = synthesizer._extract_citations(sample_chunks, answer)
    
    assert len(citations) > 0


def test_build_prompt(synthesizer):
    """Test prompt building"""
    query = "How does auth work?"
    context = "def authenticate(): pass"
    
    prompt = synthesizer._build_prompt(query, context, include_confidence=True)
    
    assert query in prompt
    assert context in prompt
    assert "confidence" in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])