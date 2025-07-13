# Job Automation Tool

A comprehensive Python-based job automation tool that searches for and applies to jobs automatically across multiple job portals including LinkedIn, Naukri, Indeed, Wellfound, and RemoteOK.

## 🚀 Features

### Core Functionality
- **Multi-Portal Job Search**: Automatically searches jobs from LinkedIn, Naukri, Indeed, Wellfound, RemoteOK, and company career pages
- **Smart Job Filtering**: Filters jobs based on roles, experience, salary, location, and keywords
- **Automated Application**: Fills out application forms, uploads resume, and submits applications
- **Intelligent Matching**: Uses AI-powered job eligibility scoring based on your criteria
- **Duplicate Prevention**: Tracks applied jobs to avoid duplicate applications

### Job Criteria Support
- **Target Roles**: Prompt Engineer, AI Engineer, ML Engineer, Data Scientist, Python Developer
- **Experience Range**: 0-3 years (configurable)
- **Salary Filtering**: Minimum ₹7 LPA (configurable)
- **Location Preferences**: Remote from India (Kolkata) or onsite in Kolkata
- **Keyword Matching**: AI, Machine Learning, Python, LLM, GPT, Prompt Engineering

### Automation Features
- **Scheduled Runs**: Automated job searches and applications at specified times
- **Daily Limits**: Configurable maximum applications per day
- **Delay Management**: Random delays between applications to avoid detection
- **Error Handling**: Comprehensive error handling with screenshots for debugging
- **Backup System**: Automatic database backups with configurable frequency

### User Interface Options
- **Command Line Interface**: Full CLI with multiple commands
- **Web Dashboard**: Optional Flask-based web interface
- **Configuration Management**: JSON-based configuration with easy setup
- **Activity Logging**: Detailed logging and activity tracking

## 📋 Prerequisites

- Python 3.8 or higher
- Chrome browser (for web automation)
- Internet connection
- Resume file (PDF format)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd job-automation-tool
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the application:**
```bash
python main.py setup
```

4. **Update configuration:**
Edit `config.json` with your personal information and preferences.

## ⚙️ Configuration

### User Information
Update your personal details in `config.json`:

```json
{
  "user_info": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "phone": "+91-XXXXXXXXXX",
    "location": "Kolkata, India",
    "experience_years": 2,
    "resume_path": "uploads/resume.pdf"
  }
}
```

### Job Criteria
Customize job search criteria:

```json
{
  "job_criteria": {
    "roles": ["Prompt Engineer", "AI Engineer", "ML Engineer"],
    "experience_range": [0, 3],
    "min_salary_lpa": 7,
    "preferred_locations": ["Remote", "Kolkata", "Work from Home"],
    "keywords": ["AI", "Machine Learning", "Python", "LLM"],
    "exclude_keywords": ["Senior", "Lead", "Manager"]
  }
}
```

### Portal Configuration
Enable/disable job portals:

```json
{
  "job_portals": {
    "linkedin": {"enabled": true, "login_required": true},
    "naukri": {"enabled": true, "login_required": true},
    "indeed": {"enabled": true, "login_required": false},
    "wellfound": {"enabled": true, "login_required": true},
    "remoteok": {"enabled": true, "login_required": false}
  }
}
```

## 🖥️ Usage

### Command Line Interface

#### Basic Commands

1. **Search for jobs:**
```bash
python main.py search
```

2. **Apply to jobs:**
```bash
python main.py apply
```

3. **Run full automation:**
```bash
python main.py run
```

4. **Start scheduler:**
```bash
python main.py scheduler
```

5. **View statistics:**
```bash
python main.py stats
```

6. **View recent activity:**
```bash
python main.py activity --limit 20
```

7. **Test configuration:**
```bash
python main.py test
```

8. **Create backup:**
```bash
python main.py backup
```

#### Advanced Usage

**Custom configuration file:**
```bash
python main.py --config custom_config.json run
```

**Interactive setup:**
```bash
python main.py setup
```

### Web Dashboard

1. **Start the web server:**
```bash
python app.py
```

2. **Access the dashboard:**
Open your browser and navigate to `http://localhost:5000`

3. **Features available:**
   - Real-time statistics dashboard
   - Job search and application management
   - Scheduler control
   - Settings management
   - Activity monitoring

### Scheduler Mode

The scheduler automatically runs job searches and applications at specified times:

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

## 📊 Database Schema

The tool uses SQLite database with the following tables:

- **jobs**: Stores discovered job listings with eligibility scores
- **applications**: Tracks application status and details
- **activity_log**: Logs all automation activities
- **config_storage**: Stores dynamic configuration values

