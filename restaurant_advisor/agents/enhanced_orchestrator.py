"""
Enhanced multi-agent orchestrator with advanced routing and agent-leading-agents capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple, Literal, TypedDict, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import operator
from langgraph.graph import StateGraph, END

from agents.agent_definitions import (
    RoutingAgent, 
    LocationRecommenderAgent, 
    RegulatoryAdvisorAgent, 
    MarketAnalysisAgent,
    BasicQueryAgent,
    PDFResearchAgent,
    ExternalMarketResearchAgent,
    ExternalConsumerSurveyAgent,
    ExternalRealEstateAgent,
    ExternalDemographicsAgent,
    DocumentIngestionManager
)
from agents.domain_agents import DomainSpecialistAgent
from agents.memory_management import MemoryManager
from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from utils.auth import has_agent_access, check_permission

class EnhancedAgentState(TypedDict):
    """Type definition for the state in the enhanced agent graph."""
    messages: List[BaseMessage]
    user: Dict
    context: Dict
    next_agent: Optional[str]
    subagents: List[str]
    memory: Dict
    access_control: Dict

class EnhancedAgentOrchestrator:
    """Enhanced orchestrator for the multi-agent system with advanced routing and memory."""
    
    def __init__(self, kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
        self.kb = kb
        self.kg = kg
        self.graph = self.create_agent_graph()
        
        # Initialize memory manager
        self.memory_manager = MemoryManager()
        
        # Initialize agents
        self.router = RoutingAgent()
        self.location_recommender = LocationRecommenderAgent()
        self.regulatory_advisor = RegulatoryAdvisorAgent()
        self.market_analysis = MarketAnalysisAgent()
        self.pdf_research = PDFResearchAgent()
        self.basic_query = BasicQueryAgent()
        self.domain_specialist = DomainSpecialistAgent()
        
        # Initialize external data agents
        self.external_market_research = ExternalMarketResearchAgent()
        self.external_consumer_survey = ExternalConsumerSurveyAgent()
        self.external_real_estate = ExternalRealEstateAgent()
        self.external_demographics = ExternalDemographicsAgent()
        self.document_manager = DocumentIngestionManager()
    
    def create_agent_graph(self) -> StateGraph:
        """Create the enhanced agent graph with advanced routing."""
        # Define the workflow nodes
        def initialize_state(state: EnhancedAgentState) -> EnhancedAgentState:
            """Initialize the state with necessary components."""
            # Initialize subagents list if not present
            if "subagents" not in state:
                state["subagents"] = []
            
            # Initialize memory if not present
            if "memory" not in state:
                state["memory"] = {}
            
            # Initialize access control if not present
            if "access_control" not in state:
                state["access_control"] = {
                    "checked_permissions": {},
                    "access_denied": False
                }
            
            return state
        
        def route_query(state: EnhancedAgentState) -> EnhancedAgentState:
            """Route the user's query to the appropriate agent."""
            # Get the latest message
            latest_message = state["messages"][-1]
            if not isinstance(latest_message, HumanMessage):
                return state
            
            # Route the query
            query = latest_message.content
            result = self.router.run(query)
            
            # Store routing result
            state["context"]["routing"] = result
            state["next_agent"] = result["agent"]
            
            # Update memory with routing information
            user_id = state["user"]["username"]
            state["memory"][user_id] = state["memory"].get(user_id, {})
            state["memory"][user_id]["last_route"] = result["agent"]
            state["memory"][user_id]["last_parameters"] = result["parameters"]
            
            return state
        
        def check_permissions_and_route(state: EnhancedAgentState) -> str:
            """Check if the user has access to the required agent and route accordingly."""
            next_agent = state["next_agent"]
            user = state["user"]
            
            # Check if the agent access is allowed
            has_access = has_agent_access(user, next_agent)
            
            # Store permission check result
            state["access_control"]["checked_permissions"][next_agent] = has_access
            
            if has_access:
                # Access granted
                return next_agent
            else:
                # Access denied - fall back to basic query
                state["access_control"]["access_denied"] = True
                state["next_agent"] = "basic_query"
                return "basic_query"
        
        def retrieve_context(state: EnhancedAgentState) -> EnhancedAgentState:
            """Retrieve relevant context from knowledge base and knowledge graph."""
            routing_result = state["context"].get("routing", {})
            agent_name = state["next_agent"]
            parameters = routing_result.get("parameters", {})
            
            # Initialize context containers
            kb_context = []
            kg_insights = []
            
            # Check user's KB and KG access permissions
            user = state["user"]
            has_kb_access = check_permission(user, "kb", "read")
            has_kg_access = check_permission(user, "kg", "read")
            
            # Get context based on the agent type with permission checks
            if agent_name == "location_recommender":
                city = parameters.get("city", "")
                cuisine = parameters.get("cuisine", "")
                concept = parameters.get("concept", "")
                demographic = parameters.get("demographic", "")
                
                # Get relevant documents from knowledge base if permission granted
                if has_kb_access and city:
                    # Create a more specific query using all available parameters
                    query_parts = [f"restaurant locations in {city}"]
                    if cuisine:
                        query_parts.append(f"{cuisine} cuisine")
                    if concept:
                        query_parts.append(f"{concept} restaurant concept")
                    if demographic:
                        query_parts.append(f"for {demographic} demographic")
                    
                    query = " ".join(query_parts) + " commercial real estate market insights foot traffic"
                    
                    # Perform a hybrid search for more relevant results
                    kb_docs = self.kb.hybrid_search(
                        query, 
                        user_filter={"metadata.type": {"$in": ["real_estate", "demographics", "food_consumption"]}}
                    )
                    kb_context = [doc.page_content for doc in kb_docs]
                
                # Get insights from knowledge graph if permission granted
                if has_kg_access and city and self.kg:
                    # Get detailed location recommendations
                    locations = self.kg.recommend_locations(city, cuisine_type=cuisine)
                    
                    # Format location insights with more details
                    for loc in locations:
                        area = loc.get('area', '')
                        score = loc.get('score', 0)
                        properties = loc.get('properties', {})
                        
                        insight = f"Location: {area} - Overall Score: {score:.2f}\n"
                        
                        # Add more details from properties if available
                        if properties:
                            foot_traffic = properties.get('foot_traffic', 0)
                            competition = properties.get('competition_score', 0)
                            growth = properties.get('growth_potential', 0)
                            rent = properties.get('rent_score', 0)
                            
                            insight += f"  - Foot Traffic: {foot_traffic:.2f}\n"
                            insight += f"  - Competition Level: {competition:.2f}\n"
                            insight += f"  - Growth Potential: {growth:.2f}\n"
                            insight += f"  - Rent Value (lower is better): {rent:.2f}\n"
                            
                            # Add popular cuisines if available
                            popular_cuisines = properties.get('popular_cuisines', [])
                            if popular_cuisines:
                                insight += f"  - Popular Cuisines: {', '.join(popular_cuisines)}\n"
                                
                            # Add demographics if available
                            demographics = properties.get('demographics', [])
                            if demographics:
                                insight += f"  - Key Demographics: {', '.join(demographics)}\n"
                        
                        kg_insights.append(insight)
                        
            elif agent_name == "regulatory_advisor":
                city = parameters.get("city", "")
                restaurant_type = parameters.get("restaurant_type", "")
                serves_alcohol = parameters.get("serves_alcohol", "No")
                
                # Get relevant documents from knowledge base if permission granted
                if has_kb_access and city:
                    # Create a more specific query
                    query_parts = [f"restaurant regulations in {city}"]
                    if restaurant_type:
                        query_parts.append(f"{restaurant_type}")
                    if serves_alcohol.lower() == "yes":
                        query_parts.append("liquor license alcohol serving requirements")
                    
                    query = " ".join(query_parts) + " licensing permits requirements"
                    
                    kb_docs = self.kb.hybrid_search(
                        query, 
                        user_filter={"metadata.type": {"$in": ["regulation", "food_consumption"]}}
                    )
                    kb_context = [doc.page_content for doc in kb_docs]
                
                # Get insights from knowledge graph if permission granted
                if has_kg_access and city and self.kg:
                    regulations = self.kg.get_regulatory_info(city)
                    
                    for reg in regulations:
                        reg_type = reg.get('type', '')
                        description = reg.get('description', '')
                        authority = reg.get('authority', '')
                        requirements = reg.get('requirements', [])
                        timeline = reg.get('timeline', '')
                        cost = reg.get('cost', '')
                        renewal = reg.get('renewal', '')
                        
                        insight = f"Regulation: {reg_type}\n"
                        insight += f"Description: {description}\n"
                        insight += f"Authority: {authority}\n"
                        
                        if requirements:
                            insight += "Requirements:\n"
                            for req in requirements:
                                insight += f"  - {req}\n"
                        
                        if timeline:
                            insight += f"Timeline: {timeline}\n"
                        if cost:
                            insight += f"Cost: {cost}\n"
                        if renewal:
                            insight += f"Renewal: {renewal}\n"
                        
                        kg_insights.append(insight)
            
            elif agent_name == "market_analysis":
                city = parameters.get("city", "")
                cuisine = parameters.get("cuisine", "")
                concept = parameters.get("concept", "")
                area = parameters.get("area", "")
                
                # Get relevant documents from knowledge base if permission granted
                if has_kb_access and city:
                    # Create a more specific query
                    query_parts = [f"restaurant market analysis in {city}"]
                    if cuisine:
                        query_parts.append(f"{cuisine} cuisine")
                    if concept:
                        query_parts.append(f"{concept} concept")
                    if area:
                        query_parts.append(f"{area} area")
                    
                    query = " ".join(query_parts) + " consumer trends competition demographics food preferences"
                    
                    kb_docs = self.kb.hybrid_search(
                        query, 
                        user_filter={"metadata.type": {"$in": ["food_consumption", "demographics", "real_estate"]}}
                    )
                    kb_context = [doc.page_content for doc in kb_docs]
                    
                # Get insights from knowledge graph if permission granted
                if has_kg_access and city and self.kg:
                    # Get cuisine preferences for the city
                    cuisine_preferences = self.kg.get_cuisine_preferences(city)
                    
                    # Get location demographics
                    locations = []
                    if area:
                        # Use get_detailed_location_info which accepts city and area parameters
                        locations = self.kg.get_detailed_location_info(city, area)
                    else:
                        locations = self.kg.recommend_locations(city)[:3]
                    
                    # Format cuisine preferences
                    cuisine_insights = []
                    for cuisine_pref in cuisine_preferences:
                        cuisine_type = cuisine_pref.get('cuisine_type', '')
                        score = cuisine_pref.get('score', 0)
                        cuisine_insights.append(f"Cuisine: {cuisine_type} - Popularity Score: {score:.2f}")
                    
                    # Format location insights
                    location_insights = []
                    for loc in locations:
                        area_name = loc.get('area', '')
                        properties = loc.get('properties', {})
                        
                        if properties:
                            foot_traffic = properties.get('foot_traffic', 0)
                            competition = properties.get('competition_score', 0)
                            growth = properties.get('growth_potential', 0)
                            demographics = properties.get('demographics', [])
                            
                            insight = f"Area: {area_name}\n"
                            insight += f"  - Foot Traffic: {foot_traffic:.2f}\n"
                            insight += f"  - Competition Level: {competition:.2f}\n"
                            insight += f"  - Growth Potential: {growth:.2f}\n"
                            
                            if demographics:
                                insight += f"  - Key Demographics: {', '.join(demographics)}\n"
                            
                            location_insights.append(insight)
                    
                    # Combine all insights
                    kg_insights = []
                    if cuisine_insights:
                        kg_insights.append("== Cuisine Preferences ==")
                        kg_insights.extend(cuisine_insights)
                    
                    if location_insights:
                        kg_insights.append("\n== Location Analysis ==")
                        kg_insights.extend(location_insights)
            
            elif agent_name == "pdf_research":
                # For PDF research queries, focus on extracting insights from research documents
                research_topic = parameters.get("research_topic", "")
                specific_focus = parameters.get("specific_focus", "")
                city = parameters.get("city", "")
                
                if has_kb_access:
                    # Build a query that will retrieve relevant document content
                    query_parts = ["restaurant business research"]
                    if research_topic:
                        query_parts.append(research_topic)
                    if specific_focus:
                        query_parts.append(specific_focus)
                    if city:
                        query_parts.append(f"in {city}")
                    
                    query = " ".join(query_parts) + " studies reports findings data statistics"
                    
                    # Perform knowledge base search with emphasis on research documents
                    kb_docs = self.kb.hybrid_search(
                        query,
                        user_filter={"metadata.type": {"$in": ["research", "food_consumption", "demographics", "real_estate"]}},
                        k=8  # Get more documents for research queries
                    )
                    kb_context = [doc.page_content for doc in kb_docs]
                
                if has_kg_access and city and self.kg:
                    # Get city-specific insights from the knowledge graph
                    regulations = self.kg.get_regulatory_info(city)
                    cuisine_preferences = self.kg.get_cuisine_preferences(city)
                    
                    # Format insights in a research-oriented way
                    kg_insights = [
                        f"=== Research Data for {city} ===",
                        f"City has {len(regulations)} documented regulatory frameworks",
                    ]
                    
                    # Add cuisine preference data
                    if cuisine_preferences:
                        kg_insights.append("\nCuisine Preference Data:")
                        for pref in cuisine_preferences[:5]:
                            cuisine_type = pref.get('cuisine_type', '')
                            score = pref.get('score', 0)
                            kg_insights.append(f"- {cuisine_type}: {score:.2f} popularity score")
                    
                    # Add regulatory data
                    if regulations:
                        kg_insights.append("\nRegulatory Framework Overview:")
                        for reg in regulations[:3]:
                            reg_type = reg.get('type', '')
                            authority = reg.get('authority', '')
                            kg_insights.append(f"- {reg_type} (Governing Body: {authority})")
                
            elif agent_name == "domain_specialist":
                # For domain specialist, get a wide range of context
                query = state["messages"][-1].content
                
                if has_kb_access:
                    # Extract key terms for better search
                    domain_keywords = parameters.get("domain_keywords", [])
                    city = parameters.get("city", "")
                    
                    # Create a search query with domain focus
                    search_query = query
                    if domain_keywords:
                        search_query += " " + " ".join(domain_keywords)
                    if city:
                        search_query += f" in {city}"
                    
                    # Perform knowledge base search
                    kb_docs = self.kb.hybrid_search(search_query, k=5)
                    kb_context = [doc.page_content for doc in kb_docs]
                
                if has_kg_access and self.kg:
                    # Get city information if specified
                    city = parameters.get("city", "")
                    if city:
                        # Get city demographics
                        city_data = self.kg.get_detailed_city_demographics(city)
                        
                        if city_data:
                            kg_insights.append(f"== City Demographics for {city} ==")
                            kg_insights.append(f"Population: {city_data.get('population', 'Unknown')}")
                            
                            if city_data.get('demographics'):
                                kg_insights.append("Key Demographics:")
                                for demo in city_data.get('demographics', [])[:3]:
                                    kg_insights.append(f"- {demo}")
                            
                            if city_data.get('key_markets'):
                                kg_insights.append("Key Markets:")
                                for market in city_data.get('key_markets', [])[:3]:
                                    kg_insights.append(f"- {market}")
                        
                        # Get cuisine preferences
                        cuisine_prefs = self.kg.get_cuisine_preferences(city)
                        if cuisine_prefs:
                            kg_insights.append(f"\n== Popular Cuisines in {city} ==")
                            for pref in cuisine_prefs[:3]:
                                cuisine_type = pref.get('cuisine_type', '')
                                popularity = pref.get('popularity', 0)
                                kg_insights.append(f"- {cuisine_type}: {popularity} popularity score")
            
            else:  # basic_query or fallback
                # For basic queries, get more comprehensive information
                query = state["messages"][-1].content
                
                # Extract city names from query
                city = None
                city_names = ["mumbai", "delhi", "bangalore", "chennai", "hyderabad", "kolkata", "pune", "ahmedabad"]
                query_lower = query.lower()
                for city_name in city_names:
                    if city_name in query_lower:
                        city = city_name.title()
                        break
                
                # Basic access with limited knowledge
                if has_kb_access:
                    # Perform knowledge base search
                    kb_docs = self.kb.hybrid_search(query, k=3)  # Reduced for basic access
                    kb_context = [doc.page_content for doc in kb_docs]
                
                # Limited knowledge graph access
                if has_kg_access and city and self.kg:
                    # Get some basic city information
                    regulations = self.kg.get_regulatory_info(city)
                    locations = self.kg.recommend_locations(city)[:3]  # Limited locations
                    cuisine_preferences = self.kg.get_cuisine_preferences(city)[:3]  # Limited cuisine preferences
                    
                    # Format basic insights
                    kg_insights = [
                        f"City: {city}",
                        f"Number of regulations: {len(regulations)}",
                        f"Top locations: {', '.join([loc.get('area', '') for loc in locations])}",
                        f"Popular cuisines: {', '.join([pref.get('cuisine_type', '') for pref in cuisine_preferences])}"
                    ]
            
            # Store retrieved context, ensuring not to exceed token limits
            state["context"]["kb_context"] = "\n\n".join(kb_context[:5])  # Limit context
            state["context"]["kg_insights"] = "\n\n".join(kg_insights[:8])  # Limit insights
            
            # Store sources from documents
            sources = []
            if kb_docs:
                for doc in kb_docs:
                    source_info = {
                        "file_name": doc.metadata.get("file_name", "Unknown"),
                        "category": doc.metadata.get("category", "general"),
                        "page": doc.metadata.get("page_number", 0),
                        "chunk_id": doc.metadata.get("chunk_id", 0)
                    }
                    if source_info not in sources:
                        sources.append(source_info)
            
            state["context"]["sources"] = sources
            
            # Store context in memory for future reference
            user_id = state["user"]["username"]
            state["memory"][user_id] = state["memory"].get(user_id, {})
            state["memory"][user_id]["last_kb_context"] = kb_context[:2]  # Store limited context
            state["memory"][user_id]["last_kg_insights"] = kg_insights[:3]  # Store limited insights
            
            return state
        
        def run_location_recommender(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the location recommender agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            kb_context = state["context"].get("kb_context", "")
            kg_insights = state["context"].get("kg_insights", "")
            sources = state["context"].get("sources", [])
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            preferences = user_memory.get("preferences", {})
            
            # Enhance parameters with user preferences if not explicitly provided
            if "city" not in parameters and "city" in preferences:
                parameters["city"] = preferences["city"]
            if "cuisine" not in parameters and "cuisine" in preferences:
                parameters["cuisine"] = preferences["cuisine"]
            
            response = self.location_recommender.run(parameters, kb_context, kg_insights)
            
            # Append sources to response if available
            if sources:
                response += "\n\n--- Sources ---\n"
                for i, source in enumerate(sources[:5], 1):
                    response += f"{i}. {source['file_name']} (Category: {source['category']}, Page: {source['page']})\n"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["last_sources"] = sources
            
            return state
        
        def run_regulatory_advisor(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the regulatory advisor agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            kb_context = state["context"].get("kb_context", "")
            kg_insights = state["context"].get("kg_insights", "")
            sources = state["context"].get("sources", [])
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            response = self.regulatory_advisor.run(parameters, kb_context, kg_insights)
            
            # Append sources to response if available
            if sources:
                response += "\n\n--- Sources ---\n"
                for i, source in enumerate(sources[:5], 1):
                    response += f"{i}. {source['file_name']} (Category: {source['category']}, Page: {source['page']})\n"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["last_sources"] = sources
            
            return state
        
        def run_market_analysis(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the market analysis agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            kb_context = state["context"].get("kb_context", "")
            kg_insights = state["context"].get("kg_insights", "")
            sources = state["context"].get("sources", [])
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            response = self.market_analysis.run(parameters, kb_context, kg_insights)
            
            # Append sources to response if available
            if sources:
                response += "\n\n--- Sources ---\n"
                for i, source in enumerate(sources[:5], 1):
                    response += f"{i}. {source['file_name']} (Category: {source['category']}, Page: {source['page']})\n"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["last_sources"] = sources
            
            return state
        
        def run_consumer_survey(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the external consumer survey agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            query = state["messages"][-1].content if state["messages"] else ""
            
            city = parameters.get("city", "Chennai")
            demographic = parameters.get("demographic", "all")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Run external consumer survey agent
            result = self.external_consumer_survey.run(query, location=city, demographic=demographic)
            
            # Format response
            response = f"**Consumer Survey Insights for {city}**\n\n"
            response += f"{result['preferences']['analysis']}\n\n"
            response += f"**Dining Frequency**: {result['dining_frequency']['weekly_dineout_frequency']}\n\n"
            response += f"**Delivery Trends**: Delivery adoption at {result['delivery_trends']['delivery_adoption_rate']}%\n\n"
            response += f"**Dietary Trends**: {result['dietary_trends']['analysis'][:300]}..."
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["consumer_data"] = result
            
            return state
        
        def run_real_estate(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the external real estate agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            query = state["messages"][-1].content if state["messages"] else ""
            
            city = parameters.get("city", "Chennai")
            locality = parameters.get("locality", "downtown")
            restaurant_type = parameters.get("restaurant_type", "casual_dining")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Run external real estate agent
            result = self.external_real_estate.run(query, city=city, locality=locality, restaurant_type=restaurant_type)
            
            # Format response
            response = f"**Real Estate Analysis for {locality}, {city}**\n\n"
            response += f"**Rental Costs**: ₹{result['rental_data']['rental_cost_per_sqft_monthly']['average']}/sqft/month\n"
            response += f"Range: ₹{result['rental_data']['rental_cost_per_sqft_monthly']['min']} - ₹{result['rental_data']['rental_cost_per_sqft_monthly']['max']}\n\n"
            response += f"**Foot Traffic**: {result['foot_traffic']['foot_traffic_level']}\n\n"
            response += f"**Viability Analysis**:\n{result['viability_analysis']['analysis']}"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["real_estate_data"] = result
            
            return state
        
        def run_demographics(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the external demographics agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            query = state["messages"][-1].content if state["messages"] else ""
            
            city = parameters.get("city", "Chennai")
            restaurant_type = parameters.get("restaurant_type", "casual_dining")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Run external demographics agent
            result = self.external_demographics.run(query, city=city, restaurant_type=restaurant_type)
            
            # Format response
            response = f"**Demographic & Economic Analysis for {city}**\n\n"
            response += f"**Population**: {result['demographics']['population']:,}\n"
            response += f"**Median Age**: {result['demographics']['median_age']} years\n"
            response += f"**GDP Per Capita**: ${result['economic_indicators']['gdp_per_capita_usd']:,}\n"
            response += f"**Avg Monthly Income**: ₹{result['economic_indicators']['avg_monthly_income_inr']:,}\n\n"
            response += f"**Purchasing Power**: Monthly dining budget ~ ₹{result['purchasing_power']['estimated_monthly_dining_budget']}\n\n"
            response += f"**Target Demographics Analysis**:\n{result['target_analysis']['analysis']}"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["demographics_data"] = result
            
            return state
        
        def run_market_research(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the external market research agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            query = state["messages"][-1].content if state["messages"] else ""
            
            city = parameters.get("city", "Chennai")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Run external market research agent
            result = self.external_market_research.run(query, location=city)
            
            # Format response
            response = f"**Market Research Insights for {city}**\n\n"
            response += f"**Industry Statistics**:\n"
            response += f"- Market Size: ${result['industry_stats']['market_size_usd_billion']}B\n"
            response += f"- Growth Rate: {result['industry_stats']['projected_growth_rate_percent']}%\n\n"
            response += f"**Market Analysis**:\n{result['analysis']['analysis']}"
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            state["memory"][user_id]["market_research_data"] = result
            
            return state
        
        def run_pdf_research(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the PDF research agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            query = state["messages"][-1].content if state["messages"] else ""
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            response = self.pdf_research.run(query, parameters)
            
            # Format the response for better readability
            formatted_response = f"""# Market Analysis Results

## Market Potential
Score: {response.get('market_potential', {}).get('score', 'N/A')}/10
{response.get('market_potential', {}).get('reasoning', 'No data available')}

## Competition Analysis
Saturation Level: {response.get('competition_analysis', {}).get('saturation_level', 'N/A')}
Major Competitors: {', '.join(response.get('competition_analysis', {}).get('major_competitors', ['None identified']))}

Differentiation Opportunities:
{chr(10).join('- ' + item for item in response.get('competition_analysis', {}).get('differentiation_opportunities', ['None identified']))}

## Consumer Trends
Relevant Trends:
{chr(10).join('- ' + item for item in response.get('consumer_trends', {}).get('relevant_trends', ['No trends identified']))}

Recommendations:
{chr(10).join('- ' + item for item in response.get('consumer_trends', {}).get('recommendations', ['No recommendations available']))}

## Pricing Strategy
Recommended Price Point: {response.get('pricing_strategy', {}).get('recommended_price_point', 'N/A')}
{response.get('pricing_strategy', {}).get('reasoning', 'No reasoning provided')}

## Risk Factors
{chr(10).join('- ' + item.get('factor', '') + ': ' + item.get('mitigation', '') for item in response.get('risk_factors', [{'factor': 'No risk factors identified', 'mitigation': ''}]))}
"""
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=formatted_response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = formatted_response
            
            return state
            
        def run_pdf_research(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the PDF research agent."""
            latest_message = state["messages"][-1]
            if not isinstance(latest_message, HumanMessage):
                return state
                
            query = latest_message.content
            kb_context = state["context"].get("kb_context", "")
            kg_insights = state["context"].get("kg_insights", "")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Get response from the PDF research agent
            response = self.pdf_research.run(query, kg_insights)
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            
            return state
        
        def run_domain_specialist(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the domain specialist agent."""
            routing_result = state["context"].get("routing", {})
            parameters = routing_result.get("parameters", {})
            kb_context = state["context"].get("kb_context", "")
            kg_insights = state["context"].get("kg_insights", "")
            
            # Get the latest message
            latest_message = state["messages"][-1]
            if not isinstance(latest_message, HumanMessage):
                return state
                
            query = latest_message.content
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Get response from the domain specialist agent
            response = self.domain_specialist.run(query, parameters, kb_context, kg_insights)
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            
            return state
        
        def run_basic_query(state: EnhancedAgentState) -> EnhancedAgentState:
            """Run the basic query agent."""
            latest_message = state["messages"][-1]
            if not isinstance(latest_message, HumanMessage):
                return state
                
            query = latest_message.content
            kb_context = state["context"].get("kb_context", "")
            
            # Get user memory context
            user_id = state["user"]["username"]
            user_memory = state["memory"].get(user_id, {})
            
            # Check if access was denied to another agent
            if state["access_control"].get("access_denied"):
                response = f"""I'm sorry, but you don't have access to that functionality with your current permissions.
                
Your query has been processed with limited access. Here's what I can tell you:

{self.basic_query.run(query, kb_context)}

For more detailed information, please contact your administrator to upgrade your access level."""
            else:
                response = self.basic_query.run(query, kb_context)
            
            # Add the response to messages
            state["messages"].append(AIMessage(content=response))
            
            # Store response in memory
            state["memory"][user_id]["last_response"] = response
            
            return state
        
        # Build the graph
        workflow = StateGraph(EnhancedAgentState)
        
        # Add nodes
        workflow.add_node("initialize", initialize_state)
        workflow.add_node("route_query", route_query)
        workflow.add_node("retrieve_context", retrieve_context)
        workflow.add_node("location_recommender", run_location_recommender)
        workflow.add_node("regulatory_advisor", run_regulatory_advisor)
        workflow.add_node("market_analysis", run_market_analysis)
        workflow.add_node("consumer_survey", run_consumer_survey)
        workflow.add_node("real_estate", run_real_estate)
        workflow.add_node("demographics", run_demographics)
        workflow.add_node("market_research", run_market_research)
        workflow.add_node("pdf_research", run_pdf_research)
        workflow.add_node("domain_specialist", run_domain_specialist)
        workflow.add_node("basic_query", run_basic_query)
        
        # Add edges
        workflow.add_edge("initialize", "route_query")
        workflow.add_edge("route_query", "retrieve_context")
        
        # Create a router function that returns the next agent as a string
        def router_func(state):
            return check_permissions_and_route(state)
            
        # Add conditional edges based on agent selection
        workflow.add_conditional_edges(
            "retrieve_context",
            router_func,
            {
                "location_recommender": "location_recommender",
                "regulatory_advisor": "regulatory_advisor",
                "market_analysis": "market_analysis",
                "consumer_survey": "consumer_survey",
                "real_estate": "real_estate",
                "demographics": "demographics",
                "market_research": "market_research",
                "pdf_research": "pdf_research",
                "domain_specialist": "domain_specialist",
                "basic_query": "basic_query"
            }
        )
        
        workflow.add_edge("location_recommender", END)
        workflow.add_edge("regulatory_advisor", END)
        workflow.add_edge("market_analysis", END)
        workflow.add_edge("consumer_survey", END)
        workflow.add_edge("real_estate", END)
        workflow.add_edge("demographics", END)
        workflow.add_edge("market_research", END)
        workflow.add_edge("pdf_research", END)
        workflow.add_edge("domain_specialist", END)
        workflow.add_edge("basic_query", END)
        
        # Set the entry point
        workflow.set_entry_point("initialize")
        
        # Compile the graph
        return workflow.compile()
    
    def process_message(self, user_id: str, message: BaseMessage) -> None:
        """Process a message for a user, updating memory."""
        self.memory_manager.process_message(user_id, message)
    
    def get_conversation_history(self, user_id: str, max_messages: int = 10) -> List[BaseMessage]:
        """Get conversation history for a user."""
        user_memory = self.memory_manager.get_user_memory(user_id)
        return user_memory.get_conversation_context(max_messages)
    
    def run(self, query: str, user: Dict) -> str:
        """Run the agent graph with user query and user information."""
        try:
            user_id = user["username"]
            
            # Process the new query
            self.memory_manager.process_message(user_id, HumanMessage(content=query))
            
            # Get conversation history
            messages = self.get_conversation_history(user_id)
            
            # Get user context from memory
            user_memory = self.memory_manager.get_user_memory(user_id)
            user_context = user_memory.get_user_context()
            
            # Prepare the initial state
            initial_state = {
                "messages": messages,
                "user": user,
                "context": {"user_context": user_context},
                "next_agent": None,
                "subagents": [],
                "memory": {user_id: user_context},
                "access_control": {"checked_permissions": {}, "access_denied": False}
            }
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            # Update memory with the result
            if result["messages"] and isinstance(result["messages"][-1], AIMessage):
                self.memory_manager.process_message(user_id, result["messages"][-1])
            
            # Return the latest response
            return result["messages"][-1].content
            
        except Exception as e:
            print(f"Error in enhanced orchestrator.run: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing your request: {str(e)}"
    
    def save_memory_to_disk(self, file_path: str = "memory_data.json") -> None:
        """Save memory to disk."""
        self.memory_manager.save_to_disk(file_path)
    
    def load_memory_from_disk(self, file_path: str = "memory_data.json") -> None:
        """Load memory from disk."""
        self.memory_manager.load_from_disk(file_path)
    
    def cleanup_inactive_sessions(self) -> None:
        """Clean up inactive sessions."""
        self.memory_manager.cleanup_inactive_sessions()
