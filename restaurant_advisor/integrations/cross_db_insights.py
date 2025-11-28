"""
Integration module that combines data from MongoDB knowledge base and Neo4j knowledge graph
to provide comprehensive restaurant location insights.
"""

from typing import Dict, List, Optional, Any, Tuple
import os
import sys

# Add the parent directory to the path so we can import modules correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from langchain_core.documents import Document

class CrossDBInsights:
    """Class that integrates MongoDB knowledge base and Neo4j knowledge graph for comprehensive insights."""
    
    def __init__(self, kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
        """Initialize the cross-database integration with MongoDB KB and Neo4j KG instances."""
        self.kb = kb
        self.kg = kg
    
    def get_comprehensive_city_insights(self, city: str, cuisine_type: Optional[str] = None) -> Dict:
        """
        Get comprehensive insights about a city by combining structured data from Neo4j
        and unstructured data from MongoDB.
        
        Args:
            city: The city name to analyze
            cuisine_type: Optional cuisine type to focus on
            
        Returns:
            Dict with combined structured and unstructured insights
        """
        # Get structured data from Neo4j
        locations = self.kg.recommend_locations(city, cuisine_type)
        regulations = self.kg.get_regulatory_info(city)
        cuisine_preferences = self.kg.get_cuisine_preferences(city)
        
        # Get unstructured data from MongoDB
        city_insights = self.kb.get_city_specific_insights(city, k=5)
        market_trends = self.kb.get_recent_market_trends()
        
        # If cuisine type is provided, get specific insights
        cuisine_insights = []
        if cuisine_type:
            cuisine_query = f"{cuisine_type} cuisine in {city}"
            cuisine_insights = self.kb.hybrid_search(cuisine_query, k=3)
        
        # Combine the insights
        return {
            "city": city,
            "structured_data": {
                "recommended_locations": locations[:3],
                "regulations": regulations[:5],
                "cuisine_preferences": cuisine_preferences[:5]
            },
            "unstructured_data": {
                "city_insights": [doc.page_content for doc in city_insights],
                "market_trends": [doc.page_content for doc in market_trends[:3]],
                "cuisine_insights": [doc.page_content for doc in cuisine_insights]
            }
        }
    
    def get_restaurant_opportunity_score(self, city: str, area: str, cuisine_type: str) -> Dict:
        """
        Calculate an opportunity score for opening a restaurant of a specific cuisine type
        in a given city and area, based on combined data from both sources.
        
        Args:
            city: The target city
            area: The specific area/neighborhood in the city
            cuisine_type: The type of cuisine for the restaurant
            
        Returns:
            Dict with opportunity score and contributing factors
        """
        score_components = {}
        
        # Check location data from Neo4j
        locations = self.kg.recommend_locations(city, cuisine_type)
        target_location = None
        for loc in locations:
            if loc.get("area", "").lower() == area.lower():
                target_location = loc
                break
        
        if target_location:
            # Location found, extract factors
            foot_traffic = target_location.get("foot_traffic", 0)
            score_components["location_score"] = min(foot_traffic / 1000, 10) # Scale to 0-10
            
            # Check if this cuisine is already popular in the area
            existing_cuisines = target_location.get("popular_cuisines", [])
            cuisine_saturation = 1.0
            if cuisine_type.lower() in [c.lower() for c in existing_cuisines]:
                # This cuisine already exists here, might be saturated
                cuisine_saturation = 0.5
            score_components["uniqueness_score"] = cuisine_saturation * 10
        else:
            # Location not found in structured data
            score_components["location_score"] = 5.0  # Neutral score
            score_components["uniqueness_score"] = 7.0  # Assume moderate uniqueness
        
        # Get market insights from MongoDB
        market_query = f"{cuisine_type} restaurant demand {city} {area}"
        market_insights = self.kb.semantic_search(market_query, k=3)
        
        # Analyze the sentiment in the market insights
        sentiment_score = 7.0  # Default slightly positive
        if market_insights:
            # Count positive and negative keywords
            positive_keywords = ["growing", "increasing", "popular", "demand", "opportunity", "trend"]
            negative_keywords = ["declining", "saturated", "competitive", "struggling", "oversupplied"]
            
            positive_count = 0
            negative_count = 0
            
            for insight in market_insights:
                content = insight.page_content.lower()
                positive_count += sum(1 for word in positive_keywords if word in content)
                negative_count += sum(1 for word in negative_keywords if word in content)
            
            if positive_count + negative_count > 0:
                # Calculate sentiment ratio and scale to 0-10
                sentiment_score = 10 * (positive_count / (positive_count + negative_count))
        
        score_components["market_sentiment"] = sentiment_score
        
        # Get regulatory complexity from Neo4j
        regulations = self.kg.get_regulatory_info(city)
        regulatory_complexity = len(regulations) / 2  # Scale based on number of regulations
        score_components["regulatory_ease"] = max(10 - regulatory_complexity, 1)  # Inverse scale, more regs = lower score
        
        # Calculate overall opportunity score (weighted average)
        weights = {
            "location_score": 0.35,
            "uniqueness_score": 0.25,
            "market_sentiment": 0.25,
            "regulatory_ease": 0.15
        }
        
        overall_score = sum(score * weights[component] for component, score in score_components.items())
        
        return {
            "opportunity_score": round(overall_score, 1),
            "components": score_components,
            "interpretation": self._interpret_opportunity_score(overall_score),
            "supporting_insights": [doc.page_content for doc in market_insights]
        }
    
    def _interpret_opportunity_score(self, score: float) -> str:
        """Interpret the opportunity score with a textual description."""
        if score >= 8.5:
            return "Excellent opportunity with very favorable conditions"
        elif score >= 7.0:
            return "Good opportunity with favorable conditions"
        elif score >= 5.5:
            return "Moderate opportunity with some challenges"
        elif score >= 4.0:
            return "Challenging opportunity with significant barriers"
        else:
            return "Difficult opportunity with unfavorable conditions"
            
    def find_market_gaps(self, city: str) -> Dict:
        """
        Identify potential market gaps by comparing popular cuisines across India
        with what's already established in this city.
        
        Args:
            city: The target city
            
        Returns:
            Dict with identified market gaps and supporting data
        """
        # Get cuisine preferences in the target city
        city_cuisines = self.kg.get_cuisine_preferences(city)
        city_cuisine_types = [c["cuisine_type"].lower() for c in city_cuisines]
        
        # Get popular cuisines from unstructured data
        cuisine_insights = self.kb.hybrid_search("popular cuisines food trends India", k=5)
        
        # Extract cuisine mentions from unstructured data
        all_cuisine_mentions = {}
        for doc in cuisine_insights:
            content = doc.page_content.lower()
            # Check for common cuisine types
            for cuisine in ["north indian", "south indian", "chinese", "italian", "mexican", 
                           "thai", "japanese", "korean", "mediterranean", "lebanese", 
                           "continental", "fusion", "bengali", "gujarati", "punjabi", 
                           "seafood", "vegan", "vegetarian", "street food"]:
                if cuisine in content and cuisine not in city_cuisine_types:
                    if cuisine in all_cuisine_mentions:
                        all_cuisine_mentions[cuisine] += 1
                    else:
                        all_cuisine_mentions[cuisine] = 1
        
        # Rank the potential gaps
        potential_gaps = sorted(
            [{"cuisine": cuisine, "mentions": count} for cuisine, count in all_cuisine_mentions.items()],
            key=lambda x: x["mentions"],
            reverse=True
        )
        
        # Get supporting insights for the top gaps
        supporting_insights = {}
        for gap in potential_gaps[:3]:
            cuisine = gap["cuisine"]
            query = f"{cuisine} cuisine market opportunity in {city}"
            insights = self.kb.hybrid_search(query, k=2)
            supporting_insights[cuisine] = [doc.page_content for doc in insights]
        
        return {
            "identified_gaps": potential_gaps[:5],
            "supporting_insights": supporting_insights
        }
