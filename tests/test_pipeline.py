"""
Tests for RAG Pipeline
"""

import pytest


def test_pipeline_can_import():
    """Test that all components can be imported"""
    from src.core.repo_parser import RepositoryParser
    from src.core.semantic_chunker import SemanticChunker
    from src.core.embedder import Embedder
    from src.core.vector_store import VectorStore
    from src.core.retriever import Retriever
    from src.core.synthesizer import Synthesizer
    
    assert RepositoryParser is not None
    assert SemanticChunker is not None
    assert Embedder is not None
    assert VectorStore is not None
    assert Retriever is not None
    assert Synthesizer is not None


def test_individual_components():
    """Test each component initializes"""
    from src.core.semantic_chunker import SemanticChunker
    from src.core.embedder import Embedder
    from src.core.vector_store import VectorStore
    from src.core.retriever import Retriever
    
    chunker = SemanticChunker()
    assert chunker.chunk_size == 512
    
    embedder = Embedder()
    assert embedder.dimension == 384
    
    vector_store = VectorStore()
    assert vector_store.client is not None
    
    retriever = Retriever()
    assert retriever.embedder is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])