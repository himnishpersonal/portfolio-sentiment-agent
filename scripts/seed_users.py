#!/usr/bin/env python3
"""CLI script for managing users and portfolios."""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.portfolio_manager import PortfolioManager
from db import db_manager, User, Portfolio


def add_user(email: str) -> None:
    """Add a new user."""
    try:
        user = PortfolioManager.create_user(email)
        print(f"✓ Created user {user.id} with email {email}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def add_portfolio(email: str, ticker: str, weight: float) -> None:
    """Add ticker to user portfolio."""
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                print(f"✗ User with email {email} not found")
                sys.exit(1)

            PortfolioManager.add_ticker(user.id, ticker, weight)
            print(f"✓ Added {ticker} ({weight:.1%}) to {email}'s portfolio")
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def list_users() -> None:
    """List all users."""
    with db_manager.get_session() as session:
        users = session.query(User).all()
        if not users:
            print("No users found")
            return

        print(f"\nUsers ({len(users)}):")
        print("-" * 50)
        for user in users:
            portfolio_count = session.query(Portfolio).filter(Portfolio.user_id == user.id).count()
            print(f"ID: {user.id:3d} | Email: {user.email:30s} | Portfolio: {portfolio_count} tickers")


def list_portfolio(email: str) -> None:
    """List user portfolio."""
    with db_manager.get_session() as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"✗ User with email {email} not found")
            sys.exit(1)

        portfolio = PortfolioManager.get_user_portfolio(user.id)
        if not portfolio:
            print(f"No portfolio found for {email}")
            return

        total_weight = sum(portfolio.values())
        print(f"\nPortfolio for {email}:")
        print("-" * 50)
        for ticker, weight in sorted(portfolio.items(), key=lambda x: x[1], reverse=True):
            print(f"{ticker:10s} | {weight:6.2%}")
        print("-" * 50)
        print(f"{'Total':10s} | {total_weight:6.2%}")


def remove_ticker(email: str, ticker: str) -> None:
    """Remove ticker from user portfolio."""
    with db_manager.get_session() as session:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"✗ User with email {email} not found")
            sys.exit(1)

        portfolio_item = (
            session.query(Portfolio)
            .filter(Portfolio.user_id == user.id, Portfolio.ticker == ticker)
            .first()
        )

        if not portfolio_item:
            print(f"✗ Ticker {ticker} not found in {email}'s portfolio")
            sys.exit(1)

        session.delete(portfolio_item)
        session.commit()
        print(f"✓ Removed {ticker} from {email}'s portfolio")


def update_portfolio(email: str, file_path: str) -> None:
    """Update portfolio from JSON file."""
    try:
        with open(file_path, "r") as f:
            portfolio = json.load(f)

        # Validate weights
        if not PortfolioManager.validate_weights(portfolio):
            total = sum(portfolio.values())
            print(f"✗ Portfolio weights sum to {total:.4f}, expected 1.0")
            sys.exit(1)

        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                print(f"✗ User with email {email} not found")
                sys.exit(1)

            PortfolioManager.update_portfolio(user.id, portfolio)
            print(f"✓ Updated portfolio for {email} with {len(portfolio)} tickers")

    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage users and portfolios")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add user
    parser_add_user = subparsers.add_parser("add-user", help="Add a new user")
    parser_add_user.add_argument("--email", required=True, help="User email address")

    # Add portfolio
    parser_add_portfolio = subparsers.add_parser("add-portfolio", help="Add ticker to portfolio")
    parser_add_portfolio.add_argument("--email", required=True, help="User email address")
    parser_add_portfolio.add_argument("--ticker", required=True, help="Stock ticker symbol")
    parser_add_portfolio.add_argument("--weight", type=float, required=True, help="Portfolio weight (0.0-1.0)")

    # List users
    subparsers.add_parser("list-users", help="List all users")

    # List portfolio
    parser_list_portfolio = subparsers.add_parser("list-portfolio", help="List user portfolio")
    parser_list_portfolio.add_argument("--email", required=True, help="User email address")

    # Remove ticker
    parser_remove = subparsers.add_parser("remove-ticker", help="Remove ticker from portfolio")
    parser_remove.add_argument("--email", required=True, help="User email address")
    parser_remove.add_argument("--ticker", required=True, help="Stock ticker symbol")

    # Update portfolio
    parser_update = subparsers.add_parser("update-portfolio", help="Update portfolio from JSON file")
    parser_update.add_argument("--email", required=True, help="User email address")
    parser_update.add_argument("--file", required=True, help="JSON file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "add-user":
        add_user(args.email)
    elif args.command == "add-portfolio":
        add_portfolio(args.email, args.ticker, args.weight)
    elif args.command == "list-users":
        list_users()
    elif args.command == "list-portfolio":
        list_portfolio(args.email)
    elif args.command == "remove-ticker":
        remove_ticker(args.email, args.ticker)
    elif args.command == "update-portfolio":
        update_portfolio(args.email, args.file)


if __name__ == "__main__":
    main()

