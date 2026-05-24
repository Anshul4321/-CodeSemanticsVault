"""
Vector Store
Store and retrieve embeddings using ChromaDB
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import chromadb

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages embedding storage and retrieval using ChromaDB.
    Handles persistence, collections, and semantic search.
    """
    
    def __init__(
        self,
        persist_dir: str = "data/processed/chromadb",
        collection_name: str = "code_docs"
    ):
        """
        Initialize vector store
        
        Args:
            persist_dir: Directory to store ChromaDB data
            collection_name: Default collection name
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        try:
            logger.info(f"Initializing ChromaDB at {self.persist_dir}")
            
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir)
            )
            logger.info("✅ ChromaDB client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
        
        # Get or create default collection
        self.collection = None
    
    def create_collection(
        self,
        collection_name: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Create a new collection
        
        Args:
            collection_name: Name of collection
            metadata: Optional metadata dict
        """
        try:
            logger.info(f"Creating collection: {collection_name}")
            
            # Delete if exists (to avoid conflicts)
            try:
                self.client.delete_collection(name=collection_name)
                logger.debug(f"Deleted existing collection: {collection_name}")
            except:
                pass
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata or {"description": f"Collection: {collection_name}"}
            )
            
            logger.info(f"✅ Created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get existing collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            logger.info(f"Retrieved collection: {collection_name}")
            return collection
        except Exception as e:
            logger.warning(f"Collection {collection_name} not found: {e}")
            return None
    
    def add_embeddings(
        self,
        chunks: List[Dict],
        collection_name: Optional[str] = None
    ) -> None:
        """
        Add embeddings to collection
        
        Args:
            chunks: List of chunks with "embedding" key
            collection_name: Collection to add to (uses default if None)
        """
        if collection_name:
            self.collection = self.get_collection(collection_name)
            if not self.collection:
                self.create_collection(collection_name)
        
        if not self.collection:
            raise ValueError("No collection selected. Call create_collection() first.")
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk.get('filename', 'unknown')}_{chunk.get('start_line', 0)}_{i}"
            
            ids.append(chunk_id)
            embeddings.append(chunk["embedding"].tolist())  # Convert numpy to list
            documents.append(chunk["content"])
            
            # Store metadata
            metadatas.append({
                "filename": str(chunk.get("filename", "")),
                "start_line": str(chunk.get("start_line", 0)),
                "end_line": str(chunk.get("end_line", 0)),
                "context": str(chunk.get("context", "")),
                "line_count": str(chunk.get("line_count", 0))
            })
        
        try:
            logger.info(f"Adding {len(chunks)} embeddings to collection")
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"✅ Added {len(chunks)} embeddings")
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            collection_name: Collection to search (uses default if None)
            
        Returns:
            List of similar chunks with scores
        """
        if collection_name:
            self.collection = self.get_collection(collection_name)
        
        if not self.collection:
            logger.warning("No collection to search")
            return []
        
        try:
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            
            if results["ids"] and len(results["ids"]) > 0:
                for i, (chunk_id, distance, metadata, document) in enumerate(
                    zip(
                        results["ids"][0],
                        results["distances"][0],
                        results["metadatas"][0],
                        results["documents"][0]
                    )
                ):
                    # Convert distance to similarity (lower distance = higher similarity)
                    similarity = 1 / (1 + distance)  # Approximate conversion
                    
                    formatted_results.append({
                        "id": chunk_id,
                        "content": document,
                        "similarity": round(similarity, 3),
                        "distance": round(distance, 3),
                        "metadata": metadata,
                        "filename": metadata.get("filename", ""),
                        "start_line": int(metadata.get("start_line", 0)),
                        "end_line": int(metadata.get("end_line", 0)),
                        "context": metadata.get("context", "")
                    })
            
            logger.debug(f"Found {len(formatted_results)} similar chunks")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            names = [c.name for c in collections]
            logger.info(f"Found {len(names)} collections: {names}")
            return names
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_size(self, collection_name: Optional[str] = None) -> int:
        """Get number of embeddings in collection"""
        collection = self.collection
        if collection_name:
            collection = self.get_collection(collection_name)
        
        if not collection:
            return 0
        
        try:
            count = collection.count()
            logger.info(f"Collection {collection.name} has {count} embeddings")
            return count
        except Exception as e:
            logger.error(f"Failed to get collection size: {e}")
            return 0
    
    def persist(self) -> None:
        """Persist data to disk"""
        try:
            self.client.persist()
            logger.info(f"✅ Persisted data to {self.persist_dir}")
        except Exception as e:
            logger.warning(f"Persistence not supported or failed: {e}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    import numpy as np
    
    # Initialize store
    store = VectorStore(persist_dir="data/processed/chromadb")
    store.create_collection("test_repo")
    
    # Create sample embeddings
    sample_chunks = [
        {
            "filename": "auth.py",
            "content": "def authenticate(user): return validate_token(user)",
            "start_line": 10,
            "end_line": 12,
            "context": "authenticate",
            "embedding": np.random.rand(384)  # Fake embedding
        },
        {
            "filename": "payment.py",
            "content": "def process_payment(amount): return charge_card(amount)",
            "start_line": 20,
            "end_line": 22,
            "context": "process_payment",
            "embedding": np.random.rand(384)
        },
        {
            "filename": "user.py",
            "content": "class User: def __init__(self, name): self.name = name",
            "start_line": 30,
            "end_line": 32,
            "context": "User",
            "embedding": np.random.rand(384)
        }
    ]
    
    # Add embeddings
    store.add_embeddings(sample_chunks, "test_repo")
    
    # Search
    query = np.random.rand(384)
    results = store.search(query, top_k=2, collection_name="test_repo")
    
    print(f"\n✅ Found {len(results)} results:")
    for result in results:
        print(f"  - {result['filename']}:{result['start_line']} (similarity: {result['similarity']})")
    
    # Cleanup
    store.delete_collection("test_repo")
    print("\n✅ Test complete")