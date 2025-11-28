import os
import shutil
import argparse
from pathlib import Path

def copy_pdfs(source_dir: str, target_dir: str, verbose: bool = False):
    """Copy PDF files from source directory to target directory."""
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    # Get list of PDF files in source directory
    pdf_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {source_dir}")
        return
    
    # Copy files
    copied_count = 0
    for pdf_file in pdf_files:
        source_path = os.path.join(source_dir, pdf_file)
        target_path = os.path.join(target_dir, pdf_file)
        
        # Skip if file already exists in target directory
        if os.path.exists(target_path):
            if verbose:
                print(f"Skipping {pdf_file} (already exists in target directory)")
            continue
        
        # Copy file
        shutil.copy2(source_path, target_path)
        copied_count += 1
        
        if verbose:
            print(f"Copied {pdf_file}")
    
    print(f"Copied {copied_count} PDF files to {target_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy PDF files from source directory to target directory")
    parser.add_argument("--source", type=str, default="../data", help="Source directory containing PDF files")
    parser.add_argument("--target", type=str, default="data/raw", help="Target directory for PDF files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    copy_pdfs(args.source, args.target, args.verbose)
