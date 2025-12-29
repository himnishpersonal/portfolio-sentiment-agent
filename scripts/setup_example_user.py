#!/usr/bin/env python3
"""Setup script to create example user with sample portfolio."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.portfolio_manager import PortfolioManager


def main():
    """Create example user with sample portfolio."""
    email = "demo@example.com"

    # Sample portfolio (popular tech stocks)
    portfolio = {
        "AAPL": 0.25,
        "MSFT": 0.20,
        "GOOGL": 0.15,
        "AMZN": 0.15,
        "TSLA": 0.10,
        "META": 0.10,
        "NVDA": 0.05,
    }

    try:
        # Create user
        print(f"Creating user: {email}")
        user = PortfolioManager.create_user(email)
        print(f"✓ Created user {user.id}")

        # Add portfolio
        print(f"Adding portfolio with {len(portfolio)} tickers...")
        PortfolioManager.update_portfolio(user.id, portfolio)
        print("✓ Portfolio created successfully")

        print("\nExample user setup complete!")
        print(f"User ID: {user.id}")
        print(f"Email: {email}")
        print(f"Portfolio: {', '.join(portfolio.keys())}")

    except ValueError as e:
        if "already exists" in str(e):
            print(f"User {email} already exists. Updating portfolio...")
            from db import db_manager, User

            with db_manager.get_session() as session:
                user = session.query(User).filter(User.email == email).first()
                PortfolioManager.update_portfolio(user.id, portfolio)
                print("✓ Portfolio updated successfully")
        else:
            print(f"✗ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()

