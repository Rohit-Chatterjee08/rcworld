# Job Application Automation Tool

A Python-based automation tool that helps you search for jobs and apply to them automatically across multiple job portals including LinkedIn, Naukri.com, Indeed, Wellfound, and RemoteOK.

## 🚀 Features

### Core Functionality
- **Multi-Portal Job Search**: Search across LinkedIn, Naukri.com, Indeed, Wellfound, RemoteOK, and company career pages
- **Automated Applications**: Automatically fill out application forms and submit applications
- **Smart Filtering**: Filter jobs by role, experience, salary, location, and keywords
- **Duplicate Prevention**: Avoid applying to the same job multiple times
- **Resume Upload**: Automatically upload your resume to job applications
- **Scheduling**: Set up automated job searches and applications on a schedule

### User Interface
- **Modern Web Interface**: Clean, responsive Flask-based web application
- **Profile Management**: Complete profile setup with resume upload
- **Application Tracking**: View and manage all your job applications
- **Real-time Monitoring**: Track application status and success rates
- **Help & Documentation**: Comprehensive help system and troubleshooting guides

### Safety Features
- **Rate Limiting**: Respects job portal rate limits
- **Application Limits**: Configurable daily application limits
- **Error Handling**: Comprehensive error handling and recovery
- **Manual Override**: Always allows manual intervention and review

## 📋 Target Audience

This tool is specifically designed for:
- **AI/ML Engineers** looking for roles like "Prompt Engineer", "AI Engineer"
- **Fresh graduates** with 0-3 years of experience
- **Job seekers** targeting ₹7+ LPA positions
- **Remote workers** or those preferring Kolkata-based roles
- **Professionals** who want to automate repetitive job application tasks

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Google Chrome browser (for web scraping)
- Internet connection
- 2GB+ RAM recommended

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/job-automation-tool.git
cd job-automation-tool
```

### Step 2: Set up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set up Environment Variables (Optional)
```bash
# Create .env file
touch .env

# Add configuration (optional)
echo "SECRET_KEY=your-secret-key-here" >> .env
echo "EMAIL_USERNAME=your-email@gmail.com" >> .env
echo "EMAIL_PASSWORD=your-app-password" >> .env
```

### Step 5: Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🚀 Quick Start

### 1. Complete Your Profile
- Open the web interface at `http://localhost:5000`
- Navigate to **Profile** section
- Fill in all required information:
  - Full name, email, phone number
  - Years of experience (0-3 for target roles)
  - Expected salary (minimum ₹7 LPA)
  - Location preference (Remote/Kolkata)
  - Key skills (Python, AI, ML, etc.)
- Upload your resume in PDF format

### 2. Test Job Search
- Go to **Job Search** section
- Select target roles: "Prompt Engineer", "AI Engineer"
- Set experience range: 0-3 years
- Set minimum salary: ₹7,00,000
- Choose job portals to search
- Click **Search Jobs**

### 3. Manual Application
- Review found jobs
- Select jobs you want to apply to
- Click **Apply to Selected Jobs**
- Monitor application status in **Applications** section

### 4. Set Up Automation
- Go to **Schedule** section
- Set preferred run time (recommended: 9:00 AM)
- Choose frequency (Daily recommended)
- Set maximum applications per run (default: 5)
- Save schedule

## 📖 Usage Guide

### Profile Setup
Your profile is crucial for successful applications:

```python
# Required fields:
- Name: Your full legal name
- Email: Professional email address
- Phone: Valid Indian mobile number
- Experience: Years of relevant experience
- Expected Salary: Target salary in INR
- Location: "Remote" or city name
- Skills: Comma-separated technical skills
- Resume: PDF file (max 2MB)
```

### Job Search Criteria
Configure search parameters for optimal results:

```python
# Default criteria for AI/ML roles:
{
    'roles': ['Prompt Engineer', 'AI Engineer'],
    'experience_min': 0,
    'experience_max': 3,
    'salary_min': 700000,  # ₹7 LPA
    'location': 'Remote',
    'portals': ['linkedin', 'naukri', 'indeed', 'wellfound']
}
```

### Application Process
The tool follows this workflow:
1. **Search**: Query job portals with your criteria
2. **Filter**: Remove irrelevant jobs based on keywords
3. **Validate**: Check for duplicates and eligibility
4. **Apply**: Fill forms and submit applications
5. **Track**: Record application status and results

## 🔧 Configuration

### Application Settings
Modify `config.py` to customize behavior:

```python
# Application limits
APPLICATION_CONFIG = {
    'max_applications_per_day': 20,
    'max_applications_per_session': 5,
    'application_delay': 30,  # seconds
    'auto_apply_enabled': False,  # Safety feature
}

# Job portal settings
JOB_SEARCH_PORTALS = {
    'linkedin': {'enabled': True, 'rate_limit': 2},
    'naukri': {'enabled': True, 'rate_limit': 3},
    'indeed': {'enabled': True, 'rate_limit': 2},
    # ...
}
```

