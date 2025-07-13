"""
Job search module for automating job searches across multiple portals
Supports LinkedIn, Naukri, Indeed, Wellfound, RemoteOK, and custom company career pages
"""

import time
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database import JobDatabase
from utils import (
    create_driver, random_delay, clean_text, format_job_data,
    calculate_job_eligibility, extract_salary_info, take_screenshot
)

logger = logging.getLogger(__name__)

class JobSearcher:
    """Main job searcher class that coordinates searches across multiple portals"""
    
    def __init__(self, config: Dict, database: JobDatabase):
        self.config = config
        self.database = database
        self.driver = None
        
    def search_all_portals(self) -> List[Dict]:
        """Search all enabled job portals"""
        all_jobs = []
        job_portals = self.config.get('job_portals', {})
        
        for portal_name, portal_config in job_portals.items():
            if not portal_config.get('enabled', False):
                continue
                
            logger.info(f"Searching {portal_name}...")
            
            try:
                if portal_name == 'linkedin':
                    jobs = self.search_linkedin()
                elif portal_name == 'naukri':
                    jobs = self.search_naukri()
                elif portal_name == 'indeed':
                    jobs = self.search_indeed()
                elif portal_name == 'wellfound':
                    jobs = self.search_wellfound()
                elif portal_name == 'remoteok':
                    jobs = self.search_remoteok()
                else:
                    logger.warning(f"Unknown portal: {portal_name}")
                    continue
                    
                # Process and store jobs
                processed_jobs = self.process_jobs(jobs, portal_name)
                all_jobs.extend(processed_jobs)
                
                logger.info(f"Found {len(processed_jobs)} eligible jobs from {portal_name}")
                
            except Exception as e:
                logger.error(f"Error searching {portal_name}: {e}")
                continue
                
        return all_jobs
    
    def search_linkedin(self) -> List[Dict]:
        """Search LinkedIn for jobs"""
        if not self.driver:
            self.driver = create_driver(self.config.get('automation_settings', {}).get('headless_browser', True))
        
        jobs = []
        criteria = self.config.get('job_criteria', {})
        
        # Build search URL
        base_url = "https://www.linkedin.com/jobs/search/"
        keywords = " OR ".join(criteria.get('roles', []))
        location = "India"
        
        search_params = {
            'keywords': keywords,
            'location': location,
            'f_E': '1,2',  # Entry level and Associate
            'f_WT': '2',   # Remote work
            'sortBy': 'DD'  # Date posted
        }
        
        # Construct URL
        url = f"{base_url}?{'&'.join([f'{k}={quote(str(v))}' for k, v in search_params.items()])}"
        
        try:
            self.driver.get(url)
            random_delay(3, 5)
            
            # Handle login if required
            if "login" in self.driver.current_url:
                logger.warning("LinkedIn login required. Skipping LinkedIn search.")
                return jobs
            
            # Scroll to load more jobs
            self._scroll_to_load_jobs()
            
            # Extract job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_linkedin_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting LinkedIn job data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            
        return jobs
    
    def search_naukri(self) -> List[Dict]:
        """Search Naukri for jobs"""
        if not self.driver:
            self.driver = create_driver(self.config.get('automation_settings', {}).get('headless_browser', True))
        
        jobs = []
        criteria = self.config.get('job_criteria', {})
        
        # Build search URL
        base_url = "https://www.naukri.com/jobs"
        keywords = "-".join(criteria.get('roles', []))
        location = "kolkata"
        
        url = f"{base_url}-{keywords}-{location}"
        
        try:
            self.driver.get(url)
            random_delay(3, 5)
            
            # Extract job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".srp-jobtuple-wrapper")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_naukri_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting Naukri job data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching Naukri: {e}")
            
        return jobs
    
    def search_indeed(self) -> List[Dict]:
        """Search Indeed for jobs"""
        if not self.driver:
            self.driver = create_driver(self.config.get('automation_settings', {}).get('headless_browser', True))
        
        jobs = []
        criteria = self.config.get('job_criteria', {})
        
        # Build search URL
        base_url = "https://in.indeed.com/jobs"
        keywords = " OR ".join(criteria.get('roles', []))
        location = "Kolkata"
        
        search_params = {
            'q': keywords,
            'l': location,
            'sort': 'date',
            'fromage': '7'  # Last 7 days
        }
        
        url = f"{base_url}?{'&'.join([f'{k}={quote(str(v))}' for k, v in search_params.items()])}"
        
        try:
            self.driver.get(url)
            random_delay(3, 5)
            
            # Extract job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobsearch-SerpJobCard")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_indeed_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting Indeed job data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
            
        return jobs
    
    def search_wellfound(self) -> List[Dict]:
        """Search Wellfound (formerly AngelList) for jobs"""
        if not self.driver:
            self.driver = create_driver(self.config.get('automation_settings', {}).get('headless_browser', True))
        
        jobs = []
        criteria = self.config.get('job_criteria', {})
        
        # Build search URL
        base_url = "https://wellfound.com/jobs"
        
        try:
            self.driver.get(base_url)
            random_delay(3, 5)
            
            # Search for specific roles
            search_box = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search']")
            search_box.send_keys(" OR ".join(criteria.get('roles', [])))
            search_box.submit()
            
            random_delay(3, 5)
            
            # Extract job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-listing")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_wellfound_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting Wellfound job data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching Wellfound: {e}")
            
        return jobs
    
    def search_remoteok(self) -> List[Dict]:
        """Search RemoteOK for jobs using requests (no JavaScript needed)"""
        jobs = []
        criteria = self.config.get('job_criteria', {})
        
        # RemoteOK has a simple API-like structure
        url = "https://remoteok.io/remote-dev-jobs"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('tr', class_='job')
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_remoteok_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting RemoteOK job data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching RemoteOK: {e}")
            
        return jobs
    
    def _extract_linkedin_job_data(self, card) -> Optional[Dict]:
        """Extract job data from LinkedIn job card"""
        try:
            # Title and company
            title_elem = card.find_element(By.CSS_SELECTOR, ".job-search-card__title")
            company_elem = card.find_element(By.CSS_SELECTOR, ".job-search-card__subtitle")
            location_elem = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
            
            # Job URL
            link_elem = card.find_element(By.CSS_SELECTOR, "a")
            job_url = link_elem.get_attribute("href")
            
            # Extract additional details by clicking job
            description = ""
            try:
                link_elem.click()
                random_delay(2, 3)
                
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-insight")
                description = desc_elem.text
            except:
                pass
            
            return {
                'title': title_elem.text.strip(),
                'company': company_elem.text.strip(),
                'location': location_elem.text.strip(),
                'job_url': job_url,
                'description': description,
                'portal': 'linkedin'
            }
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job data: {e}")
            return None
    
    def _extract_naukri_job_data(self, card) -> Optional[Dict]:
        """Extract job data from Naukri job card"""
        try:
            # Title and company
            title_elem = card.find_element(By.CSS_SELECTOR, ".jobTuple-bdJobs a")
            company_elem = card.find_element(By.CSS_SELECTOR, ".jobTuple-employerName")
            
            # Experience and salary
            experience_elem = card.find_element(By.CSS_SELECTOR, ".jobTuple-experience span")
            salary_elem = card.find_element(By.CSS_SELECTOR, ".jobTuple-salary span")
            
            # Location
            location_elem = card.find_element(By.CSS_SELECTOR, ".jobTuple-location span")
            
            # Job URL
            job_url = title_elem.get_attribute("href")
            
            return {
                'title': title_elem.text.strip(),
                'company': company_elem.text.strip(),
                'location': location_elem.text.strip(),
                'experience_required': experience_elem.text.strip(),
                'salary': salary_elem.text.strip(),
                'job_url': job_url,
                'portal': 'naukri'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Naukri job data: {e}")
            return None
    
    def _extract_indeed_job_data(self, card) -> Optional[Dict]:
        """Extract job data from Indeed job card"""
        try:
            # Title and company
            title_elem = card.find_element(By.CSS_SELECTOR, "h2 a span")
            company_elem = card.find_element(By.CSS_SELECTOR, ".company")
            location_elem = card.find_element(By.CSS_SELECTOR, ".location")
            
            # Job URL
            link_elem = card.find_element(By.CSS_SELECTOR, "h2 a")
            job_url = "https://in.indeed.com" + link_elem.get_attribute("href")
            
            # Salary if available
            salary = ""
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, ".salary")
                salary = salary_elem.text.strip()
            except:
                pass
            
            return {
                'title': title_elem.text.strip(),
                'company': company_elem.text.strip(),
                'location': location_elem.text.strip(),
                'salary': salary,
                'job_url': job_url,
                'portal': 'indeed'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job data: {e}")
            return None
    
    def _extract_wellfound_job_data(self, card) -> Optional[Dict]:
        """Extract job data from Wellfound job card"""
        try:
            # Title and company
            title_elem = card.find_element(By.CSS_SELECTOR, ".job-title")
            company_elem = card.find_element(By.CSS_SELECTOR, ".company-name")
            
            # Job URL
            link_elem = card.find_element(By.CSS_SELECTOR, "a")
            job_url = link_elem.get_attribute("href")
            
            # Location and salary
            location = "Remote"
            salary = ""
            
            try:
                details = card.find_element(By.CSS_SELECTOR, ".job-details").text
                if "salary" in details.lower():
                    salary = details
            except:
                pass
            
            return {
                'title': title_elem.text.strip(),
                'company': company_elem.text.strip(),
                'location': location,
                'salary': salary,
                'job_url': job_url,
                'portal': 'wellfound'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Wellfound job data: {e}")
            return None
    
    def _extract_remoteok_job_data(self, card) -> Optional[Dict]:
        """Extract job data from RemoteOK job card"""
        try:
            # Title and company
            title_elem = card.find('h2')
            company_elem = card.find('h3')
            
            if not title_elem or not company_elem:
                return None
            
            # Job URL
            link_elem = card.find('a')
            job_url = "https://remoteok.io" + link_elem.get('href') if link_elem else ""
            
            # Tags for requirements
            tags = []
            tag_elements = card.find_all('span', class_='tag')
            for tag in tag_elements:
                tags.append(tag.text.strip())
            
            return {
                'title': title_elem.text.strip(),
                'company': company_elem.text.strip(),
                'location': 'Remote',
                'requirements': ', '.join(tags),
                'job_url': job_url,
                'portal': 'remoteok'
            }
            
        except Exception as e:
            logger.error(f"Error extracting RemoteOK job data: {e}")
            return None
    
    def _scroll_to_load_jobs(self):
        """Scroll to load more jobs on infinite scroll pages"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < 3:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            random_delay(2, 4)
            
            # Check if more content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
                
            last_height = new_height
            scroll_attempts += 1
    
    def process_jobs(self, jobs: List[Dict], portal: str) -> List[Dict]:
        """Process and filter jobs based on criteria"""
        eligible_jobs = []
        
        for job in jobs:
            # Format job data
            formatted_job = format_job_data(job)
            
            # Check if job already exists
            if self.database.check_job_exists(formatted_job['job_url']):
                continue
            
            # Calculate eligibility
            is_eligible, score, matched_keywords = calculate_job_eligibility(formatted_job, self.config)
            
            # Add eligibility data
            formatted_job['is_eligible'] = is_eligible
            formatted_job['eligibility_score'] = score
            formatted_job['keywords_matched'] = matched_keywords
            formatted_job['portal'] = portal
            
            # Store in database
            job_id = self.database.add_job(formatted_job)
            formatted_job['id'] = job_id
            
            if is_eligible:
                eligible_jobs.append(formatted_job)
        
        return eligible_jobs
    
    def search_company_careers(self, company_urls: List[str]) -> List[Dict]:
        """Search company career pages directly"""
        jobs = []
        
        for url in company_urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Generic patterns for job listings
                job_links = soup.find_all('a', href=re.compile(r'job|career|position'))
                
                for link in job_links[:5]:  # Limit to first 5 jobs per company
                    job_url = urljoin(url, link.get('href'))
                    job_title = link.text.strip()
                    
                    if job_title and any(role.lower() in job_title.lower() for role in self.config.get('job_criteria', {}).get('roles', [])):
                        jobs.append({
                            'title': job_title,
                            'company': url.split('//')[1].split('/')[0],
                            'location': 'Remote',
                            'job_url': job_url,
                            'portal': 'company_direct'
                        })
                        
            except Exception as e:
                logger.error(f"Error searching company careers at {url}: {e}")
                continue
        
        return jobs
    
    def close(self):
        """Close the web driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None