# Gemini Model Configuration

## Current Model: gemini-flash-latest

This project is configured to use **gemini-flash-latest** as the default Gemini model for all AI agents.

## Why gemini-flash-latest?

- **Fast response times** - Optimized for low latency
- **Cost-effective** - Lower pricing compared to pro models
- **Good performance** - Suitable for most restaurant advisory tasks
- **Latest features** - Access to newest Gemini capabilities

## How It Works

### Configuration Hierarchy

1. **Environment Variable** (`.env` file):
   ```
   GEMINI_MODEL="gemini-flash-latest"
   ```

2. **Config Module** (`utils/config.py`):
   ```python
   GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
   ```

3. **All Agents** automatically use this configuration through `get_gemini_model()`

### Changing the Model

To use a different Gemini model across the entire project:

**Option 1: Update .env file (Recommended)**
```bash
GEMINI_MODEL="gemini-1.5-pro"  # or any other Gemini model
```

**Option 2: Set environment variable**
```bash
# Windows PowerShell
$env:GEMINI_MODEL="gemini-1.5-pro"

# Linux/Mac
export GEMINI_MODEL="gemini-1.5-pro"
```

**Option 3: Override for specific agent**
```python
# Use a different model for one agent only
agent = LocationRecommenderAgent(model_name="gemini-1.5-pro")
```

## Available Gemini Models

- `gemini-flash-latest` - Fast, cost-effective (current default)
- `gemini-1.5-flash` - Stable flash version
- `gemini-1.5-pro` - Higher quality, slower, more expensive
- `gemini-pro-latest` - Latest pro version

## Updated Files

All agents have been updated to use the centralized configuration:

### Core Agent Files
- ✅ `agents/agent_definitions.py` - All base agents
- ✅ `agents/domain_agents.py` - Domain specialist agents
- ✅ `agents/real_estate_agent.py` - Real estate agent
- ✅ `agents/market_research_agent.py` - Market research agent
- ✅ `agents/demographics_agent.py` - Demographics agent
- ✅ `agents/consumer_survey_agent.py` - Consumer survey agent

### Configuration Files
- ✅ `utils/config.py` - Added GEMINI_MODEL constant
- ✅ `.env` - Added GEMINI_MODEL environment variable

### Examples
- ✅ `examples/enhanced_advisor_demo.py` - Uses gemini-flash-latest

## Response Format Handling

All agents now include the `extract_text_from_response()` helper function that handles different response formats from Gemini models:

```python
def extract_text_from_response(response) -> str:
    """Extract text content from various Gemini response formats."""
    # Handles both:
    # - Old format: simple string
    # - New format: [{'type': 'text', 'text': '...', 'extras': {...}}]
```

This ensures compatibility regardless of which Gemini model you choose.

## Testing

Run the test suite to verify all agents work correctly:

```bash
python test_agents.py
```

This will test:
- ✅ Response format extraction
- ✅ RoutingAgent
- ✅ LocationRecommenderAgent
- ✅ RegulatoryAdvisorAgent
- ✅ MarketAnalysisAgent
- ✅ BasicQueryAgent
- ✅ DomainSpecialistAgent

## Migration History

- **v1.0**: Originally used `gemini-pro-latest` and `gemini-1.5-flash`
- **v2.0**: Migrated to `gemini-flash-latest` (current)
- All agents updated with response format handling
- Centralized configuration for easy model switching

## Notes

- The model is configured globally but can be overridden per agent if needed
- All agents use the same `extract_text_from_response()` helper for consistency
- LangSmith tracing works with all Gemini models
- Rate limits apply based on your Gemini API tier
