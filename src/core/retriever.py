"""
Retriever
Semantic search over indexed code using embeddings and vector store
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from src.core.embedder import Embedder
from src.core.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant code chunks based on semantic similarity.
    Combines embedder and vector store for end-to-end retrieval.
    """
    
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        vector_store: Optional[VectorStore] = None,
        model_name: str = "all-MiniLM-L6-v2",
        persist_dir: str = "data/processed/chromadb"
    ):
        """
        Initialize retriever
        
        Args:
            embedder: Embedder instance (creates if None)
            vector_store: VectorStore instance (creates if None)
            model_name: Embedding model name
            persist_dir: ChromaDB persistence directory
        """
        self.embedder = embedder or Embedder(model_name)
        self.vector_store = vector_store or VectorStore(persist_dir=persist_dir)
        
        logger.info("✅ Retriever initialized")
    
    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User's natural language question
            collection_name: Collection to search
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            logger.info(f"Retrieving for query: '{query}'")
            
            # Embed the query
            query_embedding = self.embedder.embed(query)
            logger.debug(f"Query embedding shape: {query_embedding.shape}")
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                collection_name=collection_name
            )
            
            # Filter by threshold
            filtered_results = [
                r for r in results if r["similarity"] >= similarity_threshold
            ]
            
            logger.info(f"Retrieved {len(filtered_results)} chunks (threshold: {similarity_threshold})")
            
            return filtered_results
        
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def retrieve_batch(
        self,
        queries: List[str],
        collection_name: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[List[Dict]]:
        """
        Retrieve for multiple queries
        
        Args:
            queries: List of queries
            collection_name: Collection to search
            top_k: Results per query
            similarity_threshold: Minimum similarity
            
        Returns:
            List of result lists (one per query)
        """
        logger.info(f"Batch retrieving {len(queries)} queries")
        
        results = []
        for query in queries:
            result = self.retrieve(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            results.append(result)
        
        return results
    
    def get_retrieval_stats(
        self,
        results: List[Dict]
    ) -> Dict:
        """
        Get statistics about retrieval results
        
        Args:
            results: Retrieval results
            
        Returns:
            Statistics dict
        """
        if not results:
            return {
                "count": 0,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "min_similarity": 0.0,
                "files": []
            }
        
        similarities = [r["similarity"] for r in results]
        files = list(set(r["filename"] for r in results))
        
        return {
            "count": len(results),
            "avg_similarity": round(np.mean(similarities), 3),
            "max_similarity": round(max(similarities), 3),
            "min_similarity": round(min(similarities), 3),
            "files": files
        }