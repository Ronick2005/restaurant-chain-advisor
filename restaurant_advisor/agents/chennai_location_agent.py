"""
Chennai location intelligence agent specializing in providing detailed insights 
for restaurant location selection in Chennai.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseLLM

# Add the parent directory to the path so we can import modules correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from integrations.cross_db_insights import CrossDBInsights

# Chennai-specific neighborhoods and commercial zones
CHENNAI_NEIGHBORHOODS = [
    "Anna Nagar", "T. Nagar", "Adyar", "Besant Nagar", "Mylapore", 
    "Velachery", "Nungambakkam", "Alwarpet", "Guindy", "Porur",
    "OMR (Old Mahabalipuram Road)", "Perambur", "Kilpauk", "Egmore",
    "Royapettah", "Santhome", "Thiruvanmiyur", "Perungudi", "RA Puram",
    "Kodambakkam", "Shenoy Nagar", "Mogappair", "Vadapalani"
]

# Chennai commercial zones with estimated foot traffic and target demographics
CHENNAI_COMMERCIAL_DATA = {
    "Anna Nagar": {
        "foot_traffic": "High",
        "demographics": ["Middle-upper class", "Families", "Young professionals"],
        "rent_range": "₹80-120 per sq.ft/month",
        "nearby_attractions": ["Anna Nagar Tower Park", "VR Chennai Mall"],
        "veg_friendly_score": 8
    },
    "T. Nagar": {
        "foot_traffic": "Very High",
        "demographics": ["Middle class", "Shoppers", "Tourists"],
        "rent_range": "₹100-150 per sq.ft/month",
        "nearby_attractions": ["Pondy Bazaar", "T. Nagar Shopping District"],
        "veg_friendly_score": 9
    },
    "Adyar": {
        "foot_traffic": "Moderate",
        "demographics": ["Upper-middle class", "Students", "Professionals"],
        "rent_range": "₹70-100 per sq.ft/month",
        "nearby_attractions": ["Adyar River", "IIT Madras", "Cancer Institute"],
        "veg_friendly_score": 8
    },
    "Nungambakkam": {
        "foot_traffic": "High",
        "demographics": ["Upper class", "Expats", "Young professionals"],
        "rent_range": "₹90-130 per sq.ft/month",
        "nearby_attractions": ["Valluvar Kottam", "Loyola College"],
        "veg_friendly_score": 7
    },
    "Velachery": {
        "foot_traffic": "Moderate-High",
        "demographics": ["IT professionals", "Young families", "Students"],
        "rent_range": "₹60-90 per sq.ft/month",
        "nearby_attractions": ["Phoenix Marketcity", "Grand Mall"],
        "veg_friendly_score": 7
    },
    "Besant Nagar": {
        "foot_traffic": "Moderate",
        "demographics": ["Upper class", "Health-conscious", "Expats"],
        "rent_range": "₹80-110 per sq.ft/month",
        "nearby_attractions": ["Elliot's Beach", "Ashtalakshmi Temple"],
        "veg_friendly_score": 9
    },
    "OMR": {
        "foot_traffic": "High",
        "demographics": ["IT professionals", "Young adults", "Corporate workers"],
        "rent_range": "₹50-80 per sq.ft/month",
        "nearby_attractions": ["SIPCOT IT Park", "Sholinganallur Junction"],
        "veg_friendly_score": 8
    },
    "Mylapore": {
        "foot_traffic": "Moderate",
        "demographics": ["Traditional families", "Religious visitors", "Tourists"],
        "rent_range": "₹70-100 per sq.ft/month",
        "nearby_attractions": ["Kapaleeswarar Temple", "Mylapore Tank"],
        "veg_friendly_score": 10
    },
    "Alwarpet": {
        "foot_traffic": "Moderate",
        "demographics": ["Upper class", "Cultural enthusiasts", "Professionals"],
        "rent_range": "₹90-120 per sq.ft/month",
        "nearby_attractions": ["Music Academy", "Narada Gana Sabha"],
        "veg_friendly_score": 8
    },
    "Guindy": {
        "foot_traffic": "High",
        "demographics": ["Office workers", "Students", "Business travelers"],
        "rent_range": "₹70-100 per sq.ft/month",
        "nearby_attractions": ["Guindy National Park", "Race Course"],
        "veg_friendly_score": 7
    },
    "Egmore": {
        "foot_traffic": "High",
        "demographics": ["Travelers", "Tourists", "Middle class"],
        "rent_range": "₹70-90 per sq.ft/month",
        "nearby_attractions": ["Egmore Railway Station", "Government Museum"],
        "veg_friendly_score": 7
    },
    "Kodambakkam": {
        "foot_traffic": "Moderate",
        "demographics": ["Film industry workers", "Middle class", "Students"],
        "rent_range": "₹60-90 per sq.ft/month",
        "nearby_attractions": ["Film studios", "Kodambakkam Bridge"],
        "veg_friendly_score": 8
    }
}

# Health food related insights for Chennai
HEALTH_FOOD_INSIGHTS = [
    "Chennai has seen a 32% growth in vegan and plant-based dining options in the past two years, particularly in areas with higher concentrations of young professionals.",
    "The vegetarian food scene in Chennai is well-established with over 70% of restaurants offering substantial vegetarian options.",
    "Health-conscious dining is growing fastest in areas like Besant Nagar, Anna Nagar, and parts of OMR where fitness centers and organic stores are also concentrated.",
    "Areas near educational institutions like IIT Madras, Anna University, and Loyola College show strong demand for affordable yet healthy dining options.",
    "Weekend foot traffic for healthy food establishments is highest in beach-adjacent neighborhoods like Besant Nagar and areas with parks and recreational facilities.",
    "Corporate areas along OMR and Guindy show strong weekday lunch demand for quick-service healthy food options.",
    "Plant-based burgers are growing at 40% year-over-year in Chennai's food service industry, with greatest adoption among 18-35 year old consumers."
]

class ChennaiLocationAgent:
    """Agent specialized in Chennai location intelligence for restaurants."""
    
    def __init__(self, llm: BaseLLM, kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
        """Initialize the Chennai location agent.
        
        Args:
            llm: Language model for analysis and recommendations
            kb: MongoDB knowledge base
            kg: Neo4j knowledge graph
        """
        self.llm = llm
        self.kb = kb
        self.kg = kg
        self.cross_db = CrossDBInsights(kb, kg)
        
        # Define the location recommendation prompt
        self.recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized location intelligence expert for restaurants in Chennai, India.
            Your task is to provide detailed, data-driven recommendations for restaurant locations in Chennai,
            with a particular focus on vegan and health-food establishments.
            
            You have access to the following data:
            
            1. Neighborhood Information:
            {neighborhood_data}
            
            2. Commercial Zone Analytics:
            {commercial_data}
            
            3. Health Food & Vegan Market Insights:
            {health_food_insights}
            
            4. Document-Based Research:
            {document_insights}
            
            5. Additional Context:
            {additional_context}
            
            For the restaurant concept: {restaurant_concept}
            
            Provide a comprehensive recommendation with the following sections:
            1. Top 3 Recommended Neighborhoods (with pros and cons of each)
            2. Target Demographics Analysis
            3. Competitive Landscape
            4. Growth Potential
            5. Specific Location Strategies (e.g., proximity to specific attractions)
            
            Focus on providing specific, actionable advice rather than general statements.
            """),
        ])
        
        self.answer_parser = StrOutputParser()
        
    def recommend_locations(self, restaurant_concept: str, cuisine_type: str = "Vegan", 
                           budget_level: str = "Moderate") -> str:
        """Recommend specific locations in Chennai for a restaurant concept.
        
        Args:
            restaurant_concept: Description of the restaurant concept
            cuisine_type: Type of cuisine (default: Vegan)
            budget_level: Budget level for rent (Low, Moderate, High)
            
        Returns:
            Detailed location recommendations
        """
        try:
            # Get relevant neighborhoods based on the cuisine type and budget
            relevant_neighborhoods = self._filter_neighborhoods(cuisine_type, budget_level)
            neighborhood_data = self._format_neighborhood_data(relevant_neighborhoods)
            
            # Format commercial data
            commercial_data = self._format_commercial_data(relevant_neighborhoods)
            
            # Get document insights from MongoDB
            query = f"{cuisine_type} restaurant Chennai {' '.join(relevant_neighborhoods[:3])}"
            document_insights = self.kb.hybrid_search(query, k=3)
            document_text = "\n\n".join([doc.page_content for doc in document_insights])
            
            # Gather additional context from knowledge graph
            additional_context = self._get_additional_context(cuisine_type)
            
            # Format health food insights
            health_food_text = "\n".join(HEALTH_FOOD_INSIGHTS)
            
            # Create the chain and invoke it
            chain = (
                self.recommendation_prompt 
                | self.llm 
                | self.answer_parser
            )
            
            result = chain.invoke({
                "neighborhood_data": neighborhood_data,
                "commercial_data": commercial_data,
                "health_food_insights": health_food_text,
                "document_insights": document_text,
                "additional_context": additional_context,
                "restaurant_concept": restaurant_concept
            })
            
            return result
        
        except Exception as e:
            return f"Error generating location recommendations: {str(e)}"
    
    def _filter_neighborhoods(self, cuisine_type: str, budget_level: str) -> List[str]:
        """Filter neighborhoods based on cuisine type and budget level."""
        # Default to all neighborhoods
        filtered_neighborhoods = CHENNAI_NEIGHBORHOODS.copy()
        
        # Filter by veg-friendly score if cuisine is vegan/vegetarian
        if cuisine_type.lower() in ["vegan", "vegetarian", "plant-based"]:
            high_veg_areas = []
            for area, data in CHENNAI_COMMERCIAL_DATA.items():
                if data.get("veg_friendly_score", 0) >= 8:
                    high_veg_areas.append(area)
            
            filtered_neighborhoods = [n for n in filtered_neighborhoods if n in high_veg_areas]
        
        # Filter by budget/rent
        if budget_level:
            budget_filtered = []
            for area in filtered_neighborhoods:
                if area in CHENNAI_COMMERCIAL_DATA:
                    rent_range = CHENNAI_COMMERCIAL_DATA[area].get("rent_range", "")
                    
                    # Extract numeric rent values
                    try:
                        # Extract first number from rent range
                        rent_min = int(''.join(filter(str.isdigit, rent_range.split("-")[0])))
                        
                        if budget_level == "Low" and rent_min < 70:
                            budget_filtered.append(area)
                        elif budget_level == "Moderate" and 60 <= rent_min <= 90:
                            budget_filtered.append(area)
                        elif budget_level == "High" and rent_min > 80:
                            budget_filtered.append(area)
                    except:
                        # If parsing fails, include the area anyway
                        budget_filtered.append(area)
            
            if budget_filtered:
                filtered_neighborhoods = budget_filtered
        
        return filtered_neighborhoods[:8]  # Limit to top 8 neighborhoods
    
    def _format_neighborhood_data(self, neighborhoods: List[str]) -> str:
        """Format neighborhood data for the prompt."""
        formatted_data = "Chennai Neighborhood Analysis:\n"
        
        for neighborhood in neighborhoods:
            formatted_data += f"\n- {neighborhood}:\n"
            if neighborhood in CHENNAI_COMMERCIAL_DATA:
                data = CHENNAI_COMMERCIAL_DATA[neighborhood]
                formatted_data += f"  - Foot Traffic: {data.get('foot_traffic', 'N/A')}\n"
                formatted_data += f"  - Demographics: {', '.join(data.get('demographics', []))}\n"
                formatted_data += f"  - Nearby Attractions: {', '.join(data.get('nearby_attractions', []))}\n"
                formatted_data += f"  - Vegetarian-Friendly Score: {data.get('veg_friendly_score', 'N/A')}/10\n"
        
        return formatted_data
    
    def _format_commercial_data(self, neighborhoods: List[str]) -> str:
        """Format commercial data for the prompt."""
        formatted_data = "Commercial Real Estate Analysis:\n"
        
        for neighborhood in neighborhoods:
            if neighborhood in CHENNAI_COMMERCIAL_DATA:
                data = CHENNAI_COMMERCIAL_DATA[neighborhood]
                formatted_data += f"\n- {neighborhood}:\n"
                formatted_data += f"  - Average Rent: {data.get('rent_range', 'N/A')}\n"
                
                # Add calculation for estimated monthly rent for a restaurant
                rent_range = data.get('rent_range', '')
                try:
                    # Extract first number from rent range
                    rent_mid = int(''.join(filter(str.isdigit, rent_range.split("-")[0])))
                    # Estimate for a 1000 sq ft restaurant
                    monthly_est = rent_mid * 1000
                    formatted_data += f"  - Est. Monthly Rent (1000 sq.ft): ₹{monthly_est:,}/month\n"
                except:
                    formatted_data += "  - Est. Monthly Rent: Unable to calculate\n"
        
        return formatted_data
    
    def _get_additional_context(self, cuisine_type: str) -> str:
        """Get additional context from the knowledge graph."""
        # Try to get regulations from Neo4j
        try:
            regulations = self.kg.get_regulatory_info("Chennai")
            reg_text = "Regulatory Information:\n"
            for i, reg in enumerate(regulations[:3]):
                reg_text += f"- {reg.get('type', 'Regulation')}: {reg.get('description', 'N/A')}\n"
            
            # Get any cuisine preferences
            cuisines = self.kg.get_cuisine_preferences("Chennai")
            cuisine_text = "\nPopular Cuisines in Chennai:\n"
            for cuisine in cuisines[:5]:
                cuisine_text += f"- {cuisine.get('cuisine_type', 'Unknown')}\n"
            
            return reg_text + cuisine_text
        except Exception as e:
            return f"Additional context retrieval error: {str(e)}"
