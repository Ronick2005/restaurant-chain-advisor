"""
Example script demonstrating how to use the enhanced knowledge base and knowledge graph integrations
to extract deeper insights for restaurant recommendation.
"""

import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the parent directory to the path so we can import modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from integrations.cross_db_insights import CrossDBInsights
from utils.config import MONGODB_URI, NEO4J_URI

# Initialize rich console
console = Console()

def main():
    """Main function demonstrating the enhanced knowledge base and graph capabilities."""
    console.print(Panel("Restaurant Advisor - Enhanced Knowledge Base Demo", style="bold blue"))
    
    # Initialize the knowledge base and graph
    console.print("[yellow]Connecting to MongoDB knowledge base...[/yellow]")
    try:
        kb = MongoKnowledgeBase()
        console.print("[green]Successfully connected to MongoDB![/green]")
    except Exception as e:
        console.print(f"[red]Error connecting to MongoDB: {str(e)}[/red]")
        console.print(f"[yellow]Please check your MongoDB connection settings. URI: {MONGODB_URI}[/yellow]")
        return
    
    console.print("[yellow]Connecting to Neo4j knowledge graph...[/yellow]")
    try:
        kg = Neo4jKnowledgeGraph()
        console.print("[green]Successfully connected to Neo4j![/green]")
    except Exception as e:
        console.print(f"[red]Error connecting to Neo4j: {str(e)}[/red]")
        console.print(f"[yellow]Please check your Neo4j connection settings. URI: {NEO4J_URI}[/yellow]")
        return
    
    # Initialize the cross-database integration
    insights = CrossDBInsights(kb, kg)
    
    # Demo 1: Get document topics from MongoDB
    console.print("\n[bold]Document Topics in Knowledge Base:[/bold]")
    topics = kb.get_document_topics()
    
    topic_table = Table(title="Top Topics in Knowledge Base")
    topic_table.add_column("Topic", style="cyan")
    topic_table.add_column("Count", style="green")
    
    for topic, count in list(topics.items())[:10]:  # Show top 10 topics
        topic_table.add_row(topic, str(count))
    
    console.print(topic_table)
    
    # Demo 2: Get recent market trends
    console.print("\n[bold]Recent Market Trends:[/bold]")
    trends = kb.get_recent_market_trends(year_threshold=2023)
    
    for i, trend in enumerate(trends[:3]):
        console.print(f"[cyan]Trend {i+1}:[/cyan]")
        console.print(f"Source: {trend.metadata.get('source', 'Unknown')}")
        console.print(trend.page_content[:300] + "...\n")
    
    # Demo 3: Get comprehensive insights for a city
    city = "Mumbai"
    cuisine = "Italian"
    console.print(f"\n[bold]Comprehensive Insights for {cuisine} Restaurant in {city}:[/bold]")
    
    city_insights = insights.get_comprehensive_city_insights(city, cuisine)
    
    # Display structured data
    console.print("[cyan]Top Recommended Locations:[/cyan]")
    for loc in city_insights["structured_data"]["recommended_locations"]:
        console.print(f"- {loc.get('area', 'Unknown')}: {loc.get('type', 'Commercial')} area")
    
    console.print("\n[cyan]Popular Cuisines:[/cyan]")
    for cuisine in city_insights["structured_data"]["cuisine_preferences"]:
        console.print(f"- {cuisine.get('cuisine_type', 'Unknown')}: {cuisine.get('popularity', 0)} locations")
    
    # Display unstructured insights
    console.print("\n[cyan]Market Trends:[/cyan]")
    for trend in city_insights["unstructured_data"]["market_trends"]:
        console.print(f"- {trend[:150]}...")
    
    # Demo 4: Calculate opportunity score
    console.print(f"\n[bold]Restaurant Opportunity Score - {cuisine} in {city}:[/bold]")
    score = insights.get_restaurant_opportunity_score(city, "Bandra", cuisine)
    
    console.print(f"[cyan]Overall Score:[/cyan] [bold]{score['opportunity_score']}/10[/bold]")
    console.print(f"[cyan]Interpretation:[/cyan] {score['interpretation']}")
    
    score_table = Table(title="Score Components")
    score_table.add_column("Component", style="cyan")
    score_table.add_column("Score", style="green")
    
    for component, component_score in score["components"].items():
        score_table.add_row(component.replace("_", " ").title(), f"{component_score:.1f}/10")
    
    console.print(score_table)
    
    # Demo 5: Find market gaps
    console.print(f"\n[bold]Market Gaps in {city}:[/bold]")
    gaps = insights.find_market_gaps(city)
    
    gap_table = Table(title=f"Cuisine Gaps in {city}")
    gap_table.add_column("Cuisine", style="cyan")
    gap_table.add_column("Mentions", style="green")
    
    for gap in gaps["identified_gaps"]:
        gap_table.add_row(gap["cuisine"].title(), str(gap["mentions"]))
    
    console.print(gap_table)
    
    # Show a sample supporting insight for the top gap
    if gaps["identified_gaps"]:
        top_gap = gaps["identified_gaps"][0]["cuisine"]
        if top_gap in gaps["supporting_insights"]:
            console.print(f"\n[cyan]Supporting Insight for {top_gap.title()}:[/cyan]")
            console.print(gaps["supporting_insights"][top_gap][0][:300] + "...")
    
    console.print("\n[green]Enhanced knowledge base demo completed![/green]")

if __name__ == "__main__":
    main()
