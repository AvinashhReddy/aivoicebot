"""
IT Help Desk Voice Bot Agent

This module contains the main voice assistant agent that handles
conversations with customers and manages the ticket creation process.
"""

import logging
from livekit.agents import llm
from livekit.agents.voice import Agent
from config import SYSTEM_PROMPT, get_issue_type_and_price
from tools import ALL_TOOLS, bot_state

logger = logging.getLogger(__name__)


class ITHelpDeskBot(Agent):
    """
    IT Help Desk Voice Assistant Agent
    
    This agent handles customer conversations, collects information,
    and creates support tickets for IT issues.
    """
    
    def __init__(self):
        super().__init__(
            instructions=SYSTEM_PROMPT,
            tools=ALL_TOOLS
        )
        
        # Reset bot state for new session
        global bot_state
        bot_state.__init__()  # Reset to initial state
    
    async def on_start(self):
        """Called when the agent starts"""
        logger.info("🤖 IT Help Desk Voice Bot started")
        logger.info("🔊 Saying welcome message...")
        await self.say("Welcome to IT Help Desk. May I have your name and email?")
        logger.info("✅ Welcome message sent")
    
    async def on_user_speech_started(self):
        """Called when user starts speaking"""
        logger.info("🎤 User speech detected - listening...")
    
    async def on_user_speech_stopped(self):
        """Called when user stops speaking"""
        logger.info("🔇 User speech ended - processing...")
    
    async def on_user_turn_completed(self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage) -> None:
        """Handle user turn completion and update conversation state"""
        # Extract text content from message (handle both string and list formats)
        if isinstance(new_message.content, str):
            user_text = new_message.content
        elif isinstance(new_message.content, list):
            # Extract text from content parts
            user_text = ""
            for part in new_message.content:
                if hasattr(part, 'text'):
                    user_text += part.text + " "
                elif isinstance(part, str):
                    user_text += part + " "
            user_text = user_text.strip()
        else:
            user_text = str(new_message.content)
        
        logger.info(f"User said: {user_text}")
        
        # Extract and store customer information from the conversation
        self._extract_customer_info(user_text)
        
        # Log current collected information for debugging
        logger.info(f"Current collected info: {bot_state.collected_info}")
        logger.info(f"Conversation stage: {bot_state.conversation_stage}")
    
    def _extract_customer_info(self, user_text: str):
        """Extract customer information from user input and store in bot state"""
        text_lower = user_text.lower()
        
        # Extract email if present
        if "@" in user_text and not bot_state.collected_info.get("email"):
            import re
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_text)
            if email_match:
                bot_state.collected_info["email"] = email_match.group()
                logger.info(f"Extracted email: {bot_state.collected_info['email']}")
        
        # Extract phone number if present
        if any(keyword in text_lower for keyword in ["phone", "number", "call", "reach"]) and not bot_state.collected_info.get("phone"):
            import re
            # Look for phone number patterns
            phone_match = re.search(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b', user_text)
            if phone_match:
                bot_state.collected_info["phone"] = phone_match.group()
                logger.info(f"Extracted phone: {bot_state.collected_info['phone']}")
        
        # Extract name (look for patterns like "my name is", "I'm", etc.)
        if any(keyword in text_lower for keyword in ["name is", "i'm", "i am", "this is"]) and not bot_state.collected_info.get("name"):
            import re
            name_patterns = [
                r"name is\s+([A-Za-z\s]+)",
                r"i'm\s+([A-Za-z\s]+)",
                r"i am\s+([A-Za-z\s]+)",
                r"this is\s+([A-Za-z\s]+)"
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, text_lower)
                if name_match:
                    name = name_match.group(1).strip().title()
                    if len(name) > 1 and name not in ["the", "a", "an"]:  # Basic validation
                        bot_state.collected_info["name"] = name
                        logger.info(f"Extracted name: {bot_state.collected_info['name']}")
                        break
        
        # Extract address if present
        if any(keyword in text_lower for keyword in ["address", "live at", "street", "city", "state"]) and not bot_state.collected_info.get("address"):
            # Look for address-like patterns
            if "live at" in text_lower:
                address_start = text_lower.find("live at") + 7
                address = user_text[address_start:].strip()
                if len(address) > 5:  # Basic validation
                    bot_state.collected_info["address"] = address
                    logger.info(f"Extracted address: {bot_state.collected_info['address']}")
        
        # Extract issue description and price
        if not bot_state.collected_info.get("issue"):
            issue_desc, price = get_issue_type_and_price(user_text)
            if price > 0:
                bot_state.collected_info["issue"] = issue_desc
                bot_state.collected_info["price"] = price
                logger.info(f"Extracted issue: {issue_desc}, price: ${price}")
