#!/usr/bin/env python3
"""
Test script for location insights functionality from Neo4j knowledge graph.
"""

import sys
import os
from rich.console import Console

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg.neo4j_kg import Neo4jKnowledgeGraph
from kb.mongodb_kb import MongoKnowledgeBase

console = Console()

def test_neo4j_city_data():
    """Test getting city demographic data from Neo4j."""
    console.print("[bold blue]Testing Neo4j City Demographics[/bold blue]")
    
    try:
        kg = Neo4jKnowledgeGraph()
        console.print("[green]Connected to Neo4j successfully[/green]")
        
        # Test city with data
        city = "Chennai"
        console.print(f"\nTesting city data for: [cyan]{city}[/cyan]")
        city_data = kg.get_detailed_city_demographics(city)
        
        if city_data:
            console.print("[green]City data found:[/green]")
            console.print(f"Name: {city_data.get('name', 'Unknown')}")
            console.print(f"State: {city_data.get('state', 'Unknown')}")
            console.print(f"Population: {city_data.get('population', 'Unknown')}")
            
            if city_data.get('demographics'):
                console.print("\nDemographics:")
                for demo in city_data.get('demographics', []):
                    console.print(f"- {demo}")
            
            if city_data.get('key_markets'):
                console.print("\nKey Markets:")
                for market in city_data.get('key_markets', []):
                    console.print(f"- {market}")
        else:
            console.print(f"[yellow]No data found for {city}[/yellow]")
            console.print("You may need to add sample data to your Neo4j database first.")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()
    
def test_neo4j_location_data():
    """Test getting location data from Neo4j."""
    console.print("\n[bold blue]Testing Neo4j Location Data[/bold blue]")
    
    try:
        kg = Neo4jKnowledgeGraph()
        
        # Test locations in a city
        city = "Chennai"
        console.print(f"\nTesting locations in: [cyan]{city}[/cyan]")
        locations = kg.get_detailed_location_info(city)
        
        if locations:
            console.print(f"[green]Found {len(locations)} locations[/green]")
            
            # Display sample locations
            for i, loc in enumerate(locations[:3]):
                console.print(f"\nLocation {i+1}:")
                console.print(f"Area: {loc.get('area', 'Unknown')}")
                console.print(f"Type: {loc.get('type', 'Unknown')}")
                console.print(f"Foot Traffic: {loc.get('foot_traffic', 'Unknown')}")
                console.print(f"Rent Range: {loc.get('rent_range', 'Unknown')}")
                
                if loc.get('popular_cuisines'):
                    console.print("Popular Cuisines:")
                    for cuisine in loc.get('popular_cuisines', []):
                        console.print(f"- {cuisine}")
        else:
            console.print(f"[yellow]No locations found for {city}[/yellow]")
            console.print("You may need to add sample data to your Neo4j database first.")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

def test_mongodb_hybrid_search():
    """Test hybrid search in MongoDB knowledge base."""
    console.print("\n[bold blue]Testing MongoDB Hybrid Search[/bold blue]")
    
    try:
        kb = MongoKnowledgeBase()
        console.print("[green]Connected to MongoDB successfully[/green]")
        
        # Test search query
        query = "restaurant market trends Chennai"
        console.print(f"\nSearching for: [cyan]{query}[/cyan]")
        results = kb.hybrid_search(query, k=2)
        
        if results:
            console.print(f"[green]Found {len(results)} results[/green]")
            
            for i, doc in enumerate(results):
                console.print(f"\nResult {i+1}:")
                console.print(f"Source: {doc.metadata.get('source', 'Unknown')}")
                
                # Show a snippet of the content
                content = doc.page_content
                if len(content) > 200:
                    content = content[:200] + "..."
                console.print(f"Content: {content}")
        else:
            console.print("[yellow]No results found[/yellow]")
            console.print("You may need to add documents to your MongoDB database first.")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_neo4j_city_data()
    test_neo4j_location_data()
    test_mongodb_hybrid_search()
    
    console.print("\n[bold green]Tests complete![/bold green]")
