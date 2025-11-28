"""
MongoDB connection test utility
This script helps diagnose MongoDB connection issues.
"""

import os
import sys
import pymongo
from pymongo import MongoClient

def test_mongodb_connection(uri=None, disable_cert_verification=True):
    """Test connection to MongoDB Atlas."""
    if not uri:
        # Try to get from environment
        uri = os.getenv("MONGODB_URI")
        if not uri:
            print("No MongoDB URI provided. Please set MONGODB_URI environment variable or pass as argument.")
            return False
    
    print(f"Attempting to connect to MongoDB at {uri}")
    
    try:
        # Try connection with or without cert verification
        client = MongoClient(uri, tlsAllowInvalidCertificates=disable_cert_verification, serverSelectionTimeoutMS=5000)
        
        # Force connection to verify it works
        db_names = client.list_database_names()
        print(f"Connection successful! Available databases: {db_names}")
        
        return True
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print("Connection failed with ServerSelectionTimeoutError:")
        print(f"  {str(e)}")
        
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print("\nSSL Certificate verification failed. This is often caused by:")
            print("1. Missing or outdated root certificates on your system")
            print("2. A proxy or firewall interfering with the connection")
            print("\nSolutions:")
            print("- Install certificates package: pip install certifi")
            print("- Run your Python's certificate installer if available")
            print("- Add tlsAllowInvalidCertificates=True to your connection string")
            print("- Check if your network/proxy is interfering with SSL connections")
        
        return False
    except Exception as e:
        print(f"Connection failed with unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    
    # Try with certificate verification first
    print("Testing MongoDB connection with certificate verification...")
    if not test_mongodb_connection(uri, disable_cert_verification=False):
        print("\nTrying again with certificate verification disabled...")
        if test_mongodb_connection(uri, disable_cert_verification=True):
            print("\nSuccess with certificate verification disabled!")
            print("The system will work with tlsAllowInvalidCertificates=True,")
            print("but consider fixing your certificate store for better security.")
