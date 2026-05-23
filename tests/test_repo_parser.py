"""
Tests for Repository Parser
"""

import pytest
from pathlib import Path
from src.core.repo_parser import RepositoryParser


def test_repo_parser_initialization():
    """Test parser initializes correctly"""
    parser = RepositoryParser()
    assert parser.cache_dir.exists()
    assert len(parser.SUPPORTED_EXTENSIONS) > 0


def test_invalid_url():
    """Test parser rejects invalid URLs"""
    parser = RepositoryParser()
    
    with pytest.raises(ValueError):
        parser.clone_repo("https://invalid-url.com/repo")


def test_supported_extensions():
    """Test that supported extensions are correct"""
    parser = RepositoryParser()
    
    assert ".py" in parser.SUPPORTED_EXTENSIONS
    assert ".md" in parser.SUPPORTED_EXTENSIONS
    assert ".exe" not in parser.SUPPORTED_EXTENSIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])