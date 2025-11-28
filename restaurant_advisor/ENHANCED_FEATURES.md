## Enhanced Knowledge Extraction Features

This update adds advanced capabilities to extract more value from both the MongoDB knowledge base and Neo4j knowledge graph:

### Enhanced MongoDB Knowledge Base

- **Advanced Hybrid Search**: Improved hybrid search with configurable weighting between semantic and keyword results
- **Metadata Filtering**: Enhanced filtering capabilities for more targeted searches
- **Topic Analysis**: Extract common topics from document metadata to identify knowledge clusters
- **City-Specific Insights**: Targeted retrieval of information about specific cities
- **Recent Market Trends**: Extract insights from the most recent documents to identify market trends

### Enhanced Neo4j Knowledge Graph

- **Detailed Location Analysis**: Get comprehensive insights about locations with neighborhood data
- **Cross-City Comparison**: Find similar locations across different cities
- **Cuisine Preference Analytics**: Analyze cuisine preferences and popularity by location

### Cross-Database Integration

A new `CrossDBInsights` integration layer combines structured and unstructured data:

- **Comprehensive City Insights**: Combines location data from Neo4j with market insights from MongoDB
- **Restaurant Opportunity Scoring**: Calculates an opportunity score for restaurant concepts based on:
  - Location score (foot traffic, accessibility)
  - Uniqueness score (concept differentiation)
  - Market sentiment (from unstructured data)
  - Regulatory ease (complexity of regulations)
- **Market Gap Analysis**: Identifies potential cuisine gaps in target markets

### Enhanced Restaurant Advisor Agent

The new `EnhancedRestaurantAdvisorAgent` leverages these capabilities to provide:

- More comprehensive recommendations
- Data-driven opportunity scoring
- Specific actionable insights
- Market gap identification
- Regulatory awareness

## Using the Enhanced Features

Try the example scripts in the `examples` directory:

```bash
# Demonstrate enhanced knowledge base features
python examples/enhanced_kb_demo.py

# Interactive demo of the enhanced advisor agent
python examples/enhanced_advisor_demo.py
```
