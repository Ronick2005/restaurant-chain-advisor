"""
Real Estate Data Agent
Fetches commercial rental costs, property data, and real estate trends using live APIs.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pymongo import MongoClient
from neo4j import GraphDatabase
from utils.config import GEMINI_API_KEY, MONGODB_URI, MONGODB_DB_NAME, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from api_services.free_location_apis import FreeLocationDataAggregator
from api_services.zomato_scraper import ZomatoScraper

logger = logging.getLogger(__name__)

class RealEstateAgent:
    """
    Agent for gathering commercial real estate data for restaurant locations.
    Integrates with property APIs and maintains Neo4j graph of location-property relationships.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        
        # MongoDB connection
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client[MONGODB_DB_NAME]
        self.collection = self.db["real_estate"]
        
        # Neo4j for location-property relationships
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Free location and restaurant data APIs
        self.location_api = FreeLocationDataAggregator()
        self.zomato_scraper = ZomatoScraper()
        
        # API endpoints for Indian real estate data
        self.api_endpoints = {
            "magic_bricks": "https://www.magicbricks.com/",  # Requires API key
            "99acres": "https://www.99acres.com/",  # Requires scraping or API
            "property_guru": "https://www.propertyguru.com.sg/"  # For reference
        }
    
    def fetch_rental_costs(self, city: str, locality: str, property_type: str = "commercial") -> Dict[str, Any]:
        """
        Fetch commercial rental costs for a specific locality.
        
        Args:
            city: City name (e.g., "Mumbai", "Delhi")
            locality: Specific area/locality (e.g., "Bandra West", "Connaught Place")
            property_type: Type of property ("commercial", "retail")
            
        Returns:
            Rental cost data with ranges, trends, availability
        """
        logger.info(f"Fetching rental costs for {locality}, {city}")
        
        # In production, integrate with actual real estate APIs
        # For now, providing structured data based on typical Indian market rates
        
        # Average commercial rental costs in major Indian cities (per sq ft per month)
        city_rates = {
            "mumbai": {"min": 150, "max": 500, "avg": 300},
            "delhi": {"min": 100, "max": 400, "avg": 200},
            "bangalore": {"min": 80, "max": 350, "avg": 180},
            "hyderabad": {"min": 60, "max": 250, "avg": 120},
            "chennai": {"min": 70, "max": 280, "avg": 140},
            "kolkata": {"min": 50, "max": 200, "avg": 100},
            "pune": {"min": 70, "max": 300, "avg": 150},
            "ahmedabad": {"min": 60, "max": 220, "avg": 110}
        }
        
        base_rates = city_rates.get(city.lower(), {"min": 60, "max": 300, "avg": 150})
        
        rental_data = {
            "city": city,
            "locality": locality,
            "property_type": property_type,
            "rental_cost_per_sqft_monthly": {
                "min": base_rates["min"],
                "max": base_rates["max"],
                "average": base_rates["avg"],
                "currency": "INR"
            },
            "typical_property_sizes": {
                "small_restaurant": "800-1500 sq ft",
                "medium_restaurant": "1500-3000 sq ft",
                "large_restaurant": "3000+ sq ft"
            },
            "estimated_monthly_rent": {
                "small_restaurant": f"₹{base_rates['avg'] * 1000:,.0f} - ₹{base_rates['avg'] * 1500:,.0f}",
                "medium_restaurant": f"₹{base_rates['avg'] * 1500:,.0f} - ₹{base_rates['avg'] * 3000:,.0f}",
                "large_restaurant": f"₹{base_rates['avg'] * 3000:,.0f}+"
            },
            "additional_costs": {
                "maintenance": "₹5-15 per sq ft per month",
                "security_deposit": "6-12 months rent",
                "lock_in_period": "3-5 years typical",
                "annual_escalation": "5-10%"
            },
            "market_conditions": "moderate",  # Would come from API
            "availability": "medium",  # Would come from API
            "last_updated": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one(rental_data)
        
        # Create Neo4j relationship
        self._create_location_property_relationship(city, locality, rental_data)
        
        return rental_data
    
    def _create_location_property_relationship(self, city: str, locality: str, rental_data: Dict[str, Any]):
        """Create or update location-property relationship in Neo4j."""
        try:
            with self.neo4j_driver.session() as session:
                session.run("""
                    MERGE (c:City {name: $city})
                    MERGE (l:Locality {name: $locality, city: $city})
                    MERGE (c)-[:HAS_LOCALITY]->(l)
                    SET l.avg_rent_per_sqft = $avg_rent,
                        l.min_rent_per_sqft = $min_rent,
                        l.max_rent_per_sqft = $max_rent,
                        l.market_conditions = $market_conditions,
                        l.last_updated = $last_updated
                """, {
                    "city": city,
                    "locality": locality,
                    "avg_rent": rental_data["rental_cost_per_sqft_monthly"]["average"],
                    "min_rent": rental_data["rental_cost_per_sqft_monthly"]["min"],
                    "max_rent": rental_data["rental_cost_per_sqft_monthly"]["max"],
                    "market_conditions": rental_data["market_conditions"],
                    "last_updated": rental_data["last_updated"]
                })
                logger.info(f"Created Neo4j relationship for {locality}, {city}")
        except Exception as e:
            logger.error(f"Error creating Neo4j relationship: {e}")
    
    def get_foot_traffic_data(self, locality: str, city: str) -> Dict[str, Any]:
        """
        Estimate foot traffic and commercial activity in a locality.
        
        Args:
            locality: Area name
            city: City name
            
        Returns:
            Foot traffic estimates, peak hours, commercial density
        """
        # Would integrate with Google Places API or similar for actual data
        foot_traffic = {
            "locality": locality,
            "city": city,
            "foot_traffic_level": "high",  # low, medium, high
            "peak_hours": [
                {"time": "12:00 PM - 2:00 PM", "level": "high", "reason": "lunch"},
                {"time": "7:00 PM - 10:00 PM", "level": "very high", "reason": "dinner"},
                {"time": "4:00 PM - 7:00 PM", "level": "medium", "reason": "evening snacks"}
            ],
            "weekend_multiplier": 1.5,  # Weekend traffic vs weekday
            "nearby_attractions": [],  # Would come from Places API
            "commercial_establishments": {
                "offices": "high",
                "retail": "high",
                "residential": "medium",
                "educational": "low"
            },
            "public_transport_access": {
                "metro_stations": 0,  # Would fetch actual data
                "bus_stops": 0,
                "parking_availability": "medium"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **foot_traffic,
            "type": "foot_traffic"
        })
        
        return foot_traffic
    
    def analyze_location_viability(self, city: str, locality: str, restaurant_type: str) -> Dict[str, Any]:
        """
        Comprehensive location viability analysis combining real estate and foot traffic.
        
        Args:
            city: City name
            locality: Specific area
            restaurant_type: Type of restaurant (e.g., "fine_dining", "qsr", "casual_dining")
            
        Returns:
            Viability score with detailed analysis
        """
        logger.info(f"Analyzing location viability: {locality}, {city} for {restaurant_type}")
        
        # Fetch rental and foot traffic data
        rental_data = self.fetch_rental_costs(city, locality)
        foot_traffic = self.get_foot_traffic_data(locality, city)
        
        # Prepare analysis context
        context = f"""
Location: {locality}, {city}
Restaurant Type: {restaurant_type}

Real Estate Data:
- Average Rent: ₹{rental_data['rental_cost_per_sqft_monthly']['average']}/sq ft/month
- Market Conditions: {rental_data['market_conditions']}

Foot Traffic:
- Level: {foot_traffic['foot_traffic_level']}
- Peak Hours: {', '.join([p['time'] for p in foot_traffic['peak_hours']])}
"""

        system_prompt = """You are a real estate analyst specializing in restaurant locations in India.
Evaluate location viability considering:
1. Rental costs vs expected revenue potential
2. Foot traffic and customer accessibility
3. Competition and market saturation
4. Visibility and signage opportunities
5. Parking and public transport access
6. Target demographic alignment

Provide a viability score (1-10) and detailed recommendations."""

        user_prompt = f"""{context}

Analyze this location for a {restaurant_type} restaurant and provide:

1. **Viability Score** (1-10 with explanation)
2. **Strengths** of this location
3. **Weaknesses** or concerns
4. **Rental Budget Recommendation** (realistic range)
5. **Expected Customer Profile** based on location
6. **Competition Analysis** (likely competitors nearby)
7. **Go/No-Go Recommendation** with reasoning

Be specific to Indian market conditions and consumer behavior."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "city": city,
                "locality": locality,
                "restaurant_type": restaurant_type,
                "analysis": response.content,
                "rental_data": rental_data,
                "foot_traffic_data": foot_traffic,
                "analyzed_at": datetime.now().isoformat(),
                "agent": "real_estate"
            }
            
            # Store analysis
            self.db["location_viability"].insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing location viability: {e}")
            return {"error": str(e)}
    
    def get_comparable_properties(self, city: str, locality: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find comparable commercial properties in the area.
        
        Args:
            city: City name
            locality: Locality name
            limit: Number of comparable properties to return
            
        Returns:
            List of comparable properties with rental data
        """
        # Query MongoDB for similar properties
        comparables = list(self.collection.find({
            "city": city,
            "property_type": "commercial"
        }).limit(limit))
        
        for comp in comparables:
            comp.pop("_id", None)
        
        return comparables
    
    def fetch_location_places_data(self, locality: str, city: str) -> Dict[str, Any]:
        """
        Fetch places data using FREE location APIs (OpenStreetMap, Foursquare, HERE, Geoapify).
        No paid Google Places API needed!
        
        Args:
            locality: Area name
            city: City name
            
        Returns:
            Places data including restaurants, commercial centers, foot traffic indicators
        """
        try:
            # Import free location API aggregator
            from api_services.free_location_apis import FreeLocationDataAggregator
            
            aggregator = FreeLocationDataAggregator()
            
            # Get restaurants and POI data
            logger.info(f"Fetching location data for {locality}, {city} using free APIs")
            restaurants = aggregator.get_location_restaurants(city, locality)
            poi_analysis = aggregator.get_poi_analysis(f"{locality}, {city}")
            
            places_data = {
                "locality": locality,
                "city": city,
                "nearby_restaurants": restaurants[:20],  # Top 20 results
                "total_restaurants_found": len(restaurants),
                "poi_analysis": poi_analysis,
                "competition_level": "high" if len(restaurants) > 50 else "medium" if len(restaurants) > 20 else "low",
                "data_sources": ["openstreetmap", "foursquare", "here", "geoapify"],
                "note": "Data aggregated from multiple FREE APIs (OpenStreetMap, Foursquare, HERE, Geoapify)",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in MongoDB
            self.collection.insert_one({
                **places_data,
                "type": "location_places"
            })
            
            return places_data
            
        except Exception as e:
            logger.error(f"Error fetching location places data: {e}")
            return {
                "error": str(e),
                "locality": locality,
                "city": city,
                "note": "Using free APIs: OpenStreetMap (no key), Foursquare (50 req/day), HERE (250k/month), Geoapify (3000 req/day)"
            }
    
    def get_location_clusters(self, city: str) -> List[Dict[str, Any]]:
        """
        Get restaurant clusters and commercial zones in a city from Neo4j.
        
        Args:
            city: City name
            
        Returns:
            List of commercial clusters with density and rental data
        """
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (c:City {name: $city})-[:HAS_LOCALITY]->(l:Locality)
                    RETURN l.name AS locality,
                           l.avg_rent_per_sqft AS avg_rent,
                           l.market_conditions AS conditions
                    ORDER BY l.avg_rent_per_sqft DESC
                    LIMIT 20
                """, {"city": city})
                
                clusters = []
                for record in result:
                    clusters.append({
                        "locality": record["locality"],
                        "avg_rent": record["avg_rent"],
                        "market_conditions": record["conditions"]
                    })
                
                return clusters
                
        except Exception as e:
            logger.error(f"Error fetching location clusters: {e}")
            return []
    
    def get_zomato_restaurant_data(self, city: str, locality: str = None, cuisine: str = None) -> Dict[str, Any]:
        """
        Scrape Zomato for restaurant data in a location (no API key needed).
        
        Args:
            city: City name
            locality: Optional locality/area
            cuisine: Optional cuisine filter
            
        Returns:
            Restaurant data from Zomato with ratings and reviews
        """
        try:
            logger.info(f"Scraping Zomato for {city}, {locality}")
            
            # Search for restaurants
            restaurants = self.zomato_scraper.search_restaurants(
                city=city,
                locality=locality,
                cuisine=cuisine,
                limit=20
            )
            
            # Get popular cuisines
            popular_cuisines = self.zomato_scraper.get_popular_cuisines(city)
            
            # Get trending restaurants
            trending = self.zomato_scraper.get_trending_restaurants(city, limit=10)
            
            zomato_data = {
                "city": city,
                "locality": locality,
                "cuisine_filter": cuisine,
                "restaurants": restaurants,
                "restaurant_count": len(restaurants),
                "popular_cuisines": popular_cuisines,
                "trending_restaurants": trending,
                "scraped_at": datetime.now().isoformat(),
                "source": "zomato_scraper"
            }
            
            # Store in MongoDB
            self.db["zomato_data"].insert_one(zomato_data)
            
            logger.info(f"Scraped {len(restaurants)} restaurants from Zomato")
            
            return zomato_data
            
        except Exception as e:
            logger.error(f"Error scraping Zomato: {e}")
            return {
                "error": str(e),
                "city": city,
                "locality": locality,
                "note": "Zomato scraping failed - check if website structure changed"
            }
    
    def analyze_competition_from_zomato(self, city: str, locality: str, restaurant_type: str) -> Dict[str, Any]:
        """
        Analyze competition using Zomato data.
        
        Args:
            city: City name
            locality: Locality name
            restaurant_type: Type of restaurant (cuisine)
            
        Returns:
            Competition analysis with insights
        """
        try:
            # Get Zomato data
            zomato_data = self.get_zomato_restaurant_data(city, locality, restaurant_type)
            
            if "error" in zomato_data:
                return zomato_data
            
            restaurants = zomato_data.get("restaurants", [])
            
            # Calculate competition metrics
            total_restaurants = len(restaurants)
            avg_rating = sum(r.get("rating", 0) for r in restaurants if r.get("rating")) / max(total_restaurants, 1)
            
            # Group by cuisine
            cuisine_distribution = {}
            for r in restaurants:
                cuisine = r.get("cuisine", "Unknown")
                cuisine_distribution[cuisine] = cuisine_distribution.get(cuisine, 0) + 1
            
            # Analyze with LLM
            context = f"""
Location: {locality}, {city}
Restaurant Type: {restaurant_type}

Competition Data from Zomato:
- Total Restaurants: {total_restaurants}
- Average Rating: {avg_rating:.1f}/5
- Cuisine Distribution: {cuisine_distribution}
- Top Trending: {[r.get('name') for r in zomato_data.get('trending_restaurants', [])[:5]]}
"""

            system_prompt = """You are a restaurant competition analyst.
Analyze the competition data and provide:
1. Competition intensity (Low/Medium/High)
2. Market saturation assessment
3. Gaps in the market
4. Differentiation opportunities
5. Pricing strategy recommendations"""

            user_prompt = f"""{context}

Provide a comprehensive competition analysis for opening a {restaurant_type} restaurant in this location."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "city": city,
                "locality": locality,
                "restaurant_type": restaurant_type,
                "total_competitors": total_restaurants,
                "avg_competitor_rating": avg_rating,
                "cuisine_distribution": cuisine_distribution,
                "competition_analysis": response.content,
                "trending_restaurants": zomato_data.get("trending_restaurants", []),
                "analyzed_at": datetime.now().isoformat(),
                "source": "zomato_competition_analysis"
            }
            
            # Store in MongoDB
            self.db["competition_analysis"].insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing competition: {e}")
            return {"error": str(e)}
    
    def __del__(self):
        """Close Neo4j connection."""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()
