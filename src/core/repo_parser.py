"""
Repository Parser
Clones GitHub repos and extracts code files
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


class RepositoryParser:
    """Parse and extract code from GitHub repositories"""
    
    def __init__(self, cache_dir: str = "data/raw/repos"):
        """
        Initialize parser
        
        Args:
            cache_dir: Directory to store cloned repos
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # File extensions to include
        self.SUPPORTED_EXTENSIONS = {
            ".py", ".md", ".txt", ".java", ".js", ".cpp", ".c",
            ".ts", ".jsx", ".tsx", ".rb", ".go", ".rs"
        }
        
        # Directories to ignore
        self.IGNORE_DIRS = {
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".env", "dist", "build", ".pytest_cache", ".vscode", ".idea"
        }
    
    def clone_repo(self, github_url: str, repo_name: str = None) -> Path:
        """
        Clone a GitHub repository
        
        Args:
            github_url: Full GitHub URL (e.g., https://github.com/user/repo)
            repo_name: Optional custom name for local folder
            
        Returns:
            Path to cloned repository
            
        Raises:
            ValueError: If URL is invalid
            GitCommandError: If cloning fails
        """
        # Validate URL
        if not github_url.startswith("https://github.com/"):
            raise ValueError("Only GitHub URLs supported (https://github.com/user/repo)")
        
        # Extract repo name from URL if not provided
        if repo_name is None:
            repo_name = github_url.split("/")[-1].replace(".git", "")
        
        repo_path = self.cache_dir / repo_name
        
        # If already cloned, use cached version
        if repo_path.exists():
            logger.info(f"Using cached repo: {repo_path}")
            return repo_path
        
        # Clone the repository
        try:
            logger.info(f"Cloning repository: {github_url}")
            Repo.clone_from(github_url, str(repo_path))
            logger.info(f"Successfully cloned to: {repo_path}")
            return repo_path
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def extract_files(self, repo_path: Path) -> List[Dict]:
        """
        Extract code files from repository
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List of dicts: {filename, content, extension, relative_path}
        """
        files = []
        repo_path = Path(repo_path)
        
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        logger.info(f"Extracting files from: {repo_path}")
        
        for file_path in repo_path.rglob("*"):
            # Skip directories
            if not file_path.is_file():
                continue
            
            # Skip ignored directories
            if any(ignored in file_path.parts for ignored in self.IGNORE_DIRS):
                continue
            
            # Check file extension
            if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
                continue
            
            try:
                # Read file content
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Get relative path for display
                relative_path = file_path.relative_to(repo_path)
                
                files.append({
                    "filename": file_path.name,
                    "relative_path": str(relative_path),
                    "content": content,
                    "extension": file_path.suffix,
                    "size_bytes": file_path.stat().st_size,
                    "line_count": len(content.split("\n"))
                })
                
                logger.debug(f"Extracted: {relative_path}")
            
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                continue
        
        logger.info(f"Extracted {len(files)} files")
        return files
    
    def get_repo_summary(self, files: List[Dict]) -> Dict:
        """
        Generate summary statistics about extracted files
        
        Args:
            files: List of extracted files
            
        Returns:
            Summary dict with statistics
        """
        total_files = len(files)
        total_lines = sum(f["line_count"] for f in files)
        total_size = sum(f["size_bytes"] for f in files)
        
        extensions = {}
        for f in files:
            ext = f["extension"]
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "extensions": extensions,
            "files": files
        }
    
    def cleanup(self, repo_name: str):
        """
        Delete a cached repository
        
        Args:
            repo_name: Name of repo folder to delete
        """
        repo_path = self.cache_dir / repo_name
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"Deleted cached repo: {repo_path}")


# Example usage (for testing)
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Test the parser
    parser = RepositoryParser()
    
    # Example: clone a small public repo
    url = "https://github.com/pallets/flask"
    try:
        repo_path = parser.clone_repo(url)
        files = parser.extract_files(repo_path)
        summary = parser.get_repo_summary(files)
        
        print(f"\n✅ Successfully extracted {summary['total_files']} files")
        print(f"Total lines: {summary['total_lines']}")
        print(f"Total size: {summary['total_size_mb']} MB")
        print(f"Extensions: {summary['extensions']}")
    except Exception as e:
        print(f"❌ Error: {e}")