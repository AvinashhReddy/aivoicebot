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
async def create_ticket_tool(name: str, email: str, phone: str, address: str, issue: str, price: float) -> str:
    """
    Create a new support ticket with customer information.
    
    IMPORTANT: All parameters are mandatory. Do NOT call this function unless you have collected:
    - name: Customer's full name (not empty, not placeholder)
    - email: Valid email address (must contain @ symbol)
    - phone: Customer's phone number (not empty, not placeholder)
    - address: Customer's physical address (not empty, not placeholder)
    - issue: Specific IT issue description
    - price: Exact service price (must be > 0)
    
    Only call this function after confirming ALL details with the customer.
    """
    try:
        # Validate all required fields are properly filled
        validation_errors = []
        
        if not name or name.lower() in ['', 'unknown', 'n/a', 'none', 'not provided']:
            validation_errors.append("Customer name is required")
            
        if not email or '@' not in email or email.lower() in ['', 'unknown', 'n/a', 'none', 'not provided']:
            validation_errors.append("Valid email address is required")
            
        if not phone or phone.lower() in ['', 'unknown', 'n/a', 'none', 'not provided']:
            validation_errors.append("Phone number is required")
            
        if not address or address.lower() in ['', 'unknown', 'n/a', 'none', 'not provided']:
            validation_errors.append("Physical address is required")
            
        if not issue or issue.lower() in ['', 'unknown', 'n/a', 'none', 'not provided']:
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


@llm.function_tool
async def check_information_completeness() -> str:
    """
    Check if all mandatory customer information has been collected for ticket creation.
    Use this tool to verify you have all required details before attempting to create a ticket.
    """
    missing_info = []
    
    # Check what information we still need
    if not bot_state.collected_info.get("name"):
        missing_info.append("customer name")
    if not bot_state.collected_info.get("email"):
        missing_info.append("email address")
    if not bot_state.collected_info.get("phone"):
        missing_info.append("phone number")
    if not bot_state.collected_info.get("address"):
        missing_info.append("physical address")
    if not bot_state.collected_info.get("issue"):
        missing_info.append("IT issue description")
    if not bot_state.collected_info.get("price") or bot_state.collected_info.get("price", 0) <= 0:
        missing_info.append("service price")
    
    if missing_info:
        return f"Missing required information: {', '.join(missing_info)}. Please collect these details before creating a ticket."
    else:
        return "All mandatory information collected. Ready to create ticket with: " + \
               f"Name: {bot_state.collected_info['name']}, " + \
               f"Email: {bot_state.collected_info['email']}, " + \
               f"Phone: {bot_state.collected_info['phone']}, " + \
               f"Address: {bot_state.collected_info['address']}, " + \
               f"Issue: {bot_state.collected_info['issue']}, " + \
               f"Price: ${bot_state.collected_info['price']}"


# Export all tools for easy import
ALL_TOOLS = [create_ticket_tool, update_ticket_name, update_ticket_email, check_information_completeness]
