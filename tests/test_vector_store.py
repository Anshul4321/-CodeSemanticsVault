"""
Tests for Vector Store
"""

import pytest
import numpy as np
import shutil
from pathlib import Path
from src.core.vector_store import VectorStore


# Use single store instance for all tests
@pytest.fixture(scope="session")
def store():
    """Create a single vector store for all tests"""
    test_path = "data/test_chromadb_session"
    
    # Clean before
    if Path(test_path).exists():
        shutil.rmtree(test_path)
    
    store = VectorStore(persist_dir=test_path)
    yield store
    
    # Clean after
    if Path(test_path).exists():
        shutil.rmtree(test_path)


def test_01_initialization(store):
    """Test store initializes"""
    assert store.persist_dir.exists()
    assert store.client is not None


def test_02_create_collection(store):
    """Test creating a collection"""
    store.create_collection("test_collection")
    assert store.collection is not None
    assert store.collection.name == "test_collection"


def test_03_add_embeddings(store):
    """Test adding embeddings"""
    chunks = [
        {
            "filename": "test.py",
            "content": "def foo(): pass",
            "start_line": 1,
            "end_line": 2,
            "context": "foo",
            "embedding": np.random.rand(384)
        },
        {
            "filename": "test.py",
            "content": "def bar(): pass",
            "start_line": 3,
            "end_line": 4,
            "context": "bar",
            "embedding": np.random.rand(384)
        }
    ]
    
    store.add_embeddings(chunks, "test_collection")
    size = store.get_collection_size("test_collection")
    assert size == 2


def test_04_search(store):
    """Test searching embeddings"""
    # Create specific embeddings for testing
    chunks = [
        {
            "filename": "auth.py",
            "content": "def authenticate(): pass",
            "start_line": 1,
            "end_line": 2,
            "context": "authenticate",
            "embedding": np.array([1.0, 0.0] + [0.0] * 382)
        },
        {
            "filename": "payment.py",
            "content": "def process_payment(): pass",
            "start_line": 10,
            "end_line": 11,
            "context": "process_payment",
            "embedding": np.array([0.0, 1.0] + [0.0] * 382)
        }
    ]
    
    store.create_collection("test_search")
    store.add_embeddings(chunks, "test_search")
    
    # Search
    query = np.array([1.0, 0.0] + [0.0] * 382)
    results = store.search(query, top_k=2, collection_name="test_search")
    
    assert len(results) > 0
    assert "similarity" in results[0]
    assert results[0]["similarity"] >= 0


def test_05_list_collections(store):
    """Test listing collections"""
    collections = store.list_collections()
    assert isinstance(collections, list)
    assert len(collections) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])