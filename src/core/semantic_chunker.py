"""
Semantic Chunker
Intelligently splits code while respecting boundaries (functions, classes, etc.)
"""

import re
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Split code into meaningful chunks while preserving context.
    Respects function/class boundaries instead of just splitting by tokens.
    """
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target chunk size in tokens (approximate)
            overlap: Overlap between chunks in lines (for context)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_python(self, content: str, filename: str = "") -> List[Dict]:
        """
        Chunk Python code semantically
        
        Args:
            content: Python source code
            filename: Filename (for metadata)
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        lines = content.split("\n")
        
        if not lines:
            return chunks
        
        current_chunk = []
        current_start_line = 0
        token_count = 0
        in_multiline = False
        multiline_delimiter = None
        
        for i, line in enumerate(lines):
            # Track multiline strings
            if '"""' in line or "'''" in line:
                delimiter = '"""' if '"""' in line else "'''"
                if not in_multiline:
                    in_multiline = True
                    multiline_delimiter = delimiter
                elif multiline_delimiter == delimiter:
                    in_multiline = False
            
            # Estimate tokens (rough: ~4 chars per token)
            line_tokens = max(1, len(line) // 4)
            
            # Check if we should start a new chunk
            is_boundary = (
                line.strip().startswith("def ") or
                line.strip().startswith("class ") or
                line.strip().startswith("async def ")
            )
            
            # Start new chunk at boundary if current is large enough
            if is_boundary and token_count > self.chunk_size // 2 and current_chunk:
                chunk = self._create_chunk(
                    current_chunk, filename, current_start_line, i
                )
                chunks.append(chunk)
                
                # Add overlap (previous lines for context)
                overlap_lines = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_lines.copy()
                current_start_line = max(0, i - len(overlap_lines))
                token_count = sum(max(1, len(l) // 4) for l in overlap_lines)
            
            current_chunk.append(line)
            token_count += line_tokens
            
            # Force chunk if too large
            if token_count > self.chunk_size:
                chunk = self._create_chunk(
                    current_chunk, filename, current_start_line, i
                )
                chunks.append(chunk)
                
                # Reset with overlap
                overlap_lines = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_lines.copy()
                current_start_line = max(0, i - len(overlap_lines))
                token_count = sum(max(1, len(l) // 4) for l in overlap_lines)
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, filename, current_start_line, len(lines)
            )
            chunks.append(chunk)
        
        logger.info(f"Chunked {filename}: {len(chunks)} chunks from {len(lines)} lines")
        return chunks
    
    def chunk_generic(self, content: str, filename: str = "") -> List[Dict]:
        """
        Generic chunking for non-Python files (markdown, txt, etc.)
        
        Args:
            content: File content
            filename: Filename (for metadata)
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        lines = content.split("\n")
        
        current_chunk = []
        current_start_line = 0
        token_count = 0
        
        for i, line in enumerate(lines):
            line_tokens = max(1, len(line) // 4)
            
            # For markdown, break at headers
            is_boundary = line.strip().startswith("#")
            
            if is_boundary and token_count > self.chunk_size // 2 and current_chunk:
                chunk = self._create_chunk(
                    current_chunk, filename, current_start_line, i
                )
                chunks.append(chunk)
                current_chunk = []
                current_start_line = i
                token_count = 0
            
            current_chunk.append(line)
            token_count += line_tokens
            
            if token_count > self.chunk_size:
                chunk = self._create_chunk(
                    current_chunk, filename, current_start_line, i
                )
                chunks.append(chunk)
                current_chunk = []
                current_start_line = i + 1
                token_count = 0
        
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, filename, current_start_line, len(lines)
            )
            chunks.append(chunk)
        
        logger.info(f"Chunked {filename}: {len(chunks)} chunks from {len(lines)} lines")
        return chunks
    
    def chunk_file(self, filename: str, content: str) -> List[Dict]:
        """
        Intelligently chunk a file based on extension
        
        Args:
            filename: File name with extension
            content: File content
            
        Returns:
            List of chunks
        """
        ext = Path(filename).suffix.lower()
        
        if ext == ".py":
            return self.chunk_python(content, filename)
        else:
            return self.chunk_generic(content, filename)
    
    def _create_chunk(
        self, 
        lines: List[str], 
        filename: str, 
        start_line: int, 
        end_line: int
    ) -> Dict:
        """
        Create a chunk dictionary with metadata
        
        Args:
            lines: List of lines in chunk
            filename: Source filename
            start_line: Starting line number
            end_line: Ending line number
            
        Returns:
            Chunk dictionary with content and metadata
        """
        content = "\n".join(lines)
        
        # Extract function/class name if present
        context = ""
        for line in lines:
            if line.strip().startswith("def "):
                context = re.search(r"def\s+(\w+)", line)
                context = context.group(1) if context else "function"
                break
            elif line.strip().startswith("class "):
                context = re.search(r"class\s+(\w+)", line)
                context = context.group(1) if context else "class"
                break
        
        return {
            "filename": filename,
            "content": content,
            "start_line": start_line,
            "end_line": end_line,
            "line_count": len(lines),
            "context": context,  # function/class name for reference
            "token_count": max(1, len(content) // 4)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Test with a sample Python function
    sample_code = '''
def calculate_total(items):
    """Calculate total from items"""
    total = 0
    for item in items:
        if item.get("price"):
            total += item["price"]
    return total

class PaymentProcessor:
    """Handle payment processing"""
    def __init__(self, api_key):
        self.api_key = api_key
    
    def process(self, amount):
        """Process payment"""
        return {"status": "success", "amount": amount}
'''
    
    chunker = SemanticChunker(chunk_size=256, overlap=2)
    chunks = chunker.chunk_python(sample_code, "example.py")
    
    print(f"\n✅ Created {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Lines: {chunk['start_line']}-{chunk['end_line']}")
        print(f"  Context: {chunk['context']}")
        print(f"  Tokens: {chunk['token_count']}")
        print(f"  Preview: {chunk['content'][:60]}...\n")