# API Reference

Complete API documentation for CodeSemanticsVault backend.

---

## Base URL

```
http://localhost:8000  (Development)
https://your-backend-url.com  (Production)
```

---

## Authentication

Currently, no authentication is required. In production, add:
- API key headers
- JWT tokens
- Rate limiting per API key

---

## Endpoints

### 1. Health Check

**GET** `/`

Check if backend is running.

#### Request
```bash
curl http://localhost:8000/
```

#### Response
```json
{
  "status": "ok",
  "message": "CodeSemanticsVault API"
}
```

#### Status Code
- `200 OK` — Backend is healthy

---

### 2. Index Repository

**POST** `/index`

Clone and index a GitHub repository for querying.

#### Request

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/requests/requests",
    "collection_name": "requests"
  }'
```

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `github_url` | string | Yes | GitHub repository URL (HTTPS) |
| `collection_name` | string | No | Custom name for collection. Defaults to repo name |

#### Request Examples

**Minimal (uses repo name as collection):**
```json
{
  "github_url": "https://github.com/requests/requests"
}
```

**With custom collection name:**
```json
{
  "github_url": "https://github.com/pallets/flask",
  "collection_name": "flask_framework"
}
```

#### Response (200 OK)

```json
{
  "status": "success",
  "repository": "requests/requests",
  "collection": "requests",
  "files_indexed": 42,
  "chunks_created": 1234,
  "size_mb": 3.8
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always "success" on 200 |
| `repository` | string | GitHub org/repo name |
| `collection` | string | ChromaDB collection name |
| `files_indexed` | integer | Number of code files extracted |
| `chunks_created` | integer | Number of semantic chunks |
| `size_mb` | float | Total code size in MB |

#### Error Responses

**400 Bad Request** — Invalid URL format
```json
{
  "detail": "Invalid GitHub URL format"
}
```

**404 Not Found** — Repository doesn't exist
```json
{
  "detail": "Repository not found or private"
}
```

**500 Internal Server Error** — Indexing failed
```json
{
  "detail": "Indexing failed: [error details]"
}
```

#### Expected Duration

- **Small repos** (< 100 files): 30–60 seconds
- **Medium repos** (100–1000 files): 1–3 minutes
- **Large repos** (> 1000 files): 5–15 minutes

> **Note:** First request to a repo takes longer due to cloning. Subsequent requests use cached repo.

#### Indexed File Types

Supported extensions:
- `.py` — Python
- `.js`, `.ts`, `.jsx`, `.tsx` — JavaScript/TypeScript
- `.java` — Java
- `.cpp`, `.c` — C/C++
- `.go` — Go
- `.rs` — Rust
- `.rb` — Ruby
- `.md` — Markdown (documentation)

#### Exclusions

Automatically skipped:
- `node_modules/`, `.git/`, `__pycache__/`, `.venv/`
- Binary files (images, compiled code)
- Files larger than 1MB

---

### 3. Query Repository

**POST** `/query`

Ask a natural language question about an indexed repository.

#### Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do you make an HTTP GET request?",
    "collection_name": "requests"
  }'
