#!/bin/bash
# Script to install required packages for location intelligence module

echo "Installing location intelligence module requirements..."

# Core dependencies
pip install requests python-dotenv

# Geospatial and mapping
pip install folium geopy

# Visualization
pip install matplotlib seaborn

echo "Setting up environment variables..."

# Check if .env file exists, if not create one
if [ ! -f .env ]; then
  echo "Creating .env file..."
  cat > .env << EOF
# Location API Keys
GOOGLE_MAPS_API_KEY=
HERE_MAPS_API_KEY=
TOMTOM_API_KEY=
GEOAPIFY_API_KEY=

# Default map service to use
DEFAULT_MAP_SERVICE=geoapify

# Application settings
DEBUG=True
LOG_LEVEL=INFO
APP_PORT=5000
EOF
  
  echo "Created .env file. Please add your API keys."
else
  echo ".env file already exists. Please ensure you have the required API keys."
fi

echo "Setup complete for location intelligence module!"
echo "To use Google Maps, HERE Maps or other premium services, add your API keys to the .env file."
echo "For testing purposes, you can use Geoapify which offers a free tier."
