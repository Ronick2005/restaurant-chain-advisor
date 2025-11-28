from typing import Dict, List, Optional, Any
import os
import sys
import pymongo
from pymongo import MongoClient
# Use only the updated MongoDB Atlas Vector Search implementation
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import (
    MONGODB_URI, 
    MONGODB_DATABASE, 
    MONGODB_COLLECTION, 
    MONGODB_VECTOR_COLLECTION,
    EMBEDDING_MODEL
)

class SentenceTransformerEmbeddings(Embeddings):
    """Sentence Transformer embeddings wrapper for LangChain."""
    
    def __init__(self, model_name=EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        return self.model.encode(texts).tolist()
        
    def embed_query(self, text: str) -> List[float]:
        """Embed a query."""
        return self.model.encode(text).tolist()

class MongoKnowledgeBase:
    """MongoDB-based knowledge base with vector search capabilities."""
    
    def __init__(self):
        # Connect to MongoDB with SSL certificate verification disabled
        # This is needed when there are certificate verification issues
        self.client = MongoClient(MONGODB_URI, tlsAllowInvalidCertificates=True)
        self.db = self.client[MONGODB_DATABASE]
        self.collection = self.db[MONGODB_COLLECTION]
        self.vector_collection = self.db[MONGODB_VECTOR_COLLECTION]
        
        # Initialize embeddings model
        self.embeddings = SentenceTransformerEmbeddings()
        
        # Create indexes if they don't exist
        self._create_indexes()
        
    def _create_indexes(self):
        """Create necessary indexes in MongoDB."""
        # Text index for basic search
        self.collection.create_index([("content", pymongo.TEXT)])
        
        # Index for metadata filtering
        self.collection.create_index([
            ("metadata.source", pymongo.ASCENDING),
            ("metadata.type", pymongo.ASCENDING)
        ])
        
        # Additional indexes for more specific filtering
        self.collection.create_index([("metadata.year", pymongo.DESCENDING)])
        self.collection.create_index([("metadata.topics", pymongo.ASCENDING)])
        self.collection.create_index([("metadata.city", pymongo.ASCENDING)])
        
    def store_document(self, document: Document) -> str:
        """Store a document in the knowledge base."""
        # Check for duplicates to avoid redundancy
        existing = self.collection.find_one({
            "metadata.source": document.metadata.get("source"),
            "content": document.page_content
        })
        
        if existing:
            return str(existing["_id"])
        
        # Insert document
        doc_id = self.collection.insert_one({
            "content": document.page_content,
            "metadata": document.metadata
        }).inserted_id
        
        # Calculate and store vector embedding in the vector collection
        try:
            embedding = self.embeddings.embed_query(document.page_content)
            self.vector_collection.insert_one({
                "content": document.page_content,
                "metadata": document.metadata,
                "embedding": embedding,
                "document_id": doc_id
            })
            print(f"Vector embedding stored for document {doc_id}")
        except Exception as e:
            print(f"Error storing vector embedding: {str(e)}")
        
        return str(doc_id)
        
    def store_documents(self, documents: List[Document]) -> List[str]:
        """Store multiple documents in the knowledge base."""
        return [self.store_document(doc) for doc in documents]
    
    def get_vector_store(self, user_filter: Optional[Dict] = None):
        """Get a vector store instance for semantic search."""
        # Apply user filter if provided
        index_name = "default_vector_index"  # This would be created in MongoDB Atlas UI
        
        # Create vector store with the new MongoDB Atlas Vector Search implementation
        # Note: pre_filter_pipeline is the correct parameter for filtering in the new implementation
        pre_filter = None
        if user_filter:
            pre_filter = [{"$match": user_filter}]
        
        vector_store = MongoDBAtlasVectorSearch(
            embedding=self.embeddings,
            collection=self.vector_collection,
            index_name=index_name,
            embedding_key="embedding",
            text_key="content",
            pre_filter_pipeline=pre_filter
        )
        
        return vector_store
    
    def semantic_search(self, query: str, user_filter: Optional[Dict] = None, k: int = 5) -> List[Document]:
        """Perform semantic search on the knowledge base."""
        # Get vector store with the correct pre_filter_pipeline
        vector_store = self.get_vector_store(user_filter)
        
        try:
            # Try to perform semantic search
            return vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"Error during semantic search: {str(e)}")
            # Return empty list in case of errors
            return []
    
    def hybrid_search(self, query: str, user_filter: Optional[Dict] = None, k: int = 5, 
                    reranking_factor: float = 0.5) -> List[Document]:
        """Perform hybrid search (keyword + semantic) on the knowledge base.
        
        Args:
            query: The search query
            user_filter: Optional metadata filter
            k: Number of results to return
            reranking_factor: Weight for semantic vs keyword (0.0-1.0), higher values favor semantic results
        
        Returns:
            List of document results with combined ranking
        """
        try:
            # First do a keyword search
            keyword_results = self.keyword_search(query, user_filter, k=k*2)
            
            # Then do a semantic search
            semantic_results = self.semantic_search(query, user_filter, k=k*2)
            
            # Score and combine results
            scored_results = {}
            
            # Process keyword results
            for i, doc in enumerate(keyword_results):
                doc_id = doc.metadata.get("source", "") + doc.page_content[:100]
                keyword_score = 1.0 - (i / len(keyword_results)) if keyword_results else 0
                scored_results[doc_id] = {
                    "doc": doc,
                    "keyword_score": keyword_score,
                    "semantic_score": 0.0
                }
            
            # Process semantic results
            for i, doc in enumerate(semantic_results):
                doc_id = doc.metadata.get("source", "") + doc.page_content[:100]
                semantic_score = 1.0 - (i / len(semantic_results)) if semantic_results else 0
                
                if doc_id in scored_results:
                    scored_results[doc_id]["semantic_score"] = semantic_score
                else:
                    scored_results[doc_id] = {
                        "doc": doc,
                        "keyword_score": 0.0,
                        "semantic_score": semantic_score
                    }
            
            # Calculate combined scores and rank
            for doc_id, data in scored_results.items():
                data["combined_score"] = (data["keyword_score"] * (1-reranking_factor) + 
                                          data["semantic_score"] * reranking_factor)
            
            # Sort by combined score
            ranked_results = sorted(
                scored_results.values(), 
                key=lambda x: x["combined_score"], 
                reverse=True
            )
            
            # Return the documents
            return [item["doc"] for item in ranked_results[:k]]
            
        except Exception as e:
            print(f"Error during hybrid search: {str(e)}")
            # Fall back to keyword search only if hybrid search fails
            try:
                return self.keyword_search(query, user_filter, k=k)
            except Exception as e2:
                print(f"Keyword search fallback also failed: {str(e2)}")
                return []
    
    def keyword_search(self, query: str, user_filter: Optional[Dict] = None, k: int = 5) -> List[Document]:
        """Perform keyword-based search on the knowledge base."""
        # Prepare filter
        search_filter = {"$text": {"$search": query}}
        if user_filter:
            search_filter.update(user_filter)
            
        # Execute search
        results = self.collection.find(
            search_filter
        ).sort([("score", {"$meta": "textScore"})]).limit(k)
        
        # Convert to Documents
        documents = []
        for result in results:
            # Build metadata from individual fields
            metadata = {
                "file_name": result.get("file_name", ""),
                "file_path": result.get("file_path", ""),
                "category": result.get("category", "general"),
                "chunk_id": result.get("chunk_id", 0),
                "page_number": result.get("page_number", 0)
            }
            
            doc = Document(
                page_content=result.get("content", ""),
                metadata=metadata
            )
            documents.append(doc)
            
        return documents
        
    def update_document(self, doc_id: str, document: Document) -> bool:
        """Update a document in the knowledge base."""
        result = self.collection.update_one(
            {"_id": doc_id},
            {"$set": {
                "content": document.page_content,
                "metadata": document.metadata
            }}
        )
        return result.modified_count > 0
        
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the knowledge base."""
        result = self.collection.delete_one({"_id": doc_id})
        return result.deleted_count > 0
        
    def search_by_topic(self, topic: str, k: int = 5) -> List[Document]:
        """Search documents by a specific topic in metadata."""
        results = self.collection.find(
            {"category": {"$regex": f".*{topic}.*", "$options": "i"}}
        ).limit(k)
        
        documents = []
        for r in results:
            metadata = {
                "file_name": r.get("file_name", ""),
                "category": r.get("category", "general"),
                "chunk_id": r.get("chunk_id", 0)
            }
            documents.append(Document(page_content=r["content"], metadata=metadata))
        return documents
    
    def get_document_topics(self) -> Dict[str, int]:
        """Extract all topics from document metadata and return frequency count."""
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        result = self.collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in result}
    
    def get_city_specific_insights(self, city: str, query: str = None, k: int = 5) -> List[Document]:
        """Get city-specific insights from the knowledge base."""
        filter_dict = {
            "content": {"$regex": f".*{city}.*", "$options": "i"}
        }
        
        if query:
            # If query is provided, perform semantic search with city filter
            return self.semantic_search(query, filter_dict, k)
        else:
            # Otherwise, just get documents mentioning the city
            results = self.collection.find(filter_dict).limit(k)
            documents = []
            for r in results:
                metadata = {
                    "file_name": r.get("file_name", ""),
                    "category": r.get("category", "general"),
                    "chunk_id": r.get("chunk_id", 0)
                }
                documents.append(Document(page_content=r["content"], metadata=metadata))
            return documents
            
    def get_recent_market_trends(self, year_threshold: int = 2023) -> List[Document]:
        """Get the most recent market trends from documents published after the threshold year."""
        results = self.collection.find({
            "$and": [
                {"metadata.year": {"$gte": year_threshold}},
                {"$or": [
                    {"content": {"$regex": "trend", "$options": "i"}},
                    {"content": {"$regex": "growth", "$options": "i"}},
                    {"content": {"$regex": "market analysis", "$options": "i"}},
                    {"metadata.topics": {"$regex": "market|trend|growth", "$options": "i"}}
                ]}
            ]
        }).limit(10)
        
        return [Document(page_content=r["content"], metadata=r["metadata"]) for r in results]
