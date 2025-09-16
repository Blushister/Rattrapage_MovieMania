#!/usr/bin/env python3
"""
Script to run Django tests for MovieMania frontend.
This script can be run both inside and outside Docker containers.
"""

import os
import sys
import subprocess
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Setup Django settings for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviemania_frontend.settings')
    django.setup()


def run_django_tests(verbosity=2, pattern=None, failfast=False):
    """Run Django tests using Django's test runner"""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=verbosity, interactive=False, failfast=failfast)
    
    if pattern:
        # Run specific test pattern
        test_labels = [f'users.{pattern}']
    else:
        # Run all tests in users app
        test_labels = ['users']
    
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print(f"\n✅ All tests passed!")
        return True


def run_coverage_tests():
    """Run tests with coverage report"""
    try:
        # Install coverage if not available
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'], 
                      capture_output=True, check=False)
        
        # Run tests with coverage
        cmd = [
            sys.executable, '-m', 'coverage', 'run', 
            '--source', '.', 'manage.py', 'test', 'users', '--verbosity=2'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Generate coverage report
        subprocess.run([sys.executable, '-m', 'coverage', 'report'], 
                      capture_output=False, check=False)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Coverage testing failed: {e}")
        return False


def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MovieMania Django tests')
    parser.add_argument('--pattern', '-p', help='Run specific test pattern (e.g., test_views)')
    parser.add_argument('--failfast', '-f', action='store_true', 
                       help='Stop on first failure')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage report')
    parser.add_argument('--verbosity', '-v', type=int, default=2,
                       choices=[0, 1, 2, 3], help='Test output verbosity')
    
    args = parser.parse_args()
    
    print("🧪 Starting MovieMania Django Tests...\n")
    
    if args.coverage:
        success = run_coverage_tests()
    else:
        success = run_django_tests(
            verbosity=args.verbosity,
            pattern=args.pattern,
            failfast=args.failfast
        )
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()