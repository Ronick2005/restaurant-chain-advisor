"""
Example script demonstrating how to use the enhanced restaurant advisor agent.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from agents.enhanced_advisor_agent import EnhancedRestaurantAdvisorAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.config import GEMINI_API_KEY

# Initialize rich console
console = Console()

def main():
    """Main function demonstrating the enhanced restaurant advisor agent."""
    console.print(Panel("Enhanced Restaurant Advisor Demo", style="bold blue"))
    
    # Initialize the knowledge base and graph
    console.print("[yellow]Connecting to MongoDB and Neo4j...[/yellow]")
    try:
        kb = MongoKnowledgeBase()
        kg = Neo4jKnowledgeGraph()
        console.print("[green]Successfully connected to knowledge sources![/green]")
    except Exception as e:
        console.print(f"[red]Error connecting to knowledge sources: {str(e)}[/red]")
        return
    
    # Initialize language model
    console.print("[yellow]Initializing language model...[/yellow]")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-pro-latest", google_api_key=GEMINI_API_KEY)
        console.print("[green]Language model initialized![/green]")
    except Exception as e:
        console.print(f"[red]Error initializing language model: {str(e)}[/red]")
        return
    
    # Initialize the enhanced advisor agent
    advisor = EnhancedRestaurantAdvisorAgent(llm, kb, kg)
    
    # Interactive demo
    console.print("\n[bold]Welcome to the Enhanced Restaurant Advisor![/bold]")
    console.print("This demo uses integrated knowledge from MongoDB and Neo4j to provide comprehensive restaurant advice.")
    
    while True:
        # Get user query and parameters
        query = Prompt.ask("\n[bold cyan]What would you like to know about starting a restaurant?[/bold cyan]")
        if query.lower() in ["exit", "quit"]:
            break
            
        city = Prompt.ask("[bold cyan]Which city are you interested in?[/bold cyan]", 
                         default="Mumbai")
        
        cuisine = Prompt.ask("[bold cyan]What cuisine are you planning to serve?[/bold cyan]", 
                            default="Italian")
        
        area = Prompt.ask("[bold cyan]Any specific area in mind? (optional)[/bold cyan]", 
                         default="")
        
        console.print("\n[bold yellow]Processing your request...[/bold yellow]")
        console.print("[yellow]This may take a moment as we gather insights from multiple knowledge sources[/yellow]\n")
        
        # Get the recommendation
        result = advisor.run(query, city, cuisine, area)
        
        # Display the result
        console.print(Panel(result, title="[bold green]Restaurant Advisor Recommendation[/bold green]", 
                           border_style="green", expand=False))
        
        continue_demo = Prompt.ask("\n[bold cyan]Would you like to ask another question?[/bold cyan] (y/n)", 
                                  choices=["y", "n"], default="y")
        
        if continue_demo.lower() != "y":
            break
    
    console.print("\n[bold green]Thank you for using the Enhanced Restaurant Advisor![/bold green]")

if __name__ == "__main__":
    main()
