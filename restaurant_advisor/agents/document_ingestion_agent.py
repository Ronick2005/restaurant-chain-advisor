"""
Enhanced Document Ingestion System
Processes documents from docs/ folder and embeds them into MongoDB.
Supports PDF, DOCX, TXT, and other formats with metadata extraction.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import hashlib

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pymongo import MongoClient
from utils.config import MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

class DocumentIngestionAgent:
    """
    Agent for ingesting documents from docs/ folder into MongoDB.
    Creates embeddings and maintains document metadata for retrieval.
    """
    
    def __init__(self, docs_directory: str = "docs"):
        self.docs_dir = Path(docs_directory)
        
        # MongoDB connection
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client[MONGODB_DB_NAME]
        self.collection = self.db["documents"]
        
        # Create indexes for efficient querying
        self.collection.create_index("file_hash")
        self.collection.create_index("file_path")
        self.collection.create_index([("content", "text")])
        
        # Embeddings using SentenceTransformers (all-MiniLM-L6-v2 - fast and efficient)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Supported file types
        self.supported_extensions = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.txt': TextLoader,
            '.md': TextLoader,
            '.csv': UnstructuredFileLoader,
            '.json': TextLoader
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for deduplication."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file."""
        stat = file_path.stat()
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size_bytes": stat.st_size,
            "file_extension": file_path.suffix,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_hash": self._calculate_file_hash(file_path)
        }
    
    def _load_document(self, file_path: Path) -> List[Any]:
        """Load document using appropriate loader."""
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_extensions:
            logger.warning(f"Unsupported file type: {extension}")
            return []
        
        try:
            loader_class = self.supported_extensions[extension]
            loader = loader_class(str(file_path))
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path.name}")
            return documents
        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            return []
    
    def _is_document_indexed(self, file_hash: str) -> bool:
        """Check if document is already indexed in MongoDB."""
        return self.collection.find_one({"file_hash": file_hash}) is not None
    
    def ingest_document(self, file_path: Path, category: str = "general") -> Dict[str, Any]:
        """
        Ingest a single document into MongoDB with embeddings.
        
        Args:
            file_path: Path to document file
            category: Document category (e.g., "market_research", "regulations", "reports")
            
        Returns:
            Ingestion result with statistics
        """
        logger.info(f"Ingesting document: {file_path.name}")
        
        # Extract metadata
        metadata = self._extract_metadata(file_path)
        
        # Check if already indexed
        if self._is_document_indexed(metadata["file_hash"]):
            logger.info(f"Document already indexed: {file_path.name}")
            return {
                "status": "skipped",
                "reason": "already_indexed",
                "file_name": file_path.name
            }
        
        # Load document
        documents = self._load_document(file_path)
        if not documents:
            return {
                "status": "failed",
                "reason": "load_error",
                "file_name": file_path.name
            }
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Create embeddings and store
        ingested_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = self.embeddings.embed_query(chunk.page_content)
                
                # Prepare document for MongoDB
                doc = {
                    **metadata,
                    "chunk_id": i,
                    "content": chunk.page_content,
                    "embedding": embedding,
                    "category": category,
                    "page_number": chunk.metadata.get("page", i),
                    "total_chunks": len(chunks),
                    "ingested_at": datetime.now().isoformat(),
                    "agent": "document_ingestion"
                }
                
                ingested_chunks.append(doc)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {e}")
                continue
        
        # Insert into MongoDB
        if ingested_chunks:
            self.collection.insert_many(ingested_chunks)
            logger.info(f"Ingested {len(ingested_chunks)} chunks from {file_path.name}")
        
        return {
            "status": "success",
            "file_name": file_path.name,
            "chunks_ingested": len(ingested_chunks),
            "total_chunks": len(chunks),
            "category": category,
            "file_size_bytes": metadata["file_size_bytes"]
        }
    
    def ingest_directory(self, directory: Optional[Path] = None, category: str = "general") -> Dict[str, Any]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory: Directory path (defaults to self.docs_dir)
            category: Category for all documents in directory
            
        Returns:
            Summary of ingestion operation
        """
        if directory is None:
            directory = self.docs_dir
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {
                "status": "failed",
                "reason": "directory_not_found",
                "directory": str(directory)
            }
        
        logger.info(f"Ingesting documents from: {directory}")
        
        results = {
            "directory": str(directory),
            "total_files": 0,
            "successful": 0,
            "skipped": 0,
            "failed": 0,
            "total_chunks": 0,
            "files_processed": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Process all files
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                results["total_files"] += 1
                
                # Determine category from subdirectory
                relative_path = file_path.relative_to(directory)
                if len(relative_path.parts) > 1:
                    file_category = relative_path.parts[0]  # Use first subdirectory as category
                else:
                    file_category = category
                
                # Ingest document
                result = self.ingest_document(file_path, file_category)
                
                # Update statistics
                if result["status"] == "success":
                    results["successful"] += 1
                    results["total_chunks"] += result["chunks_ingested"]
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                
                results["files_processed"].append(result)
        
        results["completed_at"] = datetime.now().isoformat()
        
        # Store summary in MongoDB
        self.db["ingestion_logs"].insert_one(results)
        
        logger.info(f"Ingestion complete: {results['successful']} successful, {results['skipped']} skipped, {results['failed']} failed")
        
        return results
    
    def search_documents(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity.
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of relevant document chunks
        """
        logger.info(f"Searching documents: {query}")
        
        try:
            # Create query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build MongoDB query
            mongo_query = {}
            if category:
                mongo_query["category"] = category
            
            # For now, using text search (would use vector search in production)
            mongo_query["$text"] = {"$search": query}
            
            results = self.collection.find(mongo_query).limit(limit)
            
            documents = []
            for doc in results:
                doc.pop("_id", None)
                doc.pop("embedding", None)  # Remove embedding from response
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_document_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks of a specific document.
        
        Args:
            filename: Document filename
            
        Returns:
            List of document chunks
        """
        results = self.collection.find({"file_name": filename}).sort("chunk_id", 1)
        
        chunks = []
        for doc in results:
            doc.pop("_id", None)
            doc.pop("embedding", None)
            chunks.append(doc)
        
        return chunks
    
    def get_all_categories(self) -> List[str]:
        """Get list of all document categories."""
        return self.collection.distinct("category")
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Get statistics about ingested documents."""
        stats = {
            "total_documents": self.collection.distinct("file_hash").__len__(),
            "total_chunks": self.collection.count_documents({}),
            "categories": {},
            "file_types": {},
            "total_size_bytes": 0
        }
        
        # Count by category
        for category in self.get_all_categories():
            count = self.collection.count_documents({"category": category})
            stats["categories"][category] = count
        
        # Count by file type
        for ext in self.supported_extensions.keys():
            count = self.collection.count_documents({"file_extension": ext})
            if count > 0:
                stats["file_types"][ext] = count
        
        # Calculate total size
        pipeline = [
            {"$group": {"_id": "$file_hash", "size": {"$first": "$file_size_bytes"}}},
            {"$group": {"_id": None, "total": {"$sum": "$size"}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        if result:
            stats["total_size_bytes"] = result[0]["total"]
        
        return stats
    
    def refresh_all_documents(self) -> Dict[str, Any]:
        """
        Re-ingest all documents (useful after updates).
        
        Returns:
            Refresh operation summary
        """
        logger.info("Refreshing all documents")
        
        # Clear existing documents
        self.collection.delete_many({})
        logger.info("Cleared existing documents")
        
        # Re-ingest
        return self.ingest_directory()
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a document from MongoDB.
        
        Args:
            filename: Document filename to delete
            
        Returns:
            Deletion result
        """
        result = self.collection.delete_many({"file_name": filename})
        
        return {
            "status": "success" if result.deleted_count > 0 else "not_found",
            "chunks_deleted": result.deleted_count,
            "filename": filename
        }
