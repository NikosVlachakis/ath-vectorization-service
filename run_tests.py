#!/usr/bin/env python3

"""
Test runner for the enhanced vectorization system
"""

import sys
import unittest
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Add the tests directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

def run_tests():
    """Run all tests"""
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    # Load tests from the tests directory
    test_suite = loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 