#!/usr/bin/env python3
"""
Main CLI entry point for job automation system.
"""

import sys
from .utils.cli import JobAutomationCLI


def main():
    """Main entry point for the job automation CLI."""
    cli = JobAutomationCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()