"""
Enhanced restaurant advisor agent that leverages the improved knowledge base and graph integration.
"""

from typing import Dict, List, Optional, Any
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from integrations.cross_db_insights import CrossDBInsights
from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph

class EnhancedRestaurantAdvisorAgent:
    """Agent that provides enhanced restaurant recommendations using integrated knowledge sources."""
    
    def __init__(self, llm: BaseLLM, kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
        """Initialize the enhanced restaurant advisor agent.
        
        Args:
            llm: Language model instance
            kb: MongoDB knowledge base instance
            kg: Neo4j knowledge graph instance
        """
        self.llm = llm
        self.kb = kb
        self.kg = kg
        self.insights = CrossDBInsights(kb, kg)
        
        # Define the enhanced advisor prompt
        self.advisor_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert restaurant business advisor specializing in the Indian market.
            You provide detailed, data-driven recommendations for restaurant entrepreneurs
            looking to open or expand restaurant chains across Indian cities.
            
            You have access to two types of knowledge:
            1. Structured data about cities, locations, regulations, and cuisine preferences
            2. Unstructured insights from research papers, reports, and industry analyses
            
            Provide comprehensive, actionable advice based on the following information:
            
            City Information: {city_info}
            
            Location Recommendations: {location_recommendations}
            
            Market Analysis: {market_analysis}
            
            Regulatory Information: {regulatory_info}
            
            Opportunity Score: {opportunity_score}
            
            Market Gaps: {market_gaps}
            
            Address the user's specific question: {user_query}
            
            Format your response with clear sections, specific recommendations, and actionable insights.
            Always cite the source of your information where possible.
            """),
        ])
        
        # Define the answer parser
        self.answer_parser = StrOutputParser()
        
    def run(self, query: str, city: str, cuisine_type: Optional[str] = None, area: Optional[str] = None) -> str:
        """Run the enhanced advisor agent to answer a query.
        
        Args:
            query: User query string
            city: Target city for recommendation
            cuisine_type: Optional cuisine type
            area: Optional specific area within the city
            
        Returns:
            Detailed restaurant recommendation
        """
        try:
            # Gather integrated insights
            comprehensive_insights = self.insights.get_comprehensive_city_insights(city, cuisine_type)
            
            # Calculate opportunity score if area is provided
            opportunity_score = "No specific area provided for opportunity scoring."
            if area and cuisine_type:
                score_result = self.insights.get_restaurant_opportunity_score(city, area, cuisine_type)
                opportunity_score = f"""
                Overall Score: {score_result['opportunity_score']}/10
                Interpretation: {score_result['interpretation']}
                
                Score Components:
                - Location Score: {score_result['components']['location_score']:.1f}/10
                - Uniqueness Score: {score_result['components']['uniqueness_score']:.1f}/10
                - Market Sentiment: {score_result['components']['market_sentiment']:.1f}/10
                - Regulatory Ease: {score_result['components']['regulatory_ease']:.1f}/10
                
                Supporting Insights:
                {' '.join([insight[:200] + '...' for insight in score_result['supporting_insights'][:2]])}
                """
            
            # Find market gaps
            market_gaps = self.insights.find_market_gaps(city)
            gaps_text = "Top market gaps identified:\n"
            for gap in market_gaps["identified_gaps"][:3]:
                gaps_text += f"- {gap['cuisine'].title()} cuisine (mentioned {gap['mentions']} times)\n"
                if gap["cuisine"] in market_gaps["supporting_insights"]:
                    insights = market_gaps["supporting_insights"][gap["cuisine"]]
                    if insights:
                        gaps_text += f"  Insight: {insights[0][:150]}...\n"
            
            # Format the input for the LLM
            city_info = f"""
            City: {city}
            Popular cuisines: {', '.join([c['cuisine_type'] for c in comprehensive_insights['structured_data']['cuisine_preferences'][:3]])}
            """
            
            location_recs = "\n".join([
                f"- {loc.get('area', 'Unknown Area')}: {loc.get('type', 'Commercial')} area, " +
                f"Foot traffic: {loc.get('foot_traffic', 'Unknown')}, " + 
                f"Rent range: {loc.get('rent_range', 'Unknown')}"
                for loc in comprehensive_insights['structured_data']['recommended_locations'][:3]
            ])
            
            market_analysis = "\n".join([
                f"- {insight[:200]}..." 
                for insight in comprehensive_insights['unstructured_data']['market_trends']
            ])
            
            regulatory_info = "\n".join([
                f"- {reg.get('type', 'Regulation')}: {reg.get('description', 'No description')}[:100]..." 
                for reg in comprehensive_insights['structured_data']['regulations'][:3]
            ])
            
            # Create the chain
            chain = (
                self.advisor_prompt 
                | self.llm 
                | self.answer_parser
            )
            
            # Run the chain with all the gathered insights
            answer = chain.invoke({
                "city_info": city_info,
                "location_recommendations": location_recs,
                "market_analysis": market_analysis,
                "regulatory_info": regulatory_info,
                "opportunity_score": opportunity_score,
                "market_gaps": gaps_text,
                "user_query": query
            })
            
            return answer
        except Exception as e:
            return f"I encountered an issue retrieving enhanced restaurant recommendations: {str(e)}. " \
                   f"Could you try again with more specific information about your restaurant concept and target location?"
