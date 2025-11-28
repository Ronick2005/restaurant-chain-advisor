import os
from neo4j import GraphDatabase

# Set environment variables
os.environ['NEO4J_URI'] = 'neo4j+s://485f2797.databases.neo4j.io'
os.environ['NEO4J_USERNAME'] = 'neo4j'
os.environ['NEO4J_PASSWORD'] = 'gIQcttXK58fKXSG3oCV7MYZityMz9SScfwnSoK6dAqU'

# Connect to Neo4j directly
driver = GraphDatabase.driver(
    os.environ['NEO4J_URI'], 
    auth=(os.environ['NEO4J_USERNAME'], os.environ['NEO4J_PASSWORD'])
)

try:
    with driver.session() as session:
        # Test 1: Check location existence
        print("=== Test 1: Check Location Existence ===")
        result = session.run("MATCH (l:Location {id: 'mumbai_powai'}) RETURN l.id, l.area")
        print(result.single())
        
        # Test 2: Check if location has commercial property
        print("\n=== Test 2: Check Location Commercial Property ===")
        result = session.run("MATCH (l:Location {id: 'mumbai_powai'}) RETURN l.commercial")
        print(f"Commercial property: {result.single()[0]}")
        
        # Test 3: Check foot_traffic property value
        print("\n=== Test 3: Check foot_traffic Property ===")
        result = session.run("MATCH (l:Location {id: 'mumbai_powai'}) RETURN l.foot_traffic")
        record = result.single()
        print(f"foot_traffic: {record[0]}, Python type: {type(record[0])}")
        
        # Test 4: Try simple scoring calculation
        print("\n=== Test 4: Try Simple Scoring ===")
        try:
            result = session.run("""
                MATCH (l:Location {id: 'mumbai_powai'})
                WITH l, 
                     toFloat(l.foot_traffic) * 0.3 AS score1,
                     (1.0 - toFloat(l.competition_score)) * 0.2 AS score2,
                     toFloat(l.growth_potential) * 0.2 AS score3,
                     (1.0 - toFloat(l.rent_score)) * 0.3 AS score4
                RETURN score1, score2, score3, score4, score1 + score2 + score3 + score4 AS total
            """)
            record = result.single()
            if record:
                print(f"Score components: {record['score1']}, {record['score2']}, {record['score3']}, {record['score4']}")
                print(f"Total score: {record['total']}")
            else:
                print("Scoring calculation failed - no result")
        except Exception as e:
            print(f"Scoring calculation error: {e}")
            
            # Try without toFloat
            print("\nTrying calculation without toFloat:")
            try:
                result = session.run("""
                    MATCH (l:Location {id: 'mumbai_powai'})
                    WITH l, 
                         l.foot_traffic * 0.3 AS score1,
                         (1.0 - l.competition_score) * 0.2 AS score2,
                         l.growth_potential * 0.2 AS score3,
                         (1.0 - l.rent_score) * 0.3 AS score4
                    RETURN score1, score2, score3, score4, score1 + score2 + score3 + score4 AS total
                """)
                record = result.single()
                if record:
                    print(f"Score components: {record['score1']}, {record['score2']}, {record['score3']}, {record['score4']}")
                    print(f"Total score: {record['total']}")
                else:
                    print("Scoring calculation failed - no result")
            except Exception as e:
                print(f"Scoring calculation error without toFloat: {e}")
        
        # Test 5: Try full recommendation query on specific location
        print("\n=== Test 5: Try Full Recommendation Query on Specific Location ===")
        try:
            result = session.run("""
                MATCH (l:Location {id: 'mumbai_powai'})
                WHERE l.commercial = true
                WITH l, 
                     l.foot_traffic * 0.3 +
                     (1.0 - l.competition_score) * 0.2 +
                     l.growth_potential * 0.2 +
                     (1.0 - l.rent_score) * 0.3 AS score
                WHERE score >= 0.6
                RETURN l.id AS id, l.area AS area, score
            """)
            record = result.single()
            if record:
                print(f"Location {record['id']} ({record['area']}) has score: {record['score']}")
            else:
                print("No results from recommendation query")
        except Exception as e:
            print(f"Recommendation query error: {e}")

finally:
    driver.close()
