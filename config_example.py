"""
Example configuration file for IT Help Desk Voice Bot
Copy this to config_local.py and update with your actual values
"""

import os

# OpenAI Configuration (Required)
OPENAI_API_KEY = "your_openai_api_key_here"

# LiveKit Configuration (Optional - defaults to local development)
LIVEKIT_URL = "ws://localhost:7880"
LIVEKIT_API_KEY = "devkey"
LIVEKIT_API_SECRET = "secret"

# Database Configuration (Optional)
DATABASE_PATH = "tickets.db"

# Set environment variables if not already set
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if not os.getenv("LIVEKIT_URL"):
    os.environ["LIVEKIT_URL"] = LIVEKIT_URL

if not os.getenv("LIVEKIT_API_KEY"):
    os.environ["LIVEKIT_API_KEY"] = LIVEKIT_API_KEY

if not os.getenv("LIVEKIT_API_SECRET"):
    os.environ["LIVEKIT_API_SECRET"] = LIVEKIT_API_SECRET
