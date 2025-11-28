import os
import sys
import argparse
from typing import List, Dict

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kb.mongodb_kb import MongoKnowledgeBase
from utils.pdf_processor import PDFProcessor
from utils.config import MONGODB_URI, MONGODB_DATABASE

def ingest_pdfs(data_dir: str, verbose: bool = False) -> Dict[str, List[str]]:
    """Ingest all PDFs from the data directory into the knowledge base."""
    if not os.path.isdir(data_dir):
        print(f"Error: {data_dir} is not a valid directory.")
        return {}

    print(f"Connecting to MongoDB at {MONGODB_URI}")
    kb = MongoKnowledgeBase()
    processor = PDFProcessor(kb)

    print(f"Processing PDFs from {data_dir}...")
    results = processor.ingest_directory(data_dir)

    # Summary
    total_files = len(results)
    successful_files = sum(1 for ids in results.values() if not any("ERROR" in str(id) for id in ids))
    total_chunks = sum(len(ids) for ids in results.values())

    print(f"\nIngest Summary:")
    print(f"- Files processed: {total_files}")
    print(f"- Successfully ingested: {successful_files}")
    print(f"- Total document chunks created: {total_chunks}")

    if verbose:
        print("\nDetailed Results:")
        for filename, doc_ids in results.items():
            print(f"- {filename}: {len(doc_ids)} chunks")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into the knowledge base.")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing PDF files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    # Make sure data_dir is an absolute path
    if not os.path.isabs(args.data_dir):
        args.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), args.data_dir))
    
    ingest_pdfs(args.data_dir, args.verbose)