## 🔧 Customization

### Adding New Job Portals

1. **Extend the JobSearcher class:**
```python
def search_new_portal(self) -> List[Dict]:
    # Implementation for new portal
    pass
```

2. **Add portal configuration:**
```json
{
  "job_portals": {
    "new_portal": {
      "enabled": true,
      "base_url": "https://newportal.com",
      "login_required": false
    }
  }
}
```

### Custom Job Filtering

Modify the `calculate_job_eligibility` function in `utils.py` to add custom filtering logic:

```python
def calculate_job_eligibility(job_data: Dict, config: Dict) -> Tuple[bool, float, List[str]]:
    # Add custom filtering logic
    pass
```

## 🚨 Safety Features

### Rate Limiting
- Configurable delays between applications
- Daily application limits
- Random delays to mimic human behavior

### Error Handling
- Comprehensive error logging
- Screenshot capture on errors
- Graceful failure recovery

### Dry Run Mode
Enable dry run mode to test without submitting applications:

```json
{
  "automation_settings": {
    "dry_run": true
  }
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Chrome driver not found:**
   - The tool automatically downloads ChromeDriver
   - Ensure Chrome browser is installed

2. **Login required for portals:**
   - Some portals require manual login
   - The tool will skip these portals if not logged in

3. **Resume not uploading:**
   - Check resume file path in configuration
   - Ensure file exists and is accessible

4. **Applications failing:**
   - Check logs for detailed error messages
   - Verify job portal website changes

### Debug Mode

Enable debug logging:

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

## 📈 Performance Optimization

### Headless Browser
Enable headless mode for faster execution:

```json
{
  "automation_settings": {
    "headless_browser": true
  }
}
```

### Resource Management
- Automatic cleanup of old logs and screenshots
- Database optimization and backups
- Memory-efficient web scraping

## 🔒 Security Considerations

### Data Privacy
- All data stored locally
- No external data transmission
- Encrypted configuration options available

### Best Practices
- Use strong passwords for portal logins
- Regularly update dependencies
- Monitor application logs
- Backup configuration and data

## 🤝 Integration with No-Code Tools

### Make.com Integration
1. Create HTTP webhooks in Make.com
2. Call the job automation tool's API endpoints
3. Set up automated workflows

### Zapier Integration
1. Use Zapier webhooks
2. Integrate with email notifications
3. Connect to other productivity tools

## 📱 API Endpoints

The web interface provides REST API endpoints:

- `POST /api/search-jobs` - Search for jobs
- `POST /api/apply-jobs` - Apply to jobs
- `POST /api/scheduler/start` - Start scheduler
- `POST /api/scheduler/stop` - Stop scheduler
- `GET /api/stats` - Get statistics
- `GET /api/activity` - Get recent activity
- `POST /api/backup` - Create backup

## 🔄 Monitoring and Alerts

### Built-in Monitoring
- Application success rates
- Error tracking
- Performance metrics
- Daily/weekly reports

### External Monitoring
- Integration with monitoring services
- Email/SMS alerts for failures
- Custom webhook notifications

## 📚 Example Workflows

### Daily Automation
```bash
# Morning job search
python main.py search

# Afternoon applications
python main.py apply

# Evening statistics review
python main.py stats
```

### Weekly Maintenance
```bash
# Create backup
python main.py backup

# Review activity
python main.py activity --limit 100

# Update configuration
python main.py setup
```

## 🆘 Support

### Getting Help
- Check the troubleshooting section
- Review log files for errors
- Test configuration with `python main.py test`

### Contributing
- Fork the repository
- Create feature branches
- Submit pull requests
- Follow code style guidelines

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and personal use only. Please ensure compliance with:
- Job portal terms of service
- Local laws and regulations
- Ethical automation practices
- Rate limiting and respectful usage

The developers are not responsible for any misuse or consequences arising from the use of this tool.

## 🔮 Future Enhancements

- **AI-Powered Cover Letters**: Generate personalized cover letters using AI
- **Interview Scheduling**: Automatic interview scheduling integration
- **Portfolio Integration**: Automatic portfolio/GitHub link inclusion
- **Advanced Analytics**: Detailed success rate analysis and optimization
- **Mobile App**: Mobile application for monitoring and control
- **Multi-Language Support**: Support for multiple languages and regions
- **Integration APIs**: RESTful APIs for third-party integrations

## 📞 Contact

For questions, suggestions, or support:
- Create an issue on GitHub
- Email: [your-email@example.com]
- Documentation: [Link to documentation]

---

**Happy Job Hunting! 🎯**