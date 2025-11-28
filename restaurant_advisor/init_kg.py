import os
import argparse
import sys
from typing import Dict, List

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kg.neo4j_kg import Neo4jKnowledgeGraph
from utils.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

# Sample data for demonstration
SAMPLE_CITIES = [
    {
        "name": "Mumbai",
        "state": "Maharashtra",
        "population": 20400000,
        # Neo4j doesn't support nested dictionaries as properties
        # Convert demographics to a list of strings in "key:value" format
        "demographics": ["young_professionals:0.32", "families:0.45", "tourists:0.15", "students:0.08"],
        "key_markets": ["Bandra", "Andheri", "South Mumbai", "Navi Mumbai", "Worli"]
    },
    {
        "name": "Bangalore",
        "state": "Karnataka",
        "population": 12500000,
        "demographics": ["tech_workers:0.38", "young_professionals:0.25", "families:0.30", "students:0.07"],
        "key_markets": ["Koramangala", "Indiranagar", "Whitefield", "Electronic City", "MG Road"]
    },
    {
        "name": "Delhi",
        "state": "Delhi",
        "population": 31400000,
        "demographics": ["government_workers:0.20", "business_professionals:0.25", 
                         "families:0.40", "students:0.10", "tourists:0.05"],
        "key_markets": ["Connaught Place", "Khan Market", "Hauz Khas", "South Extension", "Saket"]
    }
]

# Updated to use flattened properties for Neo4j compatibility
SAMPLE_LOCATIONS = [
    # Mumbai locations
    {"city": "Mumbai", "area": "Bandra West", "type": "commercial", "properties": {
        "foot_traffic": 0.85, "competition_score": 0.70, "growth_potential": 0.75, 
        "rent_score": 0.85, "commercial": True, "popular_cuisines": ["Italian", "Continental", "Asian Fusion"],
        "demographics": ["young_professionals", "tourists"]
    }},
    {"city": "Mumbai", "area": "Lower Parel", "type": "commercial", "properties": {
        "foot_traffic": 0.80, "competition_score": 0.65, "growth_potential": 0.70, 
        "rent_score": 0.90, "commercial": True, "popular_cuisines": ["Modern Indian", "Asian", "Continental"],
        "demographics": ["business_professionals", "young_professionals"]
    }},
    {"city": "Mumbai", "area": "Powai", "type": "commercial", "properties": {
        "foot_traffic": 0.75, "competition_score": 0.60, "growth_potential": 0.85, 
        "rent_score": 0.70, "commercial": True, "popular_cuisines": ["North Indian", "Fast Casual", "South Indian"],
        "demographics": ["tech_workers", "students", "families"]
    }},
    
    # Bangalore locations
    {"city": "Bangalore", "area": "Koramangala", "type": "commercial", "properties": {
        "foot_traffic": 0.90, "competition_score": 0.80, "growth_potential": 0.85, 
        "rent_score": 0.75, "commercial": True, "popular_cuisines": ["South Indian", "North Indian", "Continental", "Asian"],
        "demographics": ["tech_workers", "young_professionals", "students"]
    }},
    {"city": "Bangalore", "area": "Indiranagar", "type": "commercial", "properties": {
        "foot_traffic": 0.85, "competition_score": 0.75, "growth_potential": 0.80, 
        "rent_score": 0.80, "commercial": True, "popular_cuisines": ["Pub Food", "Asian Fusion", "Continental"],
        "demographics": ["young_professionals", "tech_workers"]
    }},
    {"city": "Bangalore", "area": "Whitefield", "type": "commercial", "properties": {
        "foot_traffic": 0.70, "competition_score": 0.60, "growth_potential": 0.90, 
        "rent_score": 0.65, "commercial": True, "popular_cuisines": ["North Indian", "South Indian", "Fast Casual"],
        "demographics": ["tech_workers", "families"]
    }},
    
    # Delhi locations
    {"city": "Delhi", "area": "Connaught Place", "type": "commercial", "properties": {
        "foot_traffic": 0.95, "competition_score": 0.85, "growth_potential": 0.60, 
        "rent_score": 0.95, "commercial": True, "popular_cuisines": ["North Indian", "Continental", "Asian"],
        "demographics": ["business_professionals", "tourists", "young_professionals"]
    }},
    {"city": "Delhi", "area": "Hauz Khas", "type": "commercial", "properties": {
        "foot_traffic": 0.80, "competition_score": 0.75, "growth_potential": 0.70, 
        "rent_score": 0.80, "commercial": True, "popular_cuisines": ["North Indian", "Continental", "Asian Fusion"],
        "demographics": ["young_professionals", "students"]
    }},
    {"city": "Delhi", "area": "Saket", "type": "commercial", "properties": {
        "foot_traffic": 0.85, "competition_score": 0.70, "growth_potential": 0.80, 
        "rent_score": 0.75, "commercial": True, "popular_cuisines": ["North Indian", "Fast Casual", "Continental"],
        "demographics": ["families", "young_professionals"]
    }}
]

