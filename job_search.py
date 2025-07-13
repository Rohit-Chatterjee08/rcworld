import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin, urlencode
from fake_useragent import UserAgent
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config
from models import save_search_history

logger = logging.getLogger(__name__)

class JobSearchManager:
    """Main job search manager that coordinates all portal scrapers"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.scrapers = {
            'linkedin': LinkedInScraper(),
            'naukri': NaukriScraper(),
            'indeed': IndeedScraper(),
            'wellfound': WellfoundScraper(),
            'remoteok': RemoteOKScraper()
        }
    
    def search_jobs(self, search_criteria):
        """Search jobs across multiple portals"""
        all_jobs = []
        portals_searched = []
        
        for portal_name in search_criteria.get('portals', []):
            if portal_name in self.scrapers:
                try:
                    logger.info(f"Searching {portal_name}...")
                    scraper = self.scrapers[portal_name]
                    jobs = scraper.search_jobs(search_criteria)
                    all_jobs.extend(jobs)
                    portals_searched.append(portal_name)
                    
                    # Rate limiting
                    time.sleep(Config.JOB_SEARCH_PORTALS[portal_name]['rate_limit'])
                    
                except Exception as e:
                    logger.error(f"Error searching {portal_name}: {str(e)}")
        
        # Filter and deduplicate jobs
        filtered_jobs = self._filter_jobs(all_jobs, search_criteria)
        
        # Save search history
        save_search_history(search_criteria, len(filtered_jobs), portals_searched)
        
        return filtered_jobs
    
    def _filter_jobs(self, jobs, search_criteria):
        """Filter jobs based on criteria"""
        filtered = []
        
        for job in jobs:
            # Check salary requirements
            if self._check_salary_requirement(job, search_criteria.get('salary_min', 0)):
                # Check location
                if self._check_location_requirement(job, search_criteria.get('location')):
                    # Check experience
                    if self._check_experience_requirement(job, search_criteria):
                        # Check keywords
                        if self._check_keyword_relevance(job, search_criteria.get('roles', [])):
                            filtered.append(job)
        
        # Remove duplicates
        return self._remove_duplicates(filtered)
    
    def _check_salary_requirement(self, job, min_salary):
        """Check if job meets salary requirements"""
        salary_text = job.get('salary', '').lower()
        
        # Extract salary using regex patterns
        for pattern_name, pattern in Config.SALARY_PATTERNS.items():
            matches = re.findall(pattern, salary_text, re.IGNORECASE)
            if matches:
                try:
                    salary_value = float(matches[0][0]) if isinstance(matches[0], tuple) else float(matches[0])
                    
                    if pattern_name == 'lpa':
                        return salary_value * 100000 >= min_salary
                    elif pattern_name == 'lakhs':
                        return salary_value * 100000 >= min_salary
                    else:
                        return salary_value >= min_salary
                except ValueError:
                    continue
        
        return True  # If no salary info found, include the job
    
    def _check_location_requirement(self, job, required_location):
        """Check if job location matches requirements"""
        if not required_location:
            return True
        
        job_location = job.get('location', '').lower()
        required_location = required_location.lower()
        
        if 'remote' in required_location:
            return any(keyword in job_location for keyword in ['remote', 'work from home', 'wfh'])
        
        return required_location in job_location
    
    def _check_experience_requirement(self, job, search_criteria):
        """Check if job experience matches requirements"""
        exp_min = search_criteria.get('experience_min', 0)
        exp_max = search_criteria.get('experience_max', 10)
        
        job_description = (job.get('description', '') + ' ' + job.get('title', '')).lower()
        
        # Look for experience requirements in job description
        exp_patterns = [
            r'(\d+)[-\s]*(\d+)?\s*years?\s*experience',
            r'(\d+)\+\s*years?',
            r'minimum\s*(\d+)\s*years?',
            r'(\d+)\s*to\s*(\d+)\s*years?'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, job_description)
            if matches:
                try:
                    required_exp = int(matches[0][0]) if isinstance(matches[0], tuple) else int(matches[0])
                    if required_exp > exp_max:
                        return False
                except ValueError:
                    continue
        
        return True
    
    def _check_keyword_relevance(self, job, target_roles):
        """Check if job is relevant based on keywords"""
        job_text = (job.get('title', '') + ' ' + job.get('description', '')).lower()
        
        # Check for positive keywords
        positive_score = sum(1 for keyword in Config.POSITIVE_KEYWORDS if keyword in job_text)
        
        # Check for negative keywords
        negative_score = sum(1 for keyword in Config.NEGATIVE_KEYWORDS if keyword in job_text)
        
        # Check for role keywords
        role_score = sum(1 for role in target_roles if role.lower() in job_text)
        
        return (positive_score + role_score) > negative_score
    
    def _remove_duplicates(self, jobs):
        """Remove duplicate jobs"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = (job.get('title', ''), job.get('company', ''))
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs

