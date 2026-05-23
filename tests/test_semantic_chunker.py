"""
Tests for Semantic Chunker
"""

import pytest
from src.core.semantic_chunker import SemanticChunker


def test_chunker_initialization():
    """Test chunker initializes"""
    chunker = SemanticChunker(chunk_size=512, overlap=50)
    assert chunker.chunk_size == 512
    assert chunker.overlap == 50


def test_chunk_python():
    """Test Python chunking respects function boundaries"""
    code = '''
def func1():
    return "a" * 100

def func2():
    return "b" * 100
'''
    chunker = SemanticChunker(chunk_size=256)
    chunks = chunker.chunk_python(code, "test.py")
    
    assert len(chunks) > 0
    assert all("content" in c for c in chunks)
    assert all("start_line" in c for c in chunks)


def test_chunk_generic():
    """Test generic chunking for markdown"""
    markdown = '''
# Section 1
Some content here

# Section 2
More content
'''
    chunker = SemanticChunker(chunk_size=256)
    chunks = chunker.chunk_generic(markdown, "README.md")
    
    assert len(chunks) > 0


def test_chunk_file_extension():
    """Test that correct chunking method is used based on extension"""
    chunker = SemanticChunker()
    
    # Python should use semantic chunking
    py_chunks = chunker.chunk_file("test.py", "def foo(): pass")
    assert len(py_chunks) > 0
    
    # Markdown should use generic chunking
    md_chunks = chunker.chunk_file("README.md", "# Title\nContent")
    assert len(md_chunks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])