SAMPLE_REGULATIONS = [
    {"city": "Mumbai", "type": "FSSAI License", "description": "Food Safety and Standards Authority of India license required for all food businesses", 
     "authority": "FSSAI", "requirements": ["Business registration", "Kitchen layout plan", "List of food categories", "Medical fitness certificates for staff"]},
    {"city": "Mumbai", "type": "Health Trade License", "description": "Municipal license for operating food establishments", 
     "authority": "BMC", "requirements": ["Shop establishment license", "Fire NOC", "Building occupancy certificate", "Pest control certificate"]},
    {"city": "Mumbai", "type": "Liquor License", "description": "FL-3 License for serving alcohol in restaurant premises", 
     "authority": "State Excise Department", "requirements": ["Age above 25", "No criminal record", "Property ownership/rental agreement", "Other business licenses"]},
     
    {"city": "Bangalore", "type": "FSSAI License", "description": "Food Safety and Standards Authority of India license required for all food businesses", 
     "authority": "FSSAI", "requirements": ["Business registration", "Kitchen layout plan", "List of food categories", "Medical fitness certificates for staff"]},
    {"city": "Bangalore", "type": "Health Trade License", "description": "Municipal license for operating food establishments", 
     "authority": "BBMP", "requirements": ["Shop establishment license", "Fire NOC", "Building occupancy certificate", "Pest control certificate"]},
    {"city": "Bangalore", "type": "Liquor License", "description": "CL-9 License for serving alcohol in restaurant premises", 
     "authority": "Karnataka Excise Department", "requirements": ["Age above 21", "No criminal record", "Property ownership/rental agreement", "Other business licenses"]},
     
    {"city": "Delhi", "type": "FSSAI License", "description": "Food Safety and Standards Authority of India license required for all food businesses", 
     "authority": "FSSAI", "requirements": ["Business registration", "Kitchen layout plan", "List of food categories", "Medical fitness certificates for staff"]},
    {"city": "Delhi", "type": "Health Trade License", "description": "Municipal license for operating food establishments", 
     "authority": "MCD", "requirements": ["Shop establishment license", "Fire NOC", "Building occupancy certificate", "Pest control certificate"]},
    {"city": "Delhi", "type": "Liquor License", "description": "L-17 License for serving alcohol in restaurant premises", 
     "authority": "Delhi Excise Department", "requirements": ["Age above 25", "No criminal record", "Property ownership/rental agreement", "Other business licenses"]}
]

SAMPLE_CUISINES = [
    {"type": "North Indian", "popularity": ["Mumbai:0.80", "Delhi:0.95", "Bangalore:0.75"], 
     "demographics": ["families", "business_professionals", "tourists"]},
    {"type": "South Indian", "popularity": ["Mumbai:0.70", "Delhi:0.65", "Bangalore:0.90"], 
     "demographics": ["families", "students", "tech_workers"]},
    {"type": "Continental", "popularity": ["Mumbai:0.75", "Delhi:0.70", "Bangalore:0.85"], 
     "demographics": ["young_professionals", "business_professionals"]},
    {"type": "Asian Fusion", "popularity": ["Mumbai:0.85", "Delhi:0.75", "Bangalore:0.80"], 
     "demographics": ["young_professionals", "tech_workers"]},
    {"type": "Fast Casual", "popularity": ["Mumbai:0.80", "Delhi:0.85", "Bangalore:0.80"], 
     "demographics": ["students", "young_professionals", "families"]}
]

def initialize_kg():
    """Initialize the knowledge graph with sample data."""
    print(f"Connecting to Neo4j at {NEO4J_URI}")
    kg = Neo4jKnowledgeGraph()
    
    try:
        # Add cities
        print("Adding cities...")
        for city in SAMPLE_CITIES:
            kg.add_city(
                name=city["name"],
                state=city["state"],
                population=city["population"],
                demographics=city["demographics"],
                key_markets=city["key_markets"]
            )
        
        # Add locations
        print("Adding locations...")
        location_ids = []
        for location in SAMPLE_LOCATIONS:
            location_id = kg.add_location(
                city=location["city"],
                area=location["area"],
                location_type=location["type"],
                properties=location["properties"]
            )
            location_ids.append(location_id)
        
        # Connect nearby locations (this would be more complex in a real system)
        print("Adding location relationships...")
        # Mumbai connections
        kg.add_relation("mumbai_bandra_west", "mumbai_lower_parel", "NEAR", {"distance_km": 8})
        kg.add_relation("mumbai_lower_parel", "mumbai_powai", "NEAR", {"distance_km": 15})
        
        # Bangalore connections
        kg.add_relation("bangalore_koramangala", "bangalore_indiranagar", "NEAR", {"distance_km": 5})
        kg.add_relation("bangalore_indiranagar", "bangalore_whitefield", "NEAR", {"distance_km": 12})
        kg.add_relation("bangalore_koramangala", "bangalore_whitefield", "NEAR", {"distance_km": 15})
        
        # Delhi connections
        kg.add_relation("delhi_connaught_place", "delhi_hauz_khas", "NEAR", {"distance_km": 10})
        kg.add_relation("delhi_hauz_khas", "delhi_saket", "NEAR", {"distance_km": 7})
        kg.add_relation("delhi_connaught_place", "delhi_saket", "NEAR", {"distance_km": 15})
        
        # Add regulations
        print("Adding regulations...")
        for reg in SAMPLE_REGULATIONS:
            kg.add_city_regulation(
                city=reg["city"],
                reg_type=reg["type"],
                description=reg["description"],
                authority=reg["authority"],
                requirements=reg["requirements"]
            )
        
        # Add cuisines
        print("Adding cuisine data...")
        for cuisine in SAMPLE_CUISINES:
            kg.add_cuisine_data(
                cuisine_type=cuisine["type"],
                popularity=cuisine["popularity"],
                demographics=cuisine["demographics"]
            )
            
        print("\nKnowledge graph initialized successfully!")
        
    finally:
        kg.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the knowledge graph with sample data.")
    parser.add_argument("--reset", action="store_true", help="Reset the knowledge graph before initialization")
    
    args = parser.parse_args()
    initialize_kg()
