"""
Utility functions for job automation tool
Contains helper functions for text processing, job filtering, and web automation
"""

import re
import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import PyPDF2
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file {config_path} not found")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file {config_path}")
        return {}

def save_config(config: Dict, config_path: str = "config.json"):
    """Save configuration to JSON file"""
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create and configure Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # Common Chrome options for better automation
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Random user agent to avoid detection
    ua = UserAgent()
    options.add_argument(f"--user-agent={ua.random}")
    
    # Disable images and CSS for faster loading
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=options
        )
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        logger.error(f"Error creating Chrome driver: {e}")
        raise

def random_delay(min_seconds: int = 1, max_seconds: int = 5):
    """Add random delay to avoid detection"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF resume"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def calculate_job_eligibility(job_data: Dict, config: Dict) -> Tuple[bool, float, List[str]]:
    """
    Calculate job eligibility based on criteria
    Returns: (is_eligible, score, matched_keywords)
    """
    criteria = config.get('job_criteria', {})
    
    # Extract relevant fields
    title = job_data.get('title', '').lower()
    description = job_data.get('description', '').lower()
    requirements = job_data.get('requirements', '').lower()
    location = job_data.get('location', '').lower()
    experience = job_data.get('experience_required', '').lower()
    
    full_text = f"{title} {description} {requirements}".lower()
    
    # Check role match
    target_roles = [role.lower() for role in criteria.get('roles', [])]
    role_match = any(role in title for role in target_roles)
    
    # Check location preference
    preferred_locations = [loc.lower() for loc in criteria.get('preferred_locations', [])]
    location_match = any(loc in location for loc in preferred_locations)
    
    # Check experience requirements
    experience_range = criteria.get('experience_range', [0, 3])
    experience_match = True
    
    # Extract experience numbers from text
    exp_numbers = re.findall(r'(\d+)(?:\s*[-to]\s*(\d+))?\s*(?:year|yr)', experience)
    if exp_numbers:
        min_exp = int(exp_numbers[0][0])
        max_exp = int(exp_numbers[0][1]) if exp_numbers[0][1] else min_exp
        experience_match = min_exp <= experience_range[1]
    
    # Check for excluded keywords
    exclude_keywords = [kw.lower() for kw in criteria.get('exclude_keywords', [])]
    has_excluded = any(kw in full_text for kw in exclude_keywords)
    
    # Check for required keywords
    required_keywords = [kw.lower() for kw in criteria.get('keywords', [])]
    matched_keywords = [kw for kw in required_keywords if kw in full_text]
    keyword_match_ratio = len(matched_keywords) / len(required_keywords) if required_keywords else 0
    
    # Calculate eligibility score
    score = 0.0
    
    # Role match (40% weight)
    if role_match:
        score += 40
    
    # Location match (20% weight)
    if location_match:
        score += 20
    
    # Experience match (15% weight)
    if experience_match:
        score += 15
    
    # Keyword match (20% weight)
    score += keyword_match_ratio * 20
    
    # Bonus for salary mention (5% weight)
    if any(sal in full_text for sal in ['salary', 'lpa', 'ctc', 'package']):
        score += 5
    
    # Determine eligibility
    is_eligible = (
        role_match and
        location_match and
        experience_match and
        not has_excluded and
        keyword_match_ratio >= 0.3  # At least 30% keywords match
    )
    
    return is_eligible, score, matched_keywords

def extract_salary_info(text: str) -> Dict:
    """Extract salary information from job text"""
    salary_info = {
        'min_salary': None,
        'max_salary': None,
        'currency': 'INR',
        'period': 'annual'
    }
    
    # Common salary patterns
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lacs?|lakhs?)',
        r'(\d+(?:\.\d+)?)\s*(?:lpa|lacs?|lakhs?)',
        r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:-|to)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:-|to)\s*rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)'
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) == 2:
                salary_info['min_salary'] = float(match.group(1).replace(',', ''))
                salary_info['max_salary'] = float(match.group(2).replace(',', ''))
            else:
                salary_info['min_salary'] = float(match.group(1).replace(',', ''))
            break
    
    return salary_info

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?()-]', '', text)
    
    return text.strip()

def format_job_data(raw_job: Dict) -> Dict:
    """Format and clean job data"""
    return {
        'title': clean_text(raw_job.get('title', '')),
        'company': clean_text(raw_job.get('company', '')),
        'location': clean_text(raw_job.get('location', '')),
        'salary': clean_text(raw_job.get('salary', '')),
        'experience_required': clean_text(raw_job.get('experience_required', '')),
        'description': clean_text(raw_job.get('description', '')),
        'requirements': clean_text(raw_job.get('requirements', '')),
        'job_url': raw_job.get('job_url', ''),
        'portal': raw_job.get('portal', ''),
        'posted_date': raw_job.get('posted_date', ''),
        'application_deadline': raw_job.get('application_deadline', '')
    }

def take_screenshot(driver: webdriver.Chrome, filename: str = None) -> str:
    """Take screenshot and save to file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    try:
        driver.save_screenshot(filename)
        return filename
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return None

def wait_for_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10):
    """Wait for element to be present and clickable"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        return element
    except TimeoutException:
        logger.warning(f"Element not found: {value}")
        return None

def scroll_to_element(driver: webdriver.Chrome, element):
    """Scroll to element"""
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        random_delay(1, 2)
    except Exception as e:
        logger.error(f"Error scrolling to element: {e}")

def safe_click(driver: webdriver.Chrome, element):
    """Safely click element with error handling"""
    try:
        scroll_to_element(driver, element)
        element.click()
        random_delay(1, 3)
        return True
    except Exception as e:
        logger.error(f"Error clicking element: {e}")
        return False

def safe_send_keys(element, text: str):
    """Safely send keys to element"""
    try:
        element.clear()
        element.send_keys(text)
        random_delay(0.5, 1.5)
        return True
    except Exception as e:
        logger.error(f"Error sending keys: {e}")
        return False

def setup_logging(config: Dict):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    
    # Create logs directory
    log_file = log_config.get('file_path', 'logs/automation.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def validate_config(config: Dict) -> bool:
    """Validate configuration completeness"""
    required_fields = [
        'user_info.name',
        'user_info.email',
        'user_info.phone',
        'job_criteria.roles',
        'job_criteria.min_salary_lpa'
    ]
    
    for field in required_fields:
        keys = field.split('.')
        value = config
        
        for key in keys:
            if key not in value:
                logger.error(f"Missing required configuration: {field}")
                return False
            value = value[key]
    
    return True

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def ensure_directory(path: str):
    """Ensure directory exists"""
    os.makedirs(path, exist_ok=True)

def generate_cover_letter(job_data: Dict, config: Dict) -> str:
    """Generate personalized cover letter"""
    user_info = config.get('user_info', {})
    template = user_info.get('cover_letter_template', '')
    
    if not template:
        return ""
    
    # Replace placeholders
    cover_letter = template.format(
        position=job_data.get('title', 'this position'),
        company=job_data.get('company', 'your company'),
        name=user_info.get('name', ''),
        experience=user_info.get('experience_years', 0)
    )
    
    return cover_letter