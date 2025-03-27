import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredImageLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

class DocumentManager:
    def __init__(
        self,
        base_path: str,
        openai_api_key: str,
        collection_name: str = "agentforge"
    ):
        self.base_path = base_path
        self.collection_name = collection_name
        self.metadata_file = os.path.join(base_path, "vectordb", f"{collection_name}_metadata.json")
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vectordb = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=os.path.join(base_path, "vectordb")
        )
        
        # Initialize file type handlers
        self.file_handlers = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".jpg": UnstructuredImageLoader,
            ".jpeg": UnstructuredImageLoader,
            ".png": UnstructuredImageLoader
        }
        
        # Load metadata
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def _save_metadata(self):
        """Save metadata to file"""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file contents"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    async def process_file(
        self,
        file_path: str,
        assistant_name: str
    ) -> Dict[str, Any]:
        """Process a single file and add to vector store"""
        try:
            # Check if file type is supported
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.file_handlers:
                return {
                    "status": "error",
                    "error": f"Unsupported file type: {file_ext}"
                }
                
            # Check if file has changed
            file_hash = self._compute_file_hash(file_path)
            file_key = f"{assistant_name}:{file_path}"
            
            if file_key in self.metadata and self.metadata[file_key]["hash"] == file_hash:
                return {
                    "status": "unchanged",
                    "message": "File unchanged since last processing"
                }
                
            # Load and split document
            loader = self.file_handlers[file_ext](file_path)
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            # Add assistant name to metadata
            for split in splits:
                split.metadata["assistant"] = assistant_name
            
            # Add to vector store
            self.vectordb.add_documents(splits)
            
            # Update metadata
            self.metadata[file_key] = {
                "hash": file_hash,
                "last_processed": os.path.getmtime(file_path),
                "num_chunks": len(splits)
            }
            self._save_metadata()
            
            return {
                "status": "success",
                "chunks_processed": len(splits)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def process_directory(
        self,
        dir_path: str,
        assistant_name: str
    ) -> Dict[str, Any]:
        """Process all supported files in directory"""
        stats = {
            "processed": 0,
            "unchanged": 0,
            "errors": 0,
            "error_files": []
        }
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                result = await self.process_file(file_path, assistant_name)
                
                if result["status"] == "success":
                    stats["processed"] += 1
                elif result["status"] == "unchanged":
                    stats["unchanged"] += 1
                else:
                    stats["errors"] += 1
                    stats["error_files"].append({
                        "file": file_path,
                        "error": result.get("error", "Unknown error")
                    })
                    
        return stats
        
    async def query_documents(
        self,
        query: str,
        assistant_name: Optional[str] = None,
        file_types: Optional[List[str]] = None,
        num_results: int = 5
    ) -> List[Any]:
        """Query vector store for relevant documents"""
        # Prepare filter based on assistant name and file types
        filter_dict = {}
        if assistant_name:
            filter_dict["assistant"] = assistant_name
            
        if file_types:
            filter_dict["source"] = {
                "$or": [
                    {"$endswith": ext}
                    for ext in file_types
                ]
            }
            
        # Query vector store
        docs = self.vectordb.similarity_search(
            query,
            k=num_results,
            filter=filter_dict if filter_dict else None
        )
        
        return docs
        
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        stats = {
            "total_files": len(self.metadata),
            "total_chunks": sum(
                meta["num_chunks"]
                for meta in self.metadata.values()
            ),
            "by_assistant": {},
            "by_type": {}
        }
        
        for file_key, meta in self.metadata.items():
            assistant = file_key.split(":")[0]
            file_type = os.path.splitext(file_key.split(":")[1])[1]
            
            # Update assistant stats
            if assistant not in stats["by_assistant"]:
                stats["by_assistant"][assistant] = {
                    "files": 0,
                    "chunks": 0
                }
            stats["by_assistant"][assistant]["files"] += 1
            stats["by_assistant"][assistant]["chunks"] += meta["num_chunks"]
            
            # Update file type stats
            if file_type not in stats["by_type"]:
                stats["by_type"][file_type] = {
                    "files": 0,
                    "chunks": 0
                }
            stats["by_type"][file_type]["files"] += 1
            stats["by_type"][file_type]["chunks"] += meta["num_chunks"]
            
        return stats 