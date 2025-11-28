"""
Maps and Location API integration for the Restaurant Chain Advisor system.
"""

import os
import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache

# Import config
from utils.config import GOOGLE_MAPS_API_KEY, HERE_MAPS_API_KEY, TOMTOM_API_KEY
from utils.config import GEOAPIFY_API_KEY, DEFAULT_MAP_SERVICE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MapServiceError(Exception):
    """Exception raised for errors in the map service API calls."""
    pass

class BaseMapService:
    """Base class for map service API integrations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.service_name = "base"
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert an address to coordinates."""
        raise NotImplementedError("Subclasses must implement geocode()")
    
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Convert coordinates to an address."""
        raise NotImplementedError("Subclasses must implement reverse_geocode()")
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get details for a specific place."""
        raise NotImplementedError("Subclasses must implement get_place_details()")
    
    def search_nearby(self, lat: float, lng: float, radius: int = 1000, type: str = "restaurant") -> List[Dict[str, Any]]:
        """Search for places near a location."""
        raise NotImplementedError("Subclasses must implement search_nearby()")
    
    def calculate_distance(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        """Calculate distance and duration between two points."""
        raise NotImplementedError("Subclasses must implement calculate_distance()")
    
    def get_place_insights(self, place_id: str) -> Dict[str, Any]:
        """Get additional insights about a place, if available."""
        raise NotImplementedError("Subclasses must implement get_place_insights()")

class GoogleMapsService(BaseMapService):
    """Google Maps API integration."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or GOOGLE_MAPS_API_KEY)
        self.service_name = "google_maps"
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    @lru_cache(maxsize=100)
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert an address to coordinates using Google Geocoding API."""
        url = f"{self.base_url}/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps Geocoding error: {data['status']}")
                return {"error": data["status"], "coordinates": None}
            
            location = data["results"][0]["geometry"]["location"]
            formatted_address = data["results"][0]["formatted_address"]
            place_id = data["results"][0]["place_id"]
            
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "address": formatted_address,
                "place_id": place_id
            }
        except Exception as e:
            logger.error(f"Error in Google Maps geocode: {str(e)}")
            return {"error": str(e), "coordinates": None}
    
    @lru_cache(maxsize=100)
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Convert coordinates to an address using Google Geocoding API."""
        url = f"{self.base_url}/geocode/json"
        params = {
            "latlng": f"{lat},{lng}",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps Reverse Geocoding error: {data['status']}")
                return {"error": data["status"], "address": None}
            
            result = data["results"][0]
            formatted_address = result["formatted_address"]
            place_id = result["place_id"]
            
            # Extract address components
            address_components = {}
            for component in result.get("address_components", []):
                types = component.get("types", [])
                if "locality" in types:
                    address_components["city"] = component.get("long_name")
                elif "administrative_area_level_1" in types:
                    address_components["state"] = component.get("long_name")
                elif "country" in types:
                    address_components["country"] = component.get("long_name")
                elif "postal_code" in types:
                    address_components["postal_code"] = component.get("long_name")
            
            return {
                "address": formatted_address,
                "place_id": place_id,
                "components": address_components
            }
        except Exception as e:
            logger.error(f"Error in Google Maps reverse geocode: {str(e)}")
            return {"error": str(e), "address": None}
    
    @lru_cache(maxsize=50)
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get details for a specific place using Google Places API."""
        url = f"{self.base_url}/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,price_level,opening_hours,geometry",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps Place Details error: {data['status']}")
                return {"error": data["status"]}
            
            result = data["result"]
            
            return {
                "name": result.get("name", ""),
                "address": result.get("formatted_address", ""),
                "phone": result.get("formatted_phone_number", ""),
                "website": result.get("website", ""),
                "rating": result.get("rating", 0),
                "total_ratings": result.get("user_ratings_total", 0),
                "price_level": result.get("price_level", 0),
                "location": result.get("geometry", {}).get("location", {}),
                "opening_hours": result.get("opening_hours", {}).get("weekday_text", [])
            }
        except Exception as e:
            logger.error(f"Error in Google Maps place details: {str(e)}")
            return {"error": str(e)}
    
    def search_nearby(self, lat: float, lng: float, radius: int = 1000, type: str = "restaurant") -> List[Dict[str, Any]]:
        """Search for places near a location using Google Places API."""
        url = f"{self.base_url}/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": type,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps Nearby Search error: {data['status']}")
                return []
            
            results = []
            for place in data.get("results", []):
                place_result = {
                    "place_id": place.get("place_id", ""),
                    "name": place.get("name", ""),
                    "address": place.get("vicinity", ""),
                    "rating": place.get("rating", 0),
                    "total_ratings": place.get("user_ratings_total", 0),
                    "price_level": place.get("price_level", 0),
                    "location": place.get("geometry", {}).get("location", {})
                }
                results.append(place_result)
            
            return results
        except Exception as e:
            logger.error(f"Error in Google Maps nearby search: {str(e)}")
            return []
    
    def calculate_distance(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        """Calculate distance and duration between two points using Google Distance Matrix API."""
        url = f"{self.base_url}/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Google Maps Distance Matrix error: {data['status']}")
                return {"error": data["status"]}
            
            # Get the first element (assumes single origin and destination)
            element = data["rows"][0]["elements"][0]
            
            if element["status"] != "OK":
                return {"error": element["status"]}
            
            return {
                "distance": {
                    "value": element["distance"]["value"],  # in meters
                    "text": element["distance"]["text"]
                },
                "duration": {
                    "value": element["duration"]["value"],  # in seconds
                    "text": element["duration"]["text"]
                },
                "origin_address": data["origin_addresses"][0],
                "destination_address": data["destination_addresses"][0]
            }
        except Exception as e:
            logger.error(f"Error in Google Maps distance calculation: {str(e)}")
            return {"error": str(e)}
    
    def get_place_insights(self, place_id: str) -> Dict[str, Any]:
        """Get additional insights about a place from Google Places API."""
        # First get basic details
        details = self.get_place_details(place_id)
        if "error" in details:
            return details
        
        # Try to get photos if available
        url = f"{self.base_url}/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "photos,reviews",
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] != "OK":
                return details  # Return basic details if photos/reviews failed
            
            result = data["result"]
            
            # Add photos if available
            photos = []
            if "photos" in result:
                for photo in result["photos"][:3]:  # Limit to 3 photos
                    photo_ref = photo.get("photo_reference")
                    if photo_ref:
                        photo_url = f"{self.base_url}/place/photo?maxwidth=400&photoreference={photo_ref}&key={self.api_key}"
                        photos.append(photo_url)
            
            details["photos"] = photos
            
            # Add reviews if available
            reviews = []
            if "reviews" in result:
                for review in result["reviews"][:3]:  # Limit to 3 reviews
                    review_data = {
                        "author": review.get("author_name", "Anonymous"),
                        "rating": review.get("rating", 0),
                        "text": review.get("text", ""),
                        "time": review.get("relative_time_description", "")
                    }
                    reviews.append(review_data)
            
            details["reviews"] = reviews
            
            return details
        except Exception as e:
            logger.error(f"Error in Google Maps place insights: {str(e)}")
            return details  # Return basic details if insights failed

