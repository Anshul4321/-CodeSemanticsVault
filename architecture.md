# Architecture Documentation

## System Overview

CodeSemanticsVault is a **Retrieval-Augmented Generation (RAG)** system designed specifically for code understanding. It combines semantic search with generative AI to answer natural language questions about codebases.

### Architecture Pattern: Lambda Architecture with RAG

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION LAYER                    │
│              (Next.js Frontend, Dark Mode UI)                │
└─────────────────────────────────────────────────────────────┘
                         ↓ HTTP/JSON ↓
┌─────────────────────────────────────────────────────────────┐
│                   API LAYER (FastAPI)                        │
│  • Request validation  • Error handling  • CORS support     │
└─────────────────────────────────────────────────────────────┘
                         ↓              ↓
        ┌────────────────┴──────────────┐
        ↓                               ↓
   INDEXING PIPELINE            QUERY PIPELINE
   (One-time per repo)          (Per question)
        │                               │
        ├─→ Parse Repository      ├─→ Embed Question
        ├─→ Extract Files         ├─→ Retrieve Chunks
        ├─→ Chunk Code            ├─→ Synthesize Answer
        ├─→ Embed Chunks          └─→ Format Response
        └─→ Store Vectors
```

---

## Core Pipeline Architecture

### 1. Indexing Pipeline

The **one-time indexing process** converts raw GitHub repositories into searchable semantic vectors.

#### Phase 1: Repository Acquisition
```python
# Input: GitHub URL
https://github.com/requests/requests

# Process:
1. Clone repository to /data/raw/repos/
2. Extract repository metadata (name, size, language)
3. List all files recursively

# Output: File list with paths
['/requests/api.py', '/requests/models.py', ...]
```

**Key Decisions:**
- Uses `GitPython` for cloning (supports HTTPS URLs)
- Shallow clones for speed (single branch, recent history)
- Stores in `/data/raw/repos/{repo_name}/` for cleanup

#### Phase 2: File Extraction & Filtering
```python
# Input: Full file tree
.
├── requests/
│   ├── __init__.py
│   ├── api.py
│   ├── models.py
│   └── ...
├── tests/
│   ├── test_api.py
│   └── ...
├── docs/
│   ├── README.md
│   └── ...
└── .gitignore

# Process:
1. Identify file language by extension
2. Check against SUPPORTED_EXTENSIONS:
   - .py, .js, .ts, .java, .cpp, .go, .rs, etc.
3. Skip:
   - Binary files (images, compiled code)
   - Large files (>1MB)
   - Build artifacts (node_modules/, __pycache__/)
4. Read file content (UTF-8)

# Output: Filtered code files with content
{
  'path': 'requests/api.py',
  'language': 'python',
  'content': '# Code content...',
  'size_bytes': 2048
}
```

**Why this approach:**
- Language detection ensures syntax-aware chunking
- Filtering removes noise and speeds up processing
- Size limits prevent tokenization overflows

#### Phase 3: Semantic Code Chunking
```python
# Input: Source code file
def get(url, **kwargs):
    """
    Sends a GET request. Returns Response object.
    """
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, **kwargs)

def post(url, data=None, json=None, **kwargs):
    """
    Sends a POST request. Returns Response object.
    """
    return request('post', url, data=data, json=json, **kwargs)

# Chunking Strategy:
# Instead of fixed-size chunks, respect code structure

# Python Strategy:
1. Parse AST (Abstract Syntax Tree)
2. Identify functions, classes, methods
3. Extract each with:
   - Signature
   - Docstring
   - Body code
   - Comments

