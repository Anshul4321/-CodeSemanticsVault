"""
Embedder
Converts text chunks into semantic embeddings using sentence-transformers
"""

import logging
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """
    Generate semantic embeddings for text chunks using pre-trained models.
    Uses sentence-transformers for efficient, local embedding generation.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedder with pre-trained model
        
        Args:
            model_name: HuggingFace model identifier
                       all-MiniLM-L6-v2 (384-dim, fast, good for code)
                       all-mpnet-base-v2 (768-dim, slower, more accurate)
        """
        self.model_name = model_name
        
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
        
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embedding(s) for text
        
        Args:
            text: Single string or list of strings
            
        Returns:
            Single embedding array or list of arrays
        """
        if isinstance(text, str):
            # Single text
            try:
                embedding = self.model.encode(text, convert_to_numpy=True)
                return embedding
            except Exception as e:
                logger.error(f"Failed to embed text: {e}")
                raise
        
        elif isinstance(text, list):
            # Multiple texts - batch embed for efficiency
            try:
                embeddings = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    batch_size=32,  # Process 32 at a time
                    show_progress_bar=False
                )
                return embeddings
            except Exception as e:
                logger.error(f"Failed to embed batch: {e}")
                raise
        
        else:
            raise TypeError(f"Expected str or list, got {type(text)}")
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Generate embeddings for a list of chunks
        
        Args:
            chunks: List of chunk dicts with "content" key
            
        Returns:
            Same chunks with added "embedding" key
        """
        logger.info(f"Embedding {len(chunks)} chunks...")
        
        # Extract contents
        contents = [chunk["content"] for chunk in chunks]
        
        # Batch embed
        embeddings = self.model.encode(
            contents,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=True
        )
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        logger.info(f"✅ Embedded {len(chunks)} chunks")
        return chunks
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        # Normalize vectors
        e1 = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        e2 = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
        
        # Cosine similarity
        similarity = float(np.dot(e1, e2))
        
        # Clamp to [0, 1] to handle floating-point precision issues
        return max(0.0, min(1.0, similarity))
    
    def get_info(self) -> dict:
        """Get embedder information"""
        return {
            "model": self.model_name,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize embedder
    embedder = Embedder("all-MiniLM-L6-v2")
    print(f"\n📊 Embedder Info: {embedder.get_info()}\n")
    
    # Test single embedding
    text1 = "def process_payment(amount): return validate(amount)"
    embedding1 = embedder.embed(text1)
    print(f"✅ Single embedding shape: {embedding1.shape}")
    
    # Test batch embedding
    texts = [
        "def process_payment(amount): return validate(amount)",
        "class PaymentHandler: def __init__(self): pass",
        "def validate_card(card): return check(card)"
    ]
    embeddings = embedder.embed(texts)
    print(f"✅ Batch embeddings shape: {embeddings.shape}")
    
    # Test similarity
    sim = embedder.similarity(embeddings[0], embeddings[1])
    print(f"✅ Similarity between text 1 & 2: {sim:.3f}")
    
    sim = embedder.similarity(embeddings[0], embeddings[2])
    print(f"✅ Similarity between text 1 & 3: {sim:.3f}")
    
    # Test chunk embedding
    sample_chunks = [
        {"content": "def foo(): pass", "filename": "a.py"},
        {"content": "def bar(): pass", "filename": "b.py"}
    ]
    chunks_with_emb = embedder.embed_chunks(sample_chunks)
    print(f"\n✅ Chunks with embeddings:")
    for chunk in chunks_with_emb:
        print(f"  {chunk['filename']}: embedding shape {chunk['embedding'].shape}")