#!/usr/bin/env python3
"""
Main smoke test runner for agent-validator.

This script can be run from the root directory and will execute
the appropriate smoke tests based on the environment.

Usage:
    python run_smoke_tests.py [--isolated|--quick|--full]
"""

import sys
import subprocess
from pathlib import Path


def run_smoke_tests():
    """Run comprehensive smoke tests."""
    print("🧪 Running comprehensive smoke tests...")
    
    smoke_tests_dir = Path(__file__).parent / "smoke_tests"
    smoke_script = smoke_tests_dir / "smoke_tests.py"
    
    if not smoke_script.exists():
        print(f"❌ Smoke test script not found: {smoke_script}")
        return False
    
    # Change to smoke_tests directory and run
    original_cwd = Path.cwd()
    try:
        os.chdir(smoke_tests_dir)
        result = subprocess.run([sys.executable, "smoke_tests.py"])
        return result.returncode == 0
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point."""
    import os
    
    print("🚀 Agent Validator Smoke Test Runner")
    print("=" * 50)
    
    success = run_smoke_tests()
    
    print("=" * 50)
    if success:
        print("🎉 Smoke tests completed successfully!")
        return 0
    else:
        print("❌ Smoke tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
