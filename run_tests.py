#!/usr/bin/env python
"""Simple test runner script for GMFT CLI."""

import subprocess
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run GMFT CLI tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--integration", action="store_true", help="Include integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("tests", nargs="*", help="Specific test files or directories")
    
    args = parser.parse_args()
    
    cmd = ["pytest"]
    
    if args.coverage:
        cmd.extend(["--cov=gmft_cli", "--cov-report=term-missing"])
    
    if not args.integration:
        cmd.extend(["-m", "not integration"])
    
    if args.verbose:
        cmd.append("-vv")
    
    if args.tests:
        cmd.extend(args.tests)
    else:
        cmd.append("tests/")
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())