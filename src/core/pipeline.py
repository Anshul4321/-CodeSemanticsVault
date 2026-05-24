"""
RAG Pipeline Orchestrator
Complete end-to-end RAG system
"""

import logging
from typing import List, Dict, Optional
from src.core.repo_parser import RepositoryParser
from src.core.semantic_chunker import SemanticChunker
from src.core.embedder import Embedder
from src.core.vector_store import VectorStore
from src.core.retriever import Retriever
from src.core.synthesizer import Synthesizer

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete retrieval-augmented generation (RAG) pipeline.
    Orchestrates all components for end-to-end code understanding.
    """
    
    def __init__(
        self,
        persist_dir: str = "data/processed/chromadb",
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 512,
        top_k: int = 5
    ):
        """
        Initialize RAG pipeline
        
        Args:
            persist_dir: Vector store directory
            model_name: Embedding model
            chunk_size: Code chunk size
            top_k: Top results to retrieve
        """
        self.persist_dir = persist_dir
        self.chunk_size = chunk_size
        self.top_k = top_k
        
        # Initialize components
        self.parser = RepositoryParser()
        self.chunker = SemanticChunker(chunk_size=chunk_size)
        self.embedder = Embedder(model_name=model_name)
        self.vector_store = VectorStore(persist_dir=persist_dir)
        self.retriever = Retriever(
            embedder=self.embedder,
            vector_store=self.vector_store
        )
        self.synthesizer = Synthesizer()
        
        logger.info("✅ RAG Pipeline initialized")
    
    def index_repository(self, github_url: str, collection_name: Optional[str] = None) -> Dict:
        """
        Index a GitHub repository
        
        Args:
            github_url: GitHub repository URL
            collection_name: Collection name (uses repo name if None)
            
        Returns:
            Indexing summary
        """
        try:
            logger.info(f"Starting indexing: {github_url}")
            
            # Extract repo name if not provided
            if not collection_name:
                collection_name = github_url.split("/")[-1].replace(".git", "")
            
            # Step 1: Clone and parse
            logger.info("Step 1/4: Parsing repository...")
            repo_path = self.parser.clone_repo(github_url)
            files = self.parser.extract_files(repo_path)
            repo_summary = self.parser.get_repo_summary(files)
            
            logger.info(f"  Extracted {repo_summary['total_files']} files, {repo_summary['total_lines']} lines")
            
            # Step 2: Chunk
            logger.info("Step 2/4: Chunking code...")
            all_chunks = []
            for file_data in files:
                chunks = self.chunker.chunk_file(
                    filename=file_data["relative_path"],
                    content=file_data["content"]
                )
                all_chunks.extend(chunks)
            
            logger.info(f"  Created {len(all_chunks)} chunks")
            
            # Step 3: Embed
            logger.info("Step 3/4: Generating embeddings...")
            all_chunks = self.embedder.embed_chunks(all_chunks)
            
            # Step 4: Store
            logger.info("Step 4/4: Storing in vector database...")
            self.vector_store.create_collection(collection_name)
            self.vector_store.add_embeddings(all_chunks, collection_name)
            
            summary = {
                "status": "success",
                "repository": github_url,
                "collection": collection_name,
                "files_indexed": repo_summary["total_files"],
                "lines_indexed": repo_summary["total_lines"],
                "chunks_created": len(all_chunks),
                "size_mb": repo_summary["total_size_mb"]
            }
            
            logger.info(f"✅ Indexing complete: {summary}")
            return summary
        
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def query(
        self,
        question: str,
        collection_name: str,
        include_confidence: bool = True
    ) -> Dict:
        """
        Ask a question about indexed code
        
        Args:
            question: User's natural language question
            collection_name: Collection to search
            include_confidence: Include confidence scores
            
        Returns:
            Answer with citations and metadata
        """
        try:
            logger.info(f"Processing query: '{question}'")
            
            # Step 1: Retrieve
            logger.info("Retrieving relevant code...")
            retrieved = self.retriever.retrieve(
                query=question,
                collection_name=collection_name,
                top_k=self.top_k
            )
            
            if not retrieved:
                return {
                    "answer": "No relevant code found for this question.",
                    "citations": [],
                    "confidence": 0.0,
                    "retrieved_chunks": 0
                }
            
            logger.info(f"  Retrieved {len(retrieved)} chunks")
            
            # Step 2: Synthesize
            logger.info("Generating answer with GPT-4...")
            result = self.synthesizer.synthesize(
                query=question,
                chunks=retrieved,
                include_confidence=include_confidence
            )
            
            logger.info(f"✅ Query complete")
            return result
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_pipeline_status(self) -> Dict:
        """Get pipeline status and statistics"""
        collections = self.vector_store.list_collections()
        
        status = {
            "initialized": True,
            "components": {
                "parser": "ready",
                "chunker": "ready",
                "embedder": f"{self.embedder.model_name}",
                "vector_store": f"{len(collections)} collections",
                "retriever": "ready",
                "synthesizer": "ready"
            },
            "collections": collections
        }
        
        return status


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize pipeline
    pipeline = RAGPipeline()
    
    print("\n🚀 RAG Pipeline Demo\n")
    print(f"Status: {pipeline.get_pipeline_status()}\n")
    
    # Note: Full demo requires GitHub access and OpenAI API key
    # For testing, show structure
    print("✅ Pipeline ready for:")
    print("  1. pipeline.index_repository('https://github.com/user/repo')")
    print("  2. pipeline.query('How does X work?', 'repo-name')")
    print("  3. pipeline.get_pipeline_status()")