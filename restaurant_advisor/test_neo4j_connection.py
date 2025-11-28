"""
Test Neo4j connection with various configurations
"""
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path so we can import project modules
current_path = Path(__file__).parent
project_root = current_path.absolute()
sys.path.append(str(project_root))

try:
    from utils.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
except ImportError:
    print("Could not import from utils.config")
    # Fallback to environment variables
    NEO4J_URI = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

def test_neo4j_connection():
    """Test Neo4j connection with various configurations."""
    print(f"Testing connection to Neo4j at {NEO4J_URI}")
    
    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        print("Missing Neo4j credentials. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD.")
        return False
    
    # Try different connection methods
    try:
        from neo4j import GraphDatabase
        
        print("\nTrying with TrustAll...")
        try:
            from neo4j import TrustAll
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
                trusted_certificates=TrustAll()
            )
            # Test connection
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                print(f"✅ Connection successful with TrustAll! Test result: {result.single()['test']}")
                driver.close()
                return True
        except Exception as e:
            print(f"❌ Connection failed with TrustAll: {str(e)}")
        
        print("\nTrying with TrustSystemCAs...")
        try:
            from neo4j import TrustSystemCAs
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
                trusted_certificates=TrustSystemCAs()
            )
            # Test connection
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                print(f"✅ Connection successful with TrustSystemCAs! Test result: {result.single()['test']}")
                driver.close()
                return True
        except Exception as e:
            print(f"❌ Connection failed with TrustSystemCAs: {str(e)}")
        
        print("\nTrying basic connection...")
        try:
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
            )
            # Test connection
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                print(f"✅ Basic connection successful! Test result: {result.single()['test']}")
                driver.close()
                return True
        except Exception as e:
            print(f"❌ Basic connection failed: {str(e)}")
        
        print("\nTrying with modified URI...")
        try:
            # Try modifying the URI if it uses neo4j+s:// scheme
            modified_uri = NEO4J_URI
            if NEO4J_URI.startswith("neo4j+s://"):
                modified_uri = "neo4j://" + NEO4J_URI[9:]
                print(f"Modified URI to: {modified_uri}")
            
            driver = GraphDatabase.driver(
                modified_uri,
                auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
                encrypted=True
            )
            # Test connection
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                print(f"✅ Connection successful with modified URI! Test result: {result.single()['test']}")
                driver.close()
                return True
        except Exception as e:
            print(f"❌ Connection with modified URI failed: {str(e)}")
        
        return False
    except ImportError:
        print("❌ Could not import Neo4j GraphDatabase. Make sure neo4j package is installed.")
        return False

if __name__ == "__main__":
    test_neo4j_connection()
