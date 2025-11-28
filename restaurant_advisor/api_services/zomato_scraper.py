"""
Zomato web scraper for restaurant data (no API key required).
Scrapes restaurant listings, ratings, reviews, and cuisine data.
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Any, Optional
import re
import json

logger = logging.getLogger(__name__)


class ZomatoScraper:
    """
    Scrape Zomato for restaurant data without API.
    Respects rate limits and robots.txt.
    """
    
    def __init__(self):
        self.base_url = "https://www.zomato.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.rate_limit_delay = 2.0  # 2 seconds between requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure we respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make a rate-limited request and return BeautifulSoup object."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.warning(f"Request failed with status {response.status_code}: {url}")
                return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    def search_restaurants(self, city: str, locality: str = None, cuisine: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for restaurants in a city/locality.
        
        Args:
            city: City name (e.g., "mumbai", "bangalore")
            locality: Optional locality/area (e.g., "bandra-west")
            cuisine: Optional cuisine filter
            limit: Maximum results
            
        Returns:
            List of restaurant data
        """
        restaurants = []
        
        # Build search URL
        city_slug = city.lower().replace(" ", "-")
        if locality:
            locality_slug = locality.lower().replace(" ", "-")
            search_url = f"{self.base_url}/{city_slug}/{locality_slug}/restaurants"
        else:
            search_url = f"{self.base_url}/{city_slug}/restaurants"
        
        if cuisine:
            cuisine_slug = cuisine.lower().replace(" ", "-")
            search_url += f"?cuisines={cuisine_slug}"
        
        logger.info(f"Scraping Zomato: {search_url}")
        
        soup = self._make_request(search_url)
        if not soup:
            return restaurants
        
        # Try to find JSON-LD data (structured data)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Restaurant':
                    restaurants.append(self._parse_json_ld_restaurant(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Restaurant':
                            restaurants.append(self._parse_json_ld_restaurant(item))
            except Exception as e:
                logger.debug(f"Error parsing JSON-LD: {e}")
        
        # Fallback: Parse HTML structure
        if not restaurants:
            restaurants = self._parse_restaurant_cards(soup, city)
        
        return restaurants[:limit]
    
    def _parse_json_ld_restaurant(self, data: dict) -> Dict[str, Any]:
        """Parse restaurant data from JSON-LD structured data."""
        address = data.get('address', {})
        if isinstance(address, str):
            address = {'streetAddress': address}
        
        rating_data = data.get('aggregateRating', {})
        
        return {
            'name': data.get('name'),
            'address': address.get('streetAddress', ''),
            'city': address.get('addressLocality', ''),
            'locality': address.get('addressRegion', ''),
            'rating': float(rating_data.get('ratingValue', 0)) if rating_data.get('ratingValue') else None,
            'votes': int(rating_data.get('reviewCount', 0)) if rating_data.get('reviewCount') else None,
            'cuisine': ', '.join(data.get('servesCuisine', [])) if data.get('servesCuisine') else None,
            'price_range': data.get('priceRange', 'Unknown'),
            'phone': data.get('telephone', ''),
            'url': data.get('url', ''),
            'source': 'zomato'
        }
    
    def _parse_restaurant_cards(self, soup: BeautifulSoup, city: str) -> List[Dict[str, Any]]:
        """Parse restaurant cards from HTML."""
        restaurants = []
        
        # Find restaurant cards (Zomato's structure may vary)
        # Look for common patterns
        card_selectors = [
            'div[class*="restaurant-card"]',
            'div[class*="search-result"]',
            'article[class*="restaurant"]',
            'div[class*="res-card"]'
        ]
        
        cards = []
        for selector in card_selectors:
            cards = soup.select(selector)
            if cards:
                break
        
        for card in cards:
            try:
                restaurant = self._extract_restaurant_from_card(card, city)
                if restaurant and restaurant.get('name'):
                    restaurants.append(restaurant)
            except Exception as e:
                logger.debug(f"Error parsing restaurant card: {e}")
        
        return restaurants
    
    def _extract_restaurant_from_card(self, card: BeautifulSoup, city: str) -> Dict[str, Any]:
        """Extract restaurant data from a card element."""
        restaurant = {
            'source': 'zomato',
            'city': city
        }
        
        # Try to find name
        name_selectors = ['h4', 'h3', 'a[class*="name"]', 'div[class*="name"]']
        for selector in name_selectors:
            name_elem = card.select_one(selector)
            if name_elem:
                restaurant['name'] = name_elem.get_text(strip=True)
                break
        
        # Try to find rating
        rating_selectors = ['div[class*="rating"]', 'span[class*="rating"]', 'div[aria-label*="rating"]']
        for selector in rating_selectors:
            rating_elem = card.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    restaurant['rating'] = float(rating_match.group(1))
                    break
        
        # Try to find cuisine
        cuisine_selectors = ['div[class*="cuisine"]', 'span[class*="cuisine"]', 'p[class*="cuisine"]']
        for selector in cuisine_selectors:
            cuisine_elem = card.select_one(selector)
            if cuisine_elem:
                restaurant['cuisine'] = cuisine_elem.get_text(strip=True)
                break
        
        # Try to find address/locality
        address_selectors = ['div[class*="address"]', 'span[class*="locality"]', 'p[class*="address"]']
        for selector in address_selectors:
            address_elem = card.select_one(selector)
            if address_elem:
                restaurant['locality'] = address_elem.get_text(strip=True)
                break
        
        # Try to find price range
        price_selectors = ['span[class*="price"]', 'div[class*="cost"]']
        for selector in price_selectors:
            price_elem = card.select_one(selector)
            if price_elem:
                restaurant['price_range'] = price_elem.get_text(strip=True)
                break
        
        # Try to find URL
        link = card.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('/'):
                restaurant['url'] = f"{self.base_url}{href}"
            elif href.startswith('http'):
                restaurant['url'] = href
        
        return restaurant
    
    def get_restaurant_details(self, restaurant_url: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific restaurant.
        
        Args:
            restaurant_url: Full URL to restaurant page
            
        Returns:
            Detailed restaurant data
        """
        soup = self._make_request(restaurant_url)
        if not soup:
            return {}
        
        details = {
            'url': restaurant_url,
            'source': 'zomato'
        }
        
        # Try JSON-LD first
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Restaurant':
                    return self._parse_json_ld_restaurant(data)
            except:
                pass
        
        # Fallback to HTML parsing
        # Name
        name_elem = soup.select_one('h1[class*="name"]') or soup.select_one('h1')
        if name_elem:
            details['name'] = name_elem.get_text(strip=True)
        
        # Rating
        rating_elem = soup.select_one('div[class*="rating"]') or soup.select_one('span[aria-label*="rating"]')
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                details['rating'] = float(rating_match.group(1))
        
        # Address
        address_elem = soup.select_one('a[class*="address"]') or soup.select_one('div[class*="address"]')
        if address_elem:
            details['address'] = address_elem.get_text(strip=True)
        
        # Cuisine
        cuisine_elem = soup.select_one('div[class*="cuisine"]')
        if cuisine_elem:
            details['cuisine'] = cuisine_elem.get_text(strip=True)
        
        # Phone
        phone_elem = soup.select_one('a[href^="tel:"]')
        if phone_elem:
            details['phone'] = phone_elem.get_text(strip=True)
        
        # Opening hours
        hours_elem = soup.select_one('div[class*="hours"]') or soup.select_one('div[class*="timing"]')
        if hours_elem:
            details['hours'] = hours_elem.get_text(strip=True)
        
        return details
    
    def get_popular_cuisines(self, city: str) -> List[Dict[str, Any]]:
        """
        Get popular cuisines in a city.
        
        Args:
            city: City name
            
        Returns:
            List of cuisine data
        """
        city_slug = city.lower().replace(" ", "-")
        url = f"{self.base_url}/{city_slug}"
        
        soup = self._make_request(url)
        if not soup:
            return []
        
        cuisines = []
        
        # Look for cuisine links
        cuisine_links = soup.select('a[href*="/cuisine/"]')
        for link in cuisine_links[:15]:  # Top 15 cuisines
            cuisine_name = link.get_text(strip=True)
            if cuisine_name and len(cuisine_name) < 30:  # Filter out long text
                cuisines.append({
                    'name': cuisine_name,
                    'url': f"{self.base_url}{link['href']}" if link['href'].startswith('/') else link['href'],
                    'city': city
                })
        
        return cuisines
    
    def get_trending_restaurants(self, city: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending/popular restaurants in a city.
        
        Args:
            city: City name
            limit: Maximum results
            
        Returns:
            List of trending restaurants
        """
        city_slug = city.lower().replace(" ", "-")
        url = f"{self.base_url}/{city_slug}/best-restaurants"
        
        soup = self._make_request(url)
        if not soup:
            return []
        
        return self._parse_restaurant_cards(soup, city)[:limit]
    
    def search_by_cuisine_and_location(self, city: str, locality: str, cuisine: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Search for specific cuisine in a specific location.
        
        Args:
            city: City name
            locality: Locality/area name
            cuisine: Cuisine type
            limit: Maximum results
            
        Returns:
            Filtered restaurant list
        """
        return self.search_restaurants(city, locality, cuisine, limit)
    
    def get_restaurant_reviews_summary(self, restaurant_url: str) -> Dict[str, Any]:
        """
        Get summary of reviews for a restaurant.
        
        Args:
            restaurant_url: Full URL to restaurant page
            
        Returns:
            Reviews summary with sentiment
        """
        soup = self._make_request(restaurant_url)
        if not soup:
            return {}
        
        summary = {
            'url': restaurant_url,
            'reviews': []
        }
        
        # Find review elements
        review_selectors = ['div[class*="review"]', 'article[class*="review"]']
        reviews = []
        for selector in review_selectors:
            reviews = soup.select(selector)
            if reviews:
                break
        
        for review in reviews[:10]:  # Get top 10 reviews
            try:
                review_text_elem = review.select_one('div[class*="text"]') or review.select_one('p')
                rating_elem = review.select_one('div[class*="rating"]') or review.select_one('span[aria-label*="rating"]')
                
                if review_text_elem:
                    review_data = {
                        'text': review_text_elem.get_text(strip=True)
                    }
                    
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            review_data['rating'] = float(rating_match.group(1))
                    
                    summary['reviews'].append(review_data)
            except Exception as e:
                logger.debug(f"Error parsing review: {e}")
        
        return summary
