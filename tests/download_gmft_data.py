#!/usr/bin/env python
"""Download GMFT test data for integration testing."""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def download_gmft_test_data(target_dir=None):
    """Download GMFT repository to get test data."""
    if target_dir is None:
        # Default to parent directory
        target_dir = Path(__file__).parent.parent.parent / "gmft-source"
    else:
        target_dir = Path(target_dir)

    if target_dir.exists():
        print(f"GMFT source already exists at: {target_dir}")
        response = input("Remove and re-download? (y/N): ")
        if response.lower() != "y":
            return target_dir
        shutil.rmtree(target_dir)

    print(f"Cloning GMFT repository to: {target_dir}")

    # Clone the repository
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",  # Shallow clone
        "--filter=blob:none",  # Partial clone
        "--sparse",
        "https://github.com/conjuncts/gmft.git",
        str(target_dir),
    ]

    try:
        subprocess.run(cmd, check=True)

        # Set up sparse checkout for just the data we need
        os.chdir(target_dir)
        subprocess.run(["git", "sparse-checkout", "init", "--cone"], check=True)
        subprocess.run(["git", "sparse-checkout", "set", "data/"], check=True)

        print("✓ Successfully downloaded GMFT test data")
        return target_dir

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download GMFT data: {e}")
        return None


def check_gmft_data():
    """Check if GMFT test data is available."""
    possible_paths = [
        Path(__file__).parent.parent.parent / "gmft-source",
        Path.home() / "Downloads" / "gmft-source",
    ]

    for path in possible_paths:
        if path.exists() and (path / "data" / "pdfs").exists():
            print(f"✓ GMFT test data found at: {path}")
            return path

    print("✗ GMFT test data not found")
    return None


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Download GMFT test data")
    parser.add_argument(
        "--target", help="Target directory for GMFT source", default=None
    )
    parser.add_argument(
        "--check", action="store_true", help="Just check if data exists"
    )

    args = parser.parse_args()

    if args.check:
        path = check_gmft_data()
        sys.exit(0 if path else 1)
    else:
        path = download_gmft_test_data(args.target)
        if path:
            print("\nTo run GMFT data tests:")
            print("  pytest tests/test_gmft_integration.py -m gmft_data")
            print("  pytest tests/test_gmft_validation.py -m validation")
        sys.exit(0 if path else 1)


if __name__ == "__main__":
    main()