class HereMapsService(BaseMapService):
    """HERE Maps API integration."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or HERE_MAPS_API_KEY)
        self.service_name = "here_maps"
        self.base_url = "https://lookup.search.hereapi.com/v1"
        self.discover_url = "https://discover.search.hereapi.com/v1"
        self.route_url = "https://router.hereapi.com/v8/routes"
    
    @lru_cache(maxsize=100)
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert an address to coordinates using HERE Geocoding API."""
        url = f"{self.base_url}/geocode"
        params = {
            "q": address,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "items" not in data or not data["items"]:
                logger.error(f"HERE Maps Geocoding error: No results found")
                return {"error": "No results found", "coordinates": None}
            
            item = data["items"][0]
            location = item["position"]
            
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "address": item.get("address", {}).get("label", ""),
                "place_id": item.get("id", "")
            }
        except Exception as e:
            logger.error(f"Error in HERE Maps geocode: {str(e)}")
            return {"error": str(e), "coordinates": None}
    
    @lru_cache(maxsize=100)
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Convert coordinates to an address using HERE Geocoding API."""
        url = f"{self.base_url}/revgeocode"
        params = {
            "at": f"{lat},{lng}",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "items" not in data or not data["items"]:
                logger.error(f"HERE Maps Reverse Geocoding error: No results found")
                return {"error": "No results found", "address": None}
            
            item = data["items"][0]
            address = item["address"]
            
            # Extract address components
            address_components = {
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "country": address.get("countryName", ""),
                "postal_code": address.get("postalCode", "")
            }
            
            return {
                "address": address.get("label", ""),
                "place_id": item.get("id", ""),
                "components": address_components
            }
        except Exception as e:
            logger.error(f"Error in HERE Maps reverse geocode: {str(e)}")
            return {"error": str(e), "address": None}
    
    @lru_cache(maxsize=50)
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get details for a specific place using HERE Lookup API."""
        url = f"{self.base_url}/lookup"
        params = {
            "id": place_id,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if not data:
                logger.error(f"HERE Maps Place Details error: No results found")
                return {"error": "No results found"}
            
            # Extract relevant information
            location = data.get("position", {})
            address = data.get("address", {})
            contacts = data.get("contacts", {})
            phone = ""
            website = ""
            
            if contacts and "phones" in contacts and contacts["phones"]:
                phone = contacts["phones"][0].get("value", "")
            
            if contacts and "website" in contacts and contacts["website"]:
                website = contacts["website"][0].get("value", "")
            
            return {
                "name": data.get("title", ""),
                "address": address.get("label", ""),
                "phone": phone,
                "website": website,
                "location": location,
                "categories": [cat.get("name", "") for cat in data.get("categories", [])],
                "opening_hours": []  # HERE API has a different format for opening hours
            }
        except Exception as e:
            logger.error(f"Error in HERE Maps place details: {str(e)}")
            return {"error": str(e)}
    
    def search_nearby(self, lat: float, lng: float, radius: int = 1000, type: str = "restaurant") -> List[Dict[str, Any]]:
        """Search for places near a location using HERE Discover API."""
        url = f"{self.discover_url}/browse"
        params = {
            "at": f"{lat},{lng}",
            "categories": self._map_category_to_here(type),
            "limit": 20,
            "radius": radius,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "items" not in data or not data["items"]:
                return []
            
            results = []
            for place in data["items"]:
                place_result = {
                    "place_id": place.get("id", ""),
                    "name": place.get("title", ""),
                    "address": place.get("address", {}).get("label", ""),
                    "location": place.get("position", {}),
                    "distance": place.get("distance", 0),
                    "categories": [cat.get("name", "") for cat in place.get("categories", [])]
                }
                results.append(place_result)
            
            return results
        except Exception as e:
            logger.error(f"Error in HERE Maps nearby search: {str(e)}")
            return []
    
    def _map_category_to_here(self, google_type: str) -> str:
        """Map Google place types to HERE categories."""
        mapping = {
            "restaurant": "100-1000",  # Eating and Drinking
            "cafe": "100-1100",
            "bar": "100-1300",
            "lodging": "500-5000",
            "shopping_mall": "600-6000"
        }
        return mapping.get(google_type, "100-1000")  # Default to restaurants
    
    def calculate_distance(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        """Calculate distance and duration between two points using HERE Routing API."""
        # First convert addresses to coordinates if needed
        origin_coords = origin
        dest_coords = destination
        
        if "," not in origin:
            geo_result = self.geocode(origin)
            if "error" not in geo_result and geo_result["coordinates"] is not None:
                origin_coords = f"{geo_result['lat']},{geo_result['lng']}"
        
        if "," not in destination:
            geo_result = self.geocode(destination)
            if "error" not in geo_result and geo_result["coordinates"] is not None:
                dest_coords = f"{geo_result['lat']},{geo_result['lng']}"
        
        # Map transport mode to HERE API format
        transport_mode = "car"
        if mode == "walking":
            transport_mode = "pedestrian"
        elif mode == "bicycling":
            transport_mode = "bicycle"
        
        url = self.route_url
        params = {
            "transportMode": transport_mode,
            "origin": origin_coords,
            "destination": dest_coords,
            "return": "summary",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "routes" not in data or not data["routes"]:
                logger.error(f"HERE Maps Distance error: No routes found")
                return {"error": "No routes found"}
            
            route = data["routes"][0]
            section = route["sections"][0]
            summary = section["summary"]
            
            # Convert meters to kilometers for display text
            distance_meters = summary.get("length", 0)
            distance_text = f"{distance_meters / 1000:.1f} km"
            
            # Convert seconds to minutes/hours for display text
            duration_seconds = summary.get("duration", 0)
            if duration_seconds < 3600:
                duration_text = f"{duration_seconds // 60} mins"
            else:
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                duration_text = f"{hours} hr {minutes} mins"
            
            return {
                "distance": {
                    "value": distance_meters,  # in meters
                    "text": distance_text
                },
                "duration": {
                    "value": duration_seconds,  # in seconds
                    "text": duration_text
                },
                "origin_address": origin,
                "destination_address": destination
            }
        except Exception as e:
            logger.error(f"Error in HERE Maps distance calculation: {str(e)}")
            return {"error": str(e)}
    
    def get_place_insights(self, place_id: str) -> Dict[str, Any]:
        """Get additional insights about a place."""
        # HERE doesn't have as much additional data as Google, so we just return place details
        return self.get_place_details(place_id)

class GeoapifyService(BaseMapService):
    """Geoapify API integration - a free alternative to Google Maps."""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or GEOAPIFY_API_KEY)
        self.service_name = "geoapify"
        self.geocode_url = "https://api.geoapify.com/v1/geocode"
        self.places_url = "https://api.geoapify.com/v2/places"
        self.routing_url = "https://api.geoapify.com/v1/routing"
    
    @lru_cache(maxsize=100)
    def geocode(self, address: str) -> Dict[str, Any]:
        """Convert an address to coordinates using Geoapify Geocoding API."""
        url = f"{self.geocode_url}/search"
        params = {
            "text": address,
            "format": "json",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "results" not in data or not data["results"]:
                logger.error(f"Geoapify Geocoding error: No results found")
                return {"error": "No results found", "coordinates": None}
            
            result = data["results"][0]
            
            return {
                "lat": result.get("lat", 0),
                "lng": result.get("lon", 0),
                "address": result.get("formatted", ""),
                "place_id": result.get("place_id", "")
            }
        except Exception as e:
            logger.error(f"Error in Geoapify geocode: {str(e)}")
            return {"error": str(e), "coordinates": None}
    
    @lru_cache(maxsize=100)
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """Convert coordinates to an address using Geoapify Geocoding API."""
        url = f"{self.geocode_url}/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "results" not in data or not data["results"]:
                logger.error(f"Geoapify Reverse Geocoding error: No results found")
                return {"error": "No results found", "address": None}
            
            result = data["results"][0]
            
            # Extract address components
            address_components = {
                "city": result.get("city", ""),
                "state": result.get("state", ""),
                "country": result.get("country", ""),
                "postal_code": result.get("postcode", "")
            }
            
            return {
                "address": result.get("formatted", ""),
                "place_id": result.get("place_id", ""),
                "components": address_components
            }
        except Exception as e:
            logger.error(f"Error in Geoapify reverse geocode: {str(e)}")
            return {"error": str(e), "address": None}
    
    @lru_cache(maxsize=50)
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get details for a specific place using Geoapify Places API."""
        url = f"{self.places_url}/details"
        params = {
            "id": place_id,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "features" not in data or not data["features"]:
                logger.error(f"Geoapify Place Details error: No results found")
                return {"error": "No results found"}
            
            feature = data["features"][0]
            properties = feature["properties"]
            
            return {
                "name": properties.get("name", ""),
                "address": properties.get("formatted", ""),
                "phone": properties.get("contact", {}).get("phone", ""),
                "website": properties.get("contact", {}).get("website", ""),
                "location": {
                    "lat": feature["geometry"]["coordinates"][1],
                    "lng": feature["geometry"]["coordinates"][0]
                },
                "categories": properties.get("categories", []),
                "opening_hours": properties.get("opening_hours", {})
            }
        except Exception as e:
            logger.error(f"Error in Geoapify place details: {str(e)}")
            return {"error": str(e)}
    
    def search_nearby(self, lat: float, lng: float, radius: int = 1000, type: str = "restaurant") -> List[Dict[str, Any]]:
        """Search for places near a location using Geoapify Places API."""
        url = f"{self.places_url}"
        params = {
            "categories": self._map_category_to_geoapify(type),
            "filter": f"circle:{lng},{lat},{radius}",
            "limit": 20,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "features" not in data or not data["features"]:
                return []
            
            results = []
            for feature in data["features"]:
                properties = feature["properties"]
                place_result = {
                    "place_id": properties.get("place_id", ""),
                    "name": properties.get("name", ""),
                    "address": properties.get("formatted", ""),
                    "location": {
                        "lat": feature["geometry"]["coordinates"][1],
                        "lng": feature["geometry"]["coordinates"][0]
                    },
                    "categories": properties.get("categories", []),
                    "distance": properties.get("distance", 0)
                }
                results.append(place_result)
            
            return results
        except Exception as e:
            logger.error(f"Error in Geoapify nearby search: {str(e)}")
            return []
    
    def _map_category_to_geoapify(self, google_type: str) -> str:
        """Map Google place types to Geoapify categories."""
        mapping = {
            "restaurant": "catering.restaurant",
            "cafe": "catering.cafe",
            "bar": "catering.bar",
            "lodging": "accommodation.hotel",
            "shopping_mall": "commercial.shopping_mall"
        }
        return mapping.get(google_type, "catering.restaurant")  # Default to restaurants
    
    def calculate_distance(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        """Calculate distance and duration between two points using Geoapify Routing API."""
        # First convert addresses to coordinates if needed
        origin_coords = origin
        dest_coords = destination
        
        if "," not in origin:
            geo_result = self.geocode(origin)
            if "error" not in geo_result and geo_result["coordinates"] is not None:
                origin_coords = f"{geo_result['lng']},{geo_result['lat']}"  # Note: Geoapify uses lon,lat order
        
        if "," not in destination:
            geo_result = self.geocode(destination)
            if "error" not in geo_result and geo_result["coordinates"] is not None:
                dest_coords = f"{geo_result['lng']},{geo_result['lat']}"  # Note: Geoapify uses lon,lat order
        
        # Map transport mode to Geoapify API format
        transport_mode = "drive"
        if mode == "walking":
            transport_mode = "walk"
        elif mode == "bicycling":
            transport_mode = "bicycle"
        
        url = f"{self.routing_url}"
        params = {
            "waypoints": f"{origin_coords}|{dest_coords}",
            "mode": transport_mode,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "features" not in data or not data["features"]:
                logger.error(f"Geoapify Routing error: No routes found")
                return {"error": "No routes found"}
            
            feature = data["features"][0]
            properties = feature["properties"]
            
            # Extract distance and duration
            distance_meters = properties.get("distance", 0)
            distance_text = f"{distance_meters / 1000:.1f} km"
            
            duration_seconds = properties.get("time", 0)
            if duration_seconds < 3600:
                duration_text = f"{duration_seconds // 60} mins"
            else:
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                duration_text = f"{hours} hr {minutes} mins"
            
            return {
                "distance": {
                    "value": distance_meters,  # in meters
                    "text": distance_text
                },
                "duration": {
                    "value": duration_seconds,  # in seconds
                    "text": duration_text
                },
                "origin_address": origin,
                "destination_address": destination
            }
        except Exception as e:
            logger.error(f"Error in Geoapify distance calculation: {str(e)}")
            return {"error": str(e)}
    
    def get_place_insights(self, place_id: str) -> Dict[str, Any]:
        """Get additional insights about a place."""
        # Geoapify doesn't have much additional data, so we just return place details
        return self.get_place_details(place_id)

class MapServiceFactory:
    """Factory for creating map service instances."""
    
    @staticmethod
    def get_service(service_name: str = None) -> BaseMapService:
        """Get a map service instance based on the service name."""
        service_name = service_name or DEFAULT_MAP_SERVICE
        
        if service_name == "google_maps":
            return GoogleMapsService()
        elif service_name == "here_maps":
            return HereMapsService()
        elif service_name == "geoapify":
            return GeoapifyService()
        else:
            # Default to the service with valid API key
            if GOOGLE_MAPS_API_KEY:
                return GoogleMapsService()
            elif HERE_MAPS_API_KEY:
                return HereMapsService()
            elif GEOAPIFY_API_KEY:
                return GeoapifyService()
            else:
                raise MapServiceError("No valid map service API key found")

# Helper functions for common map operations
def get_coordinates(address: str, service_name: str = None) -> Tuple[float, float]:
    """Get coordinates for an address."""
    service = MapServiceFactory.get_service(service_name)
    result = service.geocode(address)
    
    if "error" in result or not result:
        return None, None
    
    return result.get("lat"), result.get("lng")

def get_address(lat: float, lng: float, service_name: str = None) -> str:
    """Get address for coordinates."""
    service = MapServiceFactory.get_service(service_name)
    result = service.reverse_geocode(lat, lng)
    
    if "error" in result or not result:
        return ""
    
    return result.get("address", "")

def get_nearby_restaurants(address: str, radius: int = 1000, service_name: str = None) -> List[Dict[str, Any]]:
    """Get nearby restaurants for an address."""
    # Get coordinates for address
    lat, lng = get_coordinates(address, service_name)
    if lat is None or lng is None:
        return []
    
    # Search nearby
    service = MapServiceFactory.get_service(service_name)
    return service.search_nearby(lat, lng, radius, "restaurant")

def get_distance_between(origin: str, destination: str, mode: str = "driving", service_name: str = None) -> Dict[str, Any]:
    """Get distance between two addresses."""
    service = MapServiceFactory.get_service(service_name)
    return service.calculate_distance(origin, destination, mode)

def get_travel_times(location: str, destinations: List[str], mode: str = "driving", service_name: str = None) -> Dict[str, Dict[str, Any]]:
    """Get travel times from a location to multiple destinations."""
    service = MapServiceFactory.get_service(service_name)
    results = {}
    
    for destination in destinations:
        result = service.calculate_distance(location, destination, mode)
        results[destination] = result
    
    return results

# Cache management function
def clear_geocoding_cache():
    """Clear the geocoding cache."""
    for service_class in [GoogleMapsService, HereMapsService, GeoapifyService]:
        service_class.geocode.cache_clear()
        service_class.reverse_geocode.cache_clear()
        service_class.get_place_details.cache_clear()
