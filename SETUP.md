# Job Automation Tool Setup Guide

This guide will help you set up and configure the Job Automation Tool for optimal performance.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] Google Chrome browser installed
- [ ] Stable internet connection
- [ ] PDF resume file ready
- [ ] Job portal accounts (LinkedIn, Naukri, etc.)
- [ ] Basic knowledge of command line

## 🔧 Detailed Installation

### Step 1: Python Installation

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation:
```cmd
python --version
pip --version
```

#### macOS
```bash
# Using Homebrew
brew install python3

# Or download from python.org
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Chrome Browser

Download and install Google Chrome from [chrome.google.com](https://www.google.com/chrome/)

### Step 3: Project Setup

1. **Create project directory:**
```bash
mkdir job-automation-tool
cd job-automation-tool
```

2. **Download project files:**
```bash
# If using Git
git clone <repository-url> .

# Or download and extract ZIP file
```

3. **Create virtual environment (recommended):**
```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Step 4: Directory Structure

Create the following directory structure:
```
job-automation-tool/
├── data/           # Database files
├── logs/           # Log files
├── uploads/        # Resume and documents
├── screenshots/    # Error screenshots
├── backups/        # Database backups
├── templates/      # HTML templates (auto-created)
└── static/         # CSS/JS files (auto-created)
```

```bash
mkdir -p data logs uploads screenshots backups templates static
```

## ⚙️ Configuration Setup

### Step 1: Initial Configuration

Run the interactive setup:
```bash
python main.py setup
```

This will prompt you for:
- Full name
- Email address
- Phone number
- Location
- Years of experience
- Resume file path

### Step 2: Manual Configuration

Edit `config.json` to customize settings:

```json
{
  "user_info": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+91-9876543210",
    "location": "Kolkata, India",
    "experience_years": 2,
    "resume_path": "uploads/resume.pdf",
    "cover_letter_template": "I am writing to express my interest in the {position} role at {company}. With {experience} years of experience in AI and automation, I am excited to contribute to your team."
  },
  "job_criteria": {
    "roles": ["Prompt Engineer", "AI Engineer", "ML Engineer", "Data Scientist"],
    "experience_range": [0, 3],
    "min_salary_lpa": 7,
    "preferred_locations": ["Remote", "Kolkata", "Work from Home", "WFH"],
    "keywords": ["AI", "Machine Learning", "Python", "LLM", "GPT", "NLP"],
    "exclude_keywords": ["Senior", "Lead", "Manager", "5+ years", "10+ years"]
  },
  "job_portals": {
    "linkedin": {"enabled": true, "login_required": true},
    "naukri": {"enabled": true, "login_required": true},
    "indeed": {"enabled": true, "login_required": false},
    "wellfound": {"enabled": true, "login_required": true},
    "remoteok": {"enabled": true, "login_required": false}
  },
  "automation_settings": {
    "headless_browser": false,
    "implicit_wait": 10,
    "max_applications_per_day": 20,
    "delay_between_applications": 60,
    "screenshot_on_error": true,
    "auto_submit": false,
    "dry_run": true
  },
  "scheduler": {
    "enabled": true,
    "run_times": ["09:00", "14:00", "18:00"],
    "timezone": "Asia/Kolkata",
    "max_daily_runs": 3
  }
}
```

### Step 3: Resume Preparation

1. **Upload resume:**
```bash
cp /path/to/your/resume.pdf uploads/resume.pdf
```

2. **Verify resume:**
```bash
python main.py test
```

## 🧪 Testing Your Setup

### Step 1: Configuration Test

```bash
python main.py test
```

This will verify:
- Database connection
- Resume file accessibility
- User information completeness
- Job portal configuration
- Chrome driver installation

### Step 2: Dry Run Test

1. **Enable dry run mode:**
```json
{
  "automation_settings": {
    "dry_run": true
  }
}
```

2. **Run test automation:**
```bash
python main.py run
```

### Step 3: Portal-Specific Tests

Test individual portals:
```bash
# Test job search only
python main.py search

# View found jobs
python main.py stats
```

## 🔐 Job Portal Account Setup

### LinkedIn Setup

1. **Create/Login to LinkedIn account**
2. **Complete profile:**
   - Professional photo
   - Complete work history
   - Skills and endorsements
   - Education details

3. **Privacy settings:**
   - Enable "Open to work" (private)
   - Allow recruiters to contact you

### Naukri Setup

1. **Create Naukri account**
2. **Complete profile:**
   - Upload resume
   - Add work experience
   - Set job preferences
   - Enable recruiter services

3. **Subscription considerations:**
   - Consider paid plans for better visibility
   - Enable profile ranking features

### Indeed Setup

1. **Create Indeed account**
2. **Upload resume**
3. **Set job alerts**
4. **Complete profile information**

### Wellfound (AngelList) Setup

1. **Create Wellfound account**
2. **Complete startup profile**
3. **Set location preferences**
4. **Connect with startups**

## 🚀 First Run

### Step 1: Manual Test Run

```bash
# Search for jobs
python main.py search

# View statistics
python main.py stats

# Apply to jobs (dry run)
python main.py apply
```

### Step 2: Disable Dry Run

After successful testing:

