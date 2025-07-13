import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from config import Config
from models import get_duplicate_applications
import os

logger = logging.getLogger(__name__)

class JobApplyManager:
    """Main job application manager"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.applicators = {
            'linkedin': LinkedInApplicator(),
            'naukri': NaukriApplicator(),
            'indeed': IndeedApplicator(),
            'wellfound': WellfoundApplicator(),
            'remoteok': RemoteOKApplicator()
        }
    
    def apply_to_jobs(self, job_ids, user_profile):
        """Apply to multiple jobs"""
        results = []
        
        for job_id in job_ids:
            try:
                # Check daily application limit
                if self._check_daily_limit():
                    logger.warning("Daily application limit reached")
                    break
                
                # Extract portal from job_id
                portal = job_id.split('_')[0]
                
                if portal in self.applicators:
                    applicator = self.applicators[portal]
                    result = applicator.apply_to_job(job_id, user_profile)
                    results.append(result)
                    
                    # Delay between applications
                    time.sleep(Config.APPLICATION_CONFIG['application_delay'])
                
            except Exception as e:
                logger.error(f"Error applying to job {job_id}: {str(e)}")
                results.append({
                    'job_id': job_id,
                    'portal': portal,
                    'application_status': 'failed',
                    'error_message': str(e)
                })
        
        return results
    
    def _check_daily_limit(self):
        """Check if daily application limit is reached"""
        # This would check database for today's applications
        # For now, return False (no limit reached)
        return False

class BaseApplicator:
    """Base class for job application automation"""
    
    def __init__(self):
        self.ua = UserAgent()
    
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
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(Config.SELENIUM_CONFIG['implicit_wait'])
        return driver
    
    def fill_form_field(self, driver, field_selector, value, field_type='input'):
        """Fill a form field with given value"""
        try:
            if field_type == 'input':
                field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, field_selector))
                )
                field.clear()
                field.send_keys(value)
            elif field_type == 'select':
                select_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, field_selector))
                )
                select = Select(select_element)
                select.select_by_visible_text(value)
            elif field_type == 'textarea':
                field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, field_selector))
                )
                field.clear()
                field.send_keys(value)
            
            return True
        except Exception as e:
            logger.error(f"Error filling field {field_selector}: {str(e)}")
            return False
    
    def upload_resume(self, driver, file_input_selector, resume_path):
        """Upload resume file"""
        try:
            if not os.path.exists(resume_path):
                logger.error(f"Resume file not found: {resume_path}")
                return False
            
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, file_input_selector))
            )
            file_input.send_keys(os.path.abspath(resume_path))
            
            # Wait for upload to complete
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
            return False
    
    def click_button(self, driver, button_selector):
        """Click a button or link"""
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )
            button.click()
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Error clicking button {button_selector}: {str(e)}")
            return False
    
    def take_screenshot(self, driver, filename):
        """Take screenshot on error"""
        try:
            if Config.APPLICATION_CONFIG['screenshot_on_error']:
                screenshot_path = f"screenshots/{filename}"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")

class LinkedInApplicator(BaseApplicator):
    """LinkedIn job application automation"""
    
    def apply_to_job(self, job_id, user_profile):
        """Apply to a LinkedIn job"""
        driver = None
        try:
            driver = self.get_driver()
            
            # Note: LinkedIn requires login, which we're not implementing here
            # for security reasons. This is a placeholder structure.
            
            result = {
                'job_id': job_id,
                'portal': 'linkedin',
                'application_status': 'manual_required',
                'notes': 'LinkedIn requires manual login and application'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LinkedIn application error: {str(e)}")
            if driver:
                self.take_screenshot(driver, f"linkedin_error_{job_id}.png")
            
            return {
                'job_id': job_id,
                'portal': 'linkedin',
                'application_status': 'failed',
                'error_message': str(e)
            }
        
        finally:
            if driver:
                driver.quit()

class NaukriApplicator(BaseApplicator):
    """Naukri.com job application automation"""
    
    def apply_to_job(self, job_id, user_profile):
        """Apply to a Naukri job"""
        driver = None
        try:
            driver = self.get_driver()
            
            # Get job URL from job_id (you'd need to store this mapping)
            job_url = self._get_job_url(job_id)
            
            # Navigate to job page
            driver.get(job_url)
            time.sleep(3)
            
            # Click apply button
            apply_button_selectors = [
                'button.naukri-apply-button',
                '.apply-button',
                'button[data-test="apply-btn"]'
            ]
            
            applied = False
            for selector in apply_button_selectors:
                try:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                    button.click()
                    applied = True
                    time.sleep(2)
                    break
                except NoSuchElementException:
                    continue
            
            if not applied:
                raise Exception("Apply button not found")
            
            # Check if application form appears
            if self._check_application_form(driver):
                # Fill application form
                self._fill_naukri_form(driver, user_profile)
                
                # Submit application
                submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                submit_button.click()
                
                # Wait for confirmation
                time.sleep(3)
                
                # Check for success message
                success_indicators = [
                    'Application submitted successfully',
                    'Your application has been sent',
                    'Applied successfully'
                ]
                
                page_text = driver.page_source.lower()
                success = any(indicator.lower() in page_text for indicator in success_indicators)
                
                result = {
                    'job_id': job_id,
                    'portal': 'naukri',
                    'application_status': 'submitted' if success else 'pending',
                    'notes': 'Application submitted via automation'
                }
            else:
                result = {
                    'job_id': job_id,
                    'portal': 'naukri',
                    'application_status': 'quick_apply',
                    'notes': 'Quick apply completed'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Naukri application error: {str(e)}")
            if driver:
                self.take_screenshot(driver, f"naukri_error_{job_id}.png")
            
            return {
                'job_id': job_id,
                'portal': 'naukri',
                'application_status': 'failed',
                'error_message': str(e)
            }
        
        finally:
            if driver:
                driver.quit()
    
    def _get_job_url(self, job_id):
        """Get job URL from job_id"""
        # This would typically query your database
        # For now, return a placeholder
        return f"https://www.naukri.com/job-listings-{job_id}"
    
    def _check_application_form(self, driver):
        """Check if application form is present"""
        form_selectors = [
            'form.application-form',
            '.apply-form',
            'form[data-test="application-form"]'
        ]
        
        for selector in form_selectors:
            try:
                driver.find_element(By.CSS_SELECTOR, selector)
                return True
            except NoSuchElementException:
                continue
        
        return False
    
    def _fill_naukri_form(self, driver, user_profile):
        """Fill Naukri application form"""
        # Fill name
        self.fill_form_field(driver, 'input[name="name"]', user_profile.get('name', ''))
        
        # Fill email
        self.fill_form_field(driver, 'input[name="email"]', user_profile.get('email', ''))
        
        # Fill phone
        self.fill_form_field(driver, 'input[name="phone"]', user_profile.get('phone', ''))
        
        # Fill experience
        if user_profile.get('experience'):
            self.fill_form_field(driver, 'select[name="experience"]', 
                               f"{user_profile['experience']} years", 'select')
        
        # Fill current salary
        if user_profile.get('current_salary'):
            self.fill_form_field(driver, 'input[name="current_salary"]', 
                               str(user_profile['current_salary']))
        
        # Fill expected salary
        if user_profile.get('expected_salary'):
            self.fill_form_field(driver, 'input[name="expected_salary"]', 
                               str(user_profile['expected_salary']))
        
        # Upload resume
        if user_profile.get('resume_path'):
            self.upload_resume(driver, 'input[type="file"]', user_profile['resume_path'])
        
        # Fill cover letter or additional info
        cover_letter = self._generate_cover_letter(user_profile)
        self.fill_form_field(driver, 'textarea[name="cover_letter"]', cover_letter, 'textarea')
    
    def _generate_cover_letter(self, user_profile):
        """Generate a simple cover letter"""
        return f"""Dear Hiring Manager,

