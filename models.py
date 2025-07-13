import sqlite3
import json
from datetime import datetime
from config import Config

DB_PATH = Config.DATABASE_PATH

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User Profile table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            experience INTEGER,
            current_salary INTEGER,
            expected_salary INTEGER,
            location TEXT,
            skills TEXT,
            resume_path TEXT,
            linkedin_url TEXT,
            github_url TEXT,
            portfolio_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Job Applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY,
            job_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            portal TEXT NOT NULL,
            job_url TEXT,
            salary_range TEXT,
            location TEXT,
            job_description TEXT,
            application_status TEXT DEFAULT 'pending',
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_date TIMESTAMP,
            notes TEXT,
            error_message TEXT
        )
    ''')
    
    # Job Search History table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY,
            search_criteria TEXT,
            results_count INTEGER,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            portals_searched TEXT
        )
    ''')
    
    # Application Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_user_profile(profile_data):
    """Save or update user profile"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if profile exists
    cursor.execute('SELECT id FROM user_profile LIMIT 1')
    existing = cursor.fetchone()
    
    if existing:
        # Update existing profile
        cursor.execute('''
            UPDATE user_profile SET
                name = ?,
                email = ?,
                phone = ?,
                experience = ?,
                current_salary = ?,
                expected_salary = ?,
                location = ?,
                skills = ?,
                resume_path = ?,
                linkedin_url = ?,
                github_url = ?,
                portfolio_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            profile_data.get('name'),
            profile_data.get('email'),
            profile_data.get('phone'),
            profile_data.get('experience'),
            profile_data.get('current_salary'),
            profile_data.get('expected_salary'),
            profile_data.get('location'),
            profile_data.get('skills'),
            profile_data.get('resume_path'),
            profile_data.get('linkedin_url'),
            profile_data.get('github_url'),
            profile_data.get('portfolio_url'),
            existing[0]
        ))
    else:
        # Insert new profile
        cursor.execute('''
            INSERT INTO user_profile (
                name, email, phone, experience, current_salary, expected_salary,
                location, skills, resume_path, linkedin_url, github_url, portfolio_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_data.get('name'),
            profile_data.get('email'),
            profile_data.get('phone'),
            profile_data.get('experience'),
            profile_data.get('current_salary'),
            profile_data.get('expected_salary'),
            profile_data.get('location'),
            profile_data.get('skills'),
            profile_data.get('resume_path'),
            profile_data.get('linkedin_url'),
            profile_data.get('github_url'),
            profile_data.get('portfolio_url')
        ))
    
    conn.commit()
    conn.close()

def get_user_profile():
    """Get user profile"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_profile LIMIT 1')
    profile = cursor.fetchone()
    
    conn.close()
    
    if profile:
        return dict(profile)
    return None

def save_job_application(application_data):
    """Save job application record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO job_applications (
            job_id, job_title, company, portal, job_url, salary_range,
            location, job_description, application_status, notes, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        application_data.get('job_id'),
        application_data.get('job_title'),
        application_data.get('company'),
        application_data.get('portal'),
        application_data.get('job_url'),
        application_data.get('salary_range'),
        application_data.get('location'),
        application_data.get('job_description'),
        application_data.get('application_status', 'pending'),
        application_data.get('notes'),
        application_data.get('error_message')
    ))
    
    conn.commit()
    conn.close()

def get_job_applications(limit=None):
    """Get job applications with optional limit"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('''
            SELECT * FROM job_applications 
            ORDER BY application_date DESC 
            LIMIT ?
        ''', (limit,))
    else:
        cursor.execute('''
            SELECT * FROM job_applications 
            ORDER BY application_date DESC
        ''')
    
    applications = cursor.fetchall()
    conn.close()
    
    return [dict(app) for app in applications]

def update_application_status(application_id, status, notes=None):
    """Update application status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE job_applications 
        SET application_status = ?, notes = ?, response_date = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, notes, application_id))
    
    conn.commit()
    conn.close()

def save_search_history(search_criteria, results_count, portals_searched):
    """Save search history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO search_history (search_criteria, results_count, portals_searched)
        VALUES (?, ?, ?)
    ''', (
        json.dumps(search_criteria),
        results_count,
        json.dumps(portals_searched)
    ))
    
    conn.commit()
    conn.close()

def get_search_history(limit=10):
    """Get search history"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM search_history 
        ORDER BY search_date DESC 
        LIMIT ?
    ''', (limit,))
    
    history = cursor.fetchall()
    conn.close()
    
    return [dict(h) for h in history]

def get_application_stats():
    """Get application statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total applications
    cursor.execute('SELECT COUNT(*) FROM job_applications')
    total_applications = cursor.fetchone()[0]
    
    # Applications by status
    cursor.execute('''
        SELECT application_status, COUNT(*) 
        FROM job_applications 
        GROUP BY application_status
    ''')
    status_counts = dict(cursor.fetchall())
    
    # Applications by portal
    cursor.execute('''
        SELECT portal, COUNT(*) 
        FROM job_applications 
        GROUP BY portal
    ''')
    portal_counts = dict(cursor.fetchall())
    
    # Applications this week
    cursor.execute('''
        SELECT COUNT(*) 
        FROM job_applications 
        WHERE application_date >= date('now', '-7 days')
    ''')
    weekly_applications = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_applications': total_applications,
        'status_counts': status_counts,
        'portal_counts': portal_counts,
        'weekly_applications': weekly_applications
    }

def save_setting(setting_name, setting_value):
    """Save application setting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO app_settings (setting_name, setting_value)
        VALUES (?, ?)
    ''', (setting_name, setting_value))
    
    conn.commit()
    conn.close()

def get_setting(setting_name, default_value=None):
    """Get application setting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT setting_value FROM app_settings 
        WHERE setting_name = ?
    ''', (setting_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else default_value

def clean_old_applications(days=30):
    """Clean old application records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM job_applications 
        WHERE application_date < date('now', '-{} days')
    '''.format(days))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

def get_duplicate_applications(job_title, company):
    """Check for duplicate applications"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM job_applications 
        WHERE job_title = ? AND company = ?
        ORDER BY application_date DESC
    ''', (job_title, company))
    
    duplicates = cursor.fetchall()
    conn.close()
    
    return duplicates

def export_applications_to_csv():
    """Export applications to CSV format"""
    import csv
    import io
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM job_applications ORDER BY application_date DESC')
    applications = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'job_title', 'company', 'portal', 'location', 'salary_range',
        'application_status', 'application_date', 'notes'
    ])
    
    writer.writeheader()
    for app in applications:
        writer.writerow(dict(app))
    
    conn.close()
    return output.getvalue()