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
    # Check locations with North Indian cuisine
    with kg.driver.session() as session:
        print("=== Locations with North Indian cuisine ===")
        result = session.run("""
            MATCH (c:City {name: 'Mumbai'})-[:HAS_LOCATION]->(l:Location)
            WHERE l.commercial = true AND 'North Indian' IN l.popular_cuisines
            RETURN l.id, l.area, l.popular_cuisines
        """)
        locations = list(result)
        if locations:
            for record in locations:
                print(record)
        else:
            print("No locations found with North Indian cuisine")
    
    # Check all popular cuisines
    with kg.driver.session() as session:
        print("\n=== All popular cuisines in Mumbai locations ===")
        result = session.run("""
            MATCH (c:City {name: 'Mumbai'})-[:HAS_LOCATION]->(l:Location)
            RETURN l.id, l.area, l.popular_cuisines
        """)
        for record in result:
            print(record)
    
    # Run a more generic recommendation query
    print("\n=== Recommendations for Mumbai (any cuisine) ===")
    with kg.driver.session() as session:
        result = session.run("""
            MATCH (c:City {name: 'Mumbai'})-[:HAS_LOCATION]->(l:Location)
            WHERE l.commercial = true
            WITH l, 
                 CASE WHEN l.foot_traffic IS NOT NULL 
                      THEN l.foot_traffic * 0.3 ELSE 0 END +
                 CASE WHEN l.competition_score IS NOT NULL 
                      THEN (1 - l.competition_score) * 0.2 ELSE 0 END +
                 CASE WHEN l.growth_potential IS NOT NULL 
                      THEN l.growth_potential * 0.2 ELSE 0 END +
                 CASE WHEN l.rent_score IS NOT NULL 
                      THEN (1 - l.rent_score) * 0.3 ELSE 0 END AS score
            WHERE score >= 0.6
            RETURN l.id AS id, l.area AS area, l.type AS type, score
            ORDER BY score DESC
            LIMIT 10
        """)
        recommendations = list(result)
        if recommendations:
            for record in recommendations:
                print(record)
        else:
            print("No recommendations found")
    
    # Use the API method directly
    print("\n=== Using the API method directly ===")
    recommendations = kg.recommend_locations('Mumbai')
    print(json.dumps(recommendations, indent=2))

finally:
    kg.close()