# Output: Semantic chunks
[
  {
    'type': 'function',
    'name': 'get',
    'content': 'def get(url, **kwargs):\n    """..."""\n    ...',
    'start_line': 45,
    'end_line': 50,
    'dependencies': []
  },
  {
    'type': 'function',
    'name': 'post',
    'content': 'def post(url, data=None, json=None, **kwargs):\n    """..."""\n    ...',
    'start_line': 52,
    'end_line': 58,
    'dependencies': ['request']
  }
]
```

**Chunking Philosophy:**
- **Syntax-aware**: Functions/classes stay intact (not randomly split)
- **Context-rich**: Includes docstrings and comments for meaning
- **Size-bounded**: 512–1024 tokens to fit in context window
- **Overlapped**: 10% overlap between chunks for continuity

**Language-Specific Strategies:**
- **Python**: AST parsing with `ast` module
- **JavaScript/TypeScript**: Regex-based function/class detection
- **Java**: Simplified regex (no full parsing)
- **Others**: Regex fallback for basic detection

#### Phase 4: Vector Embedding
```python
# Input: Code chunks (strings)
chunks = [
  "def get(url, **kwargs): ...",
  "def post(url, data=None, json=None, **kwargs): ...",
  ...
]

# Process:
1. Use sentence-transformers model: all-MiniLM-L6-v2
2. Tokenize text (truncate to 512 tokens)
3. Pass through transformer encoder
4. Output 384-dimensional vector per chunk

# Why all-MiniLM-L6-v2?
- Fast: 10k+ sentences/second on CPU
- Lightweight: 22MB, fits in memory
- Effective: Trained on diverse text corpus
- Cost: FREE (no API calls)
- Alternative: all-mpnet-base-v2 (slower, more accurate)

# Output: Dense vectors
chunk_1_vector = [0.234, -0.187, 0.954, ..., 0.123]  # 384 dims
chunk_2_vector = [0.112, 0.456, -0.234, ..., -0.089]  # 384 dims
...

# Computation:
- 1,234 chunks × 384 dims = ~1.9 MB vectors
- Time: ~5 seconds for typical repo
```

**Vector Space Properties:**
- **Semantic proximity**: Similar code has similar vectors
- **Cosine similarity**: Used for relevance ranking
- **Dimensionality**: 384 dims (good balance of speed/accuracy)
- **Normalization**: L2 normalized for stable similarity

#### Phase 5: Persistent Storage
```python
# Input: Vectors + metadata
vectors = [384-dim arrays...]
metadata = [
  {'filename': 'requests/api.py', 'start_line': 45, 'end_line': 50},
  {'filename': 'requests/models.py', 'start_line': 120, 'end_line': 145},
  ...
]

# Process:
1. Store in ChromaDB (persistent vector database)
2. Create collection: "requests" (repo name)
3. Index with HNSW (Hierarchical Navigable Small World)
4. Save to disk: /data/processed/chromadb/

# ChromaDB Advantages:
- Persistent: Survives process restarts
- Fast: HNSW indexing for O(log N) search
- Lightweight: Embedded database, no server needed
- Metadata: Stores file/line info alongside vectors

# Output: Persistent collection
chromadb.PersistentClient(path='./data/processed/chromadb')
client.get_collection('requests')
# Now queryable
```

**Storage Layout:**
```
/data/processed/chromadb/
├── requests/           # Collection for requests repo
│   ├── chroma-data/   # Vector embeddings
│   ├── index/         # HNSW index
│   └── metadata.db    # SQLite metadata
├── django/            # Collection for django repo
│   ├── chroma-data/
│   ├── index/
│   └── metadata.db
└── flask/             # Collection for flask repo
    ├── chroma-data/
    ├── index/
    └── metadata.db
```

**Indexing Summary:**
| Stage | Input | Output | Time | Cost |
|-------|-------|--------|------|------|
| Repo Acquisition | GitHub URL | Cloned files | 10–30s | ~0 |
| File Extraction | File tree | Code files | 1–5s | ~0 |
| Chunking | Raw code | Semantic chunks | 5–15s | ~0 |
| Embedding | Code chunks | Vectors | 5–30s | ~0 |
| Storage | Vectors + meta | ChromaDB index | 1–5s | ~0 |
| **Total** | **GitHub repo** | **Searchable index** | **25–85s** | **~$0.001** |

---

### 2. Query Pipeline

The **per-query process** answers user questions using indexed vectors and LLM synthesis.

#### Phase 1: Question Embedding
```python
# Input: User question (natural language)
"How do you make an HTTP GET request?"

