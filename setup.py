#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="job-automation",
    version="0.1.0",
    author="Job Automation Team",
    author_email="contact@jobautomation.com",
    description="A comprehensive job automation system with scheduling, execution, and monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/job-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "croniter>=1.3.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "python-dateutil>=2.8.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
    },
    entry_points={
        "console_scripts": [
            "job-automation=job_automation.cli:main",
        ],
    },
    package_data={
        "job_automation": ["py.typed"],
    },
    include_package_data=True,
    zip_safe=False,
)