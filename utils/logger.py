"""
Logging utility for the chess application.
This module provides a consistent way to log events and errors across the application.
"""

import os
import logging
import datetime

class Logger:
    """Handles logging for the application."""
    
    _instance = None
    _initialized = False
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of the logger."""
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    def __init__(self):
        """Initialize the logger. Should be called only once."""
        if Logger._initialized:
            return
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up logging to file with rotation
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f'chess_app_{timestamp}.log')
        
        # Configure the root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=log_file,
            filemode='w'
        )
        
        # Add console handler to show logs in console as well
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        
        # Create application-specific logger
        self.logger = logging.getLogger('chess_app')
        self.logger.info("Logger initialized")
        
        Logger._initialized = True
    
    def info(self, message):
        """Log an informational message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message, exc_info=None):
        """Log an error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def critical(self, message, exc_info=None):
        """Log a critical error message with optional exception info."""
        self.logger.critical(message, exc_info=exc_info)