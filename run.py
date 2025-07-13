#!/usr/bin/env python
"""
Job Application Automation Tool - Runner Script

This script provides an easy way to start the application with proper configuration.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('job_automation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import selenium
        import beautifulsoup4
        import requests
        import apscheduler
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_chrome_driver():
    """Check if Chrome and ChromeDriver are available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.quit()
        print("✓ Chrome WebDriver is working")
        return True
    except Exception as e:
        print(f"✗ Chrome WebDriver error: {e}")
        print("Please ensure Google Chrome is installed")
        return False

def create_directories():
    """Create required directories if they don't exist"""
    directories = [
        'uploads',
        'screenshots',
        'logs',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")

def check_environment():
    """Check if the environment is properly set up"""
    print("Checking environment setup...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    print(f"✓ Python version: {sys.version}")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check Chrome WebDriver (optional for basic functionality)
    check_chrome_driver()
    
    # Create directories
    create_directories()
    
    print("✓ Environment check complete")
    return True

def run_application(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask application"""
    try:
        # Import the Flask app
        from app import app
        
        print(f"Starting Job Application Automation Tool...")
        print(f"Web interface will be available at: http://localhost:{port}")
        print(f"Press Ctrl+C to stop the application")
        
        # Run the application
        app.run(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"✗ Error importing application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error running application: {e}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Job Application Automation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run with default settings
  python run.py --debug            # Run in debug mode
  python run.py --port 8080        # Run on port 8080
  python run.py --check-only       # Only check environment
        """
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run on (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check environment setup, don\'t run the application'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Print banner
    print("=" * 60)
    print("   Job Application Automation Tool")
    print("   AI/ML Job Search & Application Assistant")
    print("=" * 60)
    print()
    
    # Check environment
    if not check_environment():
        print("✗ Environment check failed. Please fix the issues above.")
        sys.exit(1)
    
    # If check-only mode, exit after environment check
    if args.check_only:
        print("✓ Environment check passed. You can now run the application.")
        sys.exit(0)
    
    # Run the application
    run_application(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main()