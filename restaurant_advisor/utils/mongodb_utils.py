"""
MongoDB utilities for the restaurant advisor system.
"""

import pymongo
from typing import Dict, Any, List, Optional, Union

class MongoDB:
    """MongoDB connection and utility methods."""
    
    def __init__(self, uri: str, db_name: str):
        """Initialize MongoDB connection.
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document into a collection.
        
        Args:
            collection_name: Name of the collection
            document: Document to insert
            
        Returns:
            ID of the inserted document
        """
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents into a collection.
        
        Args:
            collection_name: Name of the collection
            documents: Documents to insert
            
        Returns:
            List of IDs of the inserted documents
        """
        collection = self.db[collection_name]
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Document if found, None otherwise
        """
        collection = self.db[collection_name]
        return collection.find_one(query)
    
    def find_many(self, collection_name: str, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        collection = self.db[collection_name]
        return list(collection.find(query).limit(limit))
    
    def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update a single document in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            update: Update operations
            
        Returns:
            Number of documents modified
        """
        collection = self.db[collection_name]
        result = collection.update_one(query, update)
        return result.modified_count
    
    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Delete a single document in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Number of documents deleted
        """
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count
    
    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents in a collection.
        
        Args:
            collection_name: Name of the collection
            query: Query filter
            
        Returns:
            Number of documents deleted
        """
        collection = self.db[collection_name]
        result = collection.delete_many(query)
        return result.deleted_count
    
    def has_index(self, collection_name: str, index_name: str) -> bool:
        """Check if an index exists in a collection.
        
        Args:
            collection_name: Name of the collection
            index_name: Name of the index
            
        Returns:
            True if index exists, False otherwise
        """
        collection = self.db[collection_name]
        indexes = collection.list_indexes()
        return any(index_name == idx.get("name") for idx in indexes)
    
    def create_vector_search_index(
        self,
        collection_name: str,
        index_name: str,
        text_field: str,
        dimensions: int = 1536
    ) -> None:
        """Create a vector search index on a collection.
        
        Args:
            collection_name: Name of the collection
            index_name: Name of the index
            text_field: Field containing text to be embedded
            dimensions: Dimensionality of embeddings
        """
        collection = self.db[collection_name]
        
        # Define index with Atlas Vector Search
        index_definition = {
            "mappings": {
                "dynamic": True,
                "fields": {
                    text_field: {
                        "type": "knnVector",
                        "dimensions": dimensions,
                        "similarity": "cosine"
                    }
                }
            }
        }
        
        # Create the index
        collection.create_search_index(index_name, index_definition)
        
    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection from the database.
        
        Args:
            collection_name: Name of the collection
        """
        self.db.drop_collection(collection_name)
        
    def close(self) -> None:
        """Close MongoDB connection."""
        self.client.close()
