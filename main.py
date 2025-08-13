#!/usr/bin/env python3
"""
File Auto-Decompressor - Main entry point.

This script monitors a directory for new compressed files (.zip, .rar, .7z),
automatically decompresses them to a specified output directory,
and removes the original compressed files.
"""
import os
import sys
import argparse
import logging
import signal
from pathlib import Path

from src.monitor import DirectoryMonitor
from src.utils import setup_logging


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Monitor a directory for new compressed files and automatically decompress them.'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='/downloads',
        help='Directory to monitor for new compressed files (default: /downloads)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/download_files',
        help='Directory where decompressed files will be saved (default: /download_files)'
    )
    
    parser.add_argument(
        '--log-dir',
        type=str,
        default=None,
        help='Directory where log files will be stored (default: None, logs to console only)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--default-passwords',
        type=str,
        default='',
        help='Comma-separated list of default passwords to try for password-protected archives (default: empty)'
    )
    
    return parser.parse_args()


def signal_handler(sig, frame):
    """
    Handle signals to gracefully exit the program.
    """
    logging.info("Received signal to terminate. Shutting down...")
    sys.exit(0)


def main():
    """
    Main entry point.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(args.log_dir, log_level)
    
    # Log startup information
    logger.info("File Auto-Decompressor starting up")
    logger.info(f"Monitoring directory: {args.input_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Parse default passwords
        default_passwords = []
        if args.default_passwords:
            default_passwords = [pwd.strip() for pwd in args.default_passwords.split(',') if pwd.strip()]
            logger.info(f"Loaded {len(default_passwords)} default passwords")
        
        # Create and start the directory monitor
        monitor = DirectoryMonitor(args.input_dir, args.output_dir, default_passwords)
        monitor.start()
    except Exception as e:
        logger.error(f"Error starting monitor: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
