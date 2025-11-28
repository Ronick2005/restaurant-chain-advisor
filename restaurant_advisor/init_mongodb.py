import os
import ssl
import pymongo
from pymongo import MongoClient
from utils.config import MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION, MONGODB_VECTOR_COLLECTION

def init_mongodb():
    """Initialize MongoDB collections and indexes."""
    print(f"Connecting to MongoDB at {MONGODB_URI}")
    
    # Connect to MongoDB with SSL certificate verification disabled
    # This is needed when there are certificate verification issues
    client = MongoClient(MONGODB_URI, tlsAllowInvalidCertificates=True)
    db = client[MONGODB_DATABASE]
    
    # Create collections if they don't exist
    if MONGODB_COLLECTION not in db.list_collection_names():
        print(f"Creating collection: {MONGODB_COLLECTION}")
        db.create_collection(MONGODB_COLLECTION)
    
    if MONGODB_VECTOR_COLLECTION not in db.list_collection_names():
        print(f"Creating collection: {MONGODB_VECTOR_COLLECTION}")
        db.create_collection(MONGODB_VECTOR_COLLECTION)
    
    # Create text index on the documents collection
    print("Creating text index on documents collection")
    db[MONGODB_COLLECTION].create_index([("content", pymongo.TEXT)])
    
    # Create index for metadata filtering
    print("Creating metadata indexes")
    db[MONGODB_COLLECTION].create_index([
        ("metadata.source", pymongo.ASCENDING),
        ("metadata.type", pymongo.ASCENDING)
    ])
    
    print("\nMongoDB initialization complete!")
    print("\nIMPORTANT: Vector search index must be created manually in MongoDB Atlas UI:")
    print("1. Go to MongoDB Atlas dashboard")
    print("2. Navigate to your cluster > Collections > Vector Search")
    print("3. Create Index with these settings:")
    print("   - Database: restaurant_advisor")
    print("   - Collection: vectors")
    print("   - Index name: default_vector_index")
    print("   - Vector field: embedding")
    print("   - Dimension: 384 (for sentence-transformers/all-MiniLM-L6-v2)")
    print("   - Metric: cosine")
    
    print("\nYour MongoDB database is ready for use with Restaurant Advisor!")

if __name__ == "__main__":
    init_mongodb()