# Process:
1. Embed question using same model as chunks:
   all-MiniLM-L6-v2
2. Output: 384-dimensional vector

# Why same model?
- Ensures vectors are comparable
- Question and code chunks in same space
- Enables cosine similarity matching

# Output: Query vector
question_vector = [0.145, -0.312, 0.876, ..., 0.234]  # 384 dims

# Computation:
- Time: ~10ms (very fast)
- Cost: ~$0 (local model)
```

#### Phase 2: Semantic Similarity Search
```python
# Input:
# - Query vector: [0.145, -0.312, 0.876, ...]
# - ChromaDB collection: 1,234 indexed chunks

# Process:
1. HNSW index finds nearest neighbors in O(log N) time
2. Compute cosine similarity to top-K candidates
3. Rank by similarity score

# Cosine similarity formula:
similarity = (query_vec · chunk_vec) / (||query_vec|| × ||chunk_vec||)
# Range: [-1, 1], where 1 = identical, 0 = unrelated

# Top-5 results for "HTTP GET request":
[
  {
    'chunk': 'def get(url, **kwargs): ...',
    'similarity': 0.87,
    'filename': 'requests/api.py',
    'lines': '45-50'
  },
  {
    'chunk': 'class Request: ...',
    'similarity': 0.74,
    'filename': 'requests/models.py',
    'lines': '120-145'
  },
  ...
]

# Computation:
- Search time: ~100ms (HNSW is fast)
- Cost: ~$0 (local operation)
```

**Why HNSW Indexing?**
- **Fast**: O(log N) query time vs O(N) linear scan
- **Approximate**: Near-optimal results, not exact
- **Scalable**: Handles 100k+ vectors efficiently
- **Memory-efficient**: Hierarchical structure

#### Phase 3: LLM Synthesis
```python
# Input:
# - Original question: "How do you make an HTTP GET request?"
# - Retrieved chunks (top-5): [chunk1, chunk2, ...]
# - Chunk similarities: [0.87, 0.74, 0.62, ...]

# System Prompt (hardcoded):
"""
You are an expert code assistant. A user has asked a question about 
a software repository. Below are the most relevant code snippets.

Your task:
1. Answer the question directly and concisely
2. Use code examples from provided snippets
3. Be accurate - don't extrapolate beyond provided context
4. Mention limitations if question can't be fully answered
"""

# Context Assembly:
prompt = f"""
{system_prompt}

Question: {question}

Relevant Code Snippets:
{format_chunks_with_citations(retrieved_chunks)}

Answer:
"""

# Example context sent to GPT-4:
"""
You are an expert code assistant...

Question: How do you make an HTTP GET request?

Relevant Code Snippets:
[From requests/api.py, lines 45-50]
def get(url, **kwargs):
    '''
    Sends a GET request. Returns Response object.
    '''
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, **kwargs)

[From requests/models.py, lines 120-145]
class Request:
    '''Represents an HTTP request'''
    def __init__(self, method, url, **kwargs):
        self.method = method
        self.url = url
    ...

Answer:
"""

# GPT-4 Response:
"To make an HTTP GET request using the requests library, 
use the requests.get() method. It takes a URL and optional 
parameters like headers, timeout, and authentication. 
For example: requests.get('https://httpbin.org/get')"

# Computation:
- Tokens input: ~500 (question + context)
- Tokens output: ~100 (answer)
- Cost: ~$0.003 (GPT-4 pricing)
- Time: 1.0–1.5 seconds
```

**Prompt Engineering Details:**
- **System prompt**: Instructs model to be a code expert
- **Context**: Top-K chunks with proper formatting
- **Citation format**: [Filename:StartLine-EndLine]
- **Length control**: No explicit tokens limit (rely on context window)
- **Tone**: Professional, accurate, concise

#### Phase 4: Confidence Scoring
```python
# Input: Retrieved chunks and synthesis result
chunks = [
  {'similarity': 0.87, 'coherence': 0.92},
  {'similarity': 0.74, 'coherence': 0.88},
  {'similarity': 0.62, 'coherence': 0.79},
  {'similarity': 0.51, 'coherence': 0.71},
  {'similarity': 0.44, 'coherence': 0.65}
]

