# Restaurant Chain Advisor System

A command-line system that helps users set up restaurant chains across Indian cities using:
- Agentic AI framework with LangChain, LangGraph, and LangSmith
- Knowledge Bases with MongoDB Atlas vector search
- Knowledge Graphs with Neo4j Aura
- Advanced RAG techniques and access control

This system helps customers set up restaurant chains across Indian cities by providing location recommendations based on data analysis and user preferences.

## Quick Setup

1. **Set up your environment**:
   ```bash
   # Make the setup script executable
   chmod +x setup.sh
   
   # Run the setup script
   ./setup.sh
   ```

2. **Configure your credentials**:
   Edit the `.env` file with your:
   - MongoDB Atlas URI
   - Neo4j Aura credentials
   - Gemini API key

3. **Initialize databases and data**:
   ```bash
   python init_mongodb.py
   python init_kg.py
   python copy_pdfs.py
   python ingest.py
   ```

4. **Run the system**:
   ```bash
   python main.py
   ```

## Features

- **Agentic AI Framework**:
  - Uses LangChain, LangGraph, and LangSmith for agent orchestration
  - Node-based architecture with chains, agents, memory, and tools
  - Traces agent execution with LangSmith for debugging

- **Knowledge Base (MongoDB)**:
  - Document ingestion from PDFs with metadata handling
  - Chunking strategies for optimal retrieval
  - Sentence transformer embeddings for semantic search
  - No redundant data - updates only when new information is provided

- **Knowledge Graph (Neo4j)**:
  - Graph representation of locations, markets, and restaurant types
  - Entity relationships for rich contextual recommendations
  - Advanced querying patterns and graph traversals
  - Structured location data with metadata

- **RAG Techniques**:
  - Hybrid search strategies for knowledge retrieval
  - Integration with agent queries
  - Multi-index retrieval for comprehensive recommendations

- **Access Control**:
  - User-level and role-based permissions
  - Admin privileges for system management
  - Enforcement in RAG queries and retrieval pipelines

- **Advanced Agents**:
  - Multi-agent orchestration for specialized tasks
  - Conditional routing based on query type
  - Memory management (short-term, long-term, per-user)

## Detailed Setup Instructions

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Set up external services**:
   
   - **MongoDB Atlas** (free tier available):
     - Create a cluster with vector search capability
     - Create database `restaurant_advisor`
     - Create collections: `documents` and `vectors`
     - Set up vector search index (instructions in `init_mongodb.py`)
   
   - **Neo4j Aura** (free tier available):
     - Create a Neo4j instance
     - Get connection URI, username, and password
   
   - **Google AI Studio**:
     - Sign up and get Gemini API key

3. **Configure the environment**:
   ```
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Initialize knowledge systems**:
   ```
   # Set up MongoDB collections and indexes
   python init_mongodb.py
   
   # Initialize Neo4j with sample location data
   python init_kg.py
   
   # Copy PDFs from parent directory (if available)
   python copy_pdfs.py
   
   # Process PDFs into the knowledge base
   python ingest.py
   ```

5. **Run the system**:
   ```
   python main.py
   ```

For a quick start guide, see `QUICKSTART.md`.
For comprehensive documentation, see `README_DETAILED.md`.

## Recommended PDFs

The system needs various PDFs for its knowledge base. Recommended types:

1. **Market Research Reports**:
   - Commercial real estate reports for different Indian cities
   - Restaurant industry analysis reports
   - Consumer demographics and food preference studies

2. **Regulatory Documents**:
   - Food business licensing regulations
   - Restaurant setup guidelines
   - Regional compliance requirements

3. **Consumption Pattern Reports**:
   - Food consumption trends in India
   - City-specific dining preferences
   - Consumer behavior analysis

Several PDF files from your existing data directory would be useful:
- "Commercial Real Estate_Final.pdf"
- "realty_bytes_may_2025.pdf"
- "navigating-the-dynamics-of-real-estate-in-india.pdf"
- "10 Licensing Registration of Food Businesses Regulations.pdf"
- "Changes-in-Indias-Food-Consumption-and-Policy-Implications.pdf"
- "Indian Cuisine at a Crossroads.pdf"
- "Indias-food-service.pdf"
- "Study_of_Consumer_Demographics_Awareness_Perceptio.pdf"

## User Roles

1. **Admin**: Full access to all features, can add/modify knowledge base and graph, manage users
2. **Business Analyst**: Can access all insights but cannot modify the system
3. **Restaurant Owner**: Limited access based on their specific needs and permissions
4. **Guest**: Basic query capabilities with limited recommendation features

## System Components

- `main.py`: Entry point for the CMD interface
- `ingest.py`: Data ingestion script for PDFs
- `agents/`: Contains all agent definitions and orchestration logic
- `kb/`: Knowledge base utilities and MongoDB integration
- `kg/`: Knowledge graph utilities and Neo4j integration
- `utils/`: Helper functions and shared utilities

## How It Works

1. User logs in with their credentials
2. System identifies user role and permissions
3. User provides their restaurant concept and target cities
4. Agents work together to analyze and provide recommendations:
   - Knowledge retrieval from MongoDB (market data, regulations)
   - Graph traversal in Neo4j (location relationships, proximity data)
   - Reasoning and recommendation generation with Gemini Pro
5. System provides location suggestions with supporting rationale

## Future Improvements

- Web interface for easier interaction
- Real-time data updates from public sources
- More sophisticated multi-agent collaboration patterns
- Enhanced visualization of recommended locations
