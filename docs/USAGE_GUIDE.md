# CodeSemanticsVault - Usage Guide

Complete guide to using the RAG system for code understanding.

---

## Quick Start

### 1. Setup

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/CodeSemanticsVault.git
cd CodeSemanticsVault

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

---

## Usage Patterns

### Pattern 1: Index a Repository

```python
from src.pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline()

# Index a GitHub repository
summary = pipeline.index_repository(
    github_url="https://github.com/pallets/flask",
    collection_name="flask"
)

print(f"Indexed {summary['chunks_created']} chunks from {summary['files_indexed']} files")
```

**Output:**
Indexing complete: {
'status': 'success',
'files_indexed': 42,
'chunks_created': 1234,
'size_mb': 5.2
}

---

### Pattern 2: Ask Questions

```python
# Ask a question about the indexed code
result = pipeline.query(
    question="How does request routing work?",
    collection_name="flask"
)

print(result['answer'])
print(f"Confidence: {result['confidence']}")
print(f"Citations: {result['citations']}")
```

**Output:**
Answer:
The request routing in Flask works through decorators...
[detailed answer with code references]
Confidence: 0.87
Citations: [
{'filename': 'app.py', 'start_line': 45, 'end_line': 60},
{'filename': 'routing.py', 'start_line': 100, 'end_line': 120}
]

---

### Pattern 3: Component-Level Usage

If you need fine-grained control, use components directly:

```python
from src.core.repo_parser import RepositoryParser
from src.core.semantic_chunker import SemanticChunker
from src.core.embedder import Embedder
from src.core.vector_store import VectorStore
from src.core.retriever import Retriever

# Step 1: Parse repository
parser = RepositoryParser()
repo_path = parser.clone_repo("https://github.com/user/repo")
files = parser.extract_files(repo_path)

# Step 2: Chunk code
chunker = SemanticChunker(chunk_size=512)
chunks = []
for file in files:
    file_chunks = chunker.chunk_file(file['filename'], file['content'])
    chunks.extend(file_chunks)

# Step 3: Embed
embedder = Embedder()
chunks = embedder.embed_chunks(chunks)

# Step 4: Store
store = VectorStore(persist_dir="my_vectors")
store.create_collection("my_repo")
store.add_embeddings(chunks, "my_repo")

# Step 5: Retrieve
from src.core.retriever import Retriever
retriever = Retriever(embedder=embedder, vector_store=store)
results = retriever.retrieve("query", "my_repo", top_k=5)

# Step 6: Synthesize
from src.core.synthesizer import Synthesizer
synthesizer = Synthesizer()
answer = synthesizer.synthesize("query", results)
```

---

## Configuration

Edit `.env` to customize:
OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
Retrieval
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3
Storage
CHROMADB_PATH=data/processed/chromadb
REPO_CACHE_DIR=data/raw/repos

---

## Performance Optimization

### Reduce Latency

```python
# Use smaller top_k
pipeline.query(question, "repo", top_k=3)  # Default: 5

# Increase similarity threshold
pipeline.query(question, "repo", similarity_threshold=0.5)  # Fewer results = faster
```

### Reduce Cost

```python
# Use smaller model (if acceptable)
# In synthesizer: model="gpt-3.5-turbo" instead of "gpt-4"

# Batch queries
queries = ["Q1", "Q2", "Q3"]
results = pipeline.retriever.retrieve_batch(queries, "repo")
```

---

## Troubleshooting

### Issue: "No relevant code found"

**Cause:** Query doesn't match indexed code well  
**Solution:** Try rephrasing the question more technically

```python
# Bad: "How to make it fast?"
# Good: "What optimization techniques are used in the database layer?"
```

### Issue: High latency (>5s)

**Cause:** Large repository or GPT-4 slowness  
**Solution:**
1. Reduce `top_k`
2. Increase `similarity_threshold`
3. Use smaller repo for testing

### Issue: "API rate limit exceeded"

**Cause:** Too many queries in short time  
**Solution:** Add delay between queries or use batch mode

```python
import time
for query in queries:
    result = pipeline.query(query, "repo")
    time.sleep(1)  # 1 second between queries
```

---

## Advanced: Custom Collections

```python
# Create separate collections for different purposes
pipeline.index_repository(url, collection_name="auth_module")
pipeline.index_repository(url, collection_name="payment_module")

# Query specific collection
auth_answer = pipeline.query("auth question", "auth_module")
payment_answer = pipeline.query("payment question", "payment_module")

# List all collections
status = pipeline.get_pipeline_status()
print(status['collections'])
```

---

## Testing

Run tests to verify everything works:

```bash
# Run all tests
pytest tests/ -v

# Run specific component tests
pytest tests/test_embedder.py -v
pytest tests/test_vector_store.py -v
pytest tests/test_retriever.py -v

# Run with coverage
pytest tests/ --cov=src/
```

---

## Example: Complete Workflow

```python
from src.pipeline import RAGPipeline
import time

# Initialize
pipeline = RAGPipeline()

# Index Flask repository
print("Indexing Flask...")
summary = pipeline.index_repository(
    github_url="https://github.com/pallets/flask",
    collection_name="flask"
)
print(f"✅ Indexed {summary['chunks_created']} chunks\n")

# Ask questions
questions = [
    "How does request routing work?",
    "What is the request context?",
    "How to add middleware?"
]

for question in questions:
    print(f"Q: {question}")
    result = pipeline.query(question, "flask")
    print(f"A: {result['answer'][:200]}...\n")
    time.sleep(1)  # Rate limiting
```

---

## Next Steps

1. **Deploy as API** - Use FastAPI to expose as HTTP endpoint
2. **Web UI** - Build frontend for user interactions
3. **Multi-repo support** - Index multiple repositories
4. **Caching** - Cache embeddings for faster re-indexing
5. **Evaluation** - Benchmark answer quality

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review architecture in `docs/architecture.md`
3. Check test files for usage examples

---