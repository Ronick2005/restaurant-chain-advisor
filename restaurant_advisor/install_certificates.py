#!/usr/bin/env python
"""
SSL Certificate Installation Helper Script

This script installs the necessary SSL certificates for Python by:
1. Locating the certificates from the certifi package
2. Updating the SSL_CERT_FILE environment variable
3. Creating a script to automatically set the environment variable

Usage:
    python install_certificates.py
"""

import os
import sys
import certifi
import subprocess

def main():
    """Main function to install certificates."""
    # Get the path to the certifi CA bundle
    ca_file = certifi.where()
    print(f"Found certifi CA bundle at: {ca_file}")
    
    # Set the SSL_CERT_FILE environment variable for the current session
    os.environ["SSL_CERT_FILE"] = ca_file
    print(f"Set SSL_CERT_FILE environment variable to: {ca_file}")
    
    # Create a script to set the environment variable permanently
    script_content = f"""#!/bin/bash

# Add this to your shell profile (.bashrc, .zshrc, etc.)
export SSL_CERT_FILE="{ca_file}"
"""
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "set_ssl_cert.sh")
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(script_path, 0o755)
    print(f"Created script at {script_path}")
    
    # Display instructions
    print("\n=== INSTRUCTIONS ===")
    print("1. To apply certificates for the current session:")
    print(f"   export SSL_CERT_FILE=\"{ca_file}\"")
    print("")
    print("2. To apply certificates permanently:")
    print(f"   echo 'export SSL_CERT_FILE=\"{ca_file}\"' >> ~/.zshrc")
    print("   # or for bash:")
    print(f"   echo 'export SSL_CERT_FILE=\"{ca_file}\"' >> ~/.bashrc")
    print("")
    print("3. For the current shell session, you can also run:")
    print(f"   source {script_path}")
    
    # Test the SSL certificate
    print("\nTesting SSL certificate configuration...")
    try:
        import ssl
        import urllib.request
        
        # Try to connect to a known HTTPS site
        urllib.request.urlopen("https://www.google.com")
        print("✅ SSL verification test successful!")
    except ssl.SSLCertVerificationError:
        print("❌ SSL verification test failed. Please restart your Python session after setting the environment variable.")
    except Exception as e:
        print(f"❌ Error during SSL test: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
