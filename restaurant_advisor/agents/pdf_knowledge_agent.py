"""
PDF knowledge agent for extracting insights from PDF documents.
This agent specializes in answering queries related to information
extracted from research papers, reports, and other PDF documents.
"""

from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_mongodb import MongoDBAtlasVectorSearch

class PDFKnowledgeAgent:
    """Agent for retrieving and synthesizing information from PDF documents."""
    
    def __init__(self, llm: BaseLLM, mongodb_uri: str, db_name: str):
        """Initialize the PDF knowledge agent.
        
        Args:
            llm: Language model instance
            mongodb_uri: MongoDB Atlas connection URI
            db_name: MongoDB database name
        """
        self.llm = llm
        self.mongodb_uri = mongodb_uri
        self.db_name = db_name
        
        # Define the retrieval prompt
        self.retrieval_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized knowledge retrieval agent for restaurant business in India.
            Your role is to provide accurate, insightful answers based on information extracted from PDF documents.
            These documents include research papers, industry reports, and regulatory guidelines about:
            - Food regulations and licensing in India
            - Consumer preferences and food trends
            - Real estate information for restaurant businesses
            - City-specific insights for major Indian cities
            
            Based on the context provided, generate a comprehensive and well-structured answer.
            Include specific details, citations to the sources, and actionable insights where applicable.
            If the provided context doesn't contain sufficient information, acknowledge the limitations
            but provide the best answer possible based on what is available.
            
            Context information from documents:
            {context}
            
            Question: {question}
            """),
        ])
        
        # Define the answer parser
        self.answer_parser = StrOutputParser()
        
        # Initialize the MongoDB retriever
        self.retriever = self._create_retriever()
        
        # Create the chain
        self.chain = (
            {"context": self.retriever, "question": lambda x: x}
            | self.retrieval_prompt
            | self.llm
            | self.answer_parser
        )
    
    def _create_retriever(self):
        """Create the MongoDB retriever with vector search.
        
        Returns:
            MongoDB vector search retriever
        """
        # Create sentence transformer embeddings for vector search
        from kb.mongodb_kb import SentenceTransformerEmbeddings
        embeddings = SentenceTransformerEmbeddings()
        
        # Create the MongoDB vector store
        vector_store = MongoDBAtlasVectorSearch.from_connection_string(
            embedding=embeddings,
            connection_string=self.mongodb_uri,
            namespace=f"{self.db_name}.vectors",
            index_name="default_vector_index",
            text_key="content",
            embedding_key="embedding",
            pre_filter_pipeline=[{"$match": {"metadata": {"$exists": True}}}]
        )
        
        # Create the retriever
        return vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10,
                "post_filter_pipeline": [
                    {"$limit": 10},
                    {"$project": {"text": 1, "metadata": 1, "_id": 0}}
                ]
            }
        )
    
    def run(self, query: str) -> str:
        """Run the PDF knowledge agent to answer a query.
        
        Args:
            query: User query string
            
        Returns:
            Answer based on PDF document knowledge
        """
        try:
            answer = self.chain.invoke(query)
            return answer
        except Exception as e:
            return f"I encountered an issue retrieving information from PDF documents: {str(e)}. " \
                   f"Could you try rephrasing your question or asking something else?"
