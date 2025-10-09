#!/usr/bin/env python3
"""
Test runner for dependency_manager module tests.

This script runs all tests for the dependency_manager module functions.
Can be used to run specific test files or all tests in the dependency_manager module.
"""

import sys
import unittest
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

def run_specific_test(test_file=None):
    """Run a specific test file or all tests if none specified."""
    if test_file:
        # Run specific test file
        suite = unittest.TestLoader().loadTestsFromName(f'test_{test_file}')
    else:
        # Discover and run all tests in this directory
        suite = unittest.TestLoader().discover(
            start_dir=os.path.dirname(__file__),
            pattern='test_*.py',
            top_level_dir=os.path.join(os.path.dirname(__file__), '..', '..')
        )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main function to run dependency_manager tests."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if not test_name.startswith('test_'):
            test_name = f"test_{test_name}"
        if not test_name.endswith('.py'):
            test_name = f"{test_name}.py"
        
        print(f"Running specific test: {test_name}")
        success = run_specific_test(test_name.replace('.py', ''))
    else:
        print("Running all dependency_manager tests...")
        success = run_specific_test()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)