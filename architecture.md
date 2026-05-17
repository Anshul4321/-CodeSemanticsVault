\# Architecture Design



\## System Overview



┌─────────────────────────────────────────────────────────┐

│                    USER INTERFACE                       │

│              (Web UI / API Endpoint)                    │

└────────────────────┬────────────────────────────────────┘

│

┌────────────┴────────────┐

│                         │

▼                         ▼

┌──────────────────┐      ┌──────────────────┐

│  UPLOAD REPO     │      │  QUERY HANDLER   │

│  (GitHub URL)    │      │  (User Question) │

└────────┬─────────┘      └────────┬─────────┘

│                         │

▼                         ▼

┌────────────────────────────────────┐

│      CORE RAG ENGINE               │

│  ┌──────────────────────────────┐  │

│  │ 1. Parse \& Extract Code      │  │

│  │ 2. Semantic Chunking         │  │

│  │ 3. Embed Chunks              │  │

│  │ 4. Store in Vector DB        │  │

│  │ 5. Retrieve Similar Chunks   │  │

│  │ 6. Generate Answer (LLM)     │  │

│  └──────────────────────────────┘  │

└────────┬─────────────────────────┘

│

┌────┴────┐

│          │

▼          ▼

┌────────┐  ┌──────────┐

│ChromaDB│  │  GPT-4   │

│(Vector)│  │  (LLM)   │

└────────┘  └──────────┘



\---



\## Component Details



\### \*\*1. Input Handler\*\*

\- Accepts GitHub repo URL

\- Clones repo locally

\- Extracts code files + documentation



\*\*Files involved:\*\*

\- `src/core/repo\_parser.py` - Clone and extract repo

\- `src/core/file\_extractor.py` - Filter relevant files



\*\*Input:\*\* GitHub URL (string)

\*\*Output:\*\* List of (filename, content) tuples



\---



\### \*\*2. Semantic Chunker\*\*

\- Splits code into meaningful chunks (not just token-based)

\- Preserves context: functions, classes, imports

\- Each chunk ≤ 512 tokens (but respects code boundaries)



\*\*Why semantic?\*\*

\- Token chunking breaks functions mid-way ❌

\- Semantic chunking keeps functions intact ✅



\*\*Files involved:\*\*

\- `src/core/semantic\_chunker.py`



\*\*Input:\*\* Raw code content

\*\*Output:\*\* List of chunks with metadata (filename, line number, function name)



\---



\### \*\*3. Embedding Engine\*\*

\- Uses `sentence-transformers` (local, free)

\- Model: `all-MiniLM-L6-v2` (fast, good for code)

\- Converts text chunks → 384-dimensional vectors



\*\*Why local?\*\*

\- No API calls = fast

\- No rate limits

\- Privacy (code stays on machine)



\*\*Files involved:\*\*

\- `src/core/embedder.py`



\*\*Input:\*\* Text chunk

\*\*Output:\*\* 384-dimensional embedding vector



\---



\### \*\*4. Vector Store (ChromaDB)\*\*

\- Stores embeddings + metadata

\- Fast semantic search

\- Persistent (saved on disk)



\*\*What's stored:\*\*

{

"id": "repo\_name\_file\_123",

"embedding": \[0.1, 0.2, ..., 0.384],

"metadata": {

"filename": "payments/handler.py",

"line\_start": 45,

"line\_end": 78,

"function": "process\_payment",

"content": "def process\_payment(...)..."

}

}



\*\*Files involved:\*\*

\- `src/core/vector\_store.py`



\---



\### \*\*5. Retriever\*\*

\- User asks a question

\- Question gets embedded (same model as chunks)

\- Search ChromaDB for top 5 similar chunks

\- Return with similarity scores



\*\*Files involved:\*\*

\- `src/core/retriever.py`



\*\*Input:\*\* User question (string)

\*\*Output:\*\* Top 5 chunks with scores + metadata



\---



\### \*\*6. LLM Synthesizer\*\*

\- Takes retrieved chunks + user question

\- Sends to GPT-4 with context window

\- GPT-4 generates answer + cites sources



\*\*Prompt structure:\*\*

Context from codebase:

\[Top 5 chunks inserted here]

User Question: \[question]

Answer with:



Clear explanation

Exact citations (filename:line\_number)

Code examples if relevant





\*\*Files involved:\*\*

\- `src/core/synthesizer.py`



\*\*Input:\*\* Question + Retrieved chunks

\*\*Output:\*\* Answer + Citations



\---



\### \*\*7. API Layer (FastAPI)\*\*

\- HTTP endpoint: POST `/query`

\- Input validation

\- Error handling

\- Response formatting



\*\*Endpoints:\*\*

POST /upload

Input: GitHub URL

