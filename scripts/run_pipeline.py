#!/usr/bin/env python3
"""Script to run the pipeline for all active users."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import Orchestrator
from db import db_manager, User
from config.logging_config import setup_logging

# Setup logging
setup_logging()


def main():
    """Run pipeline for all users."""
    try:
        # Get all users - extract data while session is open
        with db_manager.get_session() as session:
            users = session.query(User).all()
            # Extract user data before session closes
            user_data = [{"id": user.id, "email": user.email} for user in users]

        if not user_data:
            print("No users found")
            return

        print(f"Running pipeline for {len(user_data)} users...")

        orchestrator = Orchestrator()
        success_count = 0
        failure_count = 0

        for user_info in user_data:
            try:
                user_id = user_info["id"]
                user_email = user_info["email"]
                print(f"\nProcessing user {user_id} ({user_email})...")
                result = orchestrator.run(user_id)

                if result.get("email_sent"):
                    print(f"✓ Successfully processed user {user_id}")
                    success_count += 1
                else:
                    print(f"⚠ User {user_id} processed but email may not have been sent")
                    failure_count += 1

            except Exception as e:
                print(f"✗ Failed to process user {user_id}: {e}")
                failure_count += 1

        print(f"\n{'='*50}")
        print(f"Pipeline execution complete:")
        print(f"  Success: {success_count}")
        print(f"  Failed: {failure_count}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

