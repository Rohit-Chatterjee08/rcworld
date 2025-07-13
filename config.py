import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Database Configuration
    DATABASE_PATH = 'job_automation.db'
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Job Search Configuration
    JOB_SEARCH_PORTALS = {
        'linkedin': {
            'name': 'LinkedIn',
            'base_url': 'https://www.linkedin.com/jobs/search/',
            'enabled': True,
            'rate_limit': 2  # seconds between requests
        },
        'naukri': {
            'name': 'Naukri.com',
            'base_url': 'https://www.naukri.com/jobs-in-india',
            'enabled': True,
            'rate_limit': 3
        },
        'indeed': {
            'name': 'Indeed',
            'base_url': 'https://in.indeed.com/jobs',
            'enabled': True,
            'rate_limit': 2
        },
        'wellfound': {
            'name': 'Wellfound (AngelList)',
            'base_url': 'https://wellfound.com/jobs',
            'enabled': True,
            'rate_limit': 3
        },
        'remoteok': {
            'name': 'RemoteOK',
            'base_url': 'https://remoteok.io/remote-jobs',
            'enabled': True,
            'rate_limit': 2
        }
    }
    
    # Default Job Search Criteria
    DEFAULT_SEARCH_CRITERIA = {
        'roles': ['Prompt Engineer', 'AI Engineer', 'Machine Learning Engineer', 'Data Scientist'],
        'experience_min': 0,
        'experience_max': 3,
        'salary_min': 700000,  # 7 LPA in INR
        'location': 'Remote',
        'keywords': ['AI', 'Machine Learning', 'NLP', 'LLM', 'GPT', 'Python', 'TensorFlow', 'PyTorch']
    }
    
    # Selenium Configuration
    SELENIUM_CONFIG = {
        'headless': True,
        'window_size': (1920, 1080),
        'page_load_timeout': 30,
        'implicit_wait': 10,
        'download_path': os.path.join(os.getcwd(), 'downloads')
    }
    
    # Application Settings
    APPLICATION_CONFIG = {
        'max_applications_per_day': 20,
        'max_applications_per_session': 5,
        'application_delay': 30,  # seconds between applications
        'auto_apply_enabled': False,  # Safety feature - must be explicitly enabled
        'save_job_descriptions': True,
        'screenshot_on_error': True
    }
    
    # Email Configuration (for notifications)
    MAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'username': os.environ.get('EMAIL_USERNAME'),
        'password': os.environ.get('EMAIL_PASSWORD')
    }
    
    # Logging Configuration
    LOG_CONFIG = {
        'level': 'INFO',
        'file': 'job_automation.log',
        'max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    }
    
    # API Keys (if needed for premium features)
    API_KEYS = {
        'openai': os.environ.get('OPENAI_API_KEY'),
        'anthropic': os.environ.get('ANTHROPIC_API_KEY')
    }
    
    # Company Career Pages (for direct applications)
    COMPANY_CAREER_PAGES = [
        {
            'name': 'Google',
            'url': 'https://careers.google.com/jobs/results/',
            'location_param': 'location',
            'keyword_param': 'q'
        },
        {
            'name': 'Microsoft',
            'url': 'https://careers.microsoft.com/professionals/us/en/search-results',
            'location_param': 'location',
            'keyword_param': 'keyword'
        },
        {
            'name': 'Amazon',
            'url': 'https://www.amazon.jobs/en/search',
            'location_param': 'loc_query',
            'keyword_param': 'base_query'
        }
    ]
    
    # User Agent Strings for web scraping
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # Job filtering keywords
    POSITIVE_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 
        'nlp', 'natural language processing', 'llm', 'large language model',
        'gpt', 'prompt engineering', 'chatbot', 'conversational ai',
        'python', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
        'remote', 'work from home', 'wfh', 'telecommute'
    ]
    
    NEGATIVE_KEYWORDS = [
        'senior', 'lead', 'principal', 'director', 'manager',
        'phd', 'doctorate', '5+ years', '10+ years',
        'c++', 'java', 'scala', 'hadoop', 'spark'  # Adjust based on your preferences
    ]
    
    # Salary keywords and patterns
    SALARY_PATTERNS = {
        'lpa': r'(\d+(?:\.\d+)?)\s*(?:to\s*)?(\d+(?:\.\d+)?)?\s*lpa',
        'lakhs': r'(\d+(?:\.\d+)?)\s*(?:to\s*)?(\d+(?:\.\d+)?)?\s*lakhs?',
        'inr': r'inr\s*(\d+(?:,\d+)*)',
        'rupees': r'₹\s*(\d+(?:,\d+)*)'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SELENIUM_CONFIG = {
        **Config.SELENIUM_CONFIG,
        'headless': False  # Show browser in development
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'
    
    # More restrictive settings for production
    APPLICATION_CONFIG = {
        **Config.APPLICATION_CONFIG,
        'max_applications_per_day': 10,
        'max_applications_per_session': 3,
        'application_delay': 60
    }

# Configuration selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}