#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up the development environment for Firebase Functions.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None


def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up Firebase Functions development environment...\n")
    
    # Check if we're in the functions directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the functions directory")
        sys.exit(1)
    
    # Install production requirements
    run_command("pip install -r requirements.txt", "Installing production requirements")
    
    # Install development requirements
    run_command("pip install -r requirements-dev.txt", "Installing development requirements")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path("env.example").exists():
            run_command("cp env.example .env", "Creating .env file from template")
            print("📝 Please edit .env file with your actual API keys")
        else:
            print("⚠️  env.example not found, please create .env file manually")
    else:
        print("✅ .env file already exists")
    
    # Set up Jupyter kernel
    run_command("python -m ipykernel install --user --name firebase-functions", 
                "Setting up Jupyter kernel")
    
    print("\n🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start Jupyter Lab: jupyter lab")
    print("3. Open experiments/api_testing.ipynb to test APIs")
    print("4. Deploy functions: firebase deploy --only functions")


def test_apis():
    """Test API connections"""
    print("🧪 Testing API connections...\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test each API
    apis = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Apollo': os.getenv('APOLLO_API_KEY'),
        'Perplexity': os.getenv('PERPLEXITY_API_KEY'),
        'Apifi': os.getenv('APIFI_API_KEY')
    }
    
    for api_name, api_key in apis.items():
        if api_key:
            print(f"✅ {api_name} API key configured")
        else:
            print(f"❌ {api_name} API key missing")
    
    print("\n💡 Use experiments/api_testing.ipynb to test actual API calls")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_apis()
    else:
        setup_environment() 