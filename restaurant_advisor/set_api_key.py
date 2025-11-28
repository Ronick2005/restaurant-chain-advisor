"""
Script to set the Gemini API key for the restaurant advisor system.
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv, set_key

def set_gemini_api_key():
    """Set the Gemini API key in the .env file."""
    # Find the .env file
    dotenv_path = find_dotenv()
    if not dotenv_path:
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Load existing environment variables
    load_dotenv(dotenv_path)
    
    # Check if GEMINI_API_KEY is already set
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("\n======= Gemini API Key Setup =======")
        print("The Gemini API key is not set in your environment.")
        print("You'll need a Gemini API key to use the restaurant advisor system with real AI.")
        print("Get your API key from: https://ai.google.dev/")
        
        api_key = input("\nEnter your Gemini API key: ").strip()
        
        if api_key:
            # Update the .env file
            set_key(dotenv_path, "GEMINI_API_KEY", api_key)
            os.environ["GEMINI_API_KEY"] = api_key
            print("\nAPI key set successfully!")
            return True
        else:
            print("\nNo API key provided. The system will use mock responses.")
            return False
    else:
        print("\nGemini API key is already set.")
        return True

if __name__ == "__main__":
    set_gemini_api_key()
