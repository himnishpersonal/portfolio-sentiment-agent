#!/usr/bin/env python3
"""Script to load portfolios from YAML configuration file."""

import sys
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.portfolio_manager import PortfolioManager


def main():
    """Load portfolios from YAML file."""
    if len(sys.argv) < 2:
        print("Usage: python load_portfolios.py <config_file.yaml>")
        sys.exit(1)

    config_file = Path(sys.argv[1])

    if not config_file.exists():
        print(f"✗ Config file not found: {config_file}")
        sys.exit(1)

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        users = config.get("users", [])

        if not users:
            print("✗ No users found in config file")
            sys.exit(1)

        print(f"Loading {len(users)} users from {config_file}...")

        for user_config in users:
            email = user_config.get("email")
            portfolio = user_config.get("portfolio", {})

            if not email:
                print("✗ Skipping user with no email")
                continue

            try:
                # Create or get user
                try:
                    user = PortfolioManager.create_user(email)
                    print(f"✓ Created user: {email}")
                except ValueError:
                    # User already exists, get it
                    from db import db_manager, User

                    with db_manager.get_session() as session:
                        user = session.query(User).filter(User.email == email).first()

                # Update portfolio
                if portfolio:
                    PortfolioManager.update_portfolio(user.id, portfolio)
                    print(f"✓ Updated portfolio for {email} ({len(portfolio)} tickers)")
                else:
                    print(f"⚠ No portfolio specified for {email}")

            except Exception as e:
                print(f"✗ Error processing user {email}: {e}")
                continue

        print("\n✓ Portfolio loading complete!")

    except yaml.YAMLError as e:
        print(f"✗ Error parsing YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

