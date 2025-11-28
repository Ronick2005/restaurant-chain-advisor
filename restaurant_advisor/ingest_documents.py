"""
Document Ingestion Script
Run this to ingest all documents from the docs/ folder into MongoDB.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents.document_ingestion_agent import DocumentIngestionAgent
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

def main():
    """Main ingestion function."""
    console.print("\n[bold cyan]Document Ingestion System[/bold cyan]")
    console.print("=" * 60)
    
    # Initialize agent
    console.print("\n[yellow]Initializing document ingestion agent...[/yellow]")
    agent = DocumentIngestionAgent(docs_directory="docs")
    
    # Check if docs directory exists
    if not Path("docs").exists():
        console.print("\n[red]Error: docs/ directory not found![/red]")
        console.print("Please create a 'docs' folder and add your documents.")
        return
    
    # Get current statistics
    console.print("\n[yellow]Current document statistics:[/yellow]")
    stats = agent.get_document_statistics()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Documents", str(stats['total_documents']))
    table.add_row("Total Chunks", str(stats['total_chunks']))
    table.add_row("Total Size", f"{stats['total_size_bytes'] / 1024 / 1024:.2f} MB")
    table.add_row("Categories", str(len(stats['categories'])))
    
    console.print(table)
    
    # Ask for confirmation
    console.print("\n[bold yellow]This will ingest all documents from the docs/ folder.[/bold yellow]")
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != "yes":
        console.print("[red]Ingestion cancelled.[/red]")
        return
    
    # Start ingestion
    console.print("\n[bold green]Starting document ingestion...[/bold green]\n")
    
    result = agent.ingest_directory()
    
    # Display results
    console.print("\n[bold green]Ingestion Complete![/bold green]")
    console.print("=" * 60)
    
    results_table = Table(show_header=True, header_style="bold magenta")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Count", style="green")
    
    results_table.add_row("Total Files Found", str(result['total_files']))
    results_table.add_row("Successfully Ingested", str(result['successful']))
    results_table.add_row("Skipped (Already Indexed)", str(result['skipped']))
    results_table.add_row("Failed", str(result['failed']))
    results_table.add_row("Total Chunks Created", str(result['total_chunks']))
    
    console.print(results_table)
    
    # Show processed files
    if result['files_processed']:
        console.print("\n[bold cyan]Processed Files:[/bold cyan]")
        for file_result in result['files_processed']:
            status_color = {
                "success": "green",
                "skipped": "yellow",
                "failed": "red"
            }.get(file_result['status'], "white")
            
            console.print(f"  [{status_color}]●[/{status_color}] {file_result['file_name']} - {file_result['status']}")
    
    console.print("\n[bold green]Documents are now available for search and retrieval![/bold green]\n")

if __name__ == "__main__":
    main()
