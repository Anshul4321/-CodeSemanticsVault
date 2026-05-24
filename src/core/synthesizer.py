"""
LLM Synthesizer
Generates answers from retrieved chunks using GPT-4
"""

import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class Synthesizer:
    """
    Synthesizes answers from retrieved code chunks using GPT-4.
    Generates grounded answers with source citations.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.3
    ):
        """
        Initialize synthesizer
        
        Args:
            api_key: OpenAI API key (uses env var if None)
            model: GPT model to use
            temperature: Creativity level (0-1, lower = more deterministic)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        
        logger.info(f"✅ Synthesizer initialized with {model}")
    
    def _build_context_string(self, chunks: List[Dict]) -> str:
        """
        Build context string from retrieved chunks
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant code found."
        
        context = "# Retrieved Code Context\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.get("filename", "unknown")
            start_line = chunk.get("start_line", 0)
            end_line = chunk.get("end_line", 0)
            content = chunk.get("content", "")
            similarity = chunk.get("similarity", 0)
            
            context += f"## Source {i}: {filename}:{start_line}-{end_line}\n"
            context += f"(Relevance: {similarity:.2%})\n"
            context += f"```\n{content}\n```\n\n"
        
        return context
    
    def synthesize(
        self,
        query: str,
        chunks: List[Dict],
        include_confidence: bool = True
    ) -> Dict:
        """
        Generate answer from retrieved chunks
        
        Args:
            query: User's question
            chunks: Retrieved code chunks
            include_confidence: Include confidence score in response
            
        Returns:
            Dict with answer, citations, and metadata
        """
        try:
            logger.info(f"Synthesizing answer for: '{query}'")
            
            # Build context
            context = self._build_context_string(chunks)
            
            # Build prompt
            prompt = self._build_prompt(query, context, include_confidence)
            
            # Call GPT-4
            logger.debug(f"Calling {self.model}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code expert. Answer questions about code with exact source citations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # Extract citations from answer
            citations = self._extract_citations(chunks, answer)
            
            # Calculate confidence
            confidence = self._calculate_confidence(chunks, answer)
            
            result = {
                "answer": answer,
                "citations": citations,
                "confidence": round(confidence, 3) if include_confidence else None,
                "retrieved_chunks": len(chunks),
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            logger.info(f"✅ Generated answer ({len(answer)} chars)")
            return result
        
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "retrieved_chunks": 0,
                "error": str(e)
            }
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        include_confidence: bool
    ) -> str:
        """Build the prompt for GPT-4"""
        
        confidence_instruction = (
            "\n\nEnd your response with a confidence score (0-1) on a new line "
            "indicating how confident you are in this answer based on the code provided."
        ) if include_confidence else ""
        
        prompt = f"""You are analyzing source code to answer a question.

Question: {query}

{context}

Please answer the question based ONLY on the provided code context. 
Include specific file and line number citations for any code you reference.
Format citations as "filename:line_number".

If the provided code doesn't contain information to answer the question, say so clearly.
Be concise and technical in your response.{confidence_instruction}"""
        
        return prompt
    
    def _extract_citations(self, chunks: List[Dict], answer: str) -> List[Dict]:
        """
        Extract file citations from answer
        
        Args:
            chunks: Original chunks
            answer: Generated answer
            
        Returns:
            List of cited chunks
        """
        citations = []
        
        for chunk in chunks:
            filename = chunk.get("filename", "")
            start_line = chunk.get("start_line", 0)
            
            # Check if this file/line is mentioned in answer
            citation_str = f"{filename}:{start_line}"
            if citation_str in answer:
                citations.append({
                    "filename": filename,
                    "start_line": start_line,
                    "end_line": chunk.get("end_line", 0),
                    "context": chunk.get("context", "")
                })
        
        return citations
    
    def _calculate_confidence(self, chunks: List[Dict], answer: str) -> float:
        """
        Calculate confidence score for answer
        
        Args:
            chunks: Retrieved chunks
            answer: Generated answer
            
        Returns:
            Confidence score (0-1)
        """
        if not chunks:
            return 0.0
        
        # Average similarity of retrieved chunks
        similarities = [chunk.get("similarity", 0) for chunk in chunks]
        retrieval_score = sum(similarities) / len(similarities) if similarities else 0
        
        # Check if answer references the retrieved code
        citation_score = 0.0
        if chunks:
            for chunk in chunks:
                if chunk.get("filename", "") in answer:
                    citation_score += 1
            citation_score = citation_score / len(chunks)
        
        # Combined score: 60% retrieval quality, 40% citation rate
        confidence = (retrieval_score * 0.6) + (citation_score * 0.4)
        
        return confidence
    
    def synthesize_batch(
        self,
        queries: List[str],
        retrieved_results: List[List[Dict]]
    ) -> List[Dict]:
        """
        Synthesize answers for multiple queries
        
        Args:
            queries: List of queries
            retrieved_results: List of retrieved chunk lists (one per query)
            
        Returns:
            List of synthesized answers
        """
        logger.info(f"Batch synthesizing {len(queries)} queries")
        
        results = []
        for query, chunks in zip(queries, retrieved_results):
            result = self.synthesize(query, chunks)
            results.append(result)
        
        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize synthesizer
    synthesizer = Synthesizer()
    
    # Sample retrieved chunks
    sample_chunks = [
        {
            "filename": "auth.py",
            "start_line": 10,
            "end_line": 20,
            "content": "def authenticate(user, password):\n    if validate_password(user, password):\n        return generate_token(user)\n    return None",
            "similarity": 0.92,
            "context": "authenticate"
        },
        {
            "filename": "auth.py",
            "start_line": 25,
            "end_line": 35,
            "content": "def validate_password(user, pwd):\n    hashed = hash_password(pwd)\n    return user.password_hash == hashed",
            "similarity": 0.88,
            "context": "validate_password"
        }
    ]
    
    # Test synthesization
    query = "How does user authentication work?"
    
    print(f"\n🤖 Query: {query}\n")
    
    result = synthesizer.synthesize(query, sample_chunks)
    
    print(f"Answer:\n{result['answer']}\n")
    print(f"Citations: {result['citations']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Tokens used: {result['usage']['total_tokens']}")