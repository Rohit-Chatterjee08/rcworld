"""
Flask web application for job automation tool
Provides a web-based dashboard for managing job searches and applications
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from database import JobDatabase
from search import JobSearcher
from apply import JobApplicator
from scheduler import JobAutomationScheduler
from utils import load_config, save_config, setup_logging
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Global variables
scheduler = None
config = None
database = None

logger = logging.getLogger(__name__)

def init_app():
    """Initialize the Flask application"""
    global config, database
    
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    # Initialize database
    database = JobDatabase(config.get('database', {}).get('path', 'data/jobs.db'))
    
    logger.info("Flask application initialized")

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get application statistics
        stats = database.get_application_stats()
        
        # Get recent activity
        recent_activity = database.get_recent_activity(10)
        
        # Get eligible jobs
        eligible_jobs = database.get_eligible_jobs(5)
        
        # Get scheduler status
        scheduler_status = get_scheduler_status()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_activity=recent_activity,
                             eligible_jobs=eligible_jobs,
                             scheduler_status=scheduler_status)
    
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f"Error loading dashboard: {e}", 'error')
        return render_template('error.html', error=str(e))

@app.route('/jobs')
def jobs():
    """Jobs listing page"""
    try:
        # Get all jobs from database
        jobs = database.get_eligible_jobs(50)
        
        return render_template('jobs.html', jobs=jobs)
    
    except Exception as e:
        logger.error(f"Error loading jobs: {e}")
        flash(f"Error loading jobs: {e}", 'error')
        return render_template('error.html', error=str(e))

@app.route('/applications')
def applications():
    """Applications listing page"""
    try:
        # Get application statistics
        stats = database.get_application_stats()
        
        # Get recent activity (applications)
        activities = database.get_recent_activity(50)
        application_activities = [a for a in activities if 'application' in a['action']]
        
        return render_template('applications.html', 
                             stats=stats, 
                             activities=application_activities)
    
    except Exception as e:
        logger.error(f"Error loading applications: {e}")
        flash(f"Error loading applications: {e}", 'error')
        return render_template('error.html', error=str(e))

@app.route('/settings')
def settings():
    """Settings page"""
    try:
        return render_template('settings.html', config=config)
    
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        flash(f"Error loading settings: {e}", 'error')
        return render_template('error.html', error=str(e))

@app.route('/update-settings', methods=['POST'])
def update_settings():
    """Update application settings"""
    try:
        global config
        
        # Update user information
        user_info = config.get('user_info', {})
        user_info['name'] = request.form.get('name', '')
        user_info['email'] = request.form.get('email', '')
        user_info['phone'] = request.form.get('phone', '')
        user_info['location'] = request.form.get('location', '')
        user_info['experience_years'] = int(request.form.get('experience_years', 0))
        
        # Update job criteria
        job_criteria = config.get('job_criteria', {})
        job_criteria['min_salary_lpa'] = int(request.form.get('min_salary_lpa', 7))
        
        # Update automation settings
        automation_settings = config.get('automation_settings', {})
        automation_settings['max_applications_per_day'] = int(request.form.get('max_applications_per_day', 20))
        automation_settings['delay_between_applications'] = int(request.form.get('delay_between_applications', 60))
        automation_settings['dry_run'] = 'dry_run' in request.form
        
        # Update scheduler settings
        scheduler_config = config.get('scheduler', {})
        scheduler_config['enabled'] = 'scheduler_enabled' in request.form
        
        # Save configuration
        save_config(config)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        flash(f"Error updating settings: {e}", 'error')
        return redirect(url_for('settings'))

@app.route('/api/search-jobs', methods=['POST'])
def api_search_jobs():
    """API endpoint to search for jobs"""
    try:
        searcher = JobSearcher(config, database)
        jobs = searcher.search_all_portals()
        searcher.close()
        
        return jsonify({
            'success': True,
            'jobs_found': len(jobs),
            'jobs': jobs[:10]  # Return first 10 jobs
        })
    
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/apply-jobs', methods=['POST'])
def api_apply_jobs():
    """API endpoint to apply to jobs"""
    try:
        # Get job IDs from request
        job_ids = request.json.get('job_ids', [])
        
        if not job_ids:
            # Apply to all eligible jobs
            jobs = database.get_eligible_jobs(10)
        else:
            # Apply to specific jobs
            jobs = []
            for job_id in job_ids:
                # This would need to be implemented in database.py
                pass
        
        applicator = JobApplicator(config, database)
        results = applicator.apply_to_jobs(jobs)
        applicator.close()
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        return jsonify({
            'success': True,
            'total_applications': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error applying to jobs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/scheduler/<action>', methods=['POST'])
def api_scheduler(action):
    """API endpoint to control scheduler"""
    try:
        global scheduler
        
        if action == 'start':
            if scheduler is None:
                scheduler = JobAutomationScheduler()
            
            if not scheduler.is_running:
                scheduler.start()
                return jsonify({'success': True, 'message': 'Scheduler started'})
            else:
                return jsonify({'success': False, 'message': 'Scheduler already running'})
        
        elif action == 'stop':
            if scheduler and scheduler.is_running:
                scheduler.stop()
                return jsonify({'success': True, 'message': 'Scheduler stopped'})
            else:
                return jsonify({'success': False, 'message': 'Scheduler not running'})
        
        elif action == 'status':
            status = get_scheduler_status()
            return jsonify({'success': True, 'status': status})
        
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
    
    except Exception as e:
        logger.error(f"Error controlling scheduler: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """API endpoint to get application statistics"""
    try:
        stats = database.get_application_stats()
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/activity')
def api_activity():
    """API endpoint to get recent activity"""
    try:
        limit = request.args.get('limit', 20, type=int)
        activity = database.get_recent_activity(limit)
        return jsonify({'success': True, 'activity': activity})
    
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/backup', methods=['POST'])
def api_backup():
    """API endpoint to create database backup"""
    try:
        backup_path = database.backup_database()
        return jsonify({'success': True, 'backup_path': backup_path})
    
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify({'success': False, 'error': str(e)})

def get_scheduler_status():
    """Get scheduler status"""
    global scheduler
    
    if scheduler is None:
        return {'is_running': False, 'message': 'Scheduler not initialized'}
    
    try:
        return scheduler.get_scheduler_status()
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {'is_running': False, 'error': str(e)}

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Template functions
@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime for templates"""
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return value
    return value

