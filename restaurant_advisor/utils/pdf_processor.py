import os
import sys
from typing import List, Dict, Any, Optional
import pypdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import CHUNK_SIZE, CHUNK_OVERLAP
from kb.mongodb_kb import MongoKnowledgeBase

class PDFProcessor:
    """Process PDF documents for ingestion into the knowledge base."""
    
    def __init__(self, kb: MongoKnowledgeBase):
        self.kb = kb
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
            return text
    
    def extract_metadata_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from a PDF file."""
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            info = pdf_reader.metadata
            
            # Basic metadata
            metadata = {
                "source": os.path.basename(pdf_path),
                "path": pdf_path,
                "page_count": len(pdf_reader.pages)
            }
            
            # Extract document info if available
            if info:
                if info.get('/Title'):
                    metadata["title"] = info.get('/Title')
                if info.get('/Author'):
                    metadata["author"] = info.get('/Author')
                if info.get('/Subject'):
                    metadata["subject"] = info.get('/Subject')
                if info.get('/Keywords'):
                    metadata["keywords"] = info.get('/Keywords')
                if info.get('/CreationDate'):
                    metadata["creation_date"] = info.get('/CreationDate')
            
            # Add document type based on filename
            filename = os.path.basename(pdf_path).lower()
            if "real_estate" in filename or "realty" in filename:
                metadata["type"] = "real_estate"
            elif "consumption" in filename or "food" in filename:
                metadata["type"] = "food_consumption"
            elif "regulation" in filename or "licensing" in filename:
                metadata["type"] = "regulation"
            elif "demographics" in filename:
                metadata["type"] = "demographics"
            else:
                metadata["type"] = "general"
                
            return metadata
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """Process a PDF file and split into chunks for ingestion."""
        # Extract text and metadata
        text = self.extract_text_from_pdf(pdf_path)
        metadata = self.extract_metadata_from_pdf(pdf_path)
        
        # Split text into chunks
        docs = self.text_splitter.create_documents([text], [metadata])
        
        # Add page numbers to metadata
        for i, doc in enumerate(docs):
            doc.metadata["chunk_id"] = i
            
        return docs
    
    def ingest_pdf(self, pdf_path: str) -> List[str]:
        """Ingest a PDF file into the knowledge base."""
        # Process the PDF into document chunks
        docs = self.process_pdf(pdf_path)
        
        # Store documents in the knowledge base
        doc_ids = self.kb.store_documents(docs)
        
        return doc_ids
    
    def ingest_directory(self, directory_path: str) -> Dict[str, List[str]]:
        """Ingest all PDF files in a directory into the knowledge base."""
        results = {}
        
        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(directory_path, filename)
                try:
                    doc_ids = self.ingest_pdf(pdf_path)
                    results[filename] = doc_ids
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
                    results[filename] = ["ERROR: " + str(e)]
        
        return results
