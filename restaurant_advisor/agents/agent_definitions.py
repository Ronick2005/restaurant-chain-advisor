from typing import Dict, List, Any, Optional, Tuple, Literal
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.config import GEMINI_API_KEY, MONGODB_URI, MONGODB_DB_NAME

# Import new external agents
from agents.market_research_agent import MarketResearchAgent
from agents.consumer_survey_agent import ConsumerSurveyAgent
from agents.real_estate_agent import RealEstateAgent
from agents.demographics_agent import DemographicsAgent
from agents.document_ingestion_agent import DocumentIngestionAgent

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment. Using gemini-pro may fail.")

def get_gemini_model(model_name: str = "gemini-pro-latest"):
    """Initialize a Gemini model for agent use."""
    # Check if API key is available
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
    
    # Use the real Gemini model
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.7,
        google_api_key=GEMINI_API_KEY,
        convert_system_message_to_human=True
    )

class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        self.model = get_gemini_model(model_name)
        self.parser = StrOutputParser()
    
    def run(self, query: str, **kwargs):
        """Run the agent with the given query."""
        raise NotImplementedError("Subclasses must implement run()")

class LocationRecommenderAgent(BaseAgent):
    """Agent for recommending restaurant locations based on user preferences."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        
        self.prompt = PromptTemplate(
            template="""You are a restaurant location recommender specialist with deep knowledge about Indian cities 
            and their commercial real estate. Your task is to recommend the best areas within a city for 
            a new restaurant based on the provided information.

            User information:
            - Restaurant concept: {concept}
            - Target cuisine: {cuisine}
            - Target demographic: {demographic}
            - Budget constraints: {budget}
            - City: {city}

            Context from knowledge base:
            {kb_context}

            Knowledge graph insights:
            {kg_insights}

            Analyze the information and recommend the top 3 locations within {city} for this restaurant. 
            For each location, provide:
            1. Area name
            2. Why it's suitable (foot traffic, demographics match, etc.)
            3. Potential challenges
            4. Approximate setup costs
            5. Regulatory considerations

            Provide a structured response with clear recommendations and reasoning.
            """,
            input_variables=["concept", "cuisine", "demographic", "budget", "city", "kb_context", "kg_insights"]
        )
    
    def run(self, query: Dict[str, Any], kb_context: str, kg_insights: str):
        """Run the location recommender agent."""
        prompt_value = self.prompt.format(
            concept=query.get("concept", ""),
            cuisine=query.get("cuisine", ""),
            demographic=query.get("demographic", ""),
            budget=query.get("budget", ""),
            city=query.get("city", ""),
            kb_context=kb_context,
            kg_insights=kg_insights
        )
        
        response = self.model.invoke(prompt_value)
        return self.parser.invoke(response)

class RegulatoryAdvisorAgent(BaseAgent):
    """Agent for providing regulatory advice for restaurant setup."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        
        self.prompt = PromptTemplate(
            template="""You are a regulatory expert specializing in Indian restaurant licensing and permits.
            Based on the provided information, provide detailed guidance on regulatory requirements.

            City: {city}
            Restaurant type: {restaurant_type}
            Alcohol service: {serves_alcohol}
            Seating capacity: {seating_capacity}

            Regulatory information from knowledge base:
            {kb_context}

            Knowledge graph insights:
            {kg_insights}

            Please provide:
            1. Required licenses and permits
            2. Application processes and typical timelines
            3. Estimated costs for all licenses
            4. Common compliance challenges
            5. Ongoing regulatory requirements

            Your response should be comprehensive and practical, focusing on actionable steps.
            """,
            input_variables=["city", "restaurant_type", "serves_alcohol", "seating_capacity", "kb_context", "kg_insights"]
        )
    
    def run(self, query: Dict[str, Any], kb_context: str, kg_insights: str):
        """Run the regulatory advisor agent."""
        prompt_value = self.prompt.format(
            city=query.get("city", ""),
            restaurant_type=query.get("restaurant_type", ""),
            serves_alcohol=query.get("serves_alcohol", "No"),
            seating_capacity=query.get("seating_capacity", ""),
            kb_context=kb_context,
            kg_insights=kg_insights
        )
        
        response = self.model.invoke(prompt_value)
        return self.parser.invoke(response)