if __name__ == '__main__':
    # Initialize application
    init_app()
    
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Create basic templates if they don't exist
    create_basic_templates()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)

def create_basic_templates():
    """Create basic HTML templates"""
    
    # Base template
    base_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Automation Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">Job Automation Tool</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('jobs') }}">Jobs</a>
                <a class="nav-link" href="{{ url_for('applications') }}">Applications</a>
                <a class="nav-link" href="{{ url_for('settings') }}">Settings</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""
    
    # Dashboard template
    dashboard_template = """
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1>Job Automation Dashboard</h1>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Total Applications</h5>
                <h2 class="text-primary">{{ stats.total_applications }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Today's Applications</h5>
                <h2 class="text-success">{{ stats.today_applications }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Success Rate</h5>
                <h2 class="text-info">{{ "%.1f"|format(stats.success_rate) }}%</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Scheduler Status</h5>
                <h2 class="text-{{ 'success' if scheduler_status.is_running else 'danger' }}">
                    {{ 'Running' if scheduler_status.is_running else 'Stopped' }}
                </h2>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Quick Actions</h5>
            </div>
            <div class="card-body">
                <button class="btn btn-primary me-2" onclick="searchJobs()">Search Jobs</button>
                <button class="btn btn-success me-2" onclick="applyToJobs()">Apply to Jobs</button>
                <button class="btn btn-info me-2" onclick="toggleScheduler()">
                    {{ 'Stop' if scheduler_status.is_running else 'Start' }} Scheduler
                </button>
                <button class="btn btn-warning" onclick="createBackup()">Create Backup</button>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Recent Activity</h5>
            </div>
            <div class="card-body">
                <div style="max-height: 300px; overflow-y: auto;">
                    {% for activity in recent_activity %}
                    <div class="mb-2">
                        <small class="text-muted">{{ activity.timestamp|datetime }}</small><br>
                        <strong>{{ activity.action }}</strong>
                        {% if activity.details %}
                        <br><small>{{ activity.details }}</small>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function searchJobs() {
    $.post('/api/search-jobs', function(data) {
        if (data.success) {
            alert('Found ' + data.jobs_found + ' jobs!');
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function applyToJobs() {
    $.post('/api/apply-jobs', function(data) {
        if (data.success) {
            alert('Applied to ' + data.total_applications + ' jobs!');
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function toggleScheduler() {
    var action = {{ 'stop' if scheduler_status.is_running else 'start' }};
    $.post('/api/scheduler/' + action, function(data) {
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function createBackup() {
    $.post('/api/backup', function(data) {
        if (data.success) {
            alert('Backup created: ' + data.backup_path);
        } else {
            alert('Error: ' + data.error);
        }
    });
}
</script>
{% endblock %}
"""
    
    # Write templates
    os.makedirs('templates', exist_ok=True)
    
    with open('templates/base.html', 'w') as f:
        f.write(base_template)
    
    with open('templates/dashboard.html', 'w') as f:
        f.write(dashboard_template)
    
    # Create a simple error template
    error_template = """
{% extends "base.html" %}

{% block content %}
<div class="alert alert-danger" role="alert">
    <h4 class="alert-heading">Error!</h4>
    <p>{{ error }}</p>
</div>
{% endblock %}
"""
    
    with open('templates/error.html', 'w') as f:
        f.write(error_template)