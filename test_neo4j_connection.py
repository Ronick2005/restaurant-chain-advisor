import os
import sys
import dotenv

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
dotenv.load_dotenv()

from restaurant_advisor.kg.neo4j_kg import Neo4jKnowledgeGraph

def test_neo4j_connection():
    """Test connection to Neo4j."""
    print("Testing Neo4j connection...")
    
    try:
        # Initialize Neo4j knowledge graph
        kg = Neo4jKnowledgeGraph()
        
        # Test city query
        with kg.driver.session() as session:
            result = session.run("MATCH (c:City) RETURN c.name LIMIT 3")
            cities = [record["c.name"] for record in result]
            
            if cities:
                print(f"Successfully connected to Neo4j! Found cities: {', '.join(cities)}")
            else:
                print("Connected to Neo4j but found no cities. You may need to initialize the database.")
        
        # Test recommendation
        print("\nTesting recommendation system...")
        recommendations = kg.recommend_locations('Mumbai', min_score=0.4)
        if recommendations:
            print(f"Found {len(recommendations)} location recommendations for Mumbai:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['area']} (Score: {rec['score']:.2f})")
        else:
            print("No recommendations found.")
        
        # Close connection
        kg.close()
        
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_neo4j_connection()
