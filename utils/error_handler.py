"""
Centralized error handling for the chess application.
This module provides utilities for consistent error handling across the application.
"""

import sys
import traceback
from PyQt5.QtWidgets import QMessageBox

class ErrorHandler:
    """Handles errors in a consistent way across the application."""
    
    @staticmethod
    def install_global_except_hook():
        """Install a global exception hook to catch unhandled exceptions."""
        def exception_hook(exc_type, exc_value, exc_traceback):
            # Print to console for debugging
            print(f"Unhandled exception: {exc_type}")
            print(f"Value: {exc_value}")
            traceback.print_tb(exc_traceback)
            
            # Format the error message for display
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Log the error (could add file logging here)
            print(f"ERROR: {error_msg}")
            
            # Show an error dialog to the user if we're running in GUI mode
            # Use a try-except to avoid triggering another exception during error handling
            try:
                QMessageBox.critical(None, "Application Error", 
                                    f"An unexpected error occurred:\n{str(exc_value)}\n\n"
                                    "Please try restarting the application.")
            except Exception as e:
                print(f"Failed to show error dialog: {e}")
        
        # Install the exception hook
        sys.excepthook = exception_hook
    
    @staticmethod
    def show_error(parent, title, message, detailed_error=None):
        """Show an error message to the user with optional details."""
        try:
            msg_box = QMessageBox(parent)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            
            if detailed_error:
                msg_box.setDetailedText(str(detailed_error))
                
            msg_box.exec_()
        except Exception as e:
            print(f"Failed to show error dialog: {e}")
            print(f"Original error: {message} - {detailed_error}")
    
    @staticmethod
    def handle_exception(parent, title, e, context=None):
        """Handle an exception by showing appropriate errors and logging."""
        # Get the full traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Log the full error
        print(f"ERROR in {context or 'unknown context'}:")
        print(traceback_str)
        
        # Show a user-friendly message
        message = f"An error occurred: {str(e)}"
        if context:
            message = f"An error occurred while {context}: {str(e)}"
            
        ErrorHandler.show_error(parent, title, message, traceback_str)
        
        return False  # Return False to indicate error handling completed