"""
Location Intelligence Agent for the Restaurant Chain Advisor system.
This agent handles location-based analysis and recommendations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime

# Import map API services
from api_services.maps_api import MapServiceFactory, get_coordinates, get_address
from api_services.maps_api import get_nearby_restaurants, get_distance_between, get_travel_times

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocationIntelligenceAgent:
    """
    Agent responsible for location-based analysis and recommendations.
    """
    
    def __init__(self, map_service_name: str = None):
        """Initialize the agent with a map service."""
        self.map_service = MapServiceFactory.get_service(map_service_name)
        logger.info(f"Location Intelligence Agent initialized with {self.map_service.service_name} service")
    
    def analyze_location(self, address: str, radius: int = 1000) -> Dict[str, Any]:
        """
        Analyze a specific location for restaurant potential.
        
        Args:
            address: The address or location to analyze
            radius: Radius in meters to analyze
            
        Returns:
            Dictionary with location analysis results
        """
        try:
            # Get coordinates for the location
            geocode_result = self.map_service.geocode(address)
            if "error" in geocode_result:
                return {"error": f"Could not geocode address: {geocode_result['error']}"}
            
            lat = geocode_result["lat"]
            lng = geocode_result["lng"]
            formatted_address = geocode_result["address"]
            
            # Get nearby restaurants
            nearby = self.map_service.search_nearby(lat, lng, radius, "restaurant")
            
            # Analyze competition density
            competition_count = len(nearby)
            competition_density = "High" if competition_count > 15 else "Medium" if competition_count > 5 else "Low"
            
            # Get place details
            area_details = self.map_service.reverse_geocode(lat, lng)
            city = area_details.get("components", {}).get("city", "")
            state = area_details.get("components", {}).get("state", "")
            country = area_details.get("components", {}).get("country", "")
            postal_code = area_details.get("components", {}).get("postal_code", "")
            
            return {
                "address": formatted_address,
                "coordinates": {
                    "lat": lat,
                    "lng": lng
                },
                "area_info": {
                    "city": city,
                    "state": state,
                    "country": country,
                    "postal_code": postal_code
                },
                "competition": {
                    "count": competition_count,
                    "density": competition_density,
                    "nearby_restaurants": [
                        {
                            "name": r["name"],
                            "address": r["address"],
                            "distance": r.get("distance", 0)
                        } for r in nearby[:10]  # Limit to top 10
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing location: {str(e)}")
            return {"error": str(e)}
    
    def compare_locations(self, locations: List[str], radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Compare multiple locations for restaurant potential.
        
        Args:
            locations: List of addresses to compare
            radius: Radius in meters for analysis
            
        Returns:
            List of location analyses with comparison metrics
        """
        try:
            results = []
            for location in locations:
                result = self.analyze_location(location, radius)
                results.append(result)
            
            # Add comparative ranking
            if all("error" not in r for r in results):
                # Sort by competition (lower is better)
                competition_sorted = sorted(results, key=lambda x: x["competition"]["count"])
                for i, result in enumerate(competition_sorted):
                    result["competition_rank"] = i + 1
                
                # Calculate average competition
                avg_competition = sum(r["competition"]["count"] for r in results) / len(results)
                
                for result in results:
                    result["comparison"] = {
                        "competition_rank": result.get("competition_rank", 0),
                        "vs_average_competition": result["competition"]["count"] - avg_competition
                    }
            
            return results
        except Exception as e:
            logger.error(f"Error comparing locations: {str(e)}")
            return [{"error": str(e)}]
    
    def find_optimal_location(self, center_point: str, radius: int = 5000) -> Dict[str, Any]:
        """
        Find an optimal location for a restaurant within a given radius.
        Uses a grid search approach to analyze different areas around a center point.
        
        Args:
            center_point: Center address for the search
            radius: Radius in meters to search around
            
        Returns:
            Dictionary with recommended locations
        """
        try:
            # Get coordinates for center point
            center_coords = self.map_service.geocode(center_point)
            if "error" in center_coords:
                return {"error": f"Could not geocode center point: {center_coords['error']}"}
            
            center_lat = center_coords["lat"]
            center_lng = center_coords["lng"]
            
            # Generate grid points around center (simplified approach)
            # For a real implementation, we'd use a more sophisticated method
            grid_points = []
            steps = 3  # 3x3 grid
            
            # Approximately 0.01 degree is about 1km at the equator
            # Adjust based on latitude to account for Earth's curvature
            lat_offset = (radius / 111000) / (steps - 1)  # 111km per degree at equator
            lng_offset = lat_offset / abs(max(0.01, abs(center_lat)) * 0.0174533)  # Scale by cos(lat)
            
            for i in range(steps):
                for j in range(steps):
                    lat = center_lat - lat_offset + 2 * lat_offset * i / (steps - 1)
                    lng = center_lng - lng_offset + 2 * lng_offset * j / (steps - 1)
                    
                    # Get address at this point
                    address_result = self.map_service.reverse_geocode(lat, lng)
                    if "error" not in address_result:
                        grid_points.append({
                            "lat": lat,
                            "lng": lng,
                            "address": address_result["address"]
                        })
            
            # Analyze each grid point
            analysis_results = []
            for point in grid_points:
                analysis = self.analyze_location(point["address"], radius=1000)
                if "error" not in analysis:
                    # Calculate a simple score (lower competition is better)
                    score = 100 - min(100, analysis["competition"]["count"] * 5)
                    analysis["score"] = score
                    analysis_results.append(analysis)
            
            # Sort by score (higher is better)
            sorted_results = sorted(analysis_results, key=lambda x: x.get("score", 0), reverse=True)
            
            return {
                "center_point": center_point,
                "search_radius_meters": radius,
                "recommendations": sorted_results[:3]  # Top 3 recommendations
            }
        except Exception as e:
            logger.error(f"Error finding optimal location: {str(e)}")
            return {"error": str(e)}
    
    def calculate_accessibility(self, location: str, population_centers: List[str], 
                               mode: str = "driving") -> Dict[str, Any]:
        """
        Calculate accessibility of a location from various population centers.
        
        Args:
            location: Target location address
            population_centers: List of population center addresses
            mode: Transportation mode (driving, walking, transit)
            
        Returns:
            Dictionary with accessibility metrics
        """
        try:
            travel_times = get_travel_times(location, population_centers, mode)
            
            # Calculate accessibility metrics
            avg_distance = 0
            avg_duration = 0
            valid_results = 0
            
            for center, result in travel_times.items():
                if "error" not in result:
                    avg_distance += result["distance"]["value"]
                    avg_duration += result["duration"]["value"]
                    valid_results += 1
            
            if valid_results > 0:
                avg_distance /= valid_results
                avg_duration /= valid_results
            
            # Convert to more readable format
            avg_distance_km = avg_distance / 1000
            avg_duration_min = avg_duration / 60
            
            # Calculate accessibility score (0-100)
            # Lower time is better, max score at 10 min, min score at 60 min
            accessibility_score = max(0, min(100, 100 - (avg_duration_min - 10) * 2))
            
            return {
                "location": location,
                "mode": mode,
                "population_centers": population_centers,
                "travel_times": travel_times,
                "metrics": {
                    "average_distance_km": round(avg_distance_km, 2),
                    "average_duration_min": round(avg_duration_min, 2),
                    "accessibility_score": round(accessibility_score, 1)
                }
            }
        except Exception as e:
            logger.error(f"Error calculating accessibility: {str(e)}")
            return {"error": str(e)}
    
    def analyze_catchment_area(self, location: str, 
                              travel_times: List[int] = [5, 10, 15]) -> Dict[str, Any]:
        """
        Analyze the catchment area for a location based on travel time isochrones.
        Note: This is a simplified version. In a real-world implementation, 
        we would use actual isochrone APIs from services like Mapbox.
        
        Args:
            location: Address of the target location
            travel_times: List of travel times in minutes to analyze
            
        Returns:
            Dictionary with catchment area analysis
        """
        try:
            # Get coordinates for the location
            geocode_result = self.map_service.geocode(location)
            if "error" in geocode_result:
                return {"error": f"Could not geocode location: {geocode_result['error']}"}
            
            lat = geocode_result["lat"]
            lng = geocode_result["lng"]
            
            # For each travel time, we'll estimate a radius
            # This is a very simplified approach - in real world, use actual isochrones
            # Average driving speed in urban areas: ~25 km/h = ~400m per minute
            catchment_areas = []
            for minutes in travel_times:
                # Very rough approximation
                radius_meters = minutes * 400  # 400m per minute
                
                # Simplified estimation of population reached
                # In a real system, we would use actual population density data
                population_estimate = minutes * minutes * 1000  # Just a dummy formula
                
                catchment_areas.append({
                    "travel_time_minutes": minutes,
                    "estimated_radius_meters": radius_meters,
                    "estimated_population": population_estimate
                })
            
            return {
                "location": location,
                "coordinates": {"lat": lat, "lng": lng},
                "catchment_areas": catchment_areas
            }
        except Exception as e:
            logger.error(f"Error analyzing catchment area: {str(e)}")
            return {"error": str(e)}
    
    def analyze_competition(self, location: str, radius: int = 1000) -> Dict[str, Any]:
        """
        Perform detailed competition analysis around a location.
        
        Args:
            location: Address of the target location
            radius: Radius in meters to analyze
            
        Returns:
            Dictionary with competition analysis
        """
        try:
            # Get coordinates for the location
            geocode_result = self.map_service.geocode(location)
            if "error" in geocode_result:
                return {"error": f"Could not geocode location: {geocode_result['error']}"}
            
            lat = geocode_result["lat"]
            lng = geocode_result["lng"]
            
            # Get nearby restaurants
            nearby = self.map_service.search_nearby(lat, lng, radius, "restaurant")
            
            # Count restaurants by category/cuisine (if available)
            categories = {}
            for restaurant in nearby:
                for category in restaurant.get("categories", []):
                    if category in categories:
                        categories[category] += 1
                    else:
                        categories[category] = 1
            
            # Sort categories by count
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            # Get top 5 restaurants (if place details provide ratings)
            top_restaurants = []
            rated_restaurants = [r for r in nearby if r.get("rating", 0) > 0]
            sorted_restaurants = sorted(rated_restaurants, key=lambda x: x.get("rating", 0), reverse=True)
            
            for restaurant in sorted_restaurants[:5]:
                # Get more details if available
                details = {}
                if "place_id" in restaurant:
                    details = self.map_service.get_place_details(restaurant["place_id"])
                
                top_restaurants.append({
                    "name": restaurant["name"],
                    "address": restaurant["address"],
                    "rating": restaurant.get("rating", 0),
                    "total_ratings": details.get("total_ratings", 0),
                    "price_level": details.get("price_level", 0),
                    "website": details.get("website", "")
                })
            
            return {
                "location": location,
                "radius_meters": radius,
                "total_restaurants": len(nearby),
                "restaurant_density": len(nearby) / (3.14159 * radius * radius / 1000000),  # per sq km
                "categories": dict(sorted_categories),
                "top_rated": top_restaurants
            }
        except Exception as e:
            logger.error(f"Error analyzing competition: {str(e)}")
            return {"error": str(e)}

