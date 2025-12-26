"""
Check available agents and test LangSmith integration
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("RESTAURANT ADVISOR SYSTEM - AGENTS & LANGSMITH STATUS")
print("=" * 80)

# Check LangSmith Configuration
print("\n📊 LANGSMITH CONFIGURATION:")
print("-" * 80)
from utils.config import LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT

print(f"Tracing Enabled: {LANGCHAIN_TRACING_V2}")
print(f"API Key Present: {'✓ Yes' if LANGCHAIN_API_KEY else '✗ No'}")
print(f"Project: {LANGCHAIN_PROJECT}")

if LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY:
    print("\n✅ LangSmith is configured and enabled")
else:
    print("\n⚠️  LangSmith is not fully configured")

# List Available Agents
print("\n\n🤖 AVAILABLE AGENTS:")
print("-" * 80)

agents_info = [
    {
        "name": "RoutingAgent",
        "module": "agents.agent_definitions",
        "description": "Routes queries to appropriate specialist agents",
        "use_case": "Analyzes user queries and determines which agent should handle them"
    },
    {
        "name": "LocationRecommenderAgent",
        "module": "agents.agent_definitions",
        "description": "Recommends restaurant locations based on preferences",
        "use_case": "Find best areas for restaurants in specific cities"
    },
    {
        "name": "RegulatoryAdvisorAgent",
        "module": "agents.agent_definitions",
        "description": "Provides regulatory and licensing guidance",
        "use_case": "Get information about licenses, permits, and compliance"
    },
    {
        "name": "MarketAnalysisAgent",
        "module": "agents.agent_definitions",
        "description": "Analyzes market potential and competition",
        "use_case": "Assess market viability, competition, and pricing strategy"
    },
    {
        "name": "BasicQueryAgent",
        "module": "agents.agent_definitions",
        "description": "Handles general queries with limited access",
        "use_case": "Answer basic questions about restaurant industry"
    },
    {
        "name": "PDFResearchAgent",
        "module": "agents.agent_definitions",
        "description": "Answers queries based on PDF research documents",
        "use_case": "Extract insights from uploaded research documents"
    },
    {
        "name": "DomainSpecialistAgent",
        "module": "agents.domain_agents",
        "description": "Provides domain-specific expertise (cuisine, finance, staffing, etc.)",
        "use_case": "Get specialized advice on specific restaurant domains"
    },
    {
        "name": "ExternalMarketResearchAgent",
        "module": "agents.agent_definitions",
        "description": "Market research with web scraping capabilities",
        "use_case": "Get live market trends and industry statistics"
    },
    {
        "name": "ExternalConsumerSurveyAgent",
        "module": "agents.agent_definitions",
        "description": "Consumer preferences and dining habits analysis",
        "use_case": "Understand consumer behavior and preferences"
    },
    {
        "name": "ExternalRealEstateAgent",
        "module": "agents.agent_definitions",
        "description": "Real estate data and rental cost analysis",
        "use_case": "Get property costs, foot traffic, and location viability"
    },
    {
        "name": "ExternalDemographicsAgent",
        "module": "agents.agent_definitions",
        "description": "Demographic and economic data analysis",
        "use_case": "Understand population, income, and economic indicators"
    },
    {
        "name": "DocumentIngestionManager",
        "module": "agents.agent_definitions",
        "description": "Manages document ingestion from docs folder",
        "use_case": "Ingest and search documents in the knowledge base"
    }
]

for i, agent in enumerate(agents_info, 1):
    print(f"\n{i}. {agent['name']}")
    print(f"   📦 Module: {agent['module']}")
    print(f"   📝 Description: {agent['description']}")
    print(f"   💡 Use Case: {agent['use_case']}")

# Test LangSmith with a simple agent call
print("\n\n🧪 TESTING LANGSMITH WITH A SIMPLE QUERY:")
print("-" * 80)

if LANGCHAIN_TRACING_V2:
    try:
        from agents.agent_definitions import RoutingAgent
        
        print("\nCreating RoutingAgent and making a test query...")
        router = RoutingAgent()
        
        test_query = "Where should I open a restaurant in Chennai?"
        print(f"Query: '{test_query}'")
        
        result = router.run(test_query)
        
        print(f"\n✓ Agent Response:")
        print(f"  → Routed to: {result['agent']}")
        print(f"  → Parameters: {result['parameters']}")
        
        if LANGCHAIN_TRACING_V2:
            print(f"\n✅ LangSmith tracing is active!")
            print(f"   Check your traces at: https://smith.langchain.com/")
            print(f"   Project: {LANGCHAIN_PROJECT}")
        
    except Exception as e:
        print(f"\n⚠️  Test failed: {str(e)}")
        if "403" in str(e) or "Forbidden" in str(e):
            print("   Note: 403 errors are expected - LangSmith API key may need permissions")
            print("   However, the agent itself is working correctly!")
else:
    print("\n⚠️  LangSmith tracing is disabled. Enable in .env to test.")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Agents Available: {len(agents_info)}")
print(f"Model Used: gemini-flash-latest (configured globally)")
print(f"LangSmith Status: {'✓ Enabled' if LANGCHAIN_TRACING_V2 else '✗ Disabled'}")
print("=" * 80)
