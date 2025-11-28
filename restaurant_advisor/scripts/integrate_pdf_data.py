"""
Script to extract data from PDFs and populate the knowledge graph with information from documents.
This script enhances the restaurant advisor by incorporating insights from research papers and documents.
"""

import os
import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PDF extractor and KG connector
from scripts.pdf_extractor import PDFExtractor
from kg.neo4j_kg import Neo4jKnowledgeGraph

def extract_pdf_data(data_dir: str, output_dir: str) -> Dict[str, Any]:
    """Extract data from PDFs in the data directory.
    
    Args:
        data_dir: Path to directory with PDF files
        output_dir: Path to directory to save extracted data
        
    Returns:
        Dictionary with extracted data
    """
    print(f"Extracting data from PDFs in {data_dir}...")
    extractor = PDFExtractor(data_dir)
    results = extractor.process_all_pdfs()
    
    # Save results to JSON file
    output_path = os.path.join(output_dir, "pdf_extracted_data.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Extracted data saved to {output_path}")
    
    return results

def add_pdf_data_to_kg(kg: Neo4jKnowledgeGraph, pdf_data: Dict[str, Any]) -> None:
    """Add extracted PDF data to the knowledge graph.
    
    Args:
        kg: Neo4j knowledge graph instance
        pdf_data: Dictionary with extracted PDF data
    """
    print("Adding PDF data to knowledge graph...")
    
    # Process city-specific information
    city_info = {}
    for pdf_name, data in pdf_data.items():
        if "city_specific" in data and data["city_specific"]:
            for city, info in data["city_specific"].items():
                if city not in city_info:
                    city_info[city] = []
                for item in info:
                    if item not in city_info[city]:
                        city_info[city].append({
                            "source": pdf_name,
                            "info": item
                        })
    
    # Add city insights from PDFs
    print("Adding city insights from PDFs...")
    for city, insights in city_info.items():
        if insights:
            # Use Neo4j session directly to add PDF insights to existing city nodes
            with kg.driver.session() as session:
                session.run("""
                    MATCH (c:City {name: $city})
                    SET c.pdf_insights = $insights
                """, city=city, insights=[i["info"] for i in insights])
                
                session.run("""
                    MATCH (c:City {name: $city})
                    SET c.pdf_sources = $sources
                """, city=city, sources=list(set([i["source"] for i in insights])))
                
            print(f"  Added {len(insights)} insights to {city}")
    
    # Process regulatory information
    regulation_info = {}
    for pdf_name, data in pdf_data.items():
        if "regulations" in data and data["regulations"]:
            # Process licensing requirements
            if "licensing_requirements" in data["regulations"]:
                for req in data["regulations"]["licensing_requirements"]:
                    # Try to identify which city this applies to
                    for city in city_info.keys():
                        if city.lower() in req.lower():
                            if city not in regulation_info:
                                regulation_info[city] = {"licensing": [], "safety": [], "standards": []}
                            if req not in regulation_info[city]["licensing"]:
                                regulation_info[city]["licensing"].append({
                                    "source": pdf_name,
                                    "info": req
                                })
                    
            # Process health and safety
            if "health_safety" in data["regulations"]:
                for req in data["regulations"]["health_safety"]:
                    # Try to identify which city this applies to
                    for city in city_info.keys():
                        if city.lower() in req.lower():
                            if city not in regulation_info:
                                regulation_info[city] = {"licensing": [], "safety": [], "standards": []}
                            if req not in regulation_info[city]["safety"]:
                                regulation_info[city]["safety"].append({
                                    "source": pdf_name,
                                    "info": req
                                })
            
            # Process food standards
            if "food_standards" in data["regulations"]:
                for req in data["regulations"]["food_standards"]:
                    # Try to identify which city this applies to
                    for city in city_info.keys():
                        if city.lower() in req.lower():
                            if city not in regulation_info:
                                regulation_info[city] = {"licensing": [], "safety": [], "standards": []}
                            if req not in regulation_info[city]["standards"]:
                                regulation_info[city]["standards"].append({
                                    "source": pdf_name,
                                    "info": req
                                })
    
    # Add regulation insights from PDFs
    print("Adding regulation insights from PDFs...")
    for city, reg_types in regulation_info.items():
        
        # Add licensing requirements
        if reg_types["licensing"]:
            kg.add_city_regulation(
                city=city,
                reg_type="PDF Extracted Licensing",
                description=f"Licensing requirements extracted from research documents",
                authority="Various",
                requirements=[item["info"] for item in reg_types["licensing"]]
            )
            print(f"  Added {len(reg_types['licensing'])} licensing insights to {city}")
            
        # Add health and safety
        if reg_types["safety"]:
            kg.add_city_regulation(
                city=city,
                reg_type="PDF Extracted Health & Safety",
                description=f"Health and safety requirements extracted from research documents",
                authority="Various",
                requirements=[item["info"] for item in reg_types["safety"]]
            )
            print(f"  Added {len(reg_types['safety'])} safety insights to {city}")
            
        # Add food standards
        if reg_types["standards"]:
            kg.add_city_regulation(
                city=city,
                reg_type="PDF Extracted Food Standards",
                description=f"Food standards requirements extracted from research documents",
                authority="Various",
                requirements=[item["info"] for item in reg_types["standards"]]
            )
            print(f"  Added {len(reg_types['standards'])} standards insights to {city}")
    
    # Process consumer preferences
    preference_info = {}
    for pdf_name, data in pdf_data.items():
        if "consumer_preferences" in data and data["consumer_preferences"]:
            # Process food trends
            if "food_trends" in data["consumer_preferences"]:
                for trend in data["consumer_preferences"]["food_trends"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in trend.lower():
                            city_found = True
                            if city not in preference_info:
                                preference_info[city] = {"trends": [], "cuisines": [], "dietary": []}
                            if trend not in preference_info[city]["trends"]:
                                preference_info[city]["trends"].append({
                                    "source": pdf_name,
                                    "info": trend
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in preference_info:
                            preference_info["General"] = {"trends": [], "cuisines": [], "dietary": []}
                        if trend not in preference_info["General"]["trends"]:
                            preference_info["General"]["trends"].append({
                                "source": pdf_name,
                                "info": trend
                            })
                    
            # Process popular cuisines
            if "popular_cuisines" in data["consumer_preferences"]:
                for cuisine in data["consumer_preferences"]["popular_cuisines"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in cuisine.lower():
                            city_found = True
                            if city not in preference_info:
                                preference_info[city] = {"trends": [], "cuisines": [], "dietary": []}
                            if cuisine not in preference_info[city]["cuisines"]:
                                preference_info[city]["cuisines"].append({
                                    "source": pdf_name,
                                    "info": cuisine
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in preference_info:
                            preference_info["General"] = {"trends": [], "cuisines": [], "dietary": []}
                        if cuisine not in preference_info["General"]["cuisines"]:
                            preference_info["General"]["cuisines"].append({
                                "source": pdf_name,
                                "info": cuisine
                            })
            
            # Process dietary preferences
            if "dietary_preferences" in data["consumer_preferences"]:
                for pref in data["consumer_preferences"]["dietary_preferences"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in pref.lower():
                            city_found = True
                            if city not in preference_info:
                                preference_info[city] = {"trends": [], "cuisines": [], "dietary": []}
                            if pref not in preference_info[city]["dietary"]:
                                preference_info[city]["dietary"].append({
                                    "source": pdf_name,
                                    "info": pref
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in preference_info:
                            preference_info["General"] = {"trends": [], "cuisines": [], "dietary": []}
                        if pref not in preference_info["General"]["dietary"]:
                            preference_info["General"]["dietary"].append({
                                "source": pdf_name,
                                "info": pref
                            })
    
    # Add consumer preference insights from PDFs to knowledge graph
    print("Adding consumer preference insights from PDFs...")
    for city, pref_types in preference_info.items():
        # For general preferences, create a node that's not linked to specific cities
        if city == "General":
            # Use Neo4j session directly to create a node for general preferences
            with kg.driver.session() as session:
                session.run("""
                    MERGE (p:Preferences {name: 'General Food Preferences'})
                    SET p.food_trends = $trends,
                        p.popular_cuisines = $cuisines,
                        p.dietary_preferences = $dietary,
                        p.sources = $sources
                """, 
                trends=[item["info"] for item in pref_types["trends"]],
                cuisines=[item["info"] for item in pref_types["cuisines"]],
                dietary=[item["info"] for item in pref_types["dietary"]],
                sources=list(set([i["source"] for items in pref_types.values() for i in items]))
                )
            print(f"  Added general preference insights: {len(pref_types['trends'])} trends, {len(pref_types['cuisines'])} cuisines, {len(pref_types['dietary'])} dietary preferences")
        else:
            # Use Neo4j session to add preferences to specific cities
            with kg.driver.session() as session:
                # Create preferences node
                session.run("""
                    MATCH (c:City {name: $city})
                    MERGE (p:Preferences {name: $name})
                    SET p.food_trends = $trends,
                        p.popular_cuisines = $cuisines,
                        p.dietary_preferences = $dietary,
                        p.sources = $sources
                    MERGE (c)-[:HAS_PREFERENCES]->(p)
                """, 
                city=city,
                name=f"{city} Food Preferences",
                trends=[item["info"] for item in pref_types["trends"]],
                cuisines=[item["info"] for item in pref_types["cuisines"]],
                dietary=[item["info"] for item in pref_types["dietary"]],
                sources=list(set([i["source"] for items in pref_types.values() for i in items]))
                )
            print(f"  Added {city} preference insights: {len(pref_types['trends'])} trends, {len(pref_types['cuisines'])} cuisines, {len(pref_types['dietary'])} dietary preferences")
    
    # Process real estate information
    realestate_info = {}
    for pdf_name, data in pdf_data.items():
        if "real_estate" in data and data["real_estate"]:
            # Process location trends
            if "location_trends" in data["real_estate"]:
                for trend in data["real_estate"]["location_trends"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in trend.lower():
                            city_found = True
                            if city not in realestate_info:
                                realestate_info[city] = {"location_trends": [], "rental": [], "regulations": []}
                            if trend not in realestate_info[city]["location_trends"]:
                                realestate_info[city]["location_trends"].append({
                                    "source": pdf_name,
                                    "info": trend
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in realestate_info:
                            realestate_info["General"] = {"location_trends": [], "rental": [], "regulations": []}
                        if trend not in realestate_info["General"]["location_trends"]:
                            realestate_info["General"]["location_trends"].append({
                                "source": pdf_name,
                                "info": trend
                            })
                    
            # Process rental insights
            if "rental_insights" in data["real_estate"]:
                for insight in data["real_estate"]["rental_insights"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in insight.lower():
                            city_found = True
                            if city not in realestate_info:
                                realestate_info[city] = {"location_trends": [], "rental": [], "regulations": []}
                            if insight not in realestate_info[city]["rental"]:
                                realestate_info[city]["rental"].append({
                                    "source": pdf_name,
                                    "info": insight
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in realestate_info:
                            realestate_info["General"] = {"location_trends": [], "rental": [], "regulations": []}
                        if insight not in realestate_info["General"]["rental"]:
                            realestate_info["General"]["rental"].append({
                                "source": pdf_name,
                                "info": insight
                            })
            
            # Process property regulations
            if "property_regulations" in data["real_estate"]:
                for reg in data["real_estate"]["property_regulations"]:
                    # Try to identify which city this applies to
                    city_found = False
                    for city in city_info.keys():
                        if city.lower() in reg.lower():
                            city_found = True
                            if city not in realestate_info:
                                realestate_info[city] = {"location_trends": [], "rental": [], "regulations": []}
                            if reg not in realestate_info[city]["regulations"]:
                                realestate_info[city]["regulations"].append({
                                    "source": pdf_name,
                                    "info": reg
                                })
                    
                    # If no specific city, add to general trends
                    if not city_found:
                        if "General" not in realestate_info:
                            realestate_info["General"] = {"location_trends": [], "rental": [], "regulations": []}
                        if reg not in realestate_info["General"]["regulations"]:
                            realestate_info["General"]["regulations"].append({
                                "source": pdf_name,
                                "info": reg
                            })
    
    # Add real estate insights from PDFs to knowledge graph
    print("Adding real estate insights from PDFs...")
    for city, re_types in realestate_info.items():
        # For general real estate info, create a node that's not linked to specific cities
        if city == "General":
            # Use Neo4j session directly to create a node for general real estate info
            with kg.driver.session() as session:
                session.run("""
                    MERGE (r:RealEstate {name: 'General Real Estate Information'})
                    SET r.location_trends = $trends,
                        r.rental_insights = $rental,
                        r.property_regulations = $regulations,
                        r.sources = $sources
                """, 
                trends=[item["info"] for item in re_types["location_trends"]],
                rental=[item["info"] for item in re_types["rental"]],
                regulations=[item["info"] for item in re_types["regulations"]],
                sources=list(set([i["source"] for items in re_types.values() for i in items]))
                )
            print(f"  Added general real estate insights: {len(re_types['location_trends'])} location trends, {len(re_types['rental'])} rental insights, {len(re_types['regulations'])} property regulations")
        else:
            # Use Neo4j session to add real estate info to specific cities
            with kg.driver.session() as session:
                # Create real estate node
                session.run("""
                    MATCH (c:City {name: $city})
                    MERGE (r:RealEstate {name: $name})
                    SET r.location_trends = $trends,
                        r.rental_insights = $rental,
                        r.property_regulations = $regulations,
                        r.sources = $sources
                    MERGE (c)-[:HAS_REALESTATE_INFO]->(r)
                """, 
                city=city,
                name=f"{city} Real Estate Information",
                trends=[item["info"] for item in re_types["location_trends"]],
                rental=[item["info"] for item in re_types["rental"]],
                regulations=[item["info"] for item in re_types["regulations"]],
                sources=list(set([i["source"] for items in re_types.values() for i in items]))
                )
            print(f"  Added {city} real estate insights: {len(re_types['location_trends'])} location trends, {len(re_types['rental'])} rental insights, {len(re_types['regulations'])} property regulations")

def main():
    """Main function to extract PDF data and add it to the knowledge graph."""
    parser = argparse.ArgumentParser(description="Extract data from PDFs and add it to the knowledge graph")
    parser.add_argument("--data-dir", type=str, default="../data", 
                        help="Directory containing PDF files")
    parser.add_argument("--output-dir", type=str, default="./extracted_data", 
                        help="Directory to save extracted data")
    parser.add_argument("--skip-extraction", action="store_true", 
                        help="Skip PDF extraction and use existing extracted data")
    args = parser.parse_args()
    
    # Ensure directories are absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(args.data_dir):
        args.data_dir = os.path.abspath(os.path.join(script_dir, args.data_dir))
    if not os.path.isabs(args.output_dir):
        args.output_dir = os.path.abspath(os.path.join(script_dir, args.output_dir))
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Extract PDF data or load existing data
    if args.skip_extraction:
        # Load existing extracted data
        json_path = os.path.join(args.output_dir, "pdf_extracted_data.json")
        if not os.path.exists(json_path):
            print(f"Error: No extracted data found at {json_path}")
            print("Run without --skip-extraction to extract data from PDFs")
            return 1
        
        print(f"Loading extracted data from {json_path}...")
        with open(json_path, 'r') as f:
            pdf_data = json.load(f)
    else:
        # Extract data from PDFs
        pdf_data = extract_pdf_data(args.data_dir, args.output_dir)
    
    # Connect to Neo4j knowledge graph
    kg = Neo4jKnowledgeGraph()
    
    try:
        # Add PDF data to knowledge graph
        add_pdf_data_to_kg(kg, pdf_data)
        print("Successfully added PDF data to knowledge graph")
        return 0
    except Exception as e:
        print(f"Error adding PDF data to knowledge graph: {str(e)}")
        return 1
    finally:
        kg.close()

if __name__ == "__main__":
    sys.exit(main())