class BaseScraper:
    """Base class for job portal scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session.headers.update({
            'User-Agent': self.ua.random
        })
    
    def get_driver(self):
        """Get configured Chrome driver"""
        options = Options()
        if Config.SELENIUM_CONFIG['headless']:
            options.add_argument('--headless')
        
        options.add_argument(f'--window-size={Config.SELENIUM_CONFIG["window_size"][0]},{Config.SELENIUM_CONFIG["window_size"][1]}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self.ua.random}')
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.implicitly_wait(Config.SELENIUM_CONFIG['implicit_wait'])
        return driver

class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper"""
    
    def search_jobs(self, search_criteria):
        """Search LinkedIn jobs"""
        jobs = []
        
        try:
            driver = self.get_driver()
            
            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search/"
            params = {
                'keywords': ' OR '.join(search_criteria.get('roles', [])),
                'location': search_criteria.get('location', 'India'),
                'f_E': f"{search_criteria.get('experience_min', 0)},{search_criteria.get('experience_max', 3)}",
                'sortBy': 'DD'  # Date posted
            }
            
            url = f"{base_url}?{urlencode(params)}"
            driver.get(url)
            
            # Wait for jobs to load
            time.sleep(3)
            
            # Scroll to load more jobs
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Extract job listings
            job_cards = driver.find_elements(By.CSS_SELECTOR, '.job-search-card')
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job = self._extract_linkedin_job(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting LinkedIn job: {str(e)}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"LinkedIn search error: {str(e)}")
        
        return jobs
    
    def _extract_linkedin_job(self, card):
        """Extract job details from LinkedIn card"""
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, '.job-search-card__title a')
            title = title_elem.text.strip()
            job_url = title_elem.get_attribute('href')
            
            company_elem = card.find_element(By.CSS_SELECTOR, '.job-search-card__subtitle')
            company = company_elem.text.strip()
            
            location_elem = card.find_element(By.CSS_SELECTOR, '.job-search-card__location')
            location = location_elem.text.strip()
            
            # Try to get salary info
            salary = ''
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, '.job-search-card__salary-info')
                salary = salary_elem.text.strip()
            except:
                pass
            
            return {
                'id': f"linkedin_{hash(job_url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'portal': 'linkedin',
                'description': ''  # Would need additional request to get full description
            }
        
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job details: {str(e)}")
            return None

