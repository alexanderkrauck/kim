"""
Logging Configuration for Firebase Functions

This module provides a standard logging setup that works reliably with Firebase Functions.
All function files should use this to ensure consistent logging.
"""

import logging
import sys
import os
from typing import Optional


def get_logger(filename: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a properly configured logger for Firebase Functions.
    
    Args:
        filename: The name of the file using the logger (e.g., __file__)
        level: Logging level (default: logging.INFO)
        
    Returns:
        Configured logger instance
        
    Usage:
        from utils.logging_config import get_logger
        logger = get_logger(__file__)
        logger.info("This is a test message")
    """
    # Extract just the filename without path
    filename_only = os.path.basename(filename).replace('.py', '')
    
    # Use the same logger name that works with Firebase Functions
    logger = logging.getLogger("firebase_function_logger")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate output in hot reloads
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Force output to stdout (not stderr) - this is crucial for Firebase Functions
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(level)
    
    # Format: "filename - LEVEL: message"
    formatter = logging.Formatter(f'{filename_only} - %(levelname)s: %(message)s')
    stdout_handler.setFormatter(formatter)
    
    logger.addHandler(stdout_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def setup_function_logging(filename: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function for setting up logging in Firebase Functions.
    
    This is an alias for get_logger() with a more descriptive name.
    """
    return get_logger(filename, level) 