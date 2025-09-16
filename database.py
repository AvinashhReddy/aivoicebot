import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class Ticket(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    phone: str
    address: str
    issue: str
    price: float
    created_at: Optional[str] = None

class TicketDatabase:
    def __init__(self, db_path: str = "tickets.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with tickets table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                issue TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_ticket(self, ticket: Ticket) -> int:
        """Create a new ticket and return the ticket ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO tickets (name, email, phone, address, issue, price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticket.name, ticket.email, ticket.phone, ticket.address, 
              ticket.issue, ticket.price, created_at))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, address, issue, price, created_at
            FROM tickets WHERE id = ?
        ''', (ticket_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Ticket(
                id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                address=row[4],
                issue=row[5],
                price=row[6],
                created_at=row[7]
            )
        return None
    
    def update_ticket(self, ticket_id: int, updates: Dict[str, Any]) -> bool:
        """Update a ticket with new information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in ['name', 'email', 'phone', 'address', 'issue', 'price']:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if not set_clauses:
            conn.close()
            return False
        
        values.append(ticket_id)
        query = f"UPDATE tickets SET {', '.join(set_clauses)} WHERE id = ?"
        
        cursor.execute(query, values)
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_all_tickets(self) -> list[Ticket]:
        """Get all tickets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, address, issue, price, created_at
            FROM tickets ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Ticket(
                id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                address=row[4],
                issue=row[5],
                price=row[6],
                created_at=row[7]
            ) for row in rows
        ]

# Global database instance
db = TicketDatabase()
