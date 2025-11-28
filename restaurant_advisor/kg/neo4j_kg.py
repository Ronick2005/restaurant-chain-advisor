from typing import Dict, List, Optional, Any, Tuple
import os
import sys
import neo4j
from neo4j import GraphDatabase

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class Neo4jKnowledgeGraph:
    """Neo4j-based knowledge graph for restaurant location recommendations."""
    
    def __init__(self):
        # Connect to Neo4j
        # For neo4j+s:// URIs, SSL settings are already included in the URI scheme,
        # so we don't need additional SSL configurations
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Initialize the database schema
        self._init_schema()
        
    def _init_schema(self):
        """Initialize the Neo4j schema with constraints and indexes."""
        with self.driver.session() as session:
            # Create constraints for uniqueness
            session.run("""
                CREATE CONSTRAINT city_name IF NOT EXISTS
                FOR (c:City) REQUIRE c.name IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT location_id IF NOT EXISTS
                FOR (l:Location) REQUIRE l.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT cuisine_type IF NOT EXISTS
                FOR (c:Cuisine) REQUIRE c.type IS UNIQUE
            """)
            
            # Create indexes for better performance
            session.run("""
                CREATE INDEX location_area IF NOT EXISTS
                FOR (l:Location) ON (l.area)
            """)
            
            session.run("""
                CREATE INDEX city_population IF NOT EXISTS
                FOR (c:City) ON (c.population)
            """)
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
    
    def add_city(self, name: str, state: str, population: int, 
                 demographics: Dict = None, key_markets: List[str] = None) -> bool:
        """Add a city to the knowledge graph."""
        with self.driver.session() as session:
            # Check if city already exists
            result = session.run(
                "MATCH (c:City {name: $name}) RETURN c",
                name=name
            )
            
            if result.single():
                # City exists, update properties
                session.run("""
                    MATCH (c:City {name: $name})
                    SET c.state = $state,
                        c.population = $population,
                        c.demographics = $demographics,
                        c.key_markets = $key_markets
                    RETURN c
                """, name=name, state=state, population=population, 
                     demographics=demographics, key_markets=key_markets)
            else:
                # Create new city
                session.run("""
                    CREATE (c:City {
                        name: $name,
                        state: $state,
                        population: $population,
                        demographics: $demographics,
                        key_markets: $key_markets
                    })
                """, name=name, state=state, population=population, 
                     demographics=demographics, key_markets=key_markets)
            
            return True
    
    def add_location(self, city: str, area: str, location_type: str, 
                     properties: Dict = None) -> str:
        """Add a location within a city to the knowledge graph."""
        with self.driver.session() as session:
            # Generate a unique ID for the location
            location_id = f"{city.lower().replace(' ', '_')}_{area.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
            
            # Process the properties to ensure Neo4j compatibility
            processed_properties = {}
            if properties:
                for key, value in properties.items():
                    # Convert nested lists/dicts to flat properties
                    if isinstance(value, dict):
                        # Convert nested dict to string representation or separate properties
                        for sub_key, sub_value in value.items():
                            processed_properties[f"{key}_{sub_key}"] = sub_value
                    else:
                        processed_properties[key] = value
            
            # Check if location already exists
            result = session.run(
                "MATCH (l:Location {id: $id}) RETURN l",
                id=location_id
            )
            
            if result.single():
                # Location exists, update properties
                session.run("""
                    MATCH (l:Location {id: $id})
                    SET l.type = $type
                """, id=location_id, type=location_type)
                
                # Set each property individually to avoid nested property issues
                for key, value in processed_properties.items():
                    session.run(f"""
                        MATCH (l:Location {{id: $id}})
                        SET l.{key} = $value
                    """, id=location_id, value=value)
            else:
                # Create new location with base properties
                session.run("""
                    MATCH (c:City {name: $city})
                    CREATE (l:Location {
                        id: $id,
                        area: $area,
                        type: $type
                    })
                    CREATE (c)-[:HAS_LOCATION]->(l)
                """, city=city, id=location_id, area=area, type=location_type)
                
                # Set each property individually to avoid nested property issues
                for key, value in processed_properties.items():
                    session.run(f"""
                        MATCH (l:Location {{id: $id}})
                        SET l.{key} = $value
                    """, id=location_id, value=value)
            
            return location_id
    
    def add_relation(self, from_id: str, to_id: str, relation_type: str, 
                     properties: Dict = None) -> bool:
        """Add a relation between two entities in the knowledge graph."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a), (b)
                WHERE (a.id = $from_id OR a.name = $from_id) AND 
                      (b.id = $to_id OR b.name = $to_id)
                MERGE (a)-[r:`{}`]->(b)
                SET r += $properties
                RETURN r
            """.format(relation_type), from_id=from_id, to_id=to_id, properties=properties)
            
            return result.single() is not None
    
    def find_locations_by_city(self, city: str) -> List[Dict]:
        """Find all locations in a city."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location)
                RETURN l.id AS id, l.area AS area, l.type AS type, l.properties AS properties
            """, city=city)
            
            return [dict(record) for record in result]
    
    def find_nearby_locations(self, location_id: str, relation_type: str = "NEAR", 
                             max_distance: int = 2) -> List[Dict]:
        """Find nearby locations using graph traversal."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (l:Location {id: $id})-[:`{}`*1..{}]->(nearby:Location)
                RETURN nearby.id AS id, nearby.area AS area, nearby.type AS type, 
                       nearby.properties AS properties
            """.format(relation_type, max_distance), id=location_id)
            
            return [dict(record) for record in result]
    
    def get_detailed_city_demographics(self, city: str) -> Dict:
        """Get detailed demographic information for a city.
        
        Args:
            city: Name of the city to get demographics for
            
        Returns:
            Dict with demographic details
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:City {name: $city})
                RETURN 
                    c.name as name,
                    c.state as state,
                    c.population as population,
                    c.demographics as demographics,
                    c.key_markets as key_markets
            """, city=city)
            
            record = result.single()
            if record:
                return dict(record)
            return {}
    
    def get_detailed_location_info(self, city: str, area: str = None) -> List[Dict]:
        """Get detailed information about locations in a city or specific area.
        
        Args:
            city: City name
            area: Optional area name within the city
            
        Returns:
            List of location dictionaries with detailed information
        """
        with self.driver.session() as session:
            query = """
                MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location)
                WHERE l.commercial = true
            """
            
            params = {"city": city}
            
            # Filter by area if specified
            if area:
                query += " AND l.area = $area"
                params["area"] = area
            
            # Complete the query with detailed information
            query += """
                OPTIONAL MATCH (l)-[:NEAR]->(nearby:Location)
                WITH l, collect(nearby) as nearby_places
                RETURN 
                    l.id as id,
                    l.area as area, 
                    l.type as type,
                    l.commercial as commercial,
                    l.foot_traffic as foot_traffic,
                    l.rent_range as rent_range,
                    l.popular_cuisines as popular_cuisines,
                    l.demographics as demographics,
                    l.public_transport as public_transport,
                    l.parking as parking,
                    size(nearby_places) as connectivity,
                    [place in nearby_places | {id: place.id, area: place.area, type: place.type}] as nearby_areas
                ORDER BY l.foot_traffic DESC
            """
            
            result = session.run(query, **params)
            return [dict(record) for record in result]
    
    def recommend_locations(self, city: str, cuisine_type: str = None, 
                          target_demographic: str = None, min_score: float = 0.5) -> List[Dict]:
        """Recommend locations for a restaurant based on various factors."""
        with self.driver.session() as session:
            # Build a complex query that considers multiple factors
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
            
            # Add demographic targeting if specified
            if target_demographic:
                query += """
                    AND (l.demographics IS NULL OR
                         $target_demographic IN l.demographics)
                """
                params["target_demographic"] = target_demographic
            
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
    
    def get_location_details(self, location_id: str) -> Optional[Dict]:
        """Get detailed information about a specific location."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (l:Location {id: $id})
                OPTIONAL MATCH (l)-[r]->(related)
                RETURN l.id AS id, l.area AS area, l.type AS type,
                       {
                         foot_traffic: l.foot_traffic,
                         competition_score: l.competition_score,
                         growth_potential: l.growth_potential,
                         rent_score: l.rent_score,
                         commercial: l.commercial,
                         popular_cuisines: l.popular_cuisines,
                         demographics: l.demographics
                       } AS properties,
                       collect({type: type(r), target: CASE WHEN related:Location 
                                                           THEN related.area 
                                                           ELSE related.name END}) AS relationships
            """, id=location_id)
            
            record = result.single()
            return dict(record) if record else None

    def get_regulatory_info(self, city: str) -> List[Dict]:
        """Get regulatory information for restaurant setup in a city."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:City {name: $city})-[:HAS_REGULATION]->(r:Regulation)
                RETURN r.type AS type, r.description AS description, 
                       r.authority AS authority, r.requirements AS requirements
            """, city=city)
            
            return [dict(record) for record in result]
            
    def add_city_regulation(self, city: str, reg_type: str, description: str,
                          authority: str, requirements: List[str]) -> bool:
        """Add regulatory information for a city."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:City {name: $city})
                MERGE (r:Regulation {type: $type, city: $city})
                SET r.description = $description,
                    r.authority = $authority,
                    r.requirements = $requirements
                MERGE (c)-[:HAS_REGULATION]->(r)
                RETURN r
            """, city=city, type=reg_type, description=description,
                 authority=authority, requirements=requirements)
            
            return result.single() is not None
            
    def get_cuisine_preferences(self, city: str) -> List[Dict]:
        """Get cuisine preferences for a city."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location)
                WHERE l.popular_cuisines IS NOT NULL
                RETURN DISTINCT l.popular_cuisines AS cuisines
                LIMIT 10
            """, city=city)
            
            # Process results - flatten the list of cuisines from locations
            cuisine_counts = {}
            for record in result:
                cuisines = record.get("cuisines", [])
                if cuisines:
                    for cuisine in cuisines:
                        if cuisine in cuisine_counts:
                            cuisine_counts[cuisine] += 1
                        else:
                            cuisine_counts[cuisine] = 1
            
            # Return formatted cuisine preferences
            return [{"cuisine_type": cuisine, "popularity": count} 
                   for cuisine, count in sorted(cuisine_counts.items(), 
                                               key=lambda x: x[1], 
                                               reverse=True)]
    
    def add_cuisine_data(self, cuisine_type: str, popularity: List[str],
                       demographics: List[str] = None) -> bool:
        """Add cuisine data to the knowledge graph."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (c:Cuisine {type: $type})
                SET c.popularity = $popularity,
                    c.demographics = $demographics
                RETURN c
            """, type=cuisine_type, popularity=popularity, demographics=demographics)
            
            # Connect cuisine to cities where it's popular
            for pop_entry in popularity:
                # Parse the city:score format
                if ":" in pop_entry:
                    city, score_str = pop_entry.split(":", 1)
                    try:
                        score = float(score_str)
                        if score > 0.6:  # Only connect to cities with high popularity
                            session.run("""
                                MATCH (cuisine:Cuisine {type: $type}), (city:City {name: $city})
                                MERGE (cuisine)-[:POPULAR_IN {score: $score}]->(city)
                            """, type=cuisine_type, city=city, score=score)
                    except ValueError:
                        pass  # Skip invalid entries
            
            return True
            
    def add_cuisine_city_connection(self, cuisine_type: str, city: str, score: float) -> bool:
        """Add a direct connection between a cuisine and a city with a popularity score."""
        with self.driver.session() as session:
            # Ensure the cuisine exists
            session.run("""
                MERGE (c:Cuisine {type: $type})
            """, type=cuisine_type)
            
            # Create or update the connection
            result = session.run("""
                MATCH (cuisine:Cuisine {type: $type}), (city:City {name: $city})
                MERGE (cuisine)-[r:POPULAR_IN]->(city)
                SET r.score = $score
                RETURN r
            """, type=cuisine_type, city=city, score=score)
            
            return result.single() is not None
            
    def get_location_details_with_neighborhood_insights(self, city: str, location_id: str = None) -> Dict:
        """Get detailed location information with neighborhood insights."""
        with self.driver.session() as session:
            if location_id:
                # Get details for a specific location
                query = """
                    MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location {id: $location_id})
                    OPTIONAL MATCH (l)-[:NEAR]->(n:Location)
                    WITH l, collect(n) as nearby_locations
                    RETURN 
                        l.id as id, 
                        l.area as area, 
                        l.type as type, 
                        l.commercial as commercial,
                        l.foot_traffic as foot_traffic,
                        l.rent_range as rent_range,
                        l.popular_cuisines as popular_cuisines,
                        l.demographics as demographics,
                        l.public_transport as public_transport,
                        l.parking as parking,
                        size(nearby_locations) as num_nearby,
                        [loc in nearby_locations | {
                            id: loc.id, 
                            area: loc.area, 
                            type: loc.type, 
                            commercial: loc.commercial
                        }] as nearby
                """
                result = session.run(query, city=city, location_id=location_id)
                record = result.single()
                
                if record:
                    return dict(record)
                return {}
            else:
                # Get overview of all locations in the city
                query = """
                    MATCH (c:City {name: $city})-[:HAS_LOCATION]->(l:Location)
                    WHERE l.commercial = true
                    WITH l, size((l)-[:NEAR]->()) as connectivity
                    RETURN 
                        l.id as id,
                        l.area as area,
                        l.type as type,
                        l.foot_traffic as foot_traffic,
                        l.rent_range as rent_range,
                        connectivity as connectivity,
                        l.popular_cuisines as popular_cuisines
                    ORDER BY l.foot_traffic DESC
                """
                result = session.run(query, city=city)
                return [dict(record) for record in result]
                
    def find_similar_locations_across_cities(self, reference_location_id: str, limit: int = 3) -> List[Dict]:
        """Find locations in other cities that are similar to a reference location."""
        with self.driver.session() as session:
            # First get the reference location details
            ref_query = """
                MATCH (city:City)-[:HAS_LOCATION]->(ref:Location {id: $ref_id})
                RETURN ref, city.name as source_city
            """
            ref_result = session.run(ref_query, ref_id=reference_location_id)
            ref_record = ref_result.single()
            
            if not ref_record:
                return []
                
            ref_location = ref_record["ref"]
            source_city = ref_record["source_city"]
            
            # Find similar locations in other cities
            query = """
                MATCH (ref:Location {id: $ref_id})
                MATCH (city:City)-[:HAS_LOCATION]->(l:Location)
                WHERE city.name <> $source_city
                  AND l.type = ref.type
                  AND l.commercial = ref.commercial
                  AND abs(l.foot_traffic - ref.foot_traffic) < 500
                WITH l, city, ref,
                     abs(l.foot_traffic - ref.foot_traffic) as traffic_diff,
                     CASE
                        WHEN ref.popular_cuisines IS NULL OR l.popular_cuisines IS NULL THEN 0
                        ELSE size([x IN ref.popular_cuisines WHERE x IN l.popular_cuisines]) / toFloat(size(ref.popular_cuisines))
                     END as cuisine_similarity
                RETURN 
                    l.id as id,
                    l.area as area,
                    city.name as city,
                    l.type as type,
                    l.foot_traffic as foot_traffic,
                    l.rent_range as rent_range,
                    l.popular_cuisines as popular_cuisines,
                    traffic_diff,
                    cuisine_similarity,
                    traffic_diff * 0.4 + (1-cuisine_similarity) * 0.6 as similarity_score
                ORDER BY similarity_score ASC
                LIMIT $limit
            """
            
            result = session.run(query, 
                               ref_id=reference_location_id, 
                               source_city=source_city, 
                               limit=limit)
            
            return [dict(record) for record in result]
