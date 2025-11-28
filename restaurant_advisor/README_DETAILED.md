# Restaurant Chain Advisor System

A command-line system that helps users set up restaurant chains across Indian cities using agentic AI, knowledge bases, knowledge graphs, and RAG techniques.

## Features

### 1. Agentic AI Framework

- **LangChain & LangGraph Integration**: Multi-agent system with orchestration
- **Agent Specialization**: Location recommender, regulatory advisor, market analyst
- **LangSmith Tracing**: Debug and monitor agent interactions
- **Gemini Pro Integration**: Powerful LLM for natural language understanding

### 2. Knowledge Base (MongoDB)

- **Document Ingestion**: Process PDFs with metadata extraction
- **Chunking Strategy**: Optimized document chunking for better retrieval
- **Embedding**: Sentence Transformer embeddings for semantic search
- **Vector Storage**: MongoDB Atlas Vector Search for efficient retrieval
- **Hybrid Search**: Combines keyword and semantic search for better results

### 3. Knowledge Graph (Neo4j)

- **Location Data**: City and area information with rich metadata
- **Relationship Modeling**: Proximity, regulations, cuisine preferences
- **Graph Traversal**: Find nearby locations and related entities
- **Property Graph Model**: Detailed attributes on nodes and relationships

### 4. RAG Techniques

- **Retrieval Augmentation**: Enhance agent responses with relevant knowledge
- **Hybrid Search**: Combine semantic and keyword search for better results
- **Context Enrichment**: Knowledge graph insights combined with KB results
- **Multi-index Retrieval**: Search across different document types

### 5. Access Control

- **Role-based Permissions**: Admin, analyst, restaurant owner, guest
- **Resource Protection**: Control access to agents, knowledge, and operations
- **JWT Authentication**: Secure token-based authentication
- **Permission Enforcement**: Graceful fallback for unauthorized access attempts

### 6. Advanced Agent Features

- **Multi-Agent Orchestration**: Route queries to specialized agents
- **Memory Management**: Per-user conversation history
- **Domain Specialization**: Agents focused on specific restaurant setup aspects

## Project Structure

```
restaurant_advisor/
│
├── agents/                   # Agent definitions and orchestration
│   ├── agent_definitions.py  # Individual agent implementations
│   └── orchestrator.py       # Multi-agent orchestration with LangGraph
│
├── kb/                       # Knowledge base components
│   └── mongodb_kb.py         # MongoDB vector store integration
│
├── kg/                       # Knowledge graph components
│   └── neo4j_kg.py           # Neo4j graph database integration
│
├── utils/                    # Utility functions
│   ├── auth.py               # Authentication and access control
│   ├── config.py             # Configuration settings
│   └── pdf_processor.py      # PDF processing utilities
│
├── data/                     # Data storage
│   ├── raw/                  # Original PDF files
│   └── processed/            # Processed data
│
├── .env.example              # Environment variables template
├── README.md                 # Project documentation
├── ingest.py                 # Script to ingest PDFs into MongoDB
├── init_kg.py                # Script to initialize Neo4j with sample data
├── main.py                   # Main application entry point
├── requirements.txt          # Python dependencies
└── setup.sh                  # Setup script
```

## Setup Instructions

1. Clone this repository

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```

4. Copy your PDF files to the `data/raw` directory

5. Ingest PDFs into MongoDB:
   ```
   python ingest.py
   ```

6. Initialize the knowledge graph:
   ```
   python init_kg.py
   ```

7. Run the application:
   ```
   python main.py
   ```

## Required External Services

1. **MongoDB Atlas** (free tier available):
   - Set up a vector search capable cluster
   - Create a database named `restaurant_advisor`
   - Create collections: `documents` and `vectors`
   - Configure vector search index on the `vectors` collection

2. **Neo4j Aura** (free tier available):
   - Create a Neo4j Aura instance
   - No schema setup required (handled by the code)

3. **Google AI Studio** (Gemini API):
   - Sign up for Google AI Studio
   - Generate an API key for Gemini Pro

4. **LangSmith** (optional, for tracing):
   - Sign up for LangSmith
   - Create a project named `restaurant-advisor`
   - Generate an API key

## Recommended PDFs

For the knowledge base to be effective, include PDFs covering:

1. **Real Estate Market Reports**:
   - Commercial real estate analysis for Indian cities
   - Retail space trends and pricing
   - Urban development patterns

2. **Food Industry Reports**:
   - Restaurant market analysis
   - Food consumption trends
   - Consumer preferences studies

3. **Regulatory Documents**:
   - FSSAI licensing guidelines
   - Restaurant permit requirements
   - State-specific regulations

4. **Demographic Studies**:
   - Population distribution in urban centers
   - Income patterns and spending habits
   - Dining out preferences by demographic

## User Roles

1. **Admin**: Full access to all features and user management
2. **Analyst**: Access to market analysis, location recommendations, and regulatory information
3. **Restaurant Owner**: Access to location recommendations and regulatory information
4. **Guest**: Limited access to basic queries only

## Usage Examples

### Finding Restaurant Locations

```
Query: "I want to open an Italian fine dining restaurant in Mumbai targeting young professionals with a budget of 50 lakhs"
```

### Getting Regulatory Information

```
Query: "What licenses do I need for a 60-seat restaurant with bar in Bangalore?"
```

### Market Analysis

```
Query: "Analyze the market potential for a fast-casual South Indian chain in Delhi NCR"
```

## Extension Possibilities

- Web interface with React/Flask/FastAPI
- Real-time data sources integration
- More sophisticated agent collaboration
- Visualization of recommended locations
- Integration with real estate listing APIs

## Troubleshooting

- **MongoDB Connection Issues**: Check your connection string and network access settings
- **Neo4j Errors**: Verify credentials and that the Neo4j instance is running
- **PDF Ingestion Failures**: Ensure PDFs are not password protected or corrupted
- **Agent Response Quality**: Try adding more relevant PDFs to the knowledge base

## Credits

Built with:
- LangChain/LangGraph
- MongoDB Atlas
- Neo4j Aura
- Google Gemini Pro
- Sentence Transformers
