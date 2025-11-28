#!/bin/bash

# Initialize Restaurant Advisor System

# Ensure we're in the project directory
cd "$(dirname "$0")"

echo "Setting up Restaurant Advisor System..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
if [ "$(uname)" == "Darwin" ] || [ "$(uname)" == "Linux" ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your credentials before proceeding."
    echo "You'll need to set up:"
    echo "  - MongoDB Atlas connection"
    echo "  - Neo4j Aura connection"
    echo "  - Gemini API key"
    echo "  - LangSmith API key (optional)"
fi

# Create data directory structure if it doesn't exist
echo "Setting up data directories..."
mkdir -p data/raw
mkdir -p data/processed

# Copy PDFs from parent directory if available
echo "Checking for available PDFs..."
if [ -d "../data" ]; then
    echo "Found PDFs in parent directory, copying..."
    cp -n ../data/*.pdf data/raw/
    echo "Copied $(ls -1 data/raw/*.pdf | wc -l) PDF files to data/raw/"
else
    echo "No PDFs found in parent directory."
    echo "Please add PDF files to the data/raw directory manually."
fi

# Check for common SSL cert issues on macOS and suggest solution
if [ "$(uname)" == "Darwin" ]; then
    echo "Note for macOS users: If you encounter SSL certificate validation errors,"
    echo "you may need to install certificates for Python:"
    echo ""
    echo "Option 1: Install certificates package (recommended):"
    echo "pip install certifi"
    echo ""
    echo "Option 2: Run the Install Certificates.command file in your Python installation:"
    echo "cd /Applications/Python*/Install\ Certificates.command"
    echo ""
    echo "The system has been configured to bypass certificate validation if needed,"
    echo "but fixing your certificate store is the better long-term solution."
fi

echo "Setup complete!"
echo "To run the system:"
echo "1. Edit the .env file with your database credentials"
echo "2. Run 'python check_imports.py' to verify all dependencies are installed"
echo "3. Run 'python init_mongodb.py' to initialize the MongoDB collections"
echo "4. Run 'python init_kg.py' to initialize the knowledge graph"
echo "5. Run 'python ingest.py' to ingest PDFs"
echo "6. Run 'python main.py' to start the system"