Output: {status, repo\_id, indexed\_files\_count}

POST /query

Input: {repo\_id, question}

Output: {answer, citations, confidence, latency\_ms}

GET /health

Output: {status, db\_connected}



\*\*Files involved:\*\*

\- `src/api/main.py`

\- `src/api/routes.py`

\- `src/api/schemas.py`



\---



\## Data Flow



\### \*\*Scenario 1: User Uploads a Repo\*\*

GitHub URL ("https://github.com/user/repo")

↓

\[repo\_parser.py] Clone repo locally

↓

\[file\_extractor.py] Extract .py, .md, .txt files

↓

\[semantic\_chunker.py] Split into 512-token chunks

↓

\[embedder.py] Generate embeddings for each chunk

↓

\[vector\_store.py] Store in ChromaDB

↓

Response: "Indexed 42 files, 1,234 chunks"



\---



\### \*\*Scenario 2: User Asks a Question\*\*

User: "How does authentication work?"

↓

\[synthesizer.py] Embed the question

↓

\[retriever.py] Search ChromaDB (top 5 chunks)

↓

\[synthesizer.py] Build prompt with chunks + question

↓

\[GPT-4 API] Call OpenAI API

↓

\[synthesizer.py] Parse response + extract citations

↓

Response:

{

"answer": "Authentication is handled in auth\_module.py...",

"citations": \[

"auth\_module.py:23-45",

"user\_service.py:78-92"

],

"confidence": 0.92,

"latency\_ms": 1850

}



\---



\## File Structure (Final)

src/

├── core/

│   ├── init.py

│   ├── repo\_parser.py        # Clone \& extract repos

│   ├── file\_extractor.py     # Filter files

│   ├── semantic\_chunker.py   # Split code intelligently

│   ├── embedder.py           # Generate embeddings

│   ├── vector\_store.py       # ChromaDB wrapper

│   ├── retriever.py          # Search + retrieve

│   └── synthesizer.py        # LLM + answer generation

│

├── api/

│   ├── init.py

│   ├── main.py               # FastAPI app

│   ├── routes.py             # Endpoints

│   └── schemas.py            # Pydantic models

│

└── utils/

├── init.py

├── config.py             # Configuration

├── logger.py             # Logging

└── constants.py          # Constants

data/

├── raw/                      # Downloaded repos

└── processed/                # Vector stores

tests/

├── test\_chunker.py

├── test\_retriever.py

└── test\_synthesizer.py

deployment/

├── Dockerfile

└── docker-compose.yml

docs/

├── API.md

└── DEPLOYMENT.md



\---



\## Tech Stack Decisions



| Layer | Technology | Reasoning |

|-------|-----------|-----------|

| \*\*Code Parsing\*\* | GitPython + AST | Standard Python tools |

| \*\*Chunking\*\* | Custom semantic (respects functions) | Better than token chunking |

| \*\*Embeddings\*\* | sentence-transformers | Free, local, fast |

| \*\*Vector DB\*\* | ChromaDB | No setup, persistent, fast |

| \*\*LLM\*\* | OpenAI GPT-4 | Best quality for Q\&A |

| \*\*API\*\* | FastAPI | Modern, async, auto-docs |

| \*\*Async\*\* | asyncio | Handle concurrent requests |

| \*\*Config\*\* | .env + pydantic | Secure, type-safe |



\---



\## Performance Targets



| Operation | Target | Rationale |

|-----------|--------|-----------|

| Repo upload (50 files) | <30 seconds | Accept rate |

| Chunk embedding | <100ms per chunk | Real-time indexing |

| Question retrieval | <500ms | User experience |

| LLM synthesis | <1500ms | OpenAI latency |

| \*\*Total query latency\*\* | \*\*<2 seconds\*\* | Professional |

| \*\*Cost per query\*\* | \*\*<$0.01\*\* | Business model |



\---



\## Error Handling

User Query

↓

├─ Invalid repo URL? → Return 400 + error message

├─ Repo not found? → Return 404

├─ Empty results? → Return 200 + "No relevant code found"

├─ LLM timeout? → Return 503 + error

├─ DB connection lost? → Return 500 + retry logic

└─ Success → Return 200 + answer



\---



\## Security Considerations



1\. \*\*API Keys:\*\* Store OpenAI key in `.env` (never commit)

2\. \*\*Input validation:\*\* Sanitize GitHub URLs

3\. \*\*Rate limiting:\*\* Implement on FastAPI (prevent abuse)

4\. \*\*Code privacy:\*\* Option to delete repos from vector store

5\. \*\*CORS:\*\* Restrict if deployed



\---



\## Monitoring \& Metrics



Track:

\- Queries per day

\- Average latency

\- Error rate

\- Cost per query

\- Cache hit rate



\---