```

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | Natural language question about the code |
| `collection_name` | string | Yes | Name of indexed collection to query |

#### Request Examples

**Basic query:**
```json
{
  "question": "How do you make an HTTP GET request?",
  "collection_name": "requests"
}
```

**Specific architectural question:**
```json
{
  "question": "What patterns does this project use for error handling?",
  "collection_name": "django"
}
```

**Security-focused query:**
```json
{
  "question": "Where are credentials stored in this codebase?",
  "collection_name": "myapp"
}
```

#### Response (200 OK)

```json
{
  "answer": "To make an HTTP GET request using the requests library, use the requests.get() method. It takes a URL as the first argument and optional parameters like headers, timeout, and authentication. For example: requests.get('https://httpbin.org/get'). The method returns a Response object containing the status code, headers, and response body.",
  "citations": [
    {
      "filename": "requests/api.py",
      "start_line": 45,
      "end_line": 50
    },
    {
      "filename": "requests/__init__.py",
      "start_line": 100,
      "end_line": 115
    },
    {
      "filename": "requests/models.py",
      "start_line": 200,
      "end_line": 225
    }
  ],
  "confidence": 0.87,
  "retrieved_chunks": 5
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Natural language answer to the question |
| `citations` | array | Source code locations used for answer |
| `citations[].filename` | string | Path to source file in repository |
| `citations[].start_line` | integer | Starting line number of referenced code |
| `citations[].end_line` | integer | Ending line number of referenced code |
| `confidence` | float | Confidence score [0.0–1.0] |
| `retrieved_chunks` | integer | Number of code chunks retrieved and used |

#### Confidence Score Interpretation

| Range | Meaning | Action |
|-------|---------|--------|
| 0.0–0.3 | Very Low | Answer likely hallucinated; verify with source |
| 0.3–0.6 | Medium | Answer reasonable but context may be incomplete |
| 0.6–0.9 | High | Answer well-grounded in source code |
| 0.9–1.0 | Very High | Answer highly certain |

#### Error Responses

**400 Bad Request** — Missing required field
```json
{
  "detail": "Collection not found. Use /index to index a repository first."
}
```

**404 Not Found** — Collection doesn't exist
```json
{
  "detail": "Collection 'requests' not found"
}
```

**500 Internal Server Error** — Query processing failed
```json
{
  "detail": "Query failed: [error details]"
}
```

#### Query Performance

- **Embedding**: 10–20ms (local)
- **Retrieval**: 50–150ms (vector search)
- **Synthesis**: 1.0–1.5s (GPT-4 API)
- **Total**: 1.2–1.7 seconds

#### Query Examples

**Onboarding Question:**
```
Q: What is the main entry point of this application?
A: [Answer with file paths and class names]
```

**Architecture Question:**
```
Q: How does the authentication system work?
A: [Answer explaining flow with code references]
```

**Migration Question:**
```
Q: Which files use the old API version?
A: [Answer listing files and line numbers]
```

**Learning Question:**
```
Q: How does Django handle ORM query optimization?
A: [Answer explaining internal implementation]
```

---

### 4. List Collections

**GET** `/collections`

List all indexed repositories (collections).

#### Request

```bash
curl http://localhost:8000/collections
```

#### Response (200 OK)

```json
{
  "collections": [
    "requests",
    "django",
    "flask"
  ],
  "count": 3
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `collections` | array | List of collection names |
| `count` | integer | Total number of indexed collections |

#### Error Responses

**500 Internal Server Error** — Failed to list collections
```json
{
  "detail": "Failed to list collections"
}
```

---

## Request/Response Examples

### Example 1: Index a Repository

**Request:**
```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/psf/requests"
  }'
```

**Response:**
```json
{
  "status": "success",
  "repository": "psf/requests",
  "collection": "requests",
  "files_indexed": 42,
  "chunks_created": 1234,
  "size_mb": 3.8
}
```

---

### Example 2: Query Indexed Repository

**Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do you handle authentication?",
    "collection_name": "requests"
  }'
```

**Response:**
```json
{
  "answer": "Authentication in requests is handled through the auth parameter. You can pass a tuple of (username, password) for basic authentication, or use auth handler objects like HTTPBasicAuth or HTTPDigestAuth from requests.auth. For example: requests.get('http://httpbin.org/basic-auth/user/pass', auth=('user', 'pass')). The Session object also supports setting default auth for all requests made in that session.",
  "citations": [
    {
      "filename": "requests/auth.py",
      "start_line": 1,
      "end_line": 50
    },
    {
      "filename": "requests/sessions.py",
      "start_line": 391,
      "end_line": 468
    }
  ],
  "confidence": 0.85,
  "retrieved_chunks": 5
}
```

---

### Example 3: List All Collections

**Request:**
```bash
curl http://localhost:8000/collections
```

