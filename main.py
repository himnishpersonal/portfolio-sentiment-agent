#!/usr/bin/env python3
"""Main entry point for running the portfolio sentiment pipeline."""

import argparse
import sys
from pathlib import Path

from agents.orchestrator import Orchestrator
from config.logging_config import setup_logging

# Setup logging
setup_logging()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Portfolio Sentiment Intelligence Agent")
    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="User ID to run pipeline for",
    )

    args = parser.parse_args()

    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()

        # Run pipeline
        result = orchestrator.run(args.user_id)

        if result.get("email_sent"):
            print(f"✓ Pipeline completed successfully for user {args.user_id}")
            print(f"✓ Email sent to {result.get('user_email')}")
        else:
            print(f"⚠ Pipeline completed but email may not have been sent")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

