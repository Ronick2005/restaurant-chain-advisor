#!/bin/bash

# Setup script for restaurant advisor system

echo "========== Restaurant Advisor Setup =========="
echo "This script will set up the restaurant advisor system."

# Check if virtualenv is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo "Creating and activating virtual environment..."
  python -m venv venv
  source venv/bin/activate
else
  echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Set the Gemini API key
echo "Setting up Gemini API key..."
python set_api_key.py

# Ingest documents into the knowledge base
echo "Ingesting documents into the knowledge base..."
echo "This will process all PDFs in the data directory and store them in MongoDB."
python ingest.py --verbose

# Verify the system is ready
echo "Testing the system..."
echo "Running a simple test to verify the system is working properly..."
python -c "from kb.mongodb_kb import MongoKnowledgeBase; kb = MongoKnowledgeBase(); print(f'MongoDB connected successfully. Document count: {kb.collection.count_documents({})}')"

echo "========== Setup Complete =========="
echo "You can now run the application with: python main.py main"