**Response:**
```json
{
  "collections": ["requests", "django", "flask"],
  "count": 3
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Invalid input (missing fields, malformed JSON) |
| 404 | Not Found | Collection or resource doesn't exist |
| 422 | Unprocessable Entity | Request data is invalid |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Backend error |
| 503 | Service Unavailable | OpenAI API unavailable |

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Retry Strategy

For transient errors (500, 503):
1. Wait 1 second
2. Retry request
3. If fails again, wait 3 seconds
4. Retry again
5. After 3 retries, give up

```python
import requests
import time

def query_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data)
            return response
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

---

## Rate Limiting

### Limits (Current)

- **Indexing**: 1 concurrent operation
- **Queries**: Unlimited (but GPT-4 has usage limits)
- **API calls**: ~60 per minute (depends on infrastructure)

### Future Rate Limiting

When deployed, rate limits will be:
- 100 requests/minute per API key
- 10 concurrent indexing operations
- 500 queries/hour per API key

---

## Client Libraries

### Python

```python
import requests

class CodeSemanticsClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def index(self, github_url, collection_name=None):
        response = requests.post(
            f"{self.base_url}/index",
            json={
                "github_url": github_url,
                "collection_name": collection_name
            }
        )
        return response.json()
    
    def query(self, question, collection_name):
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "question": question,
                "collection_name": collection_name
            }
        )
        return response.json()
    
    def list_collections(self):
        response = requests.get(f"{self.base_url}/collections")
        return response.json()

# Usage:
client = CodeSemanticsClient()

# Index a repo
result = client.index("https://github.com/requests/requests")
print(f"Indexed {result['files_indexed']} files")

# Query it
answer = client.query(
    "How do you make a GET request?",
    "requests"
)
print(answer['answer'])
print(answer['confidence'])
```

### JavaScript

```javascript
class CodeSemanticsClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async index(githubUrl, collectionName = null) {
    const response = await fetch(`${this.baseUrl}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        github_url: githubUrl,
        collection_name: collectionName
      })
    });
    return response.json();
  }

  async query(question, collectionName) {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        collection_name: collectionName
      })
    });
    return response.json();
  }

  async listCollections() {
    const response = await fetch(`${this.baseUrl}/collections`);
    return response.json();
  }
}

// Usage:
const client = new CodeSemanticsClient();

const result = await client.index('https://github.com/requests/requests');
console.log(`Indexed ${result.files_indexed} files`);

const answer = await client.query(
  'How do you make a GET request?',
  'requests'
);
console.log(answer.answer);
```

---

## Webhooks (Future)

Planned webhook support for async indexing:

```json
{
  "event": "indexing_complete",
  "data": {
    "collection": "requests",
    "files_indexed": 42,
    "chunks_created": 1234
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## OpenAPI/Swagger

Interactive API documentation available at:

```
http://localhost:8000/docs
```

Or ReDoc (alternative UI):

```
http://localhost:8000/redoc
```

---

## Best Practices

### 1. Caching Results

Don't re-index the same repository frequently:

```python
# Good
indexed_repos = set()
if repo not in indexed_repos:
    client.index(repo)
    indexed_repos.add(repo)

# Bad (wasteful)
client.index(repo)  # Every time
```

### 2. Handling Long Responses

Some answers may be very long. Truncate for display:

```python
answer = response['answer']
truncated = answer[:500] + "..." if len(answer) > 500 else answer
```

### 3. Checking Confidence

Always validate confidence before relying on answer:

```python
if response['confidence'] < 0.5:
    print("Warning: Low confidence. Verify answer in source code.")
    print(f"Citations: {response['citations']}")
```

### 4. Following Citations

Always link to source files:

```python
for citation in response['citations']:
    github_url = f"https://github.com/user/repo/blob/main/{citation['filename']}#L{citation['start_line']}"
    print(f"See {github_url}")
```

---

## Support

For issues or questions about the API:
- Open an issue on GitHub
- Check documentation at `/docs`
- Review examples in this reference