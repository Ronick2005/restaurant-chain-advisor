from typing import Dict, Any
import os

# Add code here to make the models compatible if needed
# This file helps ensure the system uses imports correctly

if __name__ == "__main__":
    print("Restaurant Advisor System - Import compatibility check")
    
    # Print import checks
    print("\nChecking imports...")
    
    try:
        import langchain_core
        print("✅ langchain_core imported successfully")
    except ImportError:
        print("❌ langchain_core import failed")
        
    try:
        from langchain_community.vectorstores.mongodb_atlas import MongoDBAtlasVectorSearch
        print("✅ langchain_community imported successfully")
    except ImportError:
        print("❌ langchain_community import failed")
        
    try:
        from langchain_mongodb import MongoDBAtlasVectorSearch
        print("✅ langchain_mongodb imported successfully")
    except ImportError:
        print("❌ langchain_mongodb import failed")
        
    try:
        import langgraph
        print("✅ langgraph imported successfully")
    except ImportError:
        print("❌ langgraph import failed")
        
    try:
        import pymongo
        print("✅ pymongo imported successfully")
    except ImportError:
        print("❌ pymongo import failed")
        
    try:
        import neo4j
        print("✅ neo4j imported successfully")
    except ImportError:
        print("❌ neo4j import failed")
        
    try:
        import google.generativeai
        print("✅ google.generativeai imported successfully")
    except ImportError:
        print("❌ google.generativeai import failed")
        
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence_transformers imported successfully")
    except ImportError:
        print("❌ sentence_transformers import failed")
        
    try:
        import typer
        print("✅ typer imported successfully")
    except ImportError:
        print("❌ typer import failed")
        
    try:
        from rich.console import Console
        print("✅ rich imported successfully")
    except ImportError:
        print("❌ rich import failed")
        
    print("\nRun this script after installing dependencies to ensure all packages are correctly installed.")
    print("If any imports failed, try reinstalling the requirements with: pip install -r requirements.txt")
