import os
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional

from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from agents.orchestrator import AgentOrchestrator
from agents.enhanced_orchestrator import EnhancedAgentOrchestrator
from utils.auth import authenticate_user, create_user, get_users
from utils.config import ROLES

# Initialize rich console
console = Console()

app = typer.Typer()

# Set the callback to run the main function when no command is provided
@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Restaurant Chain Advisor System"""
    if ctx.invoked_subcommand is None:
        # If no subcommand was specified, run the main function
        main()

def get_kb_connection():
    """Get a connection to the MongoDB knowledge base."""
    try:
        return MongoKnowledgeBase()
    except Exception as e:
        console.print(f"[bold red]Error connecting to MongoDB:[/bold red] {str(e)}")
        console.print("Please check your MongoDB Atlas connection settings in .env file")
        return None

def get_kg_connection():
    """Get a connection to the Neo4j knowledge graph."""
    try:
        return Neo4jKnowledgeGraph()
    except Exception as e:
        console.print(f"[bold red]Error connecting to Neo4j:[/bold red] {str(e)}")
        console.print("Please check your Neo4j Aura connection settings in .env file")
        return None

def display_welcome():
    """Display welcome message."""
    console.print(Panel(
        Text("Restaurant Chain Advisor System", style="bold blue"), 
        subtitle="Powered by LangChain, LangGraph, MongoDB and Neo4j"
    ))
    console.print("\nThis system helps you set up restaurant chains across Indian cities.")
    console.print("It provides location recommendations, regulatory information, and market analysis.\n")

@app.command()
def login(username: str = None, password: str = None):
    """Login to the system."""
    if not username:
        username = Prompt.ask("[bold cyan]Username[/bold cyan]")
    if not password:
        password = Prompt.ask("[bold cyan]Password[/bold cyan]", password=True)
    
    user = authenticate_user(username, password)
    if not user:
        console.print("[bold red]Invalid username or password[/bold red]")
        return None
    
    console.print(f"[bold green]Welcome, {user['full_name']}![/bold green]")
    console.print(f"Role: [bold]{user['role']}[/bold]")
    
    return user

@app.command()
def create_admin():
    """Create an admin user."""
    console.print("\n[bold cyan]Create Admin User[/bold cyan]")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    full_name = Prompt.ask("Full Name")
    
    if create_user(username, password, "admin", full_name):
        console.print("[bold green]Admin user created successfully![/bold green]")
    else:
        console.print("[bold red]Failed to create admin user. Username may already exist.[/bold red]")

@app.command()
def create_new_user(current_user):
    """Create a new user (admin only)."""
    if current_user["role"] != "admin":
        console.print("[bold red]Only administrators can create new users.[/bold red]")
        return
    
    console.print("\n[bold cyan]Create New User[/bold cyan]")
    username = Prompt.ask("Username")
    password = Prompt.ask("Password", password=True)
    full_name = Prompt.ask("Full Name")
    
    # Display available roles
    console.print("\nAvailable roles:")
    for role in ROLES:
        console.print(f"- {role}")
    
    role = Prompt.ask("Role", choices=list(ROLES.keys()))
    
    if create_user(username, password, role, full_name):
        console.print(f"[bold green]User '{username}' created successfully with role '{role}'![/bold green]")
    else:
        console.print("[bold red]Failed to create user. Username may already exist.[/bold red]")

@app.command()
def list_users(current_user):
    """List all users (admin only)."""
    if current_user["role"] != "admin":
        console.print("[bold red]Only administrators can view user list.[/bold red]")
        return
    
    users = get_users()
    
    table = Table(title="System Users")
    table.add_column("Username", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Full Name")
    
    for username, user_data in users.items():
        table.add_row(username, user_data["role"], user_data["full_name"])
    
    console.print(table)

@app.command()
def location_insights():
    """Get detailed location insights for restaurant locations from the knowledge graph."""
    # Get connections to knowledge base and graph
    kb = get_kb_connection()
    kg = get_kg_connection()
    
    if not kb or not kg:
        console.print("[bold red]Cannot generate location insights without database connections.[/bold red]")
        return
    
    console.print(Panel("Restaurant Location Intelligence", style="bold blue"))
    
    # Get city selection from user
    city = Prompt.ask("[bold cyan]Which city are you interested in?[/bold cyan]", default="Chennai")
    
    # Get cuisine type
    cuisine_type = Prompt.ask("[bold cyan]What type of cuisine?[/bold cyan]", default="Vegan")
    
    console.print("\n[yellow]Loading location data from knowledge graph...[/yellow]")
    
    # Get city demographics
    try:
        city_data = kg.get_detailed_city_demographics(city)
        if not city_data:
            console.print(f"[bold red]No data found for city: {city}[/bold red]")
            return
            
        # Display city info
        console.print(f"\n[bold]City Information:[/bold] {city}")
        console.print(f"Population: {city_data.get('population', 'Unknown')}")
        
        if city_data.get('demographics'):
            console.print("\n[bold]Demographics:[/bold]")
            for demo in city_data.get('demographics', []):
                console.print(f"- {demo}")
        
        if city_data.get('key_markets'):
            console.print("\n[bold]Key Markets:[/bold]")
            for market in city_data.get('key_markets', []):
                console.print(f"- {market}")
        
        # Get location recommendations
        locations = kg.get_detailed_location_info(city)
        
        # Filter by cuisine if specified
        if cuisine_type:
            console.print(f"\n[bold]Looking for {cuisine_type} restaurant locations...[/bold]")
        
        # Get regulations
        regulations = kg.get_regulatory_info(city)
        
        # Get cuisine preferences 
        cuisine_prefs = kg.get_cuisine_preferences(city)
        
        # Display location recommendations
        console.print(f"\n[bold]Top Recommended Locations in {city}:[/bold]")
        
        table = Table(title=f"Location Recommendations for {cuisine_type} Restaurant in {city}")
        table.add_column("Area", style="cyan")
        table.add_column("Foot Traffic", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Rent Range", style="yellow")
        table.add_column("Popular Cuisines", style="magenta")
        
        for loc in locations[:5]:  # Show top 5 locations
            area = loc.get('area', 'Unknown')
            foot_traffic = str(loc.get('foot_traffic', 'Unknown'))
            loc_type = loc.get('type', 'Unknown')
            rent_range = loc.get('rent_range', 'Unknown')
            popular_cuisines = ", ".join(loc.get('popular_cuisines', [])) if loc.get('popular_cuisines') else "Unknown"
            
            table.add_row(area, foot_traffic, loc_type, rent_range, popular_cuisines)
        
        console.print(table)
        
        # Display cuisine preferences
        console.print(f"\n[bold]Popular Cuisines in {city}:[/bold]")
        cuisine_table = Table(title="Cuisine Popularity")
        cuisine_table.add_column("Cuisine", style="cyan")
        cuisine_table.add_column("Popularity", style="green")
        
        for cuisine in cuisine_prefs[:5]:
            cuisine_table.add_row(cuisine.get('cuisine_type', 'Unknown'), str(cuisine.get('popularity', 0)))
        
        console.print(cuisine_table)
        
        # Display regulations
        if regulations:
            console.print(f"\n[bold]Key Regulations in {city}:[/bold]")
            for reg in regulations[:3]:
                console.print(f"- {reg.get('type', 'Regulation')}: {reg.get('description', 'No description')}")
        
        # Document-based insights
        console.print("\n[yellow]Retrieving additional insights from knowledge base...[/yellow]")
        
        query = f"{cuisine_type} restaurant {city} market trends"
        docs = kb.hybrid_search(query, k=2)
        
        if docs:
            console.print(f"\n[bold]Market Insights for {cuisine_type} Restaurants:[/bold]")
            for doc in docs:
                console.print(f"- Source: {doc.metadata.get('source', 'Unknown')}")
                content = doc.page_content
                # Truncate content to a reasonable length
                if len(content) > 300:
                    content = content[:300] + "..."
                console.print(f"  {content}")
        
    except Exception as e:
        console.print(f"[bold red]Error retrieving location data: {str(e)}[/bold red]")
        return
    
    # Ask if user wants to save the results
    save_results = Confirm.ask("\nWould you like to save these recommendations to a file?")
    
    if save_results:
        filename = Prompt.ask("Enter a filename to save to", default=f"{city}_recommendations.txt")
        try:
            with open(filename, "w") as f:
                f.write(f"Location Recommendations for {city}\n")
                f.write(f"Cuisine: {cuisine_type}\n\n")
                
                # Write city info
                f.write(f"City Information: {city}\n")
                f.write(f"Population: {city_data.get('population', 'Unknown')}\n\n")
                
                # Write demographics
                if city_data.get('demographics'):
                    f.write("Demographics:\n")
                    for demo in city_data.get('demographics', []):
                        f.write(f"- {demo}\n")
                    f.write("\n")
                
                # Write locations
                f.write(f"Top Recommended Locations in {city}:\n")
                for loc in locations[:5]:
                    area = loc.get('area', 'Unknown')
                    foot_traffic = str(loc.get('foot_traffic', 'Unknown'))
                    loc_type = loc.get('type', 'Unknown')
                    rent_range = loc.get('rent_range', 'Unknown')
                    f.write(f"- {area}: {loc_type}, Foot Traffic: {foot_traffic}, Rent: {rent_range}\n")
                
                # Write regulations
                if regulations:
                    f.write("\nKey Regulations:\n")
                    for reg in regulations[:3]:
                        f.write(f"- {reg.get('type', 'Regulation')}: {reg.get('description', 'No description')}\n")
                
            console.print(f"[green]Recommendations saved to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving file: {str(e)}[/red]")
    
    console.print(f"\n[bold green]{city} Location Intelligence analysis complete![/bold green]")

@app.command()
def chat(current_user):
    """Start a chat session with the advisor system."""
    # Get connections to knowledge base and graph
    kb = get_kb_connection()
    kg = get_kg_connection()
    
    if not kb or not kg:
        console.print("[bold red]Cannot start chat session without database connections.[/bold red]")
        return
    
    # Initialize the enhanced agent orchestrator
    orchestrator = EnhancedAgentOrchestrator(kb, kg)
    
    # Load memory from disk if available
    try:
        orchestrator.load_memory_from_disk()
        console.print("[green]Previous conversation history loaded.[/green]")
    except Exception:
        console.print("[yellow]Starting with fresh conversation history.[/yellow]")
    
    console.print("\n[bold green]Chat session started![/bold green]")
    console.print("Type 'exit' or 'quit' to end the session.\n")
    
    # Display role-specific welcome message
    role = current_user["role"]
    if role == "admin":
        console.print("[blue]You have full access to all system capabilities.[/blue]")
        console.print("[blue]Available domains: location, regulatory, market analysis, research, cuisine, finance, marketing, technology, staffing, design.[/blue]")
    elif role == "analyst":
        console.print("[blue]You have access to market analysis, location recommendations, and regulatory information.[/blue]")
        console.print("[blue]Available domains: market analysis, location, regulatory.[/blue]")
    elif role == "restaurant_owner":
        console.print("[blue]You have access to location recommendations, regulatory information, and basic domain expertise.[/blue]")
        console.print("[blue]Available domains: location, regulatory, cuisine, design.[/blue]")
    else:  # guest
        console.print("[blue]You have limited access to basic queries only.[/blue]")
    
    # Chat loop
    while True:
        query = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        
        if query.lower() in ["exit", "quit"]:
            break
        
        console.print("[bold yellow]Processing...[/bold yellow]")
        
        try:
            response = orchestrator.run(query, current_user)
            console.print(f"\n[bold green]Advisor[/bold green]:\n{response}")
            
            # Save memory periodically
            try:
                orchestrator.save_memory_to_disk()
            except Exception as e:
                console.print(f"[yellow]Note: Unable to save conversation memory: {str(e)}[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
    
    # Final save of memory before exiting
    try:
        orchestrator.save_memory_to_disk()
    except Exception:
        pass
    
    console.print("\n[bold green]Chat session ended.[/bold green]")

@app.command()
def main():
    """Main entry point for the application."""
    display_welcome()
    
    # Check for existing users
    users = get_users()
    if not users:
        console.print("[bold yellow]No users found. Creating default admin user...[/bold yellow]")
        create_admin()
    
    # Login
    current_user = login()
    if not current_user:
        return
    
    # Main menu loop
    while True:
        console.print("\n[bold cyan]Main Menu[/bold cyan]")
        options = ["Chat with Advisor", "Location Intelligence", "Exit"]
        
        # Add admin-specific options
        if current_user["role"] == "admin":
            options.insert(2, "List Users")
            options.insert(2, "Create New User")
        
        for i, option in enumerate(options, 1):
            console.print(f"{i}. {option}")
        
        choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, len(options) + 1)])
        choice = int(choice)
        
        if choice == 1:
            # Chat with advisor
            chat(current_user)
        elif choice == 2:
            # Location Intelligence
            location_insights()
        elif current_user["role"] == "admin" and choice == 3:
            # Create new user
            create_new_user(current_user)
        elif current_user["role"] == "admin" and choice == 4:
            # List users
            list_users(current_user)
        elif choice == len(options):
            # Exit
            console.print("[bold green]Thank you for using Restaurant Chain Advisor![/bold green]")
            break

if __name__ == "__main__":
    app()
