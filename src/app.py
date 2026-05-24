"""
FastAPI backend for CodeSemanticsVault
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from src.core.pipeline import RAGPipeline

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CodeSemanticsVault",
    description="RAG system for understanding GitHub repositories"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = RAGPipeline()

# Models
class IndexRequest(BaseModel):
    github_url: str
    collection_name: str = None

class IndexResponse(BaseModel):
    status: str
    repository: str
    collection: str
    files_indexed: int
    chunks_created: int
    size_mb: float

class QueryRequest(BaseModel):
    question: str
    collection_name: str

class QueryResponse(BaseModel):
    answer: str
    citations: list
    confidence: float
    retrieved_chunks: int

# Routes
@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "CodeSemanticsVault API"}

@app.post("/index", response_model=IndexResponse)
async def index_repository(request: IndexRequest):
    """Index a GitHub repository"""
    try:
        logger.info(f"Indexing: {request.github_url}")
        
        summary = pipeline.index_repository(
            github_url=request.github_url,
            collection_name=request.collection_name
        )
        
        if summary["status"] != "success":
            raise HTTPException(status_code=400, detail=summary.get("error"))
        
        return IndexResponse(
            status="success",
            repository=summary["repository"],
            collection=summary["collection"],
            files_indexed=summary["files_indexed"],
            chunks_created=summary["chunks_created"],
            size_mb=summary["size_mb"]
        )
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_repository(request: QueryRequest):
    """Query an indexed repository"""
    try:
        logger.info(f"Query: {request.question}")
        
        result = pipeline.query(
            question=request.question,
            collection_name=request.collection_name
        )
        
        return QueryResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0),
            retrieved_chunks=result.get("retrieved_chunks", 0)
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections")
async def get_collections():
    """Get all indexed collections"""
    try:
        status = pipeline.get_pipeline_status()
        return {
            "collections": status["collections"],
            "count": len(status["collections"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)