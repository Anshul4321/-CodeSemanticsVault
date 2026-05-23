# CodeSemanticsVault

Semantic intelligence vault orchestrating code cognition at scale. Fuses vector 
retrieval, embeddings, and synthesis for architectural clarity across polyglot 
repositories. Enterprise-optimized: <2 second latency, <$0.01 cost, 80%+ 
accuracy on 100K+ LOC codebases with provenance and cloud deployment.

---

## 🎯 What This Does

Ask natural language questions about any GitHub repository and get answers with 
exact source citations (file:line number).

**Example:**
Q: "How does the authentication module work?"
A: "Authentication is handled in auth/handler.py (lines 45-78) using JWT tokens.
The token validation happens in middleware/auth.py (lines 23-35)..."

---

## 🏗️ Architecture
GitHub Repo URL
↓
[Repository Parser] - Clone & extract code
↓
[Semantic Chunker] - Split code intelligently
↓
[Embedder] - Generate semantic vectors
↓
[Vector Store] - ChromaDB (persistent)
↓
[User Question] → [Retriever] → Top 5 chunks
↓
[LLM Synthesizer] (GPT-4) → Answer + Citations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/CodeSemanticsVault.git
cd CodeSemanticsVault

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Usage

```python
from src.core.repo_parser import RepositoryParser

# Initialize parser
parser = RepositoryParser()

# Clone a repository
repo_path = parser.clone_repo("https://github.com/pallets/flask")

# Extract files
files = parser.extract_files(repo_path)

# View summary
summary = parser.get_repo_summary(files)
print(f"Extracted {summary['total_files']} files")
```

---

## 📊 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Query Latency | <2 seconds | 🔨 In Progress |
| Cost per Query | <$0.01 | 🔨 In Progress |
| Retrieval Accuracy | >80% | 🔨 In Progress |
| Support Repo Size | 100K+ LOC | ✅ Designed |

---

## 🧪 Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_repo_parser.py -v
```

---

## 📁 Project Structure
src/
├── core/              # RAG pipeline components
│   ├── repo_parser.py       # Clone & extract repos
│   ├── semantic_chunker.py  # Intelligent chunking
│   ├── embedder.py          # Embedding generation
│   ├── vector_store.py      # ChromaDB wrapper
│   ├── retriever.py         # Semantic search
│   └── synthesizer.py       # LLM answer generation
├── api/               # FastAPI application
│   ├── main.py
│   ├── routes.py
│   └── schemas.py
└── utils/             # Utilities
├── config.py      # Configuration management
├── logger.py
└── constants.py
tests/                 # Unit tests
deployment/           # Docker & deployment files
docs/                 # Architecture & guides

---

## 🔄 Development Phases

- [x] **Phase 1:** Repository Parser & File Extraction
- [ ] **Phase 2:** Semantic Chunker
- [ ] **Phase 3:** Embedding Engine
- [ ] **Phase 4:** Vector Store Integration
- [ ] **Phase 5:** Retriever & Search
- [ ] **Phase 6:** LLM Synthesizer
- [ ] **Phase 7:** FastAPI Layer
- [ ] **Phase 8:** Evaluation & Benchmarking
- [ ] **Phase 9:** Deployment (GCP/Railway)

---

## 🎓 Key Technologies

- **Vector Embeddings:** `sentence-transformers` (all-MiniLM-L6-v2)
- **Vector DB:** ChromaDB (open-source, no vendor lock-in)
- **LLM:** OpenAI GPT-4
- **Framework:** LangChain
- **Web API:** FastAPI
- **Repository Management:** GitPython

---

## 📈 Evaluation Methodology

**Retrieval Accuracy:** Does the system find the relevant code?
- Measured on benchmark dataset
- Top-5 retrieval rate

**Synthesis Quality:** Are answers grounded in code?
- Expert review (4/5 usefulness target)
- Citation accuracy

**Performance:** Is it fast enough for production?
- Latency per query
- Cost per query
- Scalability to 100K+ LOC

---

## 🛠️ Configuration

All settings in `.env`:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
CHROMADB_PATH=data/processed/chromadb
CHUNK_SIZE=512
API_PORT=8000
LOG_LEVEL=INFO

See `.env.example` for all available options.

---

## 📚 Documentation

- [Architecture Design](./docs/architecture.md) - System design & data flow
- [API Documentation](./docs/API.md) - Endpoint specs (coming soon)
- [Deployment Guide](./docs/DEPLOYMENT.md) - Production setup (coming soon)

---

## 📊 Project Goals

This project demonstrates:
- ✅ Production RAG system implementation
- ✅ Semantic search at scale
- ✅ Multi-component system architecture
- ✅ Professional Python engineering
- ✅ LLM integration and prompt engineering
- ✅ Vector database operations
- ✅ API design and deployment

**Perfect for:** AI/ML roles, backend engineering, consulting (Accenture, etc.)

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) (coming soon)

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file

---

## 👤 Author

Anshul Gupta
GitHub: [@Anshul4321](https://github.com/Anshul4321)

---

## 🔗 Links

- [Architecture Document](./docs/architecture.md)
- [Problem Definition](./problem_definition.md)

---

**Last Updated:** May 2026  
**Status:** 🔨 Active Development