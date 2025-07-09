#!/usr/bin/env python3
"""
Sample Python script for Azure Content Understanding data extraction.
This script demonstrates basic setup and can be expanded for your specific use case.
"""

import os
from dotenv import load_dotenv

def main():
    """Main function to demonstrate the Python environment setup."""
    # Load environment variables
    load_dotenv()

    print("🐍 Python Development Container is ready!")
    print("📊 Azure Content Understanding Data Extraction Project")
    print("-" * 50)

    # Check if Azure credentials are configured
    if os.getenv("AZURE_CLIENT_ID"):
        print("✅ Azure credentials found in environment")
    else:
        print("⚠️  Azure credentials not found - please configure in .env file")

    print("\n🚀 Ready to start developing!")
    print("Next steps:")
    print("1. Configure your Azure credentials in a .env file")
    print("2. Install additional packages as needed")
    print("3. Start building your data extraction pipeline")

if __name__ == "__main__":
    main()
