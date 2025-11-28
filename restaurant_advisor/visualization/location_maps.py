"""
Location data visualization utilities using Folium maps.
"""

import folium
from folium.plugins import HeatMap, MarkerCluster
from typing import Dict, List, Any, Optional, Tuple
import json
import os
import webbrowser

# Import map API services
from api_services.maps_api import MapServiceFactory, get_coordinates

class LocationVisualizer:
    """
    Visualization tools for location data using Folium maps.
    """
    
    def __init__(self, output_dir: str = "visualizations"):
        """Initialize the visualizer with output directory."""
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def create_basic_map(self, center_lat: float, center_lng: float, zoom: int = 12) -> folium.Map:
        """
        Create a basic Folium map centered at the given coordinates.
        
        Args:
            center_lat: Latitude of the center point
            center_lng: Longitude of the center point
            zoom: Initial zoom level
            
        Returns:
            Folium Map object
        """
        return folium.Map(location=[center_lat, center_lng], zoom_start=zoom,
                         tiles="OpenStreetMap")
    
    def visualize_location_analysis(self, analysis: Dict[str, Any], filename: str = "location_analysis.html") -> str:
        """
        Create a map visualization for a location analysis.
        
        Args:
            analysis: Location analysis dictionary
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Extract location coordinates
            if "coordinates" not in analysis:
                # Try to get coordinates if not in analysis
                map_service = MapServiceFactory.get_service()
                geocode_result = map_service.geocode(analysis.get("location", ""))
                center_lat = geocode_result["lat"]
                center_lng = geocode_result["lng"]
            else:
                center_lat = analysis["coordinates"]["lat"]
                center_lng = analysis["coordinates"]["lng"]
            
            # Create the map
            m = self.create_basic_map(center_lat, center_lng)
            
            # Add marker for the main location
            folium.Marker(
                location=[center_lat, center_lng],
                popup=analysis.get("address", "Target Location"),
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)
            
            # Add competition markers if available
            if "competition" in analysis and "nearby_restaurants" in analysis["competition"]:
                restaurant_group = folium.FeatureGroup(name="Nearby Restaurants")
                
                for restaurant in analysis["competition"]["nearby_restaurants"]:
                    # Try to get coordinates for the restaurant
                    restaurant_coords = get_coordinates(restaurant["address"])
                    if restaurant_coords[0] is not None:
                        folium.Marker(
                            location=[restaurant_coords[0], restaurant_coords[1]],
                            popup=restaurant["name"],
                            icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
                        ).add_to(restaurant_group)
                
                restaurant_group.add_to(m)
            
            # Add radius circle
            folium.Circle(
                location=[center_lat, center_lng],
                radius=1000,  # 1km radius
                color="green",
                fill=True,
                fill_opacity=0.2,
                popup="1km Radius"
            ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Save the map
            output_path = os.path.join(self.output_dir, filename)
            m.save(output_path)
            
            return output_path
        except Exception as e:
            print(f"Error visualizing location analysis: {str(e)}")
            return ""
    
    def visualize_location_comparison(self, comparison_results: List[Dict[str, Any]], 
                                     filename: str = "location_comparison.html") -> str:
        """
        Create a map visualization for location comparisons.
        
        Args:
            comparison_results: List of location analysis results
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Find average coordinates for centering the map
            if not comparison_results:
                return ""
            
            # Get coordinates for each location
            coords = []
            for result in comparison_results:
                if "coordinates" in result:
                    coords.append((result["coordinates"]["lat"], result["coordinates"]["lng"]))
                else:
                    # Try to get coordinates if not in analysis
                    map_service = MapServiceFactory.get_service()
                    geocode_result = map_service.geocode(result.get("location", ""))
                    if "error" not in geocode_result:
                        coords.append((geocode_result["lat"], geocode_result["lng"]))
            
            if not coords:
                return ""
            
            # Calculate average coordinates
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lng = sum(c[1] for c in coords) / len(coords)
            
            # Create the map
            m = self.create_basic_map(avg_lat, avg_lng)
            
            # Add markers for each location
            for i, result in enumerate(comparison_results):
                if "coordinates" in result:
                    lat = result["coordinates"]["lat"]
                    lng = result["coordinates"]["lng"]
                else:
                    continue
                
                # Get competition info for popup
                competition_info = ""
                if "competition" in result:
                    comp = result["competition"]
                    competition_info = f"<b>Competition:</b> {comp.get('count', 0)} restaurants<br>"
                    competition_info += f"<b>Density:</b> {comp.get('density', 'N/A')}"
                
                # Set marker color based on rank if available
                color = "blue"
                if "comparison" in result and "competition_rank" in result["comparison"]:
                    rank = result["comparison"]["competition_rank"]
                    if rank == 1:
                        color = "green"
                    elif rank == 2:
                        color = "orange"
                
                # Create popup content
                popup_content = f"""
                <h4>{result.get('address', f'Location {i+1}')}</h4>
                {competition_info}
                """
                
                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color=color)
                ).add_to(m)
            
            # Save the map
            output_path = os.path.join(self.output_dir, filename)
            m.save(output_path)
            
            return output_path
        except Exception as e:
            print(f"Error visualizing location comparison: {str(e)}")
            return ""
    
    def visualize_optimal_locations(self, optimal_results: Dict[str, Any],
                                   filename: str = "optimal_locations.html") -> str:
        """
        Create a map visualization for optimal location recommendations.
        
        Args:
            optimal_results: Dictionary with optimal location recommendations
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Extract center point coordinates
            center_point = optimal_results.get("center_point", "")
            map_service = MapServiceFactory.get_service()
            geocode_result = map_service.geocode(center_point)
            
            if "error" in geocode_result:
                return ""
            
            center_lat = geocode_result["lat"]
            center_lng = geocode_result["lng"]
            
            # Create the map
            m = self.create_basic_map(center_lat, center_lng)
            
            # Add marker for center point
            folium.Marker(
                location=[center_lat, center_lng],
                popup=f"Center: {center_point}",
                icon=folium.Icon(color="red", icon="map-marker")
            ).add_to(m)
            
            # Add search radius
            search_radius = optimal_results.get("search_radius_meters", 5000)
            folium.Circle(
                location=[center_lat, center_lng],
                radius=search_radius,
                color="blue",
                fill=True,
                fill_opacity=0.1,
                popup=f"Search Radius: {search_radius/1000}km"
            ).add_to(m)
            
            # Add markers for recommended locations
            recommendations = optimal_results.get("recommendations", [])
            for i, rec in enumerate(recommendations):
                if "coordinates" in rec:
                    lat = rec["coordinates"]["lat"]
                    lng = rec["coordinates"]["lng"]
                    
                    # Create popup content
                    popup_content = f"""
                    <h4>Recommendation #{i+1}</h4>
                    <b>Address:</b> {rec.get('address', 'N/A')}<br>
                    <b>Score:</b> {rec.get('score', 0)}/100<br>
                    <b>Competition:</b> {rec.get('competition', {}).get('count', 0)} restaurants
                    """
                    
                    folium.Marker(
                        location=[lat, lng],
                        popup=folium.Popup(popup_content, max_width=300),
                        icon=folium.Icon(color="green", icon="star")
                    ).add_to(m)
            
            # Save the map
            output_path = os.path.join(self.output_dir, filename)
            m.save(output_path)
            
            return output_path
        except Exception as e:
            print(f"Error visualizing optimal locations: {str(e)}")
            return ""
    
    def visualize_competition(self, competition_analysis: Dict[str, Any],
                             filename: str = "competition_analysis.html") -> str:
        """
        Create a map visualization for competition analysis.
        
        Args:
            competition_analysis: Dictionary with competition analysis
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Get location coordinates
            location = competition_analysis.get("location", "")
            map_service = MapServiceFactory.get_service()
            geocode_result = map_service.geocode(location)
            
            if "error" in geocode_result:
                return ""
            
            center_lat = geocode_result["lat"]
            center_lng = geocode_result["lng"]
            
            # Create the map
            m = self.create_basic_map(center_lat, center_lng)
            
            # Add marker for main location
            folium.Marker(
                location=[center_lat, center_lng],
                popup=f"Target: {location}",
                icon=folium.Icon(color="red", icon="home")
            ).add_to(m)
            
            # Add analysis radius
            radius = competition_analysis.get("radius_meters", 1000)
            folium.Circle(
                location=[center_lat, center_lng],
                radius=radius,
                color="purple",
                fill=True,
                fill_opacity=0.1,
                popup=f"Analysis Radius: {radius/1000}km"
            ).add_to(m)
            
            # Get nearby restaurants
            # In a real application, we would use the actual nearby restaurant data
            # Here we'll simulate it by searching for restaurants
            nearby = []
            if "top_rated" in competition_analysis:
                nearby = competition_analysis["top_rated"]
            
            if nearby:
                # Create a cluster group for restaurants
                restaurant_cluster = MarkerCluster(name="Restaurants")
                
                for restaurant in nearby:
                    # Get coordinates for restaurant (simplified)
                    rest_coords = get_coordinates(restaurant.get("address", ""))
                    if rest_coords[0] is not None:
                        # Create popup content
                        popup_content = f"""
                        <h4>{restaurant.get('name', 'Restaurant')}</h4>
                        <b>Rating:</b> {restaurant.get('rating', 'N/A')}<br>
                        <b>Price Level:</b> {'$' * restaurant.get('price_level', 0) or 'N/A'}<br>
                        """
                        
                        if restaurant.get('website'):
                            popup_content += f"<a href='{restaurant['website']}' target='_blank'>Website</a>"
                        
                        folium.Marker(
                            location=[rest_coords[0], rest_coords[1]],
                            popup=folium.Popup(popup_content, max_width=300),
                            icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
                        ).add_to(restaurant_cluster)
                
                restaurant_cluster.add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Save the map
            output_path = os.path.join(self.output_dir, filename)
            m.save(output_path)
            
            return output_path
        except Exception as e:
            print(f"Error visualizing competition: {str(e)}")
            return ""
    
    def visualize_catchment_area(self, catchment_analysis: Dict[str, Any],
                                filename: str = "catchment_area.html") -> str:
        """
        Create a map visualization for catchment area analysis.
        
        Args:
            catchment_analysis: Dictionary with catchment area analysis
            filename: Output HTML filename
            
        Returns:
            Path to the generated HTML file
        """
        try:
            # Get location coordinates
            if "coordinates" in catchment_analysis:
                center_lat = catchment_analysis["coordinates"]["lat"]
                center_lng = catchment_analysis["coordinates"]["lng"]
            else:
                location = catchment_analysis.get("location", "")
                map_service = MapServiceFactory.get_service()
                geocode_result = map_service.geocode(location)
                
                if "error" in geocode_result:
                    return ""
                
                center_lat = geocode_result["lat"]
                center_lng = geocode_result["lng"]
            
            # Create the map
            m = self.create_basic_map(center_lat, center_lng)
            
            # Add marker for main location
            folium.Marker(
                location=[center_lat, center_lng],
                popup=catchment_analysis.get("location", "Location"),
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)
            
            # Add circles for each catchment area
            catchment_areas = catchment_analysis.get("catchment_areas", [])
            colors = ["green", "blue", "purple"]  # Colors for different time ranges
            
            for i, area in enumerate(catchment_areas):
                minutes = area.get("travel_time_minutes", 0)
                radius = area.get("estimated_radius_meters", 0)
                population = area.get("estimated_population", 0)
                
                color = colors[i % len(colors)]
                
                folium.Circle(
                    location=[center_lat, center_lng],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_opacity=0.2,
                    popup=f"{minutes} min drive ({population:,} est. population)"
                ).add_to(m)
            
            # Save the map
            output_path = os.path.join(self.output_dir, filename)
            m.save(output_path)
            
            return output_path
        except Exception as e:
            print(f"Error visualizing catchment area: {str(e)}")
            return ""
    
    def open_in_browser(self, filepath: str) -> None:
        """Open the generated HTML file in a web browser."""
        if filepath and os.path.exists(filepath):
            webbrowser.open('file://' + os.path.realpath(filepath))
        else:
            print(f"Error: File does not exist - {filepath}")

# Example usage
if __name__ == "__main__":
    # This is a simple test
    from agents.location_agent import LocationIntelligenceAgent
    
    visualizer = LocationVisualizer()
    agent = LocationIntelligenceAgent()
    
    # Analyze a location
    location = "Bandra West, Mumbai, India"
    analysis = agent.analyze_location(location)
    
    # Visualize the analysis
    html_path = visualizer.visualize_location_analysis(analysis)
    visualizer.open_in_browser(html_path)