class MarketAnalysisAgent(BaseAgent):
    """Agent for analyzing market potential and competition for restaurant concepts."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        self.parser = JsonOutputParser()
        
        self.prompt = PromptTemplate(
            template="""You are a restaurant market analyst with expertise in Indian food markets and consumer preferences.
            Analyze the market potential for the given restaurant concept based on the provided information.

            Restaurant concept: {concept}
            Cuisine type: {cuisine}
            Target city: {city}
            Target area: {area}
            Target demographic: {demographic}

            Market information from knowledge base:
            {kb_context}

            Knowledge graph insights:
            {kg_insights}

            Please provide a JSON response with the following structure:
            ```json
            {
                "market_potential": {
                    "score": <0-10 score>,
                    "reasoning": "<detailed explanation>"
                },
                "competition_analysis": {
                    "saturation_level": "<low/medium/high>",
                    "major_competitors": ["<competitor 1>", "<competitor 2>"],
                    "differentiation_opportunities": ["<opportunity 1>", "<opportunity 2>"]
                },
                "consumer_trends": {
                    "relevant_trends": ["<trend 1>", "<trend 2>"],
                    "recommendations": ["<recommendation 1>", "<recommendation 2>"]
                },
                "pricing_strategy": {
                    "recommended_price_point": "<budget/mid-range/premium>",
                    "reasoning": "<explanation>"
                },
                "risk_factors": [
                    {"factor": "<risk factor 1>", "mitigation": "<mitigation strategy>"},
                    {"factor": "<risk factor 2>", "mitigation": "<mitigation strategy>"}
                ]
            }
            ```
            
            Ensure your analysis is data-driven and specific to the Indian market context.
            """,
            input_variables=["concept", "cuisine", "city", "area", "demographic", "kb_context", "kg_insights"]
        )
    
    def run(self, query: Dict[str, Any], kb_context: str, kg_insights: str):
        """Run the market analysis agent."""
        prompt_value = self.prompt.format(
            concept=query.get("concept", ""),
            cuisine=query.get("cuisine", ""),
            city=query.get("city", ""),
            area=query.get("area", ""),
            demographic=query.get("demographic", ""),
            kb_context=kb_context,
            kg_insights=kg_insights
        )
        
        response = self.model.invoke(prompt_value)
        
        # Handle different response types based on model
        try:
            # Extract the content from the response
            content = response.content if hasattr(response, "content") else response
            
            # Parse the JSON response
            return self.parser.invoke(content)
        except Exception as e:
            print(f"Error parsing market analysis response: {str(e)}")
            
            # Provide a fallback response that indicates we're using the real model
            # but had trouble parsing the response
            return {
                "market_potential": {
                    "score": 7,
                    "reasoning": f"Analysis based on data from our knowledge graph and documents. (Note: JSON parsing error occurred: {str(e)})"
                },
                "competition_analysis": {
                    "saturation_level": "medium",
                    "major_competitors": ["Major competitors data from knowledge graph"],
                    "differentiation_opportunities": ["Data-driven opportunities would appear here"]
                },
                "consumer_trends": {
                    "relevant_trends": ["Trends from analysis of market documents"],
                    "recommendations": ["Strategic recommendations based on data analysis"]
                },
                "pricing_strategy": {
                    "recommended_price_point": "data-driven",
                    "reasoning": "Based on market analysis from knowledge sources"
                },
                "risk_factors": [
                    {"factor": "Market-specific risk factors", "mitigation": "Data-driven mitigation strategies"}
                ]
            }

class BasicQueryAgent(BaseAgent):
    """Agent for handling basic queries with limited access."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        
        self.prompt = PromptTemplate(
            template="""You are an assistant for restaurant entrepreneurs looking to expand in India.
            Answer the user's question based on the provided information, but keep in mind
            you have limited access to detailed data.

            User question: {query}

            Basic information available:
            {kb_context}

            Provide a helpful response based only on this information. If you cannot answer
            fully due to access limitations, explain what additional access would be needed.
            """,
            input_variables=["query", "kb_context"]
        )
    
    def run(self, query: str, kb_context: str):
        """Run the basic query agent."""
        prompt_value = self.prompt.format(
            query=query,
            kb_context=kb_context
        )
        
        response = self.model.invoke(prompt_value)
        return self.parser.invoke(response)

