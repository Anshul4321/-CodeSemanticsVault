"""
End-to-end test of CodeSemanticsVault
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import logging
from src.core.pipeline import RAGPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Check API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ERROR: OPENAI_API_KEY not found in .env")
    print("Please add: OPENAI_API_KEY=sk-xxx to .env file")
    exit(1)

print("✅ API Key loaded\n")
print("🚀 Initializing CodeSemanticsVault...\n")

try:
    pipeline = RAGPipeline()
    print("✅ Pipeline initialized\n")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("=" * 60)
print("STEP 1: Indexing Repository")
print("=" * 60)

repo_url = "https://github.com/requests/requests"
print(f"\nIndexing: {repo_url}")
print("(This may take 2-3 minutes on first run...)\n")

try:
    summary = pipeline.index_repository(
        github_url=repo_url,
        collection_name="requests_lib"
    )
    
    print(f"\n✅ Indexing Complete!")
    print(f"   Files indexed: {summary['files_indexed']}")
    print(f"   Chunks created: {summary['chunks_created']}")
    print(f"   Repository size: {summary['size_mb']} MB")
except Exception as e:
    print(f"❌ Indexing failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("STEP 2: Asking Questions")
print("=" * 60)

questions = [
    "How do you make a basic HTTP GET request?",
    "What is the Session object used for?"
]

try:
    for i, question in enumerate(questions, 1):
        print(f"\n{'─' * 60}")
        print(f"Question {i}: {question}")
        print('─' * 60)
        
        result = pipeline.query(
            question=question,
            collection_name="requests_lib"
        )
        
        print(f"\n📝 Answer:")
        print(result['answer'])
        
        if result.get('citations'):
            print(f"\n📍 Source files:")
            for citation in result['citations']:
                print(f"   • {citation['filename']}:{citation['start_line']}")
        
        if result.get('confidence'):
            print(f"\n✅ Confidence score: {result['confidence']}")
        
        print(f"🔍 Retrieved chunks: {result['retrieved_chunks']}")

except Exception as e:
    print(f"❌ Query failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ SYSTEM TEST COMPLETE!")
print("=" * 60)
print("\nYour RAG system is working! 🎉")