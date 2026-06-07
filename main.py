# Path: main.py
# Description:
# Main entry point for the chess application.
# Sets up the Python path, initializes logging and global error handling,
# then creates and runs the PyQt5 application (ChessApp).
# Handles application lifecycle and exit codes.

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""
Attempt to import a Qt bindings package. Prefer PyQt5, fall back to PySide2 or qtpy.
If none are available raise a clear ImportError.
"""

from PyQt5.QtWidgets import QApplication


from utils.error_handler import ErrorHandler
from utils.logger import Logger
from ui.app import ChessApp

def main():
    """Main application entry point."""
    # Initialize the logger
    logger = Logger.get_instance()
    logger.info("Starting chess application")
    
    # Install global exception handler
    ErrorHandler.install_global_except_hook()
    
    # Initialize the application
    app = ChessApp(sys.argv)
    
    # Run the application
    exit_code = app.exec_()
    
    # Log application exit
    logger.info(f"Chess application exited with code {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())