```json
{
  "automation_settings": {
    "dry_run": false
  }
}
```

### Step 3: Full Automation

```bash
python main.py run
```

## 📊 Web Dashboard Setup

### Step 1: Start Web Server

```bash
python app.py
```

### Step 2: Access Dashboard

Open browser and navigate to:
```
http://localhost:5000
```

### Step 3: Configure Web Interface

- Update settings through web interface
- Monitor job applications
- Control scheduler
- View analytics

## ⏰ Scheduler Configuration

### Step 1: Set Run Times

Configure when the automation should run:

```json
{
  "scheduler": {
    "enabled": true,
    "run_times": ["09:00", "14:00", "18:00"],
    "timezone": "Asia/Kolkata",
    "max_daily_runs": 3
  }
}
```

### Step 2: Start Scheduler

```bash
python main.py scheduler
```

### Step 3: Background Execution

For Linux/macOS, run in background:
```bash
nohup python main.py scheduler &
```

For Windows, use Task Scheduler or install as service.

## 🛠️ Advanced Configuration

### Custom Job Filtering

Edit `utils.py` to customize job filtering:

```python
def calculate_job_eligibility(job_data: Dict, config: Dict) -> Tuple[bool, float, List[str]]:
    # Add custom logic here
    # Example: Check for specific companies
    preferred_companies = ['Google', 'Microsoft', 'Amazon']
    company_match = job_data.get('company', '') in preferred_companies
    
    # Adjust scoring based on company preference
    if company_match:
        score += 10
    
    return is_eligible, score, matched_keywords
```

### Custom Application Logic

Modify `apply.py` to add custom application logic:

```python
def apply_generic_job(self, job: Dict) -> bool:
    # Add custom application steps
    # Example: Fill additional custom fields
    
    # Look for company-specific fields
    if 'google' in job['company'].lower():
        self.fill_google_specific_fields(job)
    
    return True
```

### Database Customization

Add custom database tables or fields in `database.py`:

```python
def init_database(self):
    # Add custom tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            custom_field TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
```

## 🔧 Troubleshooting Setup Issues

### Common Setup Problems

1. **Chrome driver issues:**
```bash
# Manually install webdriver-manager
pip install webdriver-manager --upgrade

# Clear cache
rm -rf ~/.wdm
```

2. **Permission errors:**
```bash
# On Linux/macOS
chmod +x main.py
sudo chown -R $USER:$USER .

# On Windows, run as administrator
```

3. **Module not found errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

4. **Database permission issues:**
```bash
# Create data directory with proper permissions
mkdir -p data
chmod 755 data
```

### Performance Optimization

1. **Enable headless mode:**
```json
{
  "automation_settings": {
    "headless_browser": true
  }
}
```

2. **Reduce screenshot frequency:**
```json
{
  "automation_settings": {
    "screenshot_on_error": false
  }
}
```

3. **Optimize database:**
```bash
# Regular backups and cleanup
python main.py backup
```

## 📈 Monitoring Setup

### Log Management

1. **Configure log rotation:**
```json
{
  "logging": {
    "level": "INFO",
    "file_path": "logs/automation.log",
    "max_file_size": "10MB",
    "backup_count": 5
  }
}
```

2. **Monitor log files:**
```bash
# Real-time log monitoring
tail -f logs/automation.log

# Search for errors
grep -i error logs/automation.log
```

### Performance Monitoring

1. **Database monitoring:**
```bash
# Check database size
ls -lh data/jobs.db

# View recent activity
python main.py activity --limit 50
```

2. **Application monitoring:**
```bash
# Check application statistics
python main.py stats

# Monitor scheduler status
python main.py scheduler status
```

## 🔒 Security Setup

### Data Protection

1. **Secure configuration:**
```bash
# Restrict file permissions
chmod 600 config.json
```

2. **Backup encryption:**
```bash
# Encrypt backups (optional)
gpg -c backups/jobs_backup_*.db
```

### Network Security

1. **Use VPN when needed**
2. **Monitor network traffic**
3. **Avoid public Wi-Fi for sensitive operations**

## 📝 Final Checklist

Before going live:

- [ ] All dependencies installed
- [ ] Configuration file complete
- [ ] Resume file uploaded and accessible
- [ ] Test run completed successfully
- [ ] Job portal accounts set up
- [ ] Dry run mode disabled
- [ ] Scheduler configured
- [ ] Monitoring set up
- [ ] Backup system working
- [ ] Security measures in place

## 🎯 Quick Start Summary

For experienced users:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup configuration
python main.py setup

# 3. Test setup
python main.py test

# 4. Dry run
python main.py run  # (with dry_run: true)

# 5. Go live
# Edit config.json: "dry_run": false
python main.py run

# 6. Start scheduler
python main.py scheduler
```

## 🆘 Getting Help

If you encounter issues:

1. **Check logs:**
```bash
tail -f logs/automation.log
```

2. **Test configuration:**
```bash
python main.py test
```

3. **Reset database:**
```bash
rm data/jobs.db
python main.py test  # Recreates database
```

4. **Fresh start:**
```bash
# Backup current config
cp config.json config.json.bak

# Reset to defaults
python main.py setup
```

---

**You're now ready to start your automated job search! 🚀**