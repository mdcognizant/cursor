#!/usr/bin/env python3
"""
Advanced Development Automation Suite
A comprehensive tool for automating development workflows with minimal user intervention.
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config_manager import ConfigManager
from src.gui.main_window import MainWindow
from src.core.logger import setup_logging

def main():
    """Main entry point for the development automation suite."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Development Automation Suite")
        
        # Initialize configuration manager
        config_manager = ConfigManager()
        
        # Start the GUI application
        app = MainWindow(config_manager)
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        logging.error(f"Application startup error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 