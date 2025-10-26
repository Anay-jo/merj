#!/usr/bin/env python3
"""
Sample application for testing RAG pipeline conflict resolution.
This file simulates a typical Python application with various components.
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime

# Global configuration
CONFIG = {
    "api_version": "1.0.0",
    "max_retries": 3,
    "timeout": 30
}


class UserManager:
    """Manages user accounts and authentication."""

    def __init__(self, database_url: str = "sqlite:///users.db"):
        """Initialize the user manager with database connection."""
        self.database_url = database_url
        self.users = []
        self.active_sessions = {}

    def add_user(self, username: str, email: str, password: str) -> Dict:
        """Add a new user to the system.

        Args:
            username: Unique username
            email: User's email address
            password: Encrypted password

        Returns:
            Dict containing user details
        """
        user = {
            "id": len(self.users) + 1,
            "username": username,
            "email": email,
            "password": self._hash_password(password),
            "created_at": datetime.now().isoformat()
        }
        self.users.append(user)
        return user

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return session token."""
        for user in self.users:
            if user["username"] == username:
                if self._verify_password(password, user["password"]):
                    token = self._generate_token()
                    self.active_sessions[token] = user["id"]
                    return token
        return None

    def _hash_password(self, password: str) -> str:
        """Hash password for storage."""
        # Simplified for demo - would use bcrypt in production
        return f"hashed_{password}"

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return f"hashed_{password}" == hashed

    def _generate_token(self) -> str:
        """Generate session token."""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


def calculate_price(items: List[Dict], tax_rate: float = 0.08, discount: float = 0.0) -> Dict:
    """Calculate total price with tax and discount.

    Args:
        items: List of item dictionaries with 'price' and 'quantity'
        tax_rate: Tax rate to apply (default 8%)
        discount: Discount percentage to apply

    Returns:
        Dictionary with subtotal, tax, discount, and total
    """
    subtotal = sum(item['price'] * item.get('quantity', 1) for item in items)

    # Apply discount first
    discount_amount = subtotal * discount
    after_discount = subtotal - discount_amount

    # Then apply tax
    tax_amount = after_discount * tax_rate
    total = after_discount + tax_amount

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount_amount, 2),
        "tax": round(tax_amount, 2),
        "total": round(total, 2)
    }


def validate_input(data: Dict, required_fields: List[str]) -> tuple[bool, List[str]]:
    """Validate input data has required fields.

    Args:
        data: Input data dictionary
        required_fields: List of field names that must be present

    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    missing = []

    for field in required_fields:
        if field not in data or data[field] is None:
            missing.append(field)

    return len(missing) == 0, missing


class DataProcessor:
    """Process and transform data for the application."""

    def __init__(self, config: Dict = None):
        """Initialize processor with configuration."""
        self.config = config or CONFIG
        self.processed_count = 0

    def process_batch(self, records: List[Dict]) -> List[Dict]:
        """Process a batch of records.

        Args:
            records: List of records to process

        Returns:
            List of processed records
        """
        results = []
        for record in records:
            try:
                processed = self._transform_record(record)
                results.append(processed)
                self.processed_count += 1
            except Exception as e:
                print(f"Error processing record: {e}")
                continue

        return results

    def _transform_record(self, record: Dict) -> Dict:
        """Transform a single record."""
        # Add timestamp
        record['processed_at'] = datetime.now().isoformat()

        # Normalize strings
        for key, value in record.items():
            if isinstance(value, str):
                record[key] = value.strip().lower()

        return record

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "config": self.config
        }


# Utility functions
def load_config(filepath: str) -> Dict:
    """Load configuration from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_results(data: List, filepath: str) -> None:
    """Save results to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    """Main application entry point."""
    print("Sample Application Starting...")

    # Initialize components
    user_mgr = UserManager()
    processor = DataProcessor()

    # Add sample user
    user = user_mgr.add_user("john_doe", "john@example.com", "secret123")
    print(f"Created user: {user['username']}")

    # Calculate sample price
    items = [
        {"name": "Widget", "price": 10.99, "quantity": 2},
        {"name": "Gadget", "price": 25.50, "quantity": 1}
    ]
    pricing = calculate_price(items, tax_rate=0.08, discount=0.1)
    print(f"Total price: ${pricing['total']}")

    # Process some data
    records = [
        {"name": "ALICE  ", "age": 30},
        {"name": " Bob", "age": 25}
    ]
    processed = processor.process_batch(records)
    print(f"Processed {len(processed)} records")

    print("Application completed successfully!")


if __name__ == "__main__":
    main()