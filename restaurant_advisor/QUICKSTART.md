# Getting Started with Restaurant Advisor

This guide will help you set up and run the Restaurant Advisor system.

## Quick Start

1. **Setup the environment**:
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

3. **Copy PDFs to the system**:
   ```bash
   python copy_pdfs.py
   ```

4. **Ingest PDFs into the knowledge base**:
   ```bash
   python ingest.py
   ```

5. **Initialize the knowledge graph**:
   ```bash
   python init_kg.py
   ```

6. **Run the system**:
   ```bash
   python main.py
   ```

## Default Login

On first run, you'll be prompted to create an admin user. For subsequent runs:
- Username: `admin`
- Password: `admin` (unless you changed it)

## Example Queries

Try these queries after logging in:

1. "I want to open an Italian restaurant in Mumbai targeting young professionals. Where should I locate it?"

2. "What licenses do I need for a restaurant with alcohol service in Bangalore?"

3. "Analyze the market potential for a South Indian restaurant in Koramangala, Bangalore."

4. "What are the high foot traffic areas in Delhi for a fast casual restaurant?"

## Understanding System Components

- **Knowledge Base (MongoDB)**: Stores and retrieves document knowledge from PDFs
- **Knowledge Graph (Neo4j)**: Stores structured location and relationship data
- **Agent System (LangChain/LangGraph)**: Routes queries to specialized agents
- **Access Control**: Different roles have different permissions

See `README_DETAILED.md` for more comprehensive documentation.
