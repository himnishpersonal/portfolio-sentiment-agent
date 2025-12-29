#!/usr/bin/env python3
"""Script to validate sentiment model accuracy."""

import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.sentiment_agent import SentimentAgent
from agents.schemas import ArticleData
from datetime import datetime


def load_labeled_headlines(file_path: str) -> List[Tuple[str, str]]:
    """Load labeled headlines from file.

    Expected format: headline|label (one per line)
    Labels: positive, neutral, negative

    Args:
        file_path: Path to labeled data file.

    Returns:
        List of (headline, label) tuples.
    """
    labeled_data = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 2:
                headline, label = parts
                if label in ["positive", "neutral", "negative"]:
                    labeled_data.append((headline.strip(), label.strip()))
    return labeled_data


def main():
    """Run sentiment validation."""
    if len(sys.argv) < 2:
        print("Usage: python validate_sentiment.py <labeled_headlines.txt>")
        print("\nExpected file format:")
        print("headline|label")
        print("(one per line, labels: positive, neutral, negative)")
        sys.exit(1)

    labeled_file = Path(sys.argv[1])

    if not labeled_file.exists():
        print(f"✗ File not found: {labeled_file}")
        sys.exit(1)

    print("Loading labeled headlines...")
    labeled_data = load_labeled_headlines(str(labeled_file))
    print(f"Loaded {len(labeled_data)} labeled headlines} labeled headlines")

    if not labeled_data:
        print("✗ No labeled data found")
        sys.exit(1)

    print("\nInitializing sentiment agent...")
    agent = SentimentAgent()

    print("Running predictions...")
    correct = 0
    total = len(labeled_data)

    # Process in batches
    batch_size = 16
    for i in range(0, len(labeled_data), batch_size):
        batch = labeled_data[i : i + batch_size]

        # Create article data
        articles = [
            ArticleData(
                headline=headline,
                content=headline * 3,  # Repeat headline as content
                source="Test",
                url="https://test.com",
                published_at=datetime.utcnow(),
                ticker="TEST",
            )
            for headline, _ in batch
        ]

        # Get predictions
        result = agent.run({"articles": [a.model_dump() for a in articles]})
        predictions = result["sentiments"]

        # Compare with labels
        for (headline, true_label), pred in zip(batch, predictions):
            pred_label = pred["label"]
            if pred_label == true_label:
                correct += 1
            else:
                print(f"✗ Mismatch: '{headline[:50]}...' | True: {true_label}, Pred: {pred_label}")

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0.0

    print(f"\n{'='*50}")
    print(f"Validation Results:")
    print(f"  Total: {total}")
    print(f"  Correct: {correct}")
    print(f"  Accuracy: {accuracy:.2%}")
    print(f"{'='*50}")

    # Calculate per-class metrics
    from collections import defaultdict

    true_labels = defaultdict(int)
    pred_labels = defaultdict(int)
    correct_by_class = defaultdict(int)

    for (_, true_label), pred in zip(labeled_data, predictions):
        true_labels[true_label] += 1
        pred_labels[pred["label"]] += 1
        if pred["label"] == true_label:
            correct_by_class[true_label] += 1

    print("\nPer-class accuracy:")
    for label in ["positive", "neutral", "negative"]:
        if true_labels[label] > 0:
            class_acc = correct_by_class[label] / true_labels[label]
            print(f"  {label:8s}: {class_acc:.2%} ({correct_by_class[label]}/{true_labels[label]})")


if __name__ == "__main__":
    main()

