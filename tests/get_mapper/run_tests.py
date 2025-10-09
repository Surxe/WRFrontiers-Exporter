#!/usr/bin/env python3
"""
Test runner for get_mapper module tests.

Run all tests for get_mapper functions:
    python tests/get_mapper/run_tests.py

Run specific test file:
    python tests/get_mapper/run_tests.py test_get_dll_path
"""

import sys
import unittest
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

if __name__ == '__main__':
    # Determine test pattern based on command line args
    if len(sys.argv) > 1:
        # Run specific test file
        test_name = sys.argv[1]
        if not test_name.startswith('test_'):
            test_name = f'test_{test_name}'
        
        # Discover and run specific test
        loader = unittest.TestLoader()
        suite = loader.discover(
            start_dir=os.path.dirname(__file__),
            pattern=f'{test_name}.py',
            top_level_dir=os.path.join(os.path.dirname(__file__), '..', '..')
        )
    else:
        # Run all get_mapper tests
        loader = unittest.TestLoader()
        suite = loader.discover(
            start_dir=os.path.dirname(__file__),
            pattern='test_*.py',
            top_level_dir=os.path.join(os.path.dirname(__file__), '..', '..')
        )
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)