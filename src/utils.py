"""
Utility functions for the file auto-decompressor.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir=None, log_level=logging.INFO):
    """
    Set up logging configuration.
    
    Args:
        log_dir (str, optional): Directory where log files will be stored.
                                If None, logs will only be sent to console.
        log_level (int, optional): Logging level. Defaults to logging.INFO.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_dir is provided
    if log_dir:
        log_dir = Path(log_dir)
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = log_dir / 'file_decompressor.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_file_size(file_path):
    """
    Get the size of a file in bytes.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        int: Size of the file in bytes
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0


def human_readable_size(size_bytes):
    """
    Convert a size in bytes to a human-readable string.
    
    Args:
        size_bytes (int): Size in bytes
    
    Returns:
        str: Human-readable size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"