class NaukriScraper(BaseScraper):
    """Naukri.com job scraper"""
    
    def search_jobs(self, search_criteria):
        """Search Naukri jobs"""
        jobs = []
        
        try:
            # Build search URL
            base_url = "https://www.naukri.com/jobs-in-india"
            params = {
                'k': ' OR '.join(search_criteria.get('roles', [])),
                'l': search_criteria.get('location', 'India'),
                'experience': f"{search_criteria.get('experience_min', 0)}-{search_criteria.get('experience_max', 3)}"
            }
            
            url = f"{base_url}?{urlencode(params)}"
            
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            job_cards = soup.find_all('div', class_='jobTuple')
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job = self._extract_naukri_job(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting Naukri job: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Naukri search error: {str(e)}")
        
        return jobs
    
    def _extract_naukri_job(self, card):
        """Extract job details from Naukri card"""
        try:
            title_elem = card.find('a', class_='jobTupleHeader')
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            job_url = urljoin('https://www.naukri.com', title_elem.get('href', ''))
            
            company_elem = card.find('a', class_='subTitle')
            company = company_elem.text.strip() if company_elem else ''
            
            location_elem = card.find('span', class_='location')
            location = location_elem.text.strip() if location_elem else ''
            
            salary_elem = card.find('span', class_='salary')
            salary = salary_elem.text.strip() if salary_elem else ''
            
            exp_elem = card.find('span', class_='experience')
            experience = exp_elem.text.strip() if exp_elem else ''
            
            return {
                'id': f"naukri_{hash(job_url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'experience': experience,
                'url': job_url,
                'portal': 'naukri',
                'description': ''
            }
        
        except Exception as e:
            logger.error(f"Error extracting Naukri job details: {str(e)}")
            return None

class IndeedScraper(BaseScraper):
    """Indeed job scraper"""
    
    def search_jobs(self, search_criteria):
        """Search Indeed jobs"""
        jobs = []
        
        try:
            base_url = "https://in.indeed.com/jobs"
            params = {
                'q': ' OR '.join(search_criteria.get('roles', [])),
                'l': search_criteria.get('location', 'India'),
                'sort': 'date'
            }
            
            url = f"{base_url}?{urlencode(params)}"
            
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')
            
            for card in job_cards[:20]:
                try:
                    job = self._extract_indeed_job(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting Indeed job: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Indeed search error: {str(e)}")
        
        return jobs
    
    def _extract_indeed_job(self, card):
        """Extract job details from Indeed card"""
        try:
            title_elem = card.find('h2', class_='title')
            if not title_elem:
                return None
            
            title_link = title_elem.find('a')
            title = title_link.text.strip() if title_link else ''
            job_url = urljoin('https://in.indeed.com', title_link.get('href', '')) if title_link else ''
            
            company_elem = card.find('span', class_='company')
            company = company_elem.text.strip() if company_elem else ''
            
            location_elem = card.find('div', class_='recJobLoc')
            location = location_elem.text.strip() if location_elem else ''
            
            salary_elem = card.find('span', class_='salaryText')
            salary = salary_elem.text.strip() if salary_elem else ''
            
            return {
                'id': f"indeed_{hash(job_url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'portal': 'indeed',
                'description': ''
            }
        
        except Exception as e:
            logger.error(f"Error extracting Indeed job details: {str(e)}")
            return None

class WellfoundScraper(BaseScraper):
    """Wellfound (AngelList) job scraper"""
    
    def search_jobs(self, search_criteria):
        """Search Wellfound jobs"""
        jobs = []
        
        try:
            driver = self.get_driver()
            
            base_url = "https://wellfound.com/jobs"
            params = {
                'keywords': ' '.join(search_criteria.get('roles', [])),
                'location': search_criteria.get('location', 'India'),
                'remote': 'true' if 'remote' in search_criteria.get('location', '').lower() else 'false'
            }
            
            url = f"{base_url}?{urlencode(params)}"
            driver.get(url)
            
            time.sleep(3)
            
            # Extract job listings
            job_cards = driver.find_elements(By.CSS_SELECTOR, '[data-test="JobCard"]')
            
            for card in job_cards[:20]:
                try:
                    job = self._extract_wellfound_job(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting Wellfound job: {str(e)}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Wellfound search error: {str(e)}")
        
        return jobs
    
    def _extract_wellfound_job(self, card):
        """Extract job details from Wellfound card"""
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, '[data-test="JobTitle"]')
            title = title_elem.text.strip()
            
            company_elem = card.find_element(By.CSS_SELECTOR, '[data-test="CompanyName"]')
            company = company_elem.text.strip()
            
            location_elem = card.find_element(By.CSS_SELECTOR, '[data-test="JobLocation"]')
            location = location_elem.text.strip()
            
            # Try to get salary info
            salary = ''
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, '[data-test="JobSalary"]')
                salary = salary_elem.text.strip()
            except:
                pass
            
            job_url = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
            return {
                'id': f"wellfound_{hash(job_url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'portal': 'wellfound',
                'description': ''
            }
        
        except Exception as e:
            logger.error(f"Error extracting Wellfound job details: {str(e)}")
            return None

class RemoteOKScraper(BaseScraper):
    """RemoteOK job scraper"""
    
    def search_jobs(self, search_criteria):
        """Search RemoteOK jobs"""
        jobs = []
        
        try:
            base_url = "https://remoteok.io/remote-jobs"
            
            response = self.session.get(base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job listings
            job_cards = soup.find_all('tr', class_='job')
            
            for card in job_cards[:20]:
                try:
                    job = self._extract_remoteok_job(card)
                    if job and self._is_relevant_job(job, search_criteria):
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting RemoteOK job: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"RemoteOK search error: {str(e)}")
        
        return jobs
    
    def _extract_remoteok_job(self, card):
        """Extract job details from RemoteOK card"""
        try:
            title_elem = card.find('h2', itemprop='title')
            if not title_elem:
                return None
            
            title = title_elem.text.strip()
            
            company_elem = card.find('h3', itemprop='name')
            company = company_elem.text.strip() if company_elem else ''
            
            location = 'Remote'
            
            salary_elem = card.find('span', class_='salary')
            salary = salary_elem.text.strip() if salary_elem else ''
            
            job_url = f"https://remoteok.io{card.get('data-href', '')}"
            
            return {
                'id': f"remoteok_{hash(job_url)}",
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'url': job_url,
                'portal': 'remoteok',
                'description': ''
            }
        
        except Exception as e:
            logger.error(f"Error extracting RemoteOK job details: {str(e)}")
            return None
    
    def _is_relevant_job(self, job, search_criteria):
        """Check if RemoteOK job is relevant"""
        job_text = job.get('title', '').lower()
        target_roles = [role.lower() for role in search_criteria.get('roles', [])]
        
        return any(role in job_text for role in target_roles)