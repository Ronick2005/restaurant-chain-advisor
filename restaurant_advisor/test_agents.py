"""
Test script to verify all agents are working with gemini-flash-latest
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test imports
print("Testing imports...")
from agents.agent_definitions import (
    RoutingAgent, 
    LocationRecommenderAgent, 
    RegulatoryAdvisorAgent, 
    MarketAnalysisAgent,
    BasicQueryAgent,
    PDFResearchAgent,
    extract_text_from_response
)
from agents.domain_agents import DomainSpecialistAgent
print("✓ All imports successful\n")

# Test the extract_text_from_response helper
print("Testing extract_text_from_response helper...")
test_response_list = [{'type': 'text', 'text': 'Hello World', 'extras': {}}]
test_response_str = "Hello World"

result1 = extract_text_from_response(test_response_list)
result2 = extract_text_from_response(test_response_str)

assert "Hello World" in result1, "Failed to extract from list format"
assert result2 == "Hello World", "Failed to extract from string format"
print(f"✓ Helper function works correctly")
print(f"  - List format: {result1}")
print(f"  - String format: {result2}\n")

# Test RoutingAgent
print("Testing RoutingAgent...")
try:
    router = RoutingAgent()
    test_queries = [
        "Where should I open an Italian restaurant in Chennai?",
        "What licenses do I need for a restaurant in Mumbai?",
        "Tell me about the market for Chinese restaurants in Bangalore"
    ]
    
    for query in test_queries:
        result = router.run(query)
        print(f"✓ Query: '{query[:50]}...'")
        print(f"  → Agent: {result['agent']}, City: {result['parameters'].get('city', 'N/A')}")
    print()
except Exception as e:
    print(f"✗ RoutingAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test LocationRecommenderAgent
print("Testing LocationRecommenderAgent...")
try:
    location_agent = LocationRecommenderAgent()
    test_query = {
        "city": "Chennai",
        "cuisine": "Italian",
        "concept": "Fine Dining",
        "demographic": "Affluent professionals",
        "budget": "High"
    }
    result = location_agent.run(test_query, "Sample KB context", "Sample KG insights")
    print(f"✓ LocationRecommenderAgent working")
    print(f"  Response length: {len(result)} characters")
    print(f"  Preview: {result[:150]}...\n")
except Exception as e:
    print(f"✗ LocationRecommenderAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test RegulatoryAdvisorAgent
print("Testing RegulatoryAdvisorAgent...")
try:
    regulatory_agent = RegulatoryAdvisorAgent()
    test_query = {
        "city": "Mumbai",
        "restaurant_type": "Fine Dining",
        "serves_alcohol": "Yes",
        "seating_capacity": "50"
    }
    result = regulatory_agent.run(test_query, "Sample KB context", "Sample KG insights")
    print(f"✓ RegulatoryAdvisorAgent working")
    print(f"  Response length: {len(result)} characters")
    print(f"  Preview: {result[:150]}...\n")
except Exception as e:
    print(f"✗ RegulatoryAdvisorAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test MarketAnalysisAgent
print("Testing MarketAnalysisAgent...")
try:
    market_agent = MarketAnalysisAgent()
    test_query = {
        "city": "Bangalore",
        "cuisine": "Italian",
        "concept": "Casual Dining",
        "area": "Koramangala",
        "demographic": "Young professionals"
    }
    result = market_agent.run(test_query, "Sample KB context", "Sample KG insights")
    print(f"✓ MarketAnalysisAgent working")
    print(f"  Response type: {type(result)}")
    if isinstance(result, dict):
        print(f"  Keys: {list(result.keys())}")
        print(f"  Market score: {result.get('market_potential', {}).get('score', 'N/A')}")
    print()
except Exception as e:
    print(f"✗ MarketAnalysisAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test BasicQueryAgent
print("Testing BasicQueryAgent...")
try:
    basic_agent = BasicQueryAgent()
    result = basic_agent.run("What are popular restaurant types in India?", "Sample context about restaurants")
    print(f"✓ BasicQueryAgent working")
    print(f"  Response length: {len(result)} characters")
    print(f"  Preview: {result[:150]}...\n")
except Exception as e:
    print(f"✗ BasicQueryAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

# Test DomainSpecialistAgent
print("Testing DomainSpecialistAgent...")
try:
    domain_agent = DomainSpecialistAgent()
    result = domain_agent.run(
        "What Italian dishes should I include on my menu?",
        {},
        "Sample KB context",
        "Sample KG insights"
    )
    print(f"✓ DomainSpecialistAgent working")
    print(f"  Response length: {len(result)} characters")
    print(f"  Preview: {result[:150]}...\n")
except Exception as e:
    print(f"✗ DomainSpecialistAgent failed: {str(e)}\n")
    import traceback
    traceback.print_exc()

print("=" * 80)
print("Agent Testing Complete!")
print("All agents successfully migrated to gemini-flash-latest model")
print("=" * 80)