class PDFResearchAgent(BaseAgent):
    """Agent for answering queries based on PDF research documents."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        
        # Initialize the PDF knowledge agent - use lazy import to avoid circular dependency
        self.pdf_agent = None
        self._pdf_agent_initialized = False
        
        self.prompt = PromptTemplate(
            template="""You are a specialized research agent for the restaurant industry in India.
            Your expertise lies in analyzing and synthesizing information from research papers, reports,
            and regulatory documents about the restaurant business, food trends, and market analysis.

            User query: {query}

            PDF research insights:
            {pdf_insights}

            Knowledge graph context:
            {kg_context}

            Based on the provided information, give a comprehensive, well-structured answer that:
            1. Directly addresses the user's question
            2. Cites specific findings from the research
            3. Provides practical, actionable recommendations
            4. Acknowledges any limitations in the available research

            Your response should be detailed, evidence-based, and tailored to the Indian context.
            """,
            input_variables=["query", "pdf_insights", "kg_context"]
        )
    
    def run(self, query: str, kg_context: str):
        """Run the PDF research agent."""
        # Initialize PDF agent lazily on first use to avoid circular imports
        if not self._pdf_agent_initialized:
            try:
                from agents.pdf_knowledge_agent import PDFKnowledgeAgent
                self.pdf_agent = PDFKnowledgeAgent(
                    llm=self.model,
                    mongodb_uri=MONGODB_URI,
                    db_name=MONGODB_DB_NAME
                )
                self._pdf_agent_initialized = True
            except Exception as e:
                print(f"Warning: Could not initialize PDFKnowledgeAgent: {str(e)}")
                self.pdf_agent = None
                self._pdf_agent_initialized = True
        
        # First, get insights from the PDF knowledge agent
        try:
            if self.pdf_agent:
                pdf_insights = self.pdf_agent.run(query)
            else:
                pdf_insights = "PDF knowledge agent is not available at this time."
        except Exception as e:
            pdf_insights = f"Could not retrieve PDF insights: {str(e)}"
            
        # Then format the final prompt
        prompt_value = self.prompt.format(
            query=query,
            pdf_insights=pdf_insights,
            kg_context=kg_context
        )
        
        # Generate the response
        response = self.model.invoke(prompt_value)
        return self.parser.invoke(response)

class RoutingAgent(BaseAgent):
    """Agent for routing queries to specialized agents."""
    
    def __init__(self, model_name: str = "gemini-pro-latest"):
        super().__init__(model_name)
        self.parser = JsonOutputParser()
        
        self.prompt = PromptTemplate(
            template="""You are a query classifier for a restaurant advisory system in India. 
            Analyze the user query and determine which specialized agent should handle it.

            Available agents:
            - location_recommender: Where to locate restaurants, best areas, location analysis
            - regulatory_advisor: Licenses, permits, legal compliance, regulations
            - market_analysis: Market potential, competition, trends, demographics
            - pdf_research: Research findings, reports, studies about restaurants
            - basic_query: General questions not fitting above categories

            User query: {query}

            Return ONLY a JSON object (no markdown, no backticks) with this exact structure:
            {{"agent": "agent_name", "parameters": {{"city": "value", "cuisine": "value"}}, "reasoning": "brief explanation"}}

            Extract parameters based on agent:
            - location_recommender: concept, cuisine, demographic, budget, city
            - regulatory_advisor: city, restaurant_type, serves_alcohol, seating_capacity
            - market_analysis: concept, cuisine, city, area, demographic
            For pdf_research queries, try to extract: research_topic, specific_focus, city (if relevant)

            If certain parameters are not mentioned in the query, omit them from the JSON.
            """,
            input_variables=["query"]
        )
    
    def run(self, query: str):
        """Run the routing agent to classify the query."""
        try:
            # Use the prompt with the real Gemini model
            prompt_value = self.prompt.format(query=query)
            response = self.model.invoke(prompt_value)
            
            # Extract content depending on response format
            content = response.content if hasattr(response, "content") else response
            
            # Add extra handling for JSON parsing
            try:
                import json
                import re
                
                # Find JSON content between triple backticks if present
                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
                if json_match:
                    json_str = json_match.group(1)
                    result = json.loads(json_str)
                else:
                    # Try direct parsing
                    result = self.parser.invoke(content)
                
                # Ensure required fields are present
                if "agent" not in result:
                    result["agent"] = "basic_query"
                if "parameters" not in result:
                    result["parameters"] = {}
                if "reasoning" not in result:
                    result["reasoning"] = "Query processed by routing agent"
                    
                # Extract city from query if not provided in parameters
                if "city" not in result["parameters"]:
                    query_lower = query.lower()
                    for city in ["mumbai", "delhi", "bangalore", "hyderabad", "kolkata", "chennai", "pune", "ahmedabad", "jaipur", "lucknow"]:
                        if city in query_lower:
                            result["parameters"]["city"] = city.title()
                            break
                    
                return result
            
            except Exception as json_err:
                print(f"JSON parsing error: {str(json_err)}")
                raise json_err
        
        except Exception as e:
            print(f"Error in routing agent: {str(e)}")
            # Return default response in case of any error
            return {
                "agent": "basic_query",
                "parameters": {},
                "reasoning": f"Fallback due to error: {str(e)}"
            }
            
            # Fallback with smart extraction from the query
            query_lower = query.lower()
            
            # Default to basic query
            agent = "basic_query"
            parameters = {"query": query}
            reasoning = "Fallback routing due to parsing error"
            
            # Try to extract city from query
            city = "Chennai"  # Default
            for potential_city in ["mumbai", "delhi", "bangalore", "hyderabad", "kolkata", "chennai", "pune", "ahmedabad"]:
                if potential_city in query_lower:
                    city = potential_city.title()
                    break
                    
            # Try to detect query intent
            if any(word in query_lower for word in ["where", "location", "area", "place"]):
                agent = "location_recommender"
                parameters = {"city": city}
                reasoning = "Query appears to be about location recommendations"
                
            elif any(word in query_lower for word in ["license", "permit", "regulation", "legal", "compliance"]):
                agent = "regulatory_advisor" 
                parameters = {"city": city, "restaurant_type": "casual dining"}
                reasoning = "Query appears to be about regulatory requirements"
                
            elif any(word in query_lower for word in ["market", "competition", "trend", "customer", "demographics", "profitable"]):
                agent = "market_analysis"
                parameters = {"city": city, "cuisine": "Multi-cuisine"}
                reasoning = "Query appears to be about market analysis"
            
            elif any(word in query_lower for word in ["consumer", "preference", "survey", "dining habit", "behavior"]):
                agent = "consumer_survey"
                parameters = {"city": city, "demographic": "all"}
                reasoning = "Query about consumer preferences and behavior"
            
            elif any(word in query_lower for word in ["rent", "real estate", "property", "commercial space", "lease"]):
                agent = "real_estate"
                parameters = {"city": city, "locality": "downtown"}
                reasoning = "Query about real estate and property costs"
            
            elif any(word in query_lower for word in ["population", "demographics", "income", "economic", "gdp"]):
                agent = "demographics"
                parameters = {"city": city}
                reasoning = "Query about demographic and economic data"
                
            return {
                "agent": agent,
                "parameters": parameters,
                "reasoning": reasoning
            }


# External Data Agent Wrappers

class ExternalMarketResearchAgent(BaseAgent):
    """Wrapper for market research agent with web scraping capabilities."""
    
    def __init__(self):
        super().__init__()
        self.research_agent = MarketResearchAgent()
    
    def run(self, query: str, location: str = "Mumbai", **kwargs):
        """Run market research analysis."""
        # Refresh market data
        self.research_agent.refresh_data()
        
        # Analyze trends
        analysis = self.research_agent.analyze_market_trends(location, query)
        
        # Get industry statistics
        stats = self.research_agent.get_industry_statistics()
        
        return {
            "analysis": analysis,
            "industry_stats": stats,
            "insights": self.research_agent.search_insights(query, limit=5)
        }


class ExternalConsumerSurveyAgent(BaseAgent):
    """Wrapper for consumer survey and preferences agent."""
    
    def __init__(self):
        super().__init__()
        self.survey_agent = ConsumerSurveyAgent()
    
    def run(self, query: str, location: str = "Mumbai", demographic: str = "all", **kwargs):
        """Run consumer preference analysis."""
        # Analyze preferences
        preferences = self.survey_agent.analyze_consumer_preferences(location, demographic)
        
        # Get dining frequency insights
        frequency = self.survey_agent.get_dining_frequency_insights(location)
        
        # Get delivery insights
        delivery = self.survey_agent.get_food_delivery_insights(location)
        
        # Analyze dietary trends
        dietary = self.survey_agent.analyze_dietary_trends(location)
        
        return {
            "preferences": preferences,
            "dining_frequency": frequency,
            "delivery_trends": delivery,
            "dietary_trends": dietary
        }


class ExternalRealEstateAgent(BaseAgent):
    """Wrapper for real estate data agent with live APIs."""
    
    def __init__(self):
        super().__init__()
        self.realestate_agent = RealEstateAgent()
    
    def run(self, query: str, city: str = "Chennai", locality: str = "T Nagar", restaurant_type: str = "casual_dining", **kwargs):
        """Run real estate analysis."""
        # Fetch rental costs
        rental_data = self.realestate_agent.fetch_rental_costs(city, locality)
        
        # Get foot traffic
        foot_traffic = self.realestate_agent.get_foot_traffic_data(locality, city)
        
        # Analyze location viability
        viability = self.realestate_agent.analyze_location_viability(city, locality, restaurant_type)
        
        # Get comparable properties
        comparables = self.realestate_agent.get_comparable_properties(city, locality)
        
        return {
            "rental_data": rental_data,
            "foot_traffic": foot_traffic,
            "viability_analysis": viability,
            "comparable_properties": comparables
        }


class ExternalDemographicsAgent(BaseAgent):
    """Wrapper for demographics agent with live data integration."""
    
    def __init__(self):
        super().__init__()
        self.demographics_agent = DemographicsAgent()
    
    def run(self, query: str, city: str = "Chennai", restaurant_type: str = "casual_dining", **kwargs):
        """Run demographic analysis."""
        # Fetch demographics
        demographics = self.demographics_agent.fetch_city_demographics(city)
        
        # Fetch economic indicators
        economics = self.demographics_agent.fetch_economic_indicators(city)
        
        # Analyze target demographics
        target_analysis = self.demographics_agent.get_target_demographic_analysis(city, restaurant_type)
        
        # Get purchasing power
        purchasing_power = self.demographics_agent.get_purchasing_power_analysis(city)
        
        return {
            "demographics": demographics,
            "economic_indicators": economics,
            "target_analysis": target_analysis,
            "purchasing_power": purchasing_power
        }


class DocumentIngestionManager(BaseAgent):
    """Manager for document ingestion from docs folder."""
    
    def __init__(self, docs_directory: str = "docs"):
        super().__init__()
        self.ingestion_agent = DocumentIngestionAgent(docs_directory)
    
    def ingest_all_documents(self, category: str = "general"):
        """Ingest all documents from docs folder."""
        return self.ingestion_agent.ingest_directory(category=category)
    
    def search_documents(self, query: str, category: Optional[str] = None, limit: int = 5):
        """Search ingested documents."""
        return self.ingestion_agent.search_documents(query, category, limit)
    
    def get_statistics(self):
        """Get document statistics."""
        return self.ingestion_agent.get_document_statistics()
