"""
Tests for Embedder
"""

import pytest
import numpy as np
from src.core.embedder import Embedder


def test_embedder_initialization():
    """Test embedder initializes with correct model"""
    embedder = Embedder("all-MiniLM-L6-v2")
    assert embedder.dimension == 384
    assert embedder.model_name == "all-MiniLM-L6-v2"


def test_embed_single_string():
    """Test embedding a single string"""
    embedder = Embedder()
    text = "def process_payment(amount): return validate(amount)"
    embedding = embedder.embed(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)


def test_embed_list():
    """Test embedding a list of strings"""
    embedder = Embedder()
    texts = [
        "def foo(): pass",
        "def bar(): pass",
        "class MyClass: pass"
    ]
    embeddings = embedder.embed(texts)
    
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 384)


def test_similarity():
    """Test cosine similarity calculation"""
    embedder = Embedder()
    
    # Very similar texts should have high similarity
    text1 = "def process_payment"
    text2 = "def process_payment"
    
    emb1 = embedder.embed(text1)
    emb2 = embedder.embed(text2)
    
    sim = embedder.similarity(emb1, emb2)
    assert 0.9 < sim <= 1.0  # Near identical
    
    # Very different texts should have low similarity
    text3 = "completely different random text"
    emb3 = embedder.embed(text3)
    
    sim2 = embedder.similarity(emb1, emb3)
    assert sim2 < 0.5


def test_embed_chunks():
    """Test embedding a list of chunks"""
    embedder = Embedder()
    
    chunks = [
        {"content": "def foo(): pass", "filename": "a.py"},
        {"content": "def bar(): pass", "filename": "b.py"},
        {"content": "def baz(): pass", "filename": "c.py"}
    ]
    
    result = embedder.embed_chunks(chunks)
    
    assert len(result) == 3
    assert all("embedding" in chunk for chunk in result)
    assert all(chunk["embedding"].shape == (384,) for chunk in result)


def test_embedder_info():
    """Test getting embedder info"""
    embedder = Embedder()
    info = embedder.get_info()
    
    assert "model" in info
    assert "dimension" in info
    assert info["dimension"] == 384


if __name__ == "__main__":
    pytest.main([__file__, "-v"])