"""
Job application automation module
Handles automated application submission with form filling, resume upload, and tracking
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database import JobDatabase
from utils import (
    create_driver, random_delay, safe_click, safe_send_keys, 
    take_screenshot, generate_cover_letter, wait_for_element
)

logger = logging.getLogger(__name__)

class JobApplicator:
    """Main job application automation class"""
    
    def __init__(self, config: Dict, database: JobDatabase):
        self.config = config
        self.database = database
        self.driver = None
        self.user_info = config.get('user_info', {})
        self.automation_settings = config.get('automation_settings', {})
        
    def apply_to_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Apply to a list of jobs"""
        application_results = []
        
        # Check daily application limit
        daily_count = self.database.get_daily_application_count()
        max_daily = self.automation_settings.get('max_applications_per_day', 20)
        
        if daily_count >= max_daily:
            logger.warning(f"Daily application limit ({max_daily}) reached")
            return application_results
        
        # Initialize driver
        if not self.driver:
            self.driver = create_driver(self.automation_settings.get('headless_browser', True))
        
        for job in jobs:
            try:
                # Check if we've reached daily limit
                if len(application_results) >= (max_daily - daily_count):
                    logger.info("Daily application limit reached during processing")
                    break
                
                logger.info(f"Applying to: {job['title']} at {job['company']}")
                
                # Apply to job
                result = self.apply_to_single_job(job)
                application_results.append(result)
                
                # Add delay between applications
                delay = self.automation_settings.get('delay_between_applications', 60)
                random_delay(delay, delay + 30)
                
            except Exception as e:
                logger.error(f"Error applying to job {job['title']}: {e}")
                
                # Record failed application
                application_data = {
                    'status': 'failed',
                    'error_message': str(e),
                    'application_method': 'automated'
                }
                
                self.database.add_application(job['id'], application_data)
                
                result = {
                    'job': job,
                    'status': 'failed',
                    'error': str(e)
                }
                application_results.append(result)
                
        return application_results
    
    def apply_to_single_job(self, job: Dict) -> Dict:
        """Apply to a single job"""
        job_url = job['job_url']
        portal = job['portal']
        
        try:
            # Navigate to job URL
            self.driver.get(job_url)
            random_delay(3, 5)
            
            # Take screenshot for debugging
            screenshot_path = None
            if self.automation_settings.get('screenshot_on_error', True):
                screenshot_path = take_screenshot(self.driver)
            
            # Apply based on portal
            if portal == 'linkedin':
                success = self.apply_linkedin_job(job)
            elif portal == 'naukri':
                success = self.apply_naukri_job(job)
            elif portal == 'indeed':
                success = self.apply_indeed_job(job)
            elif portal == 'wellfound':
                success = self.apply_wellfound_job(job)
            elif portal == 'remoteok':
                success = self.apply_remoteok_job(job)
            else:
                success = self.apply_generic_job(job)
            
            # Record application
            status = 'success' if success else 'failed'
            application_data = {
                'status': status,
                'application_method': 'automated',
                'resume_used': self.user_info.get('resume_path', ''),
                'cover_letter': generate_cover_letter(job, self.config),
                'screenshot_path': screenshot_path
            }
            
            self.database.add_application(job['id'], application_data)
            
            return {
                'job': job,
                'status': status,
                'screenshot_path': screenshot_path
            }
            
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            raise
    
    def apply_linkedin_job(self, job: Dict) -> bool:
        """Apply to LinkedIn job"""
        try:
            # Find and click apply button
            apply_button = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                ".jobs-apply-button, .jobs-s-apply button, [data-control-name='jobdetails_topcard_inapply']"
            )
            
            if not apply_button:
                logger.warning("Apply button not found on LinkedIn")
                return False
            
            if not safe_click(self.driver, apply_button):
                return False
            
            # Handle different application flows
            random_delay(2, 3)
            
            # Check if it's an external application
            if "external" in self.driver.current_url or "redirect" in self.driver.current_url:
                logger.info("LinkedIn job redirects to external site")
                return self.apply_generic_job(job)
            
            # Fill LinkedIn application form
            return self.fill_linkedin_form(job)
            
        except Exception as e:
            logger.error(f"Error applying to LinkedIn job: {e}")
            return False
    
    def apply_naukri_job(self, job: Dict) -> bool:
        """Apply to Naukri job"""
        try:
            # Find apply button
            apply_button = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                ".apply-button, .btn-apply, [data-qa='apply_btn']"
            )
            
            if not apply_button:
                logger.warning("Apply button not found on Naukri")
                return False
            
            if not safe_click(self.driver, apply_button):
                return False
            
            random_delay(2, 3)
            
            # Fill Naukri application form
            return self.fill_naukri_form(job)
            
        except Exception as e:
            logger.error(f"Error applying to Naukri job: {e}")
            return False
    
    def apply_indeed_job(self, job: Dict) -> bool:
        """Apply to Indeed job"""
        try:
            # Find apply button
            apply_button = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                ".jobsearch-IndeedApplyButton, .ia-IndeedApplyButton, [data-jk='apply']"
            )
            
            if not apply_button:
                logger.warning("Apply button not found on Indeed")
                return False
            
            if not safe_click(self.driver, apply_button):
                return False
            
            random_delay(2, 3)
            
            # Fill Indeed application form
            return self.fill_indeed_form(job)
            
        except Exception as e:
            logger.error(f"Error applying to Indeed job: {e}")
            return False
    
    def apply_wellfound_job(self, job: Dict) -> bool:
        """Apply to Wellfound job"""
        try:
            # Find apply button
            apply_button = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                ".apply-button, .btn-primary, [data-test='apply-button']"
            )
            
            if not apply_button:
                logger.warning("Apply button not found on Wellfound")
                return False
            
            if not safe_click(self.driver, apply_button):
                return False
            
            random_delay(2, 3)
            
            # Fill Wellfound application form
            return self.fill_wellfound_form(job)
            
        except Exception as e:
            logger.error(f"Error applying to Wellfound job: {e}")
            return False
    
    def apply_remoteok_job(self, job: Dict) -> bool:
        """Apply to RemoteOK job"""
        try:
            # RemoteOK usually redirects to company application pages
            # Look for email or external application links
            
            # Check for email application
            email_link = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "a[href^='mailto:']"
            )
            
            if email_link:
                email = email_link.get_attribute('href').replace('mailto:', '')
                logger.info(f"RemoteOK job requires email application to: {email}")
                # Could implement email automation here
                return False
            
            # Check for external application link
            apply_link = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                ".apply, .btn-apply, [href*='apply']"
            )
            
            if apply_link:
                if not safe_click(self.driver, apply_link):
                    return False
                random_delay(2, 3)
                return self.apply_generic_job(job)
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying to RemoteOK job: {e}")
            return False
    
    def apply_generic_job(self, job: Dict) -> bool:
        """Apply to generic job (company career page or unknown portal)"""
        try:
            # Look for common apply button patterns
            apply_selectors = [
                ".apply-button", ".btn-apply", ".apply-now", 
                "[data-testid='apply-button']", "[data-qa='apply']",
                "button:contains('Apply')", "a:contains('Apply')",
                ".job-apply", ".application-button"
            ]
            
            apply_button = None
            for selector in apply_selectors:
                apply_button = wait_for_element(self.driver, By.CSS_SELECTOR, selector)
                if apply_button:
                    break
            
            if not apply_button:
                logger.warning("No apply button found for generic job")
                return False
            
            if not safe_click(self.driver, apply_button):
                return False
            
            random_delay(2, 3)
            
            # Fill generic application form
            return self.fill_generic_form(job)
            
        except Exception as e:
            logger.error(f"Error applying to generic job: {e}")
            return False
    
    def fill_linkedin_form(self, job: Dict) -> bool:
        """Fill LinkedIn application form"""
        try:
            # Common LinkedIn form fields
            form_fields = {
                'firstName': self.user_info.get('name', '').split()[0],
                'lastName': ' '.join(self.user_info.get('name', '').split()[1:]),
                'email': self.user_info.get('email', ''),
                'phone': self.user_info.get('phone', ''),
            }
            
            # Fill form fields
            for field_name, value in form_fields.items():
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name='{field_name}'], input[id='{field_name}']"
                )
                
                if field and value:
                    safe_send_keys(field, value)
            
            # Upload resume
            resume_uploaded = self.upload_resume()
            
            # Fill cover letter if available
            cover_letter_field = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "textarea[name='coverLetter'], textarea[id='coverLetter']"
            )
            
            if cover_letter_field:
                cover_letter = generate_cover_letter(job, self.config)
                if cover_letter:
                    safe_send_keys(cover_letter_field, cover_letter)
            
            # Submit application if not in dry run mode
            if not self.automation_settings.get('dry_run', True):
                submit_button = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    "button[type='submit'], .submit-btn, .apply-submit"
                )
                
                if submit_button:
                    safe_click(self.driver, submit_button)
                    random_delay(2, 3)
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling LinkedIn form: {e}")
            return False
    
    def fill_naukri_form(self, job: Dict) -> bool:
        """Fill Naukri application form"""
        try:
            # Naukri often just requires clicking apply if logged in
            # Check if additional form is needed
            
            # Look for additional form fields
            name_field = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "input[name='name'], input[id='name']"
            )
            
            if name_field:
                safe_send_keys(name_field, self.user_info.get('name', ''))
            
            email_field = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "input[name='email'], input[id='email']"
            )
            
            if email_field:
                safe_send_keys(email_field, self.user_info.get('email', ''))
            
            phone_field = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "input[name='phone'], input[id='phone']"
            )
            
            if phone_field:
                safe_send_keys(phone_field, self.user_info.get('phone', ''))
            
            # Submit application
            if not self.automation_settings.get('dry_run', True):
                submit_button = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    "button[type='submit'], .submit-btn, .apply-submit"
                )
                
                if submit_button:
                    safe_click(self.driver, submit_button)
                    random_delay(2, 3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling Naukri form: {e}")
            return False
    
    def fill_indeed_form(self, job: Dict) -> bool:
        """Fill Indeed application form"""
        try:
            # Indeed form fields
            form_fields = {
                'applicant.name': self.user_info.get('name', ''),
                'applicant.email': self.user_info.get('email', ''),
                'applicant.phoneNumber': self.user_info.get('phone', ''),
            }
            
            # Fill form fields
            for field_name, value in form_fields.items():
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name='{field_name}'], input[id='{field_name}']"
                )
                
                if field and value:
                    safe_send_keys(field, value)
            
            # Upload resume
            self.upload_resume()
            
            # Submit application
            if not self.automation_settings.get('dry_run', True):
                submit_button = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    "button[type='submit'], .ia-continueButton"
                )
                
                if submit_button:
                    safe_click(self.driver, submit_button)
                    random_delay(2, 3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling Indeed form: {e}")
            return False
    
    def fill_wellfound_form(self, job: Dict) -> bool:
        """Fill Wellfound application form"""
        try:
            # Wellfound often requires a note/message
            message_field = wait_for_element(
                self.driver, 
                By.CSS_SELECTOR, 
                "textarea[name='message'], textarea[id='message'], .message-textarea"
            )
            
            if message_field:
                message = generate_cover_letter(job, self.config)
                if message:
                    safe_send_keys(message_field, message)
            
            # Submit application
            if not self.automation_settings.get('dry_run', True):
                submit_button = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    "button[type='submit'], .submit-application"
                )
                
                if submit_button:
                    safe_click(self.driver, submit_button)
                    random_delay(2, 3)
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling Wellfound form: {e}")
            return False
    
    def fill_generic_form(self, job: Dict) -> bool:
        """Fill generic application form"""
        try:
            # Common field patterns
            field_patterns = {
                'name': ['name', 'fullname', 'full-name', 'applicant-name'],
                'email': ['email', 'email-address', 'applicant-email'],
                'phone': ['phone', 'mobile', 'contact', 'phone-number'],
                'experience': ['experience', 'years-experience', 'work-experience'],
                'cover-letter': ['cover-letter', 'message', 'note', 'additional-info']
            }
            
            # Fill name fields
            for pattern in field_patterns['name']:
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name*='{pattern}'], input[id*='{pattern}']"
                )
                
                if field:
                    safe_send_keys(field, self.user_info.get('name', ''))
                    break
            
            # Fill email fields
            for pattern in field_patterns['email']:
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name*='{pattern}'], input[id*='{pattern}']"
                )
                
                if field:
                    safe_send_keys(field, self.user_info.get('email', ''))
                    break
            
            # Fill phone fields
            for pattern in field_patterns['phone']:
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name*='{pattern}'], input[id*='{pattern}']"
                )
                
                if field:
                    safe_send_keys(field, self.user_info.get('phone', ''))
                    break
            
            # Fill experience fields
            for pattern in field_patterns['experience']:
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"input[name*='{pattern}'], select[name*='{pattern}']"
                )
                
                if field:
                    if field.tag_name == 'select':
                        select = Select(field)
                        try:
                            select.select_by_visible_text(str(self.user_info.get('experience_years', 2)))
                        except:
                            pass
                    else:
                        safe_send_keys(field, str(self.user_info.get('experience_years', 2)))
                    break
            
            # Fill cover letter fields
            for pattern in field_patterns['cover-letter']:
                field = wait_for_element(
                    self.driver, 
                    By.CSS_SELECTOR, 
                    f"textarea[name*='{pattern}'], textarea[id*='{pattern}']"
                )
                
                if field:
                    cover_letter = generate_cover_letter(job, self.config)
                    if cover_letter:
                        safe_send_keys(field, cover_letter)
                    break
            
            # Upload resume
            self.upload_resume()
            
            # Submit application
            if not self.automation_settings.get('dry_run', True):
                submit_selectors = [
                    "button[type='submit']", ".submit-btn", ".apply-submit",
                    "button:contains('Submit')", "button:contains('Apply')",
                    ".submit-application", ".send-application"
                ]
                
                for selector in submit_selectors:
                    submit_button = wait_for_element(self.driver, By.CSS_SELECTOR, selector)
                    if submit_button:
                        safe_click(self.driver, submit_button)
                        random_delay(2, 3)
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling generic form: {e}")
            return False
    
    def upload_resume(self) -> bool:
        """Upload resume to application form"""
        try:
            resume_path = self.user_info.get('resume_path', '')
            
            if not resume_path or not os.path.exists(resume_path):
                logger.warning("Resume file not found")
                return False
            
            # Look for file upload fields
            upload_selectors = [
                "input[type='file']",
                "input[name*='resume']",
                "input[name*='cv']",
                "input[id*='resume']",
                "input[id*='cv']",
                ".file-upload input",
                ".resume-upload input"
            ]
            
            for selector in upload_selectors:
                upload_field = wait_for_element(self.driver, By.CSS_SELECTOR, selector)
                if upload_field:
                    try:
                        upload_field.send_keys(os.path.abspath(resume_path))
                        random_delay(1, 2)
                        logger.info("Resume uploaded successfully")
                        return True
                    except Exception as e:
                        logger.error(f"Error uploading resume: {e}")
                        continue
            
            logger.warning("No resume upload field found")
            return False
            
        except Exception as e:
            logger.error(f"Error in upload_resume: {e}")
            return False
    
    def close(self):
        """Close the web driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None