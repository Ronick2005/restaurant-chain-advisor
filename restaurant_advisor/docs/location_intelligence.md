# Location Intelligence Module for Restaurant Chain Advisor

## Overview

The Location Intelligence Module provides powerful geospatial analysis capabilities for the Restaurant Chain Advisor system. It enables data-driven decision-making for restaurant location selection by analyzing factors such as:

- Competition density and distribution
- Catchment area analysis
- Accessibility from population centers
- Optimal location recommendations
- Detailed competition analysis

## Features

- **Multiple Map Service Providers**: Support for Google Maps, HERE Maps, and Geoapify
- **Location Analysis**: Detailed analysis of potential restaurant locations
- **Competition Mapping**: Identify and analyze nearby competitors
- **Comparative Analysis**: Compare multiple locations based on various factors
- **Catchment Area Analysis**: Estimate population reach based on travel time
- **Accessibility Analysis**: Calculate travel times from population centers
- **Optimal Location Finder**: Identify the best locations within a search area
- **Visualization Tools**: Generate interactive maps for all analyses

## Getting Started

### Prerequisites

- Python 3.8 or higher
- API keys for map services (at least one of: Google Maps, HERE Maps, Geoapify)
- The following Python packages:
  - requests
  - python-dotenv
  - folium
  - geopy

### Installation

1. Set up your environment variables:

```bash
cp .env.example .env
```

2. Edit the `.env` file and add your API keys:

```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
HERE_MAPS_API_KEY=your_here_maps_api_key
GEOAPIFY_API_KEY=your_geoapify_api_key
```

3. Install required packages:

```bash
./setup_location_module.sh
```

## Usage

### Basic Location Analysis

```python
from agents.location_agent import LocationIntelligenceAgent

# Initialize the agent
agent = LocationIntelligenceAgent()

# Analyze a location
location = "Bandra West, Mumbai, India"
analysis = agent.analyze_location(location)
print(analysis)
```

### Comparing Multiple Locations

```python
# Compare multiple locations
locations = [
    "Bandra West, Mumbai, India",
    "Powai, Mumbai, India",
    "Andheri East, Mumbai, India"
]
comparison = agent.compare_locations(locations)
print(comparison)
```

### Finding Optimal Locations

```python
# Find optimal locations within an area
center = "Mumbai, India"
optimal = agent.find_optimal_location(center, radius=10000)
print(optimal)
```

### Visualizing Results

```python
from visualization.location_maps import LocationVisualizer

# Initialize visualizer
visualizer = LocationVisualizer()

# Visualize a location analysis
html_path = visualizer.visualize_location_analysis(analysis)
visualizer.open_in_browser(html_path)

# Visualize a location comparison
html_path = visualizer.visualize_location_comparison(comparison)
visualizer.open_in_browser(html_path)

# Visualize optimal locations
html_path = visualizer.visualize_optimal_locations(optimal)
visualizer.open_in_browser(html_path)
```

## API Reference

### LocationIntelligenceAgent

- `analyze_location(address, radius=1000)`: Analyze a specific location
- `compare_locations(locations, radius=1000)`: Compare multiple locations
- `find_optimal_location(center_point, radius=5000)`: Find optimal locations within an area
- `calculate_accessibility(location, population_centers, mode="driving")`: Calculate accessibility metrics
- `analyze_catchment_area(location, travel_times=[5, 10, 15])`: Analyze catchment area by travel time
- `analyze_competition(location, radius=1000)`: Detailed competition analysis

### LocationVisualizer

- `visualize_location_analysis(analysis)`: Create a map for location analysis
- `visualize_location_comparison(comparison_results)`: Create a map comparing locations
- `visualize_optimal_locations(optimal_results)`: Create a map showing optimal locations
- `visualize_competition(competition_analysis)`: Create a map showing competition analysis
- `visualize_catchment_area(catchment_analysis)`: Create a map showing catchment areas
- `open_in_browser(filepath)`: Open a generated map in the browser

## Demo

Run the provided demonstration script to see all features in action:

```bash
python examples/location_intelligence_demo.py
```

## Integration with Agent System

The Location Intelligence Agent is designed to work with the multi-agent restaurant advisor system. It can be used by other agents to gather location-based insights for restaurant chain planning and expansion strategy.

## Notes

- For testing purposes, Geoapify offers a free tier that can be used without a credit card
- Google Maps provides the most comprehensive data but requires billing information
- Folium maps are generated as HTML files and can be viewed in any browser
