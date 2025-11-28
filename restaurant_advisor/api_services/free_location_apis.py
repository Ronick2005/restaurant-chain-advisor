"""
Free API integrations for location data, POI search, and demographic information.
Alternatives to paid Google Places API.
"""

import os
import requests
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenStreetMapAPI:
    """
    Free OpenStreetMap API integration using Nominatim and Overpass.
    No API key required, rate limited to 1 req/sec.
    """
    
    def __init__(self):
        self.nominatim_url = os.getenv("NOMINATIM_API_URL", "https://nominatim.openstreetmap.org")
        self.overpass_url = os.getenv("OVERPASS_API_URL", "https://overpass-api.de/api/interpreter")
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1 second between requests
    
    def _rate_limit(self):
        """Ensure we respect the 1 req/sec rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def geocode_location(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Get coordinates and details for a location using Nominatim.
        
        Args:
            location: Location name (e.g., "Bandra West, Mumbai")
            
        Returns:
            Location details with lat, lon, and metadata
        """
        self._rate_limit()
        
        try:
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {"User-Agent": "RestaurantAdvisorBot/1.0"}
            
            response = requests.get(
                f"{self.nominatim_url}/search",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    return {
                        "name": result.get("display_name"),
                        "latitude": float(result.get("lat")),
                        "longitude": float(result.get("lon")),
                        "address": result.get("address", {}),
                        "type": result.get("type"),
                        "source": "openstreetmap"
                    }
            
            logger.warning(f"Geocoding failed for {location}: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding {location}: {e}")
            return None
    
    def search_restaurants_nearby(self, latitude: float, longitude: float, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Search for restaurants near coordinates using Overpass API.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            radius: Search radius in meters (default 1km)
            
        Returns:
            List of restaurants with details
        """
        try:
            # Overpass QL query for restaurants
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
              way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                restaurants = []
                
                for element in data.get("elements", []):
                    if element.get("type") in ["node", "way"]:
                        tags = element.get("tags", {})
                        restaurants.append({
                            "name": tags.get("name", "Unknown"),
                            "cuisine": tags.get("cuisine", "Unknown"),
                            "latitude": element.get("lat"),
                            "longitude": element.get("lon"),
                            "address": tags.get("addr:full", tags.get("addr:street", "")),
                            "phone": tags.get("phone", ""),
                            "website": tags.get("website", ""),
                            "opening_hours": tags.get("opening_hours", ""),
                            "source": "openstreetmap"
                        })
                
                return restaurants
            
            logger.warning(f"Restaurant search failed: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching restaurants: {e}")
            return []
    
    def get_poi_density(self, location: str, poi_types: List[str] = None) -> Dict[str, Any]:
        """
        Get density of points of interest in an area.
        
        Args:
            location: Location name
            poi_types: Types to search (default: ["restaurant", "cafe", "fast_food"])
            
        Returns:
            POI density statistics
        """
        if poi_types is None:
            poi_types = ["restaurant", "cafe", "fast_food"]
        
        # First geocode the location
        coords = self.geocode_location(location)
        if not coords:
            return {"error": "Could not geocode location"}
        
        lat, lon = coords["latitude"], coords["longitude"]
        
        # Search for each POI type
        poi_counts = {}
        for poi_type in poi_types:
            try:
                query = f"""
                [out:json][timeout:25];
                (
                  node["amenity"="{poi_type}"](around:2000,{lat},{lon});
                  way["amenity"="{poi_type}"](around:2000,{lat},{lon});
                );
                out count;
                """
                
                response = requests.post(
                    self.overpass_url,
                    data={"data": query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data.get("elements", []))
                    poi_counts[poi_type] = count
                
                time.sleep(0.5)  # Small delay between queries
                
            except Exception as e:
                logger.error(f"Error counting {poi_type}: {e}")
                poi_counts[poi_type] = 0
        
        total_pois = sum(poi_counts.values())
        
        return {
            "location": location,
            "poi_counts": poi_counts,
            "total_pois": total_pois,
            "density_level": "high" if total_pois > 50 else "medium" if total_pois > 20 else "low",
            "source": "openstreetmap"
        }


class FoursquareAPI:
    """
    Foursquare Places API integration (FREE: 50 requests/day).
    Sign up at https://developer.foursquare.com/
    """
    
    def __init__(self):
        self.api_key = os.getenv("FOURSQUARE_API_KEY")
        self.base_url = "https://api.foursquare.com/v3"
    
    def search_places(self, query: str, near: str, categories: str = "13065") -> List[Dict[str, Any]]:
        """
        Search for places using Foursquare API.
        
        Args:
            query: Search query (e.g., "restaurants")
            near: Location (e.g., "Mumbai, India")
            categories: Category IDs (13065 = restaurants)
            
        Returns:
            List of places with ratings and popularity
        """
        if not self.api_key:
            logger.warning("Foursquare API key not configured")
            return []
        
        try:
            headers = {
                "Authorization": self.api_key,
                "Accept": "application/json"
            }
            
            params = {
                "query": query,
                "near": near,
                "categories": categories,
                "limit": 50
            }
            
            response = requests.get(
                f"{self.base_url}/places/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                places = []
                
                for result in data.get("results", []):
                    places.append({
                        "name": result.get("name"),
                        "address": result.get("location", {}).get("formatted_address"),
                        "category": result.get("categories", [{}])[0].get("name"),
                        "latitude": result.get("geocodes", {}).get("main", {}).get("latitude"),
                        "longitude": result.get("geocodes", {}).get("main", {}).get("longitude"),
                        "popularity": result.get("popularity", 0),
                        "rating": result.get("rating", 0),
                        "price": result.get("price", "unknown"),
                        "source": "foursquare"
                    })
                
                return places
            
            logger.warning(f"Foursquare search failed: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Foursquare: {e}")
            return []


class TomTomAPI:
    """
    TomTom Maps API (FREE: 2500 requests/day, 100k requests/month).
    Sign up at https://developer.tomtom.com/
    """
    
    def __init__(self):
        self.api_key = os.getenv("TOMTOM_API_KEY")
        self.base_url = "https://api.tomtom.com/search/2"
    
    def search_restaurants(self, city: str, latitude: float = None, longitude: float = None) -> List[Dict[str, Any]]:
        """
        Search for restaurants using TomTom API.
        
        Args:
            city: City name
            latitude: Optional latitude
            longitude: Optional longitude
            
        Returns:
            List of restaurants with details
        """
        if not self.api_key:
            logger.warning("TomTom API key not configured")
            return []
        
        try:
            # Use category search endpoint
            query = "restaurant"
            params = {
                "key": self.api_key,
                "limit": 50,
                "categorySet": "7315",  # Restaurant category
                "countrySet": "IN",  # India
            }
            
            # Use either coordinates or city name
            if latitude and longitude:
                endpoint = f"{self.base_url}/categorySearch/{query}.json"
                params["lat"] = latitude
                params["lon"] = longitude
                params["radius"] = 5000  # 5km radius
            else:
                endpoint = f"{self.base_url}/search/{query}.json"
                params["query"] = f"{query} {city}"
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                restaurants = []
                
                for result in data.get("results", []):
                    poi = result.get("poi", {})
                    address = result.get("address", {})
                    position = result.get("position", {})
                    
                    restaurants.append({
                        "name": poi.get("name"),
                        "address": address.get("freeformAddress"),
                        "latitude": position.get("lat"),
                        "longitude": position.get("lon"),
                        "category": poi.get("categories", ["Restaurant"])[0] if poi.get("categories") else "Restaurant",
                        "phone": poi.get("phone"),
                        "url": poi.get("url"),
                        "distance": result.get("dist"),
                        "source": "tomtom"
                    })
                
                return restaurants
            
            logger.warning(f"TomTom search failed: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching TomTom: {e}")
            return []


class GeoapifyAPI:
    """
    Geoapify Places API (FREE: 3000 requests/day).
    Sign up at https://www.geoapify.com/
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEOAPIFY_API_KEY")
        self.base_url = "https://api.geoapify.com/v2"
    
    def search_places(self, category: str, city: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for places using Geoapify.
        
        Args:
            category: Place category (e.g., "catering.restaurant")
            city: City name
            limit: Maximum results
            
        Returns:
            List of places
        """
        if not self.api_key:
            logger.warning("Geoapify API key not configured")
            return []
        
        try:
            params = {
                "categories": category,
                "filter": f"place:{city}",
                "limit": limit,
                "apiKey": self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/places",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                places = []
                
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])
                    
                    places.append({
                        "name": props.get("name"),
                        "address": props.get("address_line1"),
                        "city": props.get("city"),
                        "longitude": coords[0] if len(coords) > 0 else None,
                        "latitude": coords[1] if len(coords) > 1 else None,
                        "category": props.get("categories", []),
                        "source": "geoapify"
                    })
                
                return places
            
            logger.warning(f"Geoapify search failed: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Geoapify: {e}")
            return []


class FreeLocationDataAggregator:
    """
    Aggregates data from multiple free location APIs.
    Falls back between APIs if one fails or has no data.
    """
    
    def __init__(self):
        self.osm_api = OpenStreetMapAPI()
        self.foursquare_api = FoursquareAPI()
        self.tomtom_api = TomTomAPI()
        self.geoapify_api = GeoapifyAPI()
    
    def get_location_restaurants(self, city: str, locality: str = None) -> List[Dict[str, Any]]:
        """
        Get restaurants for a location from all available free APIs.
        
        Args:
            city: City name
            locality: Optional specific locality/area
            
        Returns:
            Aggregated list of restaurants
        """
        all_restaurants = []
        location_query = f"{locality}, {city}" if locality else city
        
        # Try OpenStreetMap first (always free, no key needed)
        logger.info(f"Searching OpenStreetMap for restaurants in {location_query}")
        coords = self.osm_api.geocode_location(location_query)
        if coords:
            osm_restaurants = self.osm_api.search_restaurants_nearby(
                coords["latitude"],
                coords["longitude"],
                radius=2000
            )
            all_restaurants.extend(osm_restaurants)
            logger.info(f"Found {len(osm_restaurants)} restaurants from OpenStreetMap")
        
        # Try Foursquare if API key available
        if os.getenv("FOURSQUARE_API_KEY"):
            logger.info("Searching Foursquare...")
            fs_restaurants = self.foursquare_api.search_places("restaurant", location_query)
            all_restaurants.extend(fs_restaurants)
            logger.info(f"Found {len(fs_restaurants)} restaurants from Foursquare")
        
        # Try TomTom if API key available
        if os.getenv("TOMTOM_API_KEY") and coords:
            logger.info("Searching TomTom Maps...")
            tomtom_restaurants = self.tomtom_api.search_restaurants(
                city,
                coords["latitude"],
                coords["longitude"]
            )
            all_restaurants.extend(tomtom_restaurants)
            logger.info(f"Found {len(tomtom_restaurants)} restaurants from TomTom")
        
        # Try Geoapify if API key available
        if os.getenv("GEOAPIFY_API_KEY"):
            logger.info("Searching Geoapify...")
            geo_restaurants = self.geoapify_api.search_places("catering.restaurant", location_query)
            all_restaurants.extend(geo_restaurants)
            logger.info(f"Found {len(geo_restaurants)} restaurants from Geoapify")
        
        return all_restaurants
    
    def get_poi_analysis(self, location: str) -> Dict[str, Any]:
        """
        Get comprehensive POI analysis for a location.
        
        Args:
            location: Location name
            
        Returns:
            POI density and analysis
        """
        # Use OpenStreetMap for POI density (always available)
        return self.osm_api.get_poi_density(location)