### Selenium Configuration
For headless operation:

```python
SELENIUM_CONFIG = {
    'headless': True,  # Set to False for debugging
    'window_size': (1920, 1080),
    'page_load_timeout': 30,
    'implicit_wait': 10,
}
```

## 🤖 Automation Features

### Scheduling
- **Daily**: Search and apply every day at specified time
- **Weekly**: Run once per week
- **Manual**: On-demand execution only

### Safety Measures
- **Application Limits**: Prevent excessive applications
- **Rate Limiting**: Respect job portal restrictions
- **Error Handling**: Graceful failure recovery
- **Manual Override**: Always allows user intervention

### Monitoring
- **Application Status**: Track submitted, pending, failed applications
- **Success Rates**: Monitor application success across portals
- **Error Logs**: Detailed error reporting and troubleshooting

## 🔍 Supported Job Portals

### Currently Supported:
- **LinkedIn**: Professional networking and job search
- **Naukri.com**: India's largest job portal
- **Indeed**: Global job search platform
- **Wellfound (AngelList)**: Startup and tech jobs
- **RemoteOK**: Remote job opportunities

### Portal-Specific Notes:
- **LinkedIn**: Requires login for full functionality
- **Naukri**: Best for Indian job market
- **Indeed**: Good for diverse opportunities
- **Wellfound**: Excellent for startup roles
- **RemoteOK**: Primarily remote tech jobs

## 🔒 Security & Privacy

### Data Protection
- All personal data stored locally
- No data sent to external servers
- Secure resume file handling
- Optional email notifications only

### Best Practices
- Use strong passwords for job portals
- Regular profile updates
- Monitor application activities
- Respect job portal terms of service

## 🐛 Troubleshooting

### Common Issues:

#### No Jobs Found
```bash
# Check search criteria
- Broaden experience range
- Lower salary expectations
- Try different portals
- Check location settings
```

#### Applications Failing
```bash
# Verify setup
- Complete profile information
- Check resume file format (PDF only)
- Test manual application first
- Review error logs
```

#### Scheduler Not Working
```bash
# Debug scheduler
- Check application is running
- Verify system time
- Review scheduler logs
- Test manual execution
```

## 📊 Performance Tips

### Optimization
- **Search Timing**: Run searches in morning (8-10 AM)
- **Application Limits**: Keep under 10 applications per day
- **Portal Selection**: Focus on 2-3 most relevant portals
- **Profile Updates**: Keep skills and experience current

### Success Metrics
- **Application Rate**: 5-10 applications per day
- **Success Rate**: Monitor response rates
- **Quality over Quantity**: Focus on relevant applications

## 🛡️ Legal Considerations

### Usage Guidelines
- Respect job portal terms of service
- Use reasonable application limits
- Provide accurate information
- Don't spam applications
- Always be prepared for manual follow-up

### Disclaimer
This tool automates legitimate job application processes. Users are responsible for:
- Following job portal terms of service
- Providing accurate information
- Maintaining professional conduct
- Following up on applications manually

## 🤝 Contributing

### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Areas for Improvement
- Add more job portals
- Improve application success rates
- Better error handling
- Mobile responsiveness
- API integrations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Flask, Selenium, and Beautiful Soup
- UI components from Bootstrap 5
- Icons from Font Awesome
- Chrome WebDriver for automation

## 📞 Support

### Getting Help
- **GitHub Issues**: Report bugs or request features
- **Email**: support@jobautomation.com
- **Documentation**: Check the built-in help system
- **Community**: Join our Discord server

### Before Asking for Help
1. Read this README completely
2. Check the built-in help system
3. Try manual execution first
4. Review error logs
5. Search existing GitHub issues

## 🔄 Version History

### v1.0.0 (Current)
- Multi-portal job search
- Automated application submission
- Web-based user interface
- Scheduling and automation
- Application tracking
- Comprehensive documentation

### Upcoming Features
- More job portals
- AI-powered job matching
- Advanced filtering options
- Mobile app
- API integrations
- Analytics dashboard

---

**Remember**: This tool is designed to help you apply for jobs more efficiently, but it's not a replacement for a thoughtful job search strategy. Always customize your applications for better results!

## 🎯 Target Roles & Companies

### Ideal Roles for This Tool:
- Prompt Engineer
- AI Engineer
- Machine Learning Engineer
- Data Scientist (entry-level)
- NLP Engineer
- Computer Vision Engineer

### Target Companies:
- AI/ML startups
- Tech companies with AI divisions
- Consulting firms
- Product companies
- Remote-first organizations

Start your automated job search today and land your dream AI/ML role! 🚀