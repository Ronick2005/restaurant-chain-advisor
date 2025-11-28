"""
Script to store PDF extracted data in MongoDB for vector search.
This allows the advisor system to search through PDF content semantically.
"""

import os
import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mongodb_utils import MongoDB
from utils.config import MONGODB_URI, MONGODB_DB_NAME

def create_pdf_vector_collection(pdf_data: Dict[str, Any]) -> None:
    """Create MongoDB collection with PDF extracted data for vector search.
    
    Args:
        pdf_data: Dictionary with extracted PDF data
    """
    print("Creating MongoDB collection for PDF data...")
    
    # Connect to MongoDB
    mongodb = MongoDB(MONGODB_URI, MONGODB_DB_NAME)
    
    # Prepare documents for insertion
    documents = []
    
    # Process each PDF and create documents
    for pdf_name, data in pdf_data.items():
        # Skip PDFs with errors
        if "error" in data:
            print(f"  Skipping {pdf_name} due to error: {data['error']}")
            continue
        
        # Create a document for regulations
        if "regulations" in data and data["regulations"]:
            for category, items in data["regulations"].items():
                for item in items:
                    doc = {
                        "pdf_name": pdf_name,
                        "content_type": f"regulation_{category}",
                        "text": item,
                        "metadata": {
                            "source": pdf_name,
                            "category": category,
                            "type": "regulation"
                        }
                    }
                    documents.append(doc)
        
        # Create documents for consumer preferences
        if "consumer_preferences" in data and data["consumer_preferences"]:
            for category, items in data["consumer_preferences"].items():
                for item in items:
                    doc = {
                        "pdf_name": pdf_name,
                        "content_type": f"preference_{category}",
                        "text": item,
                        "metadata": {
                            "source": pdf_name,
                            "category": category,
                            "type": "consumer_preference"
                        }
                    }
                    documents.append(doc)
        
        # Create documents for real estate info
        if "real_estate" in data and data["real_estate"]:
            for category, items in data["real_estate"].items():
                for item in items:
                    doc = {
                        "pdf_name": pdf_name,
                        "content_type": f"realestate_{category}",
                        "text": item,
                        "metadata": {
                            "source": pdf_name,
                            "category": category,
                            "type": "real_estate"
                        }
                    }
                    documents.append(doc)
        
        # Create documents for city-specific info
        if "city_specific" in data and data["city_specific"]:
            for city, items in data["city_specific"].items():
                for item in items:
                    doc = {
                        "pdf_name": pdf_name,
                        "content_type": "city_info",
                        "text": item,
                        "metadata": {
                            "source": pdf_name,
                            "city": city,
                            "type": "city_specific"
                        }
                    }
                    documents.append(doc)
    
    # Insert documents into MongoDB
    if documents:
        collection_name = "pdf_extracted_data"
        mongodb.insert_many(collection_name, documents)
        print(f"  Inserted {len(documents)} documents into {collection_name} collection")
        
        # Create vector search index if it doesn't exist
        index_name = "vector_index"
        if not mongodb.has_index(collection_name, index_name):
            mongodb.create_vector_search_index(
                collection_name=collection_name,
                index_name=index_name,
                text_field="text",
                dimensions=1536  # Default for OpenAI embeddings
            )
            print(f"  Created vector search index '{index_name}' on collection '{collection_name}'")
    else:
        print("  No documents to insert")
    
    print("MongoDB collection creation complete!")

def main():
    """Main function to store PDF extracted data in MongoDB."""
    parser = argparse.ArgumentParser(description="Store PDF extracted data in MongoDB for vector search")
    parser.add_argument("--input-file", type=str, default="./extracted_data/pdf_extracted_data.json", 
                        help="JSON file with extracted PDF data")
    args = parser.parse_args()
    
    # Ensure input file is absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(args.input_file):
        args.input_file = os.path.abspath(os.path.join(script_dir, args.input_file))
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        return 1
    
    # Load PDF data
    print(f"Loading PDF data from {args.input_file}...")
    with open(args.input_file, 'r') as f:
        pdf_data = json.load(f)
    
    # Create MongoDB collection
    create_pdf_vector_collection(pdf_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
