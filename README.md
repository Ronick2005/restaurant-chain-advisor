# Restaurant Chain Advisor

AI-powered location and market intelligence system for restaurant chains in India.

## Features

- Location recommendations using real estate and demographic data
- Regulatory compliance guidance for different cities
- Market analysis and consumer insights
- Knowledge base with 2,000+ document chunks
- Knowledge graph with 500+ relationships
- Role-based access control (Basic, Premium, Admin)

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account
- Neo4j Aura account
- Google API key (for Gemini)

### Installation

1. Clone the repository:
```bash
cd restaurant-chain-advisor/restaurant_advisor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```env
GOOGLE_API_KEY=your_google_api_key
MONGODB_URI=your_mongodb_connection_string
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### Run the Application

**Web Interface (Streamlit):**
```bash
streamlit run streamlit_app.py
```
Access at: http://localhost:8501

**CLI Interface:**
```bash
python main.py
```

## Architecture

```
restaurant_advisor/
├── agents/              # AI agents (routing, location, regulatory, market)
├── kb/                  # MongoDB knowledge base
├── kg/                  # Neo4j knowledge graph
├── utils/               # Authentication and configuration
├── data/                # PDF documents (ingested)
├── main.py              # CLI interface
└── streamlit_app.py     # Web interface
```

## User Roles

### Basic
- Access to general queries
- Limited document retrieval
- Basic location insights

### Premium
- Full knowledge base access
- Knowledge graph insights
- Advanced analytics
- Market research reports

### Admin
- All premium features
- User management
- System configuration
- Document ingestion

## Data Sources

- **Documents**: 20 PDF files covering food safety, consumer preferences, real estate, and market research
- **Knowledge Graph**: 194 nodes (locations, regulations, topics) with 503 relationships
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2) for semantic search

## Default Configuration

- **Default City**: Chennai
- **Default Locality**: T Nagar
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **LLM**: Google Gemini 1.5 Pro

## Response Format

All responses include:
1. **Analysis**: Detailed insights based on your query
2. **Sources**: Citations showing which documents were used

Example:
```
Based on the analysis...

--- Sources ---
1. chennai-market-report.pdf (Category: Market Research, Page: 15)
2. real-estate-trends.pdf (Category: Real Estate, Page: 8)
```

## Support

For issues or questions, refer to the PROMPT_GUIDE.md for example queries.
