import os
import json
from neo4j import GraphDatabase

# Set environment variables
os.environ['NEO4J_URI'] = 'neo4j+s://485f2797.databases.neo4j.io'
os.environ['NEO4J_USERNAME'] = 'neo4j'
os.environ['NEO4J_PASSWORD'] = 'gIQcttXK58fKXSG3oCV7MYZityMz9SScfwnSoK6dAqU'

# Connect directly to Neo4j
driver = GraphDatabase.driver(
    os.environ['NEO4J_URI'], 
    auth=(os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])
)

def recommend_locations(city, cuisine_type=None, min_score=0.5):
    with driver.session() as session:
        # Build the recommendation query
        query = """
            MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location)
            WHERE l.commercial = true
        """
        
        params = {"city": city}
        
        # Add cuisine type filtering if specified
        if cuisine_type:
            query += """
                AND (l.popular_cuisines IS NULL OR 
                     $cuisine_type IN l.popular_cuisines)
            """
            params["cuisine_type"] = cuisine_type
        
        # Calculate score
        query += """
            WITH l, (
                CASE WHEN l.foot_traffic IS NOT NULL 
                     THEN l.foot_traffic * 0.3 ELSE 0.0 END +
                CASE WHEN l.competition_score IS NOT NULL 
                     THEN (1.0 - l.competition_score) * 0.2 ELSE 0.0 END +
                CASE WHEN l.growth_potential IS NOT NULL 
                     THEN l.growth_potential * 0.2 ELSE 0.0 END +
                CASE WHEN l.rent_score IS NOT NULL 
                     THEN (1.0 - l.rent_score) * 0.3 ELSE 0.0 END
            ) AS score
            WHERE score >= $min_score
            RETURN l.id AS id, l.area AS area, l.type AS type, score,
                {
                    foot_traffic: l.foot_traffic,
                    competition_score: l.competition_score,
                    growth_potential: l.growth_potential,
                    rent_score: l.rent_score,
                    commercial: l.commercial,
                    popular_cuisines: l.popular_cuisines,
                    demographics: l.demographics
                } AS properties
            ORDER BY score DESC
            LIMIT 10
        """
        params["min_score"] = min_score
        
        try:
            result = session.run(query, **params)
            return [dict(record) for record in result]
        except Exception as e:
            print(f"Error executing recommendation query: {e}")
            return []

try:
    # Test general recommendation
    print("=== Mumbai Recommendations ===")
    recommendations = recommend_locations('Mumbai')
    print(json.dumps(recommendations, indent=2))
    
    # Test recommendations with cuisine filter
    print("\n=== Mumbai North Indian Recommendations ===")
    recommendations = recommend_locations('Mumbai', cuisine_type='North Indian')
    print(json.dumps(recommendations, indent=2))
    
    # Test with lower score threshold
    print("\n=== Mumbai Recommendations with lower score threshold ===")
    recommendations = recommend_locations('Mumbai', min_score=0.4)
    print(json.dumps(recommendations, indent=2))

finally:
    driver.close()
