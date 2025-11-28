"""
Demonstration script for using the Location Intelligence Agent.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the location agent
from agents.location_agent import LocationIntelligenceAgent

# Load environment variables
load_dotenv()

def print_json(data):
    """Print JSON data in a formatted way"""
    print(json.dumps(data, indent=2))

def main():
    """Main demonstration function"""
    print("Location Intelligence Agent Demo")
    print("===============================")
    
    # Initialize the location agent (using default map service)
    agent = LocationIntelligenceAgent()
    print(f"Using map service: {agent.map_service.service_name}")
    
    # Example locations to analyze
    print("\n1. Analyzing a single location")
    location = "Bandra West, Mumbai, India"
    print(f"Analyzing location: {location}")
    result = agent.analyze_location(location)
    print_json(result)
    
    print("\n2. Comparing multiple locations")
    locations = [
        "Bandra West, Mumbai, India",
        "Powai, Mumbai, India",
        "Andheri East, Mumbai, India"
    ]
    print(f"Comparing locations: {', '.join(locations)}")
    result = agent.compare_locations(locations)
    print_json(result)
    
    print("\n3. Finding optimal location")
    center = "Mumbai, India"
    print(f"Finding optimal location around: {center}")
    result = agent.find_optimal_location(center, radius=10000)
    print_json(result)
    
    print("\n4. Calculating accessibility")
    target = "Juhu, Mumbai, India"
    population_centers = [
        "Andheri, Mumbai, India",
        "Bandra, Mumbai, India",
        "Santacruz, Mumbai, India"
    ]
    print(f"Calculating accessibility for {target} from {', '.join(population_centers)}")
    result = agent.calculate_accessibility(target, population_centers)
    print_json(result)
    
    print("\n5. Analyzing catchment area")
    location = "Lower Parel, Mumbai, India"
    print(f"Analyzing catchment area for: {location}")
    result = agent.analyze_catchment_area(location)
    print_json(result)
    
    print("\n6. Analyzing competition")
    location = "Colaba, Mumbai, India"
    print(f"Analyzing competition around: {location}")
    result = agent.analyze_competition(location, radius=2000)
    print_json(result)

if __name__ == "__main__":
    main()
