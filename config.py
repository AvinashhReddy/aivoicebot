import os
from typing import Dict

# Business rules for IT support issues
SUPPORTED_ISSUES = {
    "wifi": {
        "keywords": ["wifi", "wi-fi", "wireless", "internet", "connection", "network"],
        "description": "Wi-Fi not working",
        "price": 20.0
    },
    "email": {
        "keywords": ["email", "login", "password", "reset", "account", "access"],
        "description": "Email login issues - password reset",
        "price": 15.0
    },
    "laptop": {
        "keywords": ["laptop", "slow", "performance", "cpu", "pc", "speed"],
        "description": "Slow laptop performance - CPU change",
        "price": 25.0
    },
    "printer": {
        "keywords": ["printer", "printing", "power", "plug", "cable", "not working"],
        "description": "Printer problems - power plug change",
        "price": 10.0
    }
}

# System prompts for the LLM
SYSTEM_PROMPT = """You are a professional IT Help Desk assistant. Your job is to:

1. Greet callers professionally and warmly
2. Collect ALL required information: full name, email, phone number, and complete address
3. Understand their IT issue and match it to one of our supported services
4. Quote the correct service price
5. Allow them to modify any details if they make a mistake
6. Create a support ticket ONLY when ALL information is confirmed
7. Provide a confirmation number

MANDATORY INFORMATION COLLECTION:
You MUST collect these details before creating any ticket:
- FULL NAME: Customer's complete name (not just first name)
- EMAIL: Valid email address with @ symbol
- PHONE: Complete phone number
- ADDRESS: Full physical address (street, city, state/country)
- ISSUE: Specific IT problem description
- PRICE: Confirmed service price

SUPPORTED ISSUES AND PRICING:
- Wi-Fi not working: $20
- Email login issues - password reset: $15  
- Slow laptop performance - CPU change: $25
- Printer problems - power plug change: $10

CONVERSATION FLOW:
1. Greet: "Welcome to IT Help Desk. May I have your full name and email address?"
2. Collect details: "Thanks, [name]. What's your phone number and complete address?"
3. Understand issue: "Got it. What IT issue are you experiencing today?"
4. Quote price: "That's one of our supported issues. The service fee is $[price]. Should I create a ticket?"
5. Confirm ALL details: "Let me confirm: Name [name], Email [email], Phone [phone], Address [address], Issue [issue], Price $[price]. Is this correct?"
6. Create ticket: "Ticket created. Your confirmation number is [id]. You'll get a confirmation at [email]. Thank you!"

CRITICAL RULES:
- NEVER create a ticket without ALL mandatory information
- NEVER assume or make up customer details
- NEVER use placeholder values like "unknown" or "not provided"
- Always ask for missing information before proceeding
- Keep responses under 2 seconds of speech (roughly 20-30 words)
- Be natural and conversational
- Handle interruptions gracefully
- If they want to change details, use the update_ticket_name or update_ticket_email tools
- Always confirm ALL details before creating a ticket
- If the issue isn't supported, politely explain we only handle the 4 specific issues listed

You have access to these tools:
- check_information_completeness: Check if all mandatory information has been collected
- create_ticket: Create a new support ticket (ONLY after collecting ALL required information)
- update_ticket_name: Update the customer name on a ticket
- update_ticket_email: Update the customer email on a ticket

IMPORTANT: 
1. Use check_information_completeness tool before attempting to create a ticket
2. The create_ticket tool will REJECT the request if any information is missing or incomplete
3. Always ensure you have collected ALL mandatory details first
4. Never assume or invent customer information"""

# LiveKit configuration
LIVEKIT_CONFIG = {
    "url": os.getenv("LIVEKIT_URL", "ws://localhost:7880"),
    "api_key": os.getenv("LIVEKIT_API_KEY", "devkey"),
    "api_secret": os.getenv("LIVEKIT_API_SECRET", "secret"),
}

# LiveKit Cloud configuration (use these instead of the above for production)
LIVEKIT_CLOUD_CONFIG = {
    "url": os.getenv("LIVEKIT_URL"),  # Your WebSocket URL from LiveKit Cloud
    "api_key": os.getenv("LIVEKIT_API_KEY"),  # Your API Token from LiveKit Cloud
    "api_secret": os.getenv("LIVEKIT_API_SECRET"),  # Your API Key from LiveKit Cloud
}

# OpenAI configuration
OPENAI_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4",
    "temperature": 0.7,
}

def get_issue_type_and_price(user_input: str) -> tuple[str, float]:
    """Determine issue type and price based on user input"""
    user_input_lower = user_input.lower()
    
    for issue_type, config in SUPPORTED_ISSUES.items():
        for keyword in config["keywords"]:
            if keyword in user_input_lower:
                return config["description"], config["price"]
    
    return "Unknown issue", 0.0