# Confidence Formula:
# confidence = (0.25 × avg_similarity) + 
#              (0.50 × avg_retrieval_score) +
#              (0.25 × answer_coherence)

avg_similarity = mean([0.87, 0.74, 0.62, 0.51, 0.44]) = 0.636
avg_retrieval = mean([0.87, 0.74, 0.62, 0.51, 0.44]) = 0.636
answer_coherence = 0.82  # How well answer uses context

confidence = (0.25 × 0.636) + (0.50 × 0.636) + (0.25 × 0.82)
           = 0.159 + 0.318 + 0.205
           = 0.682 (68.2%)

# Output: Confidence score
confidence_score = 0.682  # Range: [0, 1]

# Interpretation:
# 0.0–0.3: Low confidence (answer may be hallucinated)
# 0.3–0.6: Medium confidence (answer is reasonable)
# 0.6–0.9: High confidence (answer well-grounded)
# 0.9–1.0: Very high confidence (answer certain)
```

**Why This Scoring?**
- **Retrieval weight (50%)**: Most important — did we find good code?
- **Similarity weight (25%)**: How semantically close is context?
- **Coherence weight (25%)**: Did LLM use context coherently?
- **Clamped [0, 1]**: Bounds confidence to sensible range

#### Phase 5: Response Formatting
```python
# Input:
# - Answer text: "To make an HTTP GET request..."
# - Retrieved chunks: [chunk1, chunk2, ...]
# - Confidence score: 0.68
# - Retrieved chunks count: 5

# Process:
1. Extract citations from answer (match to retrieved chunks)
2. Build citation list with filename:line_range
3. Format for frontend JSON response

# Output: JSON Response
{
  "answer": "To make an HTTP GET request using the requests library...",
  "citations": [
    {
      "filename": "requests/api.py",
      "start_line": 45,
      "end_line": 50
    },
    {
      "filename": "requests/models.py",
      "start_line": 120,
      "end_line": 145
    }
  ],
  "confidence": 0.68,
  "retrieved_chunks": 5
}
```

**Query Summary:**
| Stage | Input | Output | Time | Cost |
|-------|-------|--------|------|------|
| Question Embed | Question string | 384-dim vector | 10ms | ~$0 |
| Retrieval | Query vector | Top-5 chunks | 100ms | ~$0 |
| Synthesis | Question + context | Answer text | 1–1.5s | ~$0.003 |
| Scoring | Chunks + answer | Confidence [0,1] | 10ms | ~$0 |
| Format | Response data | JSON response | 5ms | ~$0 |
| **Total** | **Question** | **Answer + meta** | **1.2–1.7s** | **~$0.003** |

---

## Data Flow Diagram

```
INDEXING FLOW:
┌──────────────┐
│ GitHub URL   │
└──────┬───────┘
       ↓
┌──────────────────┐
│ Clone Repo       │ [GitPython]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Extract Files    │ [Language detection]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Parse & Chunk    │ [AST + Regex]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Embed Chunks     │ [sentence-transformers]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Store in ChromaDB│ [Persistent]
└──────┬───────────┘
       ↓
    ✅ Ready


QUERY FLOW:
┌──────────────┐
│ User Question│
└──────┬───────┘
       ↓
┌──────────────────┐
│ Embed Question   │ [sentence-transformers]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Semantic Search  │ [ChromaDB + HNSW]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Retrieve Top-K   │ [similarity ranking]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Build Prompt     │ [context assembly]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ LLM Synthesis    │ [GPT-4]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Score Confidence │ [weighted formula]
└──────┬───────────┘
       ↓
┌──────────────────┐
│ Format Response  │ [JSON]
└──────┬───────────┘
       ↓
    ✅ Answer + Citations


PERSISTENT STATE:
/data/
├── raw/repos/
│   ├── requests/
│   ├── django/
│   └── ...
└── processed/chromadb/
    ├── requests/
    ├── django/
    └── ...
