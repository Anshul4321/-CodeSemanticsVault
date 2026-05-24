"""
Tests for Retriever
"""

import pytest
import numpy as np
import shutil
from pathlib import Path
from src.core.retriever import Retriever
from src.core.embedder import Embedder
from src.core.vector_store import VectorStore


@pytest.fixture(scope="session")
def retriever_setup():
    """Setup retriever with sample data"""
    test_dir = "data/test_retriever"
    if Path(test_dir).exists():
        shutil.rmtree(test_dir)
    
    embedder = Embedder()
    vector_store = VectorStore(persist_dir=test_dir)
    retriever = Retriever(embedder=embedder, vector_store=vector_store)
    
    # Create collection and add samples
    vector_store.create_collection("test")
    
    chunks = [
        {
            "filename": "auth.py",
            "content": "def authenticate(user): return validate(user)",
            "start_line": 1,
            "end_line": 2,
            "context": "authenticate",
            "embedding": np.random.rand(384)
        },
        {
            "filename": "payment.py",
            "content": "def process_payment(amount): return charge(amount)",
            "start_line": 10,
            "end_line": 11,
            "context": "process_payment",
            "embedding": np.random.rand(384)
        }
    ]
    
    vector_store.add_embeddings(chunks, "test")
    
    yield retriever


def test_retriever_initialization(retriever_setup):
    """Test retriever initializes"""
    assert retriever_setup.embedder is not None
    assert retriever_setup.vector_store is not None


def test_retrieve(retriever_setup):
    """Test basic retrieval"""
    results = retriever_setup.retrieve(
        query="authentication",
        collection_name="test",
        top_k=2
    )
    
    assert isinstance(results, list)


def test_retrieve_batch(retriever_setup):
    """Test batch retrieval"""
    queries = ["authentication", "payment processing"]
    results = retriever_setup.retrieve_batch(
        queries=queries,
        collection_name="test",
        top_k=1
    )
    
    assert len(results) == 2


def test_get_retrieval_stats(retriever_setup):
    """Test retrieval statistics"""
    results = retriever_setup.retrieve(
        query="test query",
        collection_name="test"
    )
    
    stats = retriever_setup.get_retrieval_stats(results)
    
    assert "count" in stats
    assert "avg_similarity" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])