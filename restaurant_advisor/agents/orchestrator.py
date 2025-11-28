from typing import Dict, List, Any, Optional, Literal, TypedDict
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
    PDFResearchAgent
)
from kb.mongodb_kb import MongoKnowledgeBase
from kg.neo4j_kg import Neo4jKnowledgeGraph
from utils.auth import has_agent_access

class AgentState(TypedDict):
    """Type definition for the state in the agent graph."""
    messages: List[BaseMessage]
    user: Dict
    context: Dict
    next_agent: Optional[str]

def create_agent_graph(kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
    """Create the agent graph for orchestrating the multi-agent system."""
    
    # Initialize agents
    router = RoutingAgent()
    location_recommender = LocationRecommenderAgent()
    regulatory_advisor = RegulatoryAdvisorAgent()
    market_analysis = MarketAnalysisAgent()
    pdf_research = PDFResearchAgent()
    basic_query = BasicQueryAgent()
    
    # Define the workflow nodes
    def route_query(state: AgentState) -> AgentState:
        """Route the user's query to the appropriate agent."""
        # Get the latest message
        latest_message = state["messages"][-1]
        if not isinstance(latest_message, HumanMessage):
            return state
        
        # Route the query
        query = latest_message.content
        result = router.run(query)
        
        # Store routing result
        state["context"]["routing"] = result
        state["next_agent"] = result["agent"]
        
        return state
    
    def check_permissions_and_route(state: AgentState) -> str:
        """Check if the user has access to the required agent and route accordingly."""
        next_agent = state["next_agent"]
        user = state["user"]
        
        if has_agent_access(user, next_agent):
            return next_agent
        else:
            # Fallback to basic query if no access
            state["context"]["access_denied"] = True
            state["next_agent"] = "basic_query"
            return "basic_query"
    
    def retrieve_context(state: AgentState) -> AgentState:
        """Retrieve relevant context from knowledge base and knowledge graph."""
        routing_result = state["context"].get("routing", {})
        agent_name = state["next_agent"]
        parameters = routing_result.get("parameters", {})
        
        # Initialize context containers
        kb_context = []
        kg_insights = []
        
        # Get context based on the agent type
        if agent_name == "location_recommender":
            city = parameters.get("city", "")
            cuisine = parameters.get("cuisine", "")
            concept = parameters.get("concept", "")
            demographic = parameters.get("demographic", "")
            
            # Get relevant documents from knowledge base
            if city:
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
                kb_docs = kb.hybrid_search(
                    query, 
                    user_filter={"metadata.type": {"$in": ["real_estate", "demographics", "food_consumption"]}}
                )
                kb_context = [doc.page_content for doc in kb_docs]
            
            # Get insights from knowledge graph
            if city and kg:
                # Get detailed location recommendations
                locations = kg.recommend_locations(city, cuisine_type=cuisine)
                
                # Format location insights with more details
                kg_insights = []
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
            
            # Get relevant documents from knowledge base
            if city:
                # Create a more specific query
                query_parts = [f"restaurant regulations in {city}"]
                if restaurant_type:
                    query_parts.append(f"{restaurant_type}")
                if serves_alcohol.lower() == "yes":
                    query_parts.append("liquor license alcohol serving requirements")
                
                query = " ".join(query_parts) + " licensing permits requirements"
                
                kb_docs = kb.hybrid_search(
                    query, 
                    user_filter={"metadata.type": {"$in": ["regulation", "food_consumption"]}}
                )
                kb_context = [doc.page_content for doc in kb_docs]
            
            # Get insights from knowledge graph with detailed formatting
            if city and kg:
                regulations = kg.get_regulatory_info(city)
                kg_insights = []
                
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
            
            # Get relevant documents from knowledge base
            if city:
                # Create a more specific query
                query_parts = [f"restaurant market analysis in {city}"]
                if cuisine:
                    query_parts.append(f"{cuisine} cuisine")
                if concept:
                    query_parts.append(f"{concept} concept")
                if area:
                    query_parts.append(f"{area} area")
                
                query = " ".join(query_parts) + " consumer trends competition demographics food preferences"
                
                kb_docs = kb.hybrid_search(
                    query, 
                    user_filter={"metadata.type": {"$in": ["food_consumption", "demographics", "real_estate"]}}
                )
                kb_context = [doc.page_content for doc in kb_docs]
                
            # Get insights from knowledge graph
            if city and kg:
                # Get cuisine preferences for the city
                cuisine_preferences = kg.get_cuisine_preferences(city)
                
                # Get location demographics
                locations = []
                if area:
                    # Use get_detailed_location_info which accepts city and area parameters
                    locations = kg.get_detailed_location_info(city, area)
                else:
                    locations = kg.recommend_locations(city)[:3]
                
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
            kb_docs = kb.hybrid_search(
                query,
                user_filter={"metadata.type": {"$in": ["research", "food_consumption", "demographics", "real_estate"]}},
                k=8  # Get more documents for research queries
            )
            kb_context = [doc.page_content for doc in kb_docs]
            
            # If a city was mentioned, get relevant knowledge graph insights
            if city and kg:
                # Get city-specific insights from the knowledge graph
                regulations = kg.get_regulatory_info(city)
                cuisine_preferences = kg.get_cuisine_preferences(city)
                
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
            
            else:
                # If no city specified, provide general research insights
                kg_insights = [
                    "=== General Research Insights ===",
                    "The knowledge graph contains nationwide restaurant industry data across multiple cities.",
                    "Data includes regulatory frameworks, consumer preferences, and market trends.",
                    "For city-specific insights, please specify a city in your query."
                ]
                
        else:  # basic_query
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
            
            # Perform knowledge base search
            kb_docs = kb.hybrid_search(query, k=5)
            kb_context = [doc.page_content for doc in kb_docs]
            
            # If a city was mentioned, get some basic knowledge graph insights
            if city and kg:
                # Get some basic city information
                regulations = kg.get_regulatory_info(city)
                locations = kg.recommend_locations(city)
                cuisine_preferences = kg.get_cuisine_preferences(city)
                
                # Format basic insights
                kg_insights = [
                    f"City: {city}",
                    f"Number of regulations: {len(regulations)}",
                    f"Top locations: {', '.join([loc.get('area', '') for loc in locations])}",
                    f"Popular cuisines: {', '.join([pref.get('cuisine_type', '') for pref in cuisine_preferences[:3]])}"
                ]
        
        # Store retrieved context, ensuring not to exceed token limits
        state["context"]["kb_context"] = "\n\n".join(kb_context[:5])  # Include more context
        state["context"]["kg_insights"] = "\n\n".join(kg_insights[:8])  # Include more insights
        
        return state
    
    def run_location_recommender(state: AgentState) -> AgentState:
        """Run the location recommender agent."""
        routing_result = state["context"].get("routing", {})
        parameters = routing_result.get("parameters", {})
        kb_context = state["context"].get("kb_context", "")
        kg_insights = state["context"].get("kg_insights", "")
        
        response = location_recommender.run(parameters, kb_context, kg_insights)
        
        # Add the response to messages
        state["messages"].append(AIMessage(content=response))
        return state
    
    def run_regulatory_advisor(state: AgentState) -> AgentState:
        """Run the regulatory advisor agent."""
        routing_result = state["context"].get("routing", {})
        parameters = routing_result.get("parameters", {})
        kb_context = state["context"].get("kb_context", "")
        kg_insights = state["context"].get("kg_insights", "")
        
        response = regulatory_advisor.run(parameters, kb_context, kg_insights)
        
        # Add the response to messages
        state["messages"].append(AIMessage(content=response))
        return state
    
    def run_market_analysis(state: AgentState) -> AgentState:
        """Run the market analysis agent."""
        routing_result = state["context"].get("routing", {})
        parameters = routing_result.get("parameters", {})
        kb_context = state["context"].get("kb_context", "")
        kg_insights = state["context"].get("kg_insights", "")
        
        response = market_analysis.run(parameters, kb_context, kg_insights)
        
        # Format the JSON response for better readability
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
        return state
        
    def run_pdf_research(state: AgentState) -> AgentState:
        """Run the PDF research agent."""
        latest_message = state["messages"][-1]
        if not isinstance(latest_message, HumanMessage):
            return state
            
        query = latest_message.content
        kb_context = state["context"].get("kb_context", "")
        kg_insights = state["context"].get("kg_insights", "")
        
        # Get response from the PDF research agent
        response = pdf_research.run(query, kg_insights)
        
        # Add the response to messages
        state["messages"].append(AIMessage(content=response))
        return state
    
    def run_basic_query(state: AgentState) -> AgentState:
        """Run the basic query agent."""
        latest_message = state["messages"][-1]
        if not isinstance(latest_message, HumanMessage):
            return state
            
        query = latest_message.content
        kb_context = state["context"].get("kb_context", "")
        
        # Check if access was denied to another agent
        if state["context"].get("access_denied"):
            response = f"""I'm sorry, but you don't have access to that functionality with your current permissions.
            
Your query has been processed with limited access. Here's what I can tell you:

{basic_query.run(query, kb_context)}

For more detailed information, please contact your administrator to upgrade your access level."""
        else:
            response = basic_query.run(query, kb_context)
        
        # Add the response to messages
        state["messages"].append(AIMessage(content=response))
        return state
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("route_query", route_query)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("location_recommender", run_location_recommender)
    workflow.add_node("regulatory_advisor", run_regulatory_advisor)
    workflow.add_node("market_analysis", run_market_analysis)
    workflow.add_node("pdf_research", run_pdf_research)
    workflow.add_node("basic_query", run_basic_query)
    
    # Add edges
    workflow.add_edge("route_query", "retrieve_context")
    
    # Create a router function that returns the next agent as a string
    def router_func(state):
        return check_permissions_and_route(state)
        
    # Add conditional edges
    workflow.add_conditional_edges(
        "retrieve_context",
        router_func,
        {
            "location_recommender": "location_recommender",
            "regulatory_advisor": "regulatory_advisor",
            "market_analysis": "market_analysis",
            "pdf_research": "pdf_research",
            "basic_query": "basic_query"
        }
    )
    workflow.add_edge("location_recommender", END)
    workflow.add_edge("regulatory_advisor", END)
    workflow.add_edge("market_analysis", END)
    workflow.add_edge("pdf_research", END)
    workflow.add_edge("basic_query", END)
    
    # Set the entry point
    workflow.set_entry_point("route_query")
    
    # Compile the graph
    return workflow.compile()

class AgentOrchestrator:
    """Orchestrates the multi-agent system with memory management."""
    
    def __init__(self, kb: MongoKnowledgeBase, kg: Neo4jKnowledgeGraph):
        self.kb = kb
        self.kg = kg
        self.graph = create_agent_graph(kb, kg)
        
        # Set up memory management
        self.memory = {}
    
    def get_user_memory(self, user_id: str) -> List[BaseMessage]:
        """Get user-specific memory."""
        if user_id not in self.memory:
            self.memory[user_id] = [
                SystemMessage(content="You are a restaurant advisor system that helps users set up restaurant chains across India.")
            ]
        return self.memory[user_id]
    
    def run(self, query: str, user: Dict) -> str:
        """Run the agent graph with user query and user information."""
        try:
            # Get user memory
            messages = self.get_user_memory(user["username"])
            
            # Add the new query to memory
            messages.append(HumanMessage(content=query))
            
            # Prepare the initial state
            initial_state = {
                "messages": messages.copy(),  # Make a copy to avoid modifying the original
                "user": user,
                "context": {},
                "next_agent": None
            }
            
            print("Initial state prepared")
            
            # Run the graph
            print("Running graph...")
            result = self.graph.invoke(initial_state)
            print("Graph execution completed")
            
            # Update user memory with the new conversation
            self.memory[user["username"]] = result["messages"]
            
            # Return the latest response
            return result["messages"][-1].content
        except Exception as e:
            print(f"Error in orchestrator.run: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error processing your request: {str(e)}"
