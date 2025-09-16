"""
IT Help Desk Voice Bot Agent

This module contains the main voice assistant agent that handles
conversations with customers and manages the ticket creation process.
"""

import logging
from livekit.agents import llm
from livekit.agents.voice import Agent
from config import SYSTEM_PROMPT
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
    
