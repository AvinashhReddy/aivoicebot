"""
LiveKit Voice Bot Tools

This module contains the function tools that the voice bot can use
to interact with the ticket system.
"""

import logging
from livekit.agents import llm
from database import db, Ticket

logger = logging.getLogger(__name__)

# Global bot state - will be imported and used by the main voice bot
class VoiceBotState:
    def __init__(self):
        self.current_ticket = None
        self.conversation_stage = "greeting"  # greeting, collecting_details, understanding_issue, confirming, completed
        self.collected_info = {
            "name": None,
            "email": None,
            "phone": None,
            "address": None,
            "issue": None,
            "price": None
        }

# Global state instance
bot_state = VoiceBotState()


@llm.function_tool
async def create_ticket_tool(
    name: str,          # Customer's full name (required, minimum 2 characters, cannot be placeholder)
    email: str,         # Valid email address (required, must contain @ and domain)
    phone: str,         # Customer's phone number (required, minimum 7 characters)
    address: str,       # Customer's complete physical address (required, minimum 10 characters)
    issue: str,         # Exact issue type: "Wi-Fi not working", "Email login issues - password reset", "Slow laptop performance - CPU change", or "Printer problems - power plug change"
    price: float        # Service price: 10.0, 15.0, 20.0, or 25.0 (must match issue type)
) -> str:
    """
    Create a new support ticket with customer information.
    
    All parameters are mandatory and must be valid:
    - name: Customer's full name (not placeholder like 'unknown' or 'test')
    - email: Valid email format with @ and domain
    - phone: Real phone number (not placeholder)
    - address: Physical address of Customer (not placeholder)
    - issue: Must be one of the 4 supported issue types exactly as listed
    - price: Must be 10.0, 15.0, 20.0, or 25.0 and match the issue type
    """
    try:
        
        # Validate all required fields are properly filled
        validation_errors = []
        
        if not name :
            validation_errors.append("Customer name is required")
            
        if not email or '@' not in email:
            validation_errors.append("Valid email address is required")
            
        if not phone:
            validation_errors.append("Phone number is required")
            
        if not address:
            validation_errors.append("Physical address is required")
            
        if not issue:
            validation_errors.append("Issue description is required")
            
        if price <= 0:
            validation_errors.append("Valid service price is required")
        
        # If validation fails, return error message
        if validation_errors:
            return f"Cannot create ticket. Missing required information: {', '.join(validation_errors)}. Please collect all customer details first."
        
        ticket = Ticket(
            name=name,
            email=email,
            phone=phone,
            address=address,
            issue=issue,
            price=price
        )
        
        ticket_id = db.create_ticket(ticket)
        
        # Update bot state
        bot_state.current_ticket = ticket
        bot_state.current_ticket.id = ticket_id
        bot_state.conversation_stage = "completed"
        
        return f"Ticket created successfully with ID: {ticket_id}. Confirmation number is {ticket_id}."
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return f"Sorry, I encountered an error creating the ticket: {str(e)}"


@llm.function_tool
async def update_ticket_name(ticket_id: int, name: str) -> str:
    """Update the name on a ticket"""
    try:
        success = db.update_ticket(ticket_id, {"name": name})
        if success:
            if bot_state.current_ticket and bot_state.current_ticket.id == ticket_id:
                bot_state.current_ticket.name = name
            return f"Ticket {ticket_id} name updated to: {name}"
        else:
            return f"Sorry, I couldn't find ticket {ticket_id}."
    except Exception as e:
        logger.error(f"Error updating ticket name: {e}")
        return f"Sorry, I encountered an error updating the ticket: {str(e)}"


@llm.function_tool
async def update_ticket_email(ticket_id: int, email: str) -> str:
    """Update the email on a ticket"""
    try:
        success = db.update_ticket(ticket_id, {"email": email})
        if success:
            if bot_state.current_ticket and bot_state.current_ticket.id == ticket_id:
                bot_state.current_ticket.email = email
            return f"Ticket {ticket_id} email updated to: {email}"
        else:
            return f"Sorry, I couldn't find ticket {ticket_id}."
    except Exception as e:
        logger.error(f"Error updating ticket email: {e}")
        return f"Sorry, I encountered an error updating the ticket: {str(e)}"


# Export all tools for easy import
ALL_TOOLS = [create_ticket_tool, update_ticket_name, update_ticket_email]
