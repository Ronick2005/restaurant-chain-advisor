"""
Ingest PDFs from data/ folder into MongoDB with embeddings.
"""

from agents.document_ingestion_agent import DocumentIngestionAgent
import time

def main():
    print('Starting document ingestion from data/ folder...\n')
    agent = DocumentIngestionAgent('data')

    # Ingest all documents
    print('Processing PDFs with SentenceTransformers embeddings...')
    start = time.time()
    result = agent.ingest_directory()
    elapsed = time.time() - start

    print(f'\n========================================')
    print(f'INGESTION COMPLETE!')
    print(f'========================================')
    print(f'✅ Successful: {result["successful"]} documents')
    print(f'❌ Failed: {result["failed"]} documents')
    print(f'⏱️  Time: {elapsed:.1f} seconds')
    print(f'📊 Total chunks created: {result.get("total_chunks", 0)}')

    # Get statistics
    stats = agent.get_document_statistics()
    print(f'\n📚 Document Statistics:')
    print(f'   Total documents: {stats["total_documents"]}')
    print(f'   Total chunks: {stats["total_chunks"]}')
    print(f'   File types: {stats["file_types"]}')
    if stats.get("categories"):
        print(f'   Categories: {stats["categories"]}')
    
    print('\n✅ All documents embedded and stored in MongoDB!')

if __name__ == "__main__":
    main()
