#!/usr/bin/env python3
"""
Setup script for IT Help Desk Voice Bot
"""

import os
import sys
import subprocess
import sqlite3

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_database():
    """Initialize the database"""
    print("Setting up database...")
    try:
        from database import db
        # Database is automatically initialized when imported
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

def create_env_file():
    """Create .env file template"""
    env_content = """# IT Help Desk Voice Bot Environment Variables

# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# LiveKit Configuration (Optional - defaults to local development)
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Database Configuration (Optional)
DATABASE_PATH=tickets.db
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file template")
        print("⚠️  Please edit .env file and add your OpenAI API key")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function"""
    print("🎤 IT Help Desk Voice Bot Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run: python main.py")
    print("3. Open http://localhost:8000 in your browser")
    print("\nFor LiveKit voice functionality:")
    print("1. Install LiveKit server: https://docs.livekit.io/realtime/server/installation/")
    print("2. Start LiveKit server")
    print("3. Update LIVEKIT_* variables in .env file")

if __name__ == "__main__":
    main()