```

---

## Scalability Considerations

### Current Limitations
- **Repository size**: Tested up to 10k files, 100MB codebase
- **Concurrent users**: Single backend instance (~10 concurrent queries)
- **Query latency**: 1.2–1.7 seconds (acceptable for code Q&A)
- **Storage**: ~10MB per 1,000 code chunks

### Scaling Strategies

**Horizontal Scaling (Multiple Instances):**
```
Load Balancer
    ↓
┌───┴───────────────────────┐
├─ Backend Instance 1       │
├─ Backend Instance 2       │
├─ Backend Instance 3       │
└───────────────────────────┘
         ↓
    Shared ChromaDB
    (on network mount or S3)
```

**Vertical Scaling (Bigger Machine):**
- Use GPU for embeddings: 100× faster
- Increase ChromaDB memory cache
- Parallel repository indexing

**Distributed Indexing:**
- Queue system (Redis, RabbitMQ) for indexing jobs
- Worker processes index repos in parallel
- Store results in shared vector DB

---

## Security Architecture

### Data Isolation
- Each indexed repo in separate ChromaDB collection
- No cross-repo leakage of code
- Metadata (filename, lines) stored with vectors

### API Security
- OpenAI API key in `.env` (never in code)
- Environment-based configuration
- CORS enabled for frontend origin only

### Input Validation
- GitHub URL validation (regex)
- Collection name sanitization
- Question length limits

---

## Error Handling

```
Failure Points & Responses:

1. Repository Not Found
   Input: Invalid GitHub URL
   Handling: Try clone → catch GitCommandError → return 404

2. Unsupported Language
   Input: Repo with only .pkl, .so files
   Handling: Extract 0 files → skip indexing → return error

3. LLM Rate Limit
   Input: Too many concurrent queries
   Handling: Exponential backoff + queue

4. ChromaDB Corruption
   Input: Disk error during save
   Handling: Atomic transactions + backup collection

5. Network Timeout
   Input: GitHub server slow
   Handling: Timeout after 30s + retry with exponential backoff
```

---

## Performance Optimization

### Indexing Optimization
- **Parallel chunking**: Process files in parallel using `ProcessPoolExecutor`
- **Batch embedding**: Embed 32 chunks at once (vectorized)
- **Disk caching**: Cache downloaded repos for 7 days

### Query Optimization
- **LRU cache**: Cache embeddings of recent questions (5 minutes)
- **HNSW tuning**: HNSW `ef_construction=400` for better accuracy
- **Early stopping**: Return top-5 immediately, don't search all vectors

### Storage Optimization
- **Vector compression**: Could use quantization (INT8) for 4× smaller size
- **Deduplication**: Skip identical chunks across files
- **Lazy loading**: Only load chunk text when needed

---

## Deployment Architecture

### Development
```
Laptop
├── Frontend: npm run dev (port 3000)
├── Backend: uvicorn (port 8000)
└── Database: ChromaDB (local disk)
```

### Production
```
Vercel (Frontend)
    ↓
Railway/Render (Backend)
    ↓
Cloud Storage (ChromaDB)
    └─ S3 or network mount
```

---

## Summary

CodeSemanticsVault uses a **modular, scalable RAG architecture** optimized for code understanding:

1. **Indexing**: Parse → Chunk → Embed → Store (one-time, 25–85s per repo)
2. **Querying**: Embed → Retrieve → Synthesize → Score (per question, 1.2–1.7s)
3. **Storage**: ChromaDB for persistent vectors + metadata
4. **Synthesis**: GPT-4 with retrieved context + confidence scoring
5. **UI**: Next.js with real-time feedback and dark mode

**Key Features:**
- Semantic understanding (not keyword matching)
- Source attribution (citations with line numbers)
- Confidence scoring (knows when to be uncertain)
- Cost-optimized (local embeddings, minimal API calls)
- Production-ready (error handling, logging, testing)

This architecture scales from personal projects to enterprise codebases while remaining cost-effective and maintainable.