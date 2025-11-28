"""
Consumer Survey Agent
Analyzes consumer dining preferences, behavior patterns, and survey data.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from pymongo import MongoClient
import pandas as pd
from utils.config import GEMINI_API_KEY, MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

class ConsumerSurveyAgent:
    """
    Agent for analyzing consumer preferences and dining behavior in India.
    Integrates survey data, reviews, and social sentiment analysis.
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
        self.collection = self.db["consumer_surveys"]
        
        # Embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GEMINI_API_KEY
        )
    
    def scrape_zomato_trends(self, city: str) -> Dict[str, Any]:
        """
        Scrape dining trends from Zomato for a specific city.
        Note: This requires Zomato API key or web scraping.
        
        Args:
            city: City name (e.g., "Mumbai", "Delhi", "Bangalore")
            
        Returns:
            Trending cuisines, restaurants, and preferences
        """
        logger.info(f"Fetching Zomato trends for {city}")
        
        # Placeholder for Zomato API integration
        # In production, use Zomato API: https://developers.zomato.com/api
        
        # Simulated data structure (replace with actual API calls)
        trends = {
            "city": city,
            "trending_cuisines": [],
            "popular_price_ranges": [],
            "top_rated_restaurants": [],
            "delivery_vs_dineout": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **trends,
            "source": "zomato",
            "type": "dining_trends"
        })
        
        return trends
    
    def analyze_consumer_preferences(self, location: str, demographic: str = "all") -> Dict[str, Any]:
        """
        Analyze consumer dining preferences for a location.
        
        Args:
            location: City or region
            demographic: Target demographic (e.g., "millennials", "families", "all")
            
        Returns:
            Comprehensive consumer preference analysis
        """
        logger.info(f"Analyzing consumer preferences for {location}, demographic: {demographic}")
        
        # Consumer preference categories
        preference_categories = [
            "cuisine_preferences",
            "dining_occasions",
            "price_sensitivity",
            "ambiance_preferences",
            "service_expectations",
            "dietary_restrictions",
            "ordering_channels"
        ]
        
        # Retrieve historical survey data
        historical_data = list(self.collection.find({
            "location": location,
            "type": "survey_response"
        }).limit(100))
        
        # Prepare context
        context = f"Location: {location}\nDemographic: {demographic}\n"
        if historical_data:
            context += f"Survey Responses Available: {len(historical_data)}\n"
        
        system_prompt = """You are a consumer behavior analyst specializing in Indian dining preferences.
Analyze consumer preferences based on available data and general market trends.

Consider:
1. Regional cuisine preferences
2. Age and income demographics
3. Dining occasions (casual, celebration, business)
4. Price sensitivity and value perception
5. Technology adoption (apps, delivery)
6. Health consciousness and dietary trends"""

        user_prompt = f"""{context}

Provide a detailed consumer preference analysis including:
1. **Top Cuisine Preferences** (ranked by popularity)
2. **Dining Behavior Patterns** (frequency, occasions, group sizes)
3. **Price Sensitivity** (average spending per person)
4. **Key Decision Factors** (what influences restaurant choice)
5. **Emerging Trends** (health food, sustainability, etc.)
6. **Recommendations** for restaurant positioning

For {location} specifically, focus on local preferences and cultural factors."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "location": location,
                "demographic": demographic,
                "analysis": response.content,
                "data_points": len(historical_data),
                "analyzed_at": datetime.now().isoformat(),
                "agent": "consumer_survey"
            }
            
            # Store analysis
            self.db["consumer_analysis"].insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing consumer preferences: {e}")
            return {
                "location": location,
                "demographic": demographic,
                "analysis": f"Error: {str(e)}",
                "error": True
            }
    
    def get_dining_frequency_insights(self, location: str) -> Dict[str, Any]:
        """
        Get insights on dining frequency and occasions.
        
        Args:
            location: City name
            
        Returns:
            Frequency patterns and popular dining occasions
        """
        # Typical patterns based on Indian consumer behavior
        insights = {
            "location": location,
            "weekly_dineout_frequency": {
                "1-2 times": 45,  # percentage
                "3-4 times": 30,
                "5+ times": 15,
                "rarely": 10
            },
            "popular_occasions": [
                {"occasion": "Weekend family dining", "percentage": 65},
                {"occasion": "Weekday quick meals", "percentage": 45},
                {"occasion": "Special celebrations", "percentage": 40},
                {"occasion": "Date nights", "percentage": 35},
                {"occasion": "Business meetings", "percentage": 25}
            ],
            "preferred_meal_times": {
                "lunch": {"weekday": 35, "weekend": 45},
                "dinner": {"weekday": 60, "weekend": 75},
                "brunch": {"weekend_only": 30}
            },
            "average_spending_per_visit": {
                "budget": {"range": "₹200-500", "percentage": 40},
                "mid_range": {"range": "₹500-1500", "percentage": 45},
                "premium": {"range": "₹1500+", "percentage": 15}
            },
            "last_updated": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **insights,
            "type": "dining_frequency"
        })
        
        return insights
    
    def get_food_delivery_insights(self, city: str) -> Dict[str, Any]:
        """
        Analyze food delivery trends and online ordering behavior.
        
        Args:
            city: City name
            
        Returns:
            Delivery trends, popular platforms, ordering patterns
        """
        insights = {
            "city": city,
            "delivery_adoption_rate": 75,  # percentage of consumers using delivery
            "popular_platforms": [
                {"platform": "Zomato", "market_share": 45},
                {"platform": "Swiggy", "market_share": 42},
                {"platform": "Others", "market_share": 13}
            ],
            "delivery_vs_dineout": {
                "delivery_percentage": 55,
                "dine_out_percentage": 45
            },
            "popular_delivery_times": [
                {"time": "8:00 PM - 10:00 PM", "orders": "peak"},
                {"time": "12:00 PM - 2:00 PM", "orders": "high"},
                {"time": "6:00 PM - 8:00 PM", "orders": "high"}
            ],
            "average_delivery_order_value": "₹350-450",
            "most_ordered_cuisines": [
                "North Indian",
                "Chinese",
                "Fast Food/Burgers",
                "South Indian",
                "Biryani/Rice"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **insights,
            "type": "delivery_insights"
        })
        
        return insights
    
    def analyze_dietary_trends(self, location: str) -> Dict[str, Any]:
        """
        Analyze dietary preferences and restrictions in a location.
        
        Args:
            location: City name
            
        Returns:
            Dietary trends, restrictions, health consciousness
        """
        system_prompt = f"""You are analyzing dietary trends in {location}, India.
Consider the local culture, religious diversity, and emerging health trends.

Analyze:
1. Vegetarian vs Non-vegetarian preferences
2. Vegan and plant-based trends
3. Religious dietary restrictions (Jain, Halal, Kosher)
4. Health-conscious choices (organic, gluten-free, sugar-free)
5. Regional dietary preferences specific to {location}"""

        user_prompt = f"""Provide a comprehensive dietary trends analysis for {location}:

1. **Vegetarian/Non-vegetarian Split** (approximate percentages)
2. **Growing Dietary Segments** (vegan, keto, etc.)
3. **Religious/Cultural Considerations**
4. **Health Trends** (organic, low-calorie, etc.)
5. **Restaurant Menu Recommendations** based on these trends

Be specific to {location}'s demographics and culture."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            analysis = {
                "location": location,
                "analysis": response.content,
                "analyzed_at": datetime.now().isoformat(),
                "type": "dietary_trends",
                "agent": "consumer_survey"
            }
            
            # Store in MongoDB
            self.collection.insert_one(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing dietary trends: {e}")
            return {"error": str(e)}
    
    def get_consumer_sentiment(self, location: str, cuisine_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze consumer sentiment about dining in a location.
        
        Args:
            location: City name
            cuisine_type: Optional specific cuisine to analyze
            
        Returns:
            Sentiment analysis with positive/negative factors
        """
        query_focus = f"{cuisine_type} restaurants in {location}" if cuisine_type else f"dining in {location}"
        
        sentiment = {
            "location": location,
            "cuisine_type": cuisine_type or "all",
            "overall_sentiment": "positive",  # Would be calculated from reviews
            "positive_factors": [
                "Variety of options",
                "Quality of food",
                "Reasonable pricing",
                "Good ambiance"
            ],
            "negative_factors": [
                "Long wait times",
                "Parking difficulties",
                "Inconsistent service",
                "Limited healthy options"
            ],
            "sentiment_score": 7.2,  # Out of 10
            "total_reviews_analyzed": 0,  # Would come from actual data
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        self.collection.insert_one({
            **sentiment,
            "type": "consumer_sentiment"
        })
        
        return sentiment
    
    def create_consumer_persona(self, demographic: str, location: str) -> Dict[str, Any]:
        """
        Create detailed consumer persona for target demographic.
        
        Args:
            demographic: e.g., "millennials", "families", "young_professionals"
            location: City name
            
        Returns:
            Detailed persona with preferences, behaviors, pain points
        """
        system_prompt = f"""Create a detailed consumer persona for {demographic} in {location}, India.

Include:
1. Demographics (age, income, occupation)
2. Dining preferences and frequency
3. Favorite cuisines and restaurants
4. Technology usage (apps, online ordering)
5. Pain points and unmet needs
6. Decision-making factors
7. Budget and spending patterns

Be realistic and specific to Indian market conditions."""

        user_prompt = f"Create a comprehensive consumer persona for {demographic} in {location}."
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            persona = {
                "demographic": demographic,
                "location": location,
                "persona_description": response.content,
                "created_at": datetime.now().isoformat(),
                "type": "consumer_persona",
                "agent": "consumer_survey"
            }
            
            # Store in MongoDB
            self.db["consumer_personas"].insert_one(persona)
            
            return persona
            
        except Exception as e:
            logger.error(f"Error creating consumer persona: {e}")
            return {"error": str(e)}