# Helper class for storing and retrieving location data
class LocationDataManager:
    """Manages storage and retrieval of location data."""
    
    def __init__(self, db_connector=None):
        """Initialize with optional database connector."""
        self.db = db_connector
        self.cache = {}
    
    def save_location_analysis(self, location: str, analysis: Dict[str, Any]) -> bool:
        """Save location analysis to database."""
        try:
            if self.db:
                # If we have a DB connector, save there
                collection = self.db.get_collection('location_analyses')
                analysis['location'] = location
                analysis['timestamp'] = datetime.now()
                collection.update_one(
                    {'location': location},
                    {'$set': analysis},
                    upsert=True
                )
            
            # Also save to cache
            self.cache[location] = analysis
            return True
        except Exception as e:
            logger.error(f"Error saving location analysis: {str(e)}")
            return False
    
    def get_location_analysis(self, location: str) -> Optional[Dict[str, Any]]:
        """Get location analysis from cache or database."""
        # Check cache first
        if location in self.cache:
            return self.cache[location]
        
        # If not in cache, try database
        if self.db:
            try:
                collection = self.db.get_collection('location_analyses')
                result = collection.find_one({'location': location})
                if result:
                    # Add to cache and return
                    self.cache[location] = result
                    return result
            except Exception as e:
                logger.error(f"Error retrieving location analysis: {str(e)}")
        
        return None
    
    def get_saved_locations(self, limit: int = 100) -> List[str]:
        """Get list of previously analyzed locations."""
        locations = []
        
        # Get from database if available
        if self.db:
            try:
                collection = self.db.get_collection('location_analyses')
                cursor = collection.find({}, {'location': 1}).limit(limit)
                locations = [doc['location'] for doc in cursor if 'location' in doc]
            except Exception as e:
                logger.error(f"Error retrieving saved locations: {str(e)}")
        
        # Add from cache if not already in list
        for location in self.cache.keys():
            if location not in locations:
                locations.append(location)
                if len(locations) >= limit:
                    break
        
        return locations
