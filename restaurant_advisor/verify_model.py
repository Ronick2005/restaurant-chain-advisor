"""
Quick verification script to confirm gemini-flash-latest is being used
"""
from utils.config import GEMINI_MODEL
from agents.agent_definitions import get_gemini_model, RoutingAgent

print("=" * 80)
print("GEMINI MODEL CONFIGURATION VERIFICATION")
print("=" * 80)

# Check config
print(f"\n✓ Configuration: GEMINI_MODEL = '{GEMINI_MODEL}'")

# Check get_gemini_model function
model = get_gemini_model()
print(f"✓ get_gemini_model() creates: {model.model}")

# Check agent initialization
agent = RoutingAgent()
print(f"✓ RoutingAgent uses: {agent.model.model}")

# Verify all match (model may have 'models/' prefix)
expected_model = GEMINI_MODEL if GEMINI_MODEL.startswith("models/") else f"models/{GEMINI_MODEL}"
if expected_model in model.model and expected_model in agent.model.model:
    print("\n" + "=" * 80)
    print(f"✅ SUCCESS: All components using '{GEMINI_MODEL}'")
    print("=" * 80)
else:
    print("\n❌ ERROR: Model mismatch detected!")
    
print(f"\nTo change model: Update GEMINI_MODEL in .env file")
print(f"Current model will be used for all agents unless overridden")