I am writing to express my interest in this position. With {user_profile.get('experience', 0)} years of experience in {user_profile.get('skills', 'technology')}, I am excited about the opportunity to contribute to your team.

My key skills include: {user_profile.get('skills', 'Python, AI, Machine Learning')}

I am currently based in {user_profile.get('location', 'India')} and am available for {user_profile.get('location', 'remote work')}.

Thank you for your consideration.

Best regards,
{user_profile.get('name', 'Job Seeker')}"""

class IndeedApplicator(BaseApplicator):
    """Indeed job application automation"""
    
    def apply_to_job(self, job_id, user_profile):
        """Apply to an Indeed job"""
        driver = None
        try:
            driver = self.get_driver()
            
            # Get job URL
            job_url = self._get_job_url(job_id)
            driver.get(job_url)
            time.sleep(3)
            
            # Look for apply button
            apply_selectors = [
                'button[data-jk="apply-button"]',
                '.indeed-apply-button',
                'button.apply-button',
                'a.apply-button'
            ]
            
            applied = False
            for selector in apply_selectors:
                try:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                    button.click()
                    applied = True
                    time.sleep(2)
                    break
                except NoSuchElementException:
                    continue
            
            if not applied:
                raise Exception("Apply button not found")
            
            # Check if it's Indeed Apply or external redirect
            if "indeed.com" in driver.current_url:
                # Indeed Apply form
                self._fill_indeed_form(driver, user_profile)
                
                # Submit application
                submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                submit_button.click()
                
                time.sleep(3)
                
                result = {
                    'job_id': job_id,
                    'portal': 'indeed',
                    'application_status': 'submitted',
                    'notes': 'Applied via Indeed Apply'
                }
            else:
                result = {
                    'job_id': job_id,
                    'portal': 'indeed',
                    'application_status': 'external_redirect',
                    'notes': 'Redirected to company website'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Indeed application error: {str(e)}")
            if driver:
                self.take_screenshot(driver, f"indeed_error_{job_id}.png")
            
            return {
                'job_id': job_id,
                'portal': 'indeed',
                'application_status': 'failed',
                'error_message': str(e)
            }
        
        finally:
            if driver:
                driver.quit()
    
    def _get_job_url(self, job_id):
        """Get job URL from job_id"""
        return f"https://in.indeed.com/viewjob?jk={job_id}"
    
    def _fill_indeed_form(self, driver, user_profile):
        """Fill Indeed application form"""
        # Fill standard fields
        self.fill_form_field(driver, 'input[name="name"]', user_profile.get('name', ''))
        self.fill_form_field(driver, 'input[name="email"]', user_profile.get('email', ''))
        self.fill_form_field(driver, 'input[name="phone"]', user_profile.get('phone', ''))
        
        # Upload resume
        if user_profile.get('resume_path'):
            self.upload_resume(driver, 'input[type="file"]', user_profile['resume_path'])

class WellfoundApplicator(BaseApplicator):
    """Wellfound job application automation"""
    
    def apply_to_job(self, job_id, user_profile):
        """Apply to a Wellfound job"""
        # Similar structure to other applicators
        # Implementation would depend on Wellfound's application flow
        
        return {
            'job_id': job_id,
            'portal': 'wellfound',
            'application_status': 'manual_required',
            'notes': 'Wellfound applications require manual handling'
        }

class RemoteOKApplicator(BaseApplicator):
    """RemoteOK job application automation"""
    
    def apply_to_job(self, job_id, user_profile):
        """Apply to a RemoteOK job"""
        # RemoteOK typically redirects to company websites
        # So this would mostly be about opening the application link
        
        return {
            'job_id': job_id,
            'portal': 'remoteok',
            'application_status': 'external_redirect',
            'notes': 'RemoteOK jobs typically redirect to company websites'
        }

class FormFieldMapper:
    """Maps user profile fields to common form field patterns"""
    
    FIELD_MAPPINGS = {
        'name': [
            'input[name="name"]',
            'input[name="fullname"]',
            'input[name="full_name"]',
            'input[id="name"]',
            'input[placeholder*="name"]'
        ],
        'email': [
            'input[name="email"]',
            'input[type="email"]',
            'input[id="email"]',
            'input[placeholder*="email"]'
        ],
        'phone': [
            'input[name="phone"]',
            'input[name="mobile"]',
            'input[type="tel"]',
            'input[id="phone"]',
            'input[placeholder*="phone"]'
        ],
        'resume': [
            'input[type="file"]',
            'input[name="resume"]',
            'input[name="cv"]',
            'input[accept=".pdf"]'
        ]
    }
    
    @classmethod
    def get_field_selectors(cls, field_type):
        """Get possible selectors for a field type"""
        return cls.FIELD_MAPPINGS.get(field_type, [])

class ApplicationValidator:
    """Validates application attempts and prevents duplicates"""
    
    def __init__(self):
        pass
    
    def validate_application(self, job_id, user_profile):
        """Validate if application should proceed"""
        # Check for duplicates
        job_title = self._extract_job_title(job_id)
        company = self._extract_company(job_id)
        
        duplicates = get_duplicate_applications(job_title, company)
        if duplicates:
            return False, "Already applied to this job"
        
        # Check if user profile is complete
        required_fields = ['name', 'email', 'phone']
        for field in required_fields:
            if not user_profile.get(field):
                return False, f"Missing required field: {field}"
        
        return True, "Validation passed"
    
    def _extract_job_title(self, job_id):
        """Extract job title from job_id"""
        # This would typically query your database
        return "Unknown Job"
    
    def _extract_company(self, job_id):
        """Extract company from job_id"""
        # This would typically query your database
        return "Unknown Company"