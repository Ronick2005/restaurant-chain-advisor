#!/usr/bin/env python3
"""
Main script to run the full knowledge graph population process
including PDF extraction and MongoDB integration.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def main():
    """Main function to run the full knowledge graph population process."""
    parser = argparse.ArgumentParser(description="Run the full knowledge graph population process")
    parser.add_argument("--skip-pdf-extraction", action="store_true", 
                        help="Skip PDF extraction and use existing extracted data")
    parser.add_argument("--skip-kg-population", action="store_true", 
                        help="Skip Neo4j knowledge graph population")
    parser.add_argument("--skip-mongodb", action="store_true", 
                        help="Skip MongoDB integration")
    parser.add_argument("--clear-kg", action="store_true", 
                        help="Clear existing data from Neo4j knowledge graph")
    args = parser.parse_args()
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Step 1: Extract PDF data
    if not args.skip_pdf_extraction:
        print("=== Step 1: Extracting data from PDFs ===")
        pdf_script = os.path.join(current_dir, "scripts", "pdf_extractor.py")
        cmd = [sys.executable, pdf_script]
        result = subprocess.run(cmd, check=True)
        if result.returncode != 0:
            print("Error extracting PDF data")
            return 1
        print("PDF data extraction completed successfully")
    else:
        print("Skipping PDF extraction")
    
    # Step 2: Populate Neo4j knowledge graph
    if not args.skip_kg_population:
        print("\n=== Step 2: Populating Neo4j knowledge graph ===")
        kg_script = os.path.join(current_dir, "populate_kg.py")
        cmd = [sys.executable, kg_script]
        if args.clear_kg:
            cmd.append("--clear-kg")
        result = subprocess.run(cmd, check=True)
        if result.returncode != 0:
            print("Error populating knowledge graph")
            return 1
        print("Knowledge graph population completed successfully")
    else:
        print("Skipping knowledge graph population")
    
    # Step 3: Integrate PDF data into Neo4j
    print("\n=== Step 3: Integrating PDF data into Neo4j ===")
    integrate_script = os.path.join(current_dir, "scripts", "integrate_pdf_data.py")
    cmd = [sys.executable, integrate_script]
    if args.skip_pdf_extraction:
        cmd.append("--skip-extraction")
    result = subprocess.run(cmd, check=True)
    if result.returncode != 0:
        print("Error integrating PDF data")
        return 1
    print("PDF data integration completed successfully")
    
    # Step 4: Store PDF data in MongoDB
    if not args.skip_mongodb:
        print("\n=== Step 4: Storing PDF data in MongoDB ===")
        store_script = os.path.join(current_dir, "scripts", "store_pdf_data.py")
        cmd = [sys.executable, store_script]
        result = subprocess.run(cmd, check=True)
        if result.returncode != 0:
            print("Error storing PDF data in MongoDB")
            return 1
        print("MongoDB integration completed successfully")
    else:
        print("Skipping MongoDB integration")
    
    print("\n=== Knowledge graph population process completed successfully! ===")
    print("The restaurant advisor system now has a comprehensive knowledge graph")
    print("with data from PDFs and MongoDB vector search capabilities.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
