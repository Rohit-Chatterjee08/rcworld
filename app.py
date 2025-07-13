from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from models import init_db, save_user_profile, get_user_profile, save_job_application, get_job_applications
from job_search import JobSearchManager
from job_apply import JobApplyManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db()

# Initialize job managers
job_search_manager = JobSearchManager()
job_apply_manager = JobApplyManager()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    """Main dashboard"""
    user_profile = get_user_profile()
    recent_applications = get_job_applications(limit=10)
    return render_template('index.html', user_profile=user_profile, applications=recent_applications)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile management"""
    if request.method == 'POST':
        # Handle profile update
        profile_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'experience': request.form.get('experience'),
            'current_salary': request.form.get('current_salary'),
            'expected_salary': request.form.get('expected_salary'),
            'location': request.form.get('location'),
            'skills': request.form.get('skills'),
            'linkedin_url': request.form.get('linkedin_url'),
            'github_url': request.form.get('github_url'),
            'portfolio_url': request.form.get('portfolio_url')
        }
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                profile_data['resume_path'] = filepath
        
        save_user_profile(profile_data)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    user_profile = get_user_profile()
    return render_template('profile.html', user_profile=user_profile)

@app.route('/job-search', methods=['GET', 'POST'])
def job_search():
    """Job search and filtering"""
    if request.method == 'POST':
        search_criteria = {
            'roles': request.form.getlist('roles'),
            'experience_min': int(request.form.get('experience_min', 0)),
            'experience_max': int(request.form.get('experience_max', 3)),
            'salary_min': int(request.form.get('salary_min', 700000)),
            'location': request.form.get('location', 'Remote'),
            'portals': request.form.getlist('portals')
        }
        
        # Search jobs
        jobs = job_search_manager.search_jobs(search_criteria)
        return render_template('job_search.html', jobs=jobs, search_criteria=search_criteria)
    
    default_criteria = {
        'roles': ['Prompt Engineer', 'AI Engineer'],
        'experience_min': 0,
        'experience_max': 3,
        'salary_min': 700000,
        'location': 'Remote',
        'portals': ['linkedin', 'naukri', 'indeed', 'wellfound']
    }
    
    return render_template('job_search.html', search_criteria=default_criteria)

@app.route('/apply-jobs', methods=['POST'])
def apply_jobs():
    """Apply to selected jobs"""
    job_ids = request.form.getlist('job_ids')
    user_profile = get_user_profile()
    
    if not user_profile:
        flash('Please complete your profile first!', 'error')
        return redirect(url_for('profile'))
    
    results = job_apply_manager.apply_to_jobs(job_ids, user_profile)
    
    # Save application records
    for result in results:
        save_job_application(result)
    
    flash(f'Applied to {len(results)} jobs!', 'success')
    return redirect(url_for('applications'))

@app.route('/applications')
def applications():
    """View application history"""
    applications = get_job_applications()
    return render_template('applications.html', applications=applications)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule_jobs():
    """Schedule automated job applications"""
    if request.method == 'POST':
        schedule_time = request.form.get('schedule_time')
        frequency = request.form.get('frequency')  # daily, weekly
        
        # Remove existing jobs
        for job in scheduler.get_jobs():
            scheduler.remove_job(job.id)
        
        # Add new scheduled job
        if frequency == 'daily':
            hour, minute = map(int, schedule_time.split(':'))
            scheduler.add_job(
                func=run_automated_job_search,
                trigger="cron",
                hour=hour,
                minute=minute,
                id='daily_job_search'
            )
        
        flash(f'Scheduled job search for {schedule_time} {frequency}', 'success')
        return redirect(url_for('schedule_jobs'))
    
    # Get current schedule
    current_jobs = scheduler.get_jobs()
    return render_template('schedule.html', scheduled_jobs=current_jobs)

@app.route('/run-manual')
def run_manual():
    """Run job search manually"""
    try:
        results = run_automated_job_search()
        flash(f'Manual run completed! Found {len(results)} jobs.', 'success')
    except Exception as e:
        flash(f'Error during manual run: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/jobs')
def api_jobs():
    """API endpoint for job data"""
    applications = get_job_applications()
    return jsonify(applications)

def run_automated_job_search():
    """Automated job search and application function"""
    logger.info("Starting automated job search...")
    
    user_profile = get_user_profile()
    if not user_profile:
        logger.error("No user profile found")
        return []
    
    # Default search criteria
    search_criteria = {
        'roles': ['Prompt Engineer', 'AI Engineer'],
        'experience_min': 0,
        'experience_max': 3,
        'salary_min': 700000,
        'location': 'Remote',
        'portals': ['linkedin', 'naukri', 'indeed', 'wellfound']
    }
    
    # Search for jobs
    jobs = job_search_manager.search_jobs(search_criteria)
    logger.info(f"Found {len(jobs)} jobs")
    
    # Apply to suitable jobs
    if jobs:
        job_ids = [job['id'] for job in jobs[:5]]  # Apply to top 5 jobs
        results = job_apply_manager.apply_to_jobs(job_ids, user_profile)
        
        # Save application records
        for result in results:
            save_job_application(result)
        
        logger.info(f"Applied to {len(results)} jobs")
        return results
    
    return []

@app.route('/settings')
def settings():
    """Application settings"""
    return render_template('settings.html')

@app.route('/help')
def help_page():
    """Help and documentation"""
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)