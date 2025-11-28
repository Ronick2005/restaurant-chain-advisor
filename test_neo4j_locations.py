import os
import json
from restaurant_advisor.kg.neo4j_kg import Neo4jKnowledgeGraph

# Set environment variables
os.environ['NEO4J_URI'] = 'neo4j+s://485f2797.databases.neo4j.io'
os.environ['NEO4J_USERNAME'] = 'neo4j'
os.environ['NEO4J_PASSWORD'] = 'gIQcttXK58fKXSG3oCV7MYZityMz9SScfwnSoK6dAqU'

# Connect to Neo4j
kg = Neo4jKnowledgeGraph()

try:
    # Get cities
    with kg.driver.session() as session:
        print("=== Cities in the database ===")
        city_result = session.run("MATCH (c:City) RETURN c.name, c.state, c.population LIMIT 5")
        for record in city_result:
            print(record)

    # Get locations
    with kg.driver.session() as session:
        print("\n=== Locations in the database ===")
        location_result = session.run("MATCH (l:Location) RETURN l.id, l.area, l.type LIMIT 5")
        for record in location_result:
            print(record)
    
    # Get location properties
    with kg.driver.session() as session:
        print("\n=== Location properties ===")
        props_result = session.run("MATCH (l:Location {id: 'mumbai_bandra_west'}) RETURN properties(l) as props")
        record = props_result.single()
        if record:
            print(json.dumps(record["props"], indent=2))
        else:
            print("No properties found")

    # Try recommendation
    print("\n=== Recommendations for Mumbai with North Indian cuisine ===")
    recommendations = kg.recommend_locations('Mumbai', cuisine_type='North Indian')
    print(json.dumps(recommendations, indent=2))

    # List all properties for debugging
    with kg.driver.session() as session:
        print("\n=== All properties for mumbai_bandra_west ===")
        props_result = session.run("MATCH (l:Location {id: 'mumbai_bandra_west'}) RETURN l")
        record = props_result.single()
        if record:
            node = record["l"]
            for key in node.keys():
                print(f"{key}: {node[key]}")
        else:
            print("Location not found")

finally:
    kg.close()
