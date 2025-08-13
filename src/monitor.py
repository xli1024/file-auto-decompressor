"""
File system monitoring for detecting new compressed files.
"""
import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.decompressor import Decompressor


class CompressedFileHandler(FileSystemEventHandler):
    """
    Handler for file system events related to compressed files.
    """
    
    def __init__(self, input_dir, output_dir, default_passwords=None):
        """
        Initialize the handler.
        
        Args:
            input_dir (str): Directory to monitor for new compressed files
            output_dir (str): Directory where decompressed files will be saved
            default_passwords (list): List of default passwords to try for password-protected archives
        """
        self.input_dir = Path(input_dir)
        self.decompressor = Decompressor(output_dir, default_passwords or [])
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = ['.zip', '.rar', '.7z']
        self.processing_files = {}  # Track files being processed with their last seen sizes
        
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: The file system event
        """
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if the file is a supported compressed file
        if file_path.suffix.lower() in self.supported_extensions:
            self.logger.info(f"Detected new compressed file: {file_path}")
            
            # Process the file (stability checking is now handled in _process_file)
            self._process_file(file_path)
    
    def _process_file(self, file_path):
        """
        Process a compressed file after ensuring it's stable (not being downloaded).
        
        Args:
            file_path (Path): Path to the compressed file
        """
        try:
            # Check if file is stable before processing
            if not self._wait_for_file_stability(file_path):
                self.logger.warning(f"File {file_path} never stabilized, skipping")
                return
            
            # Attempt to decompress the file
            success = self.decompressor.decompress(file_path)
            
            # If decompression was successful, remove the original file
            if success:
                self.decompressor.remove_original(file_path)
            else:
                self.logger.warning(f"Failed to decompress {file_path}, original file not removed")
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def _wait_for_file_stability(self, file_path, stability_duration=30, check_interval=5, max_retries=3):
        """
        Wait for a file to be stable (not changing size) before processing.
        
        Args:
            file_path (Path): Path to the file to check
            stability_duration (int): Seconds the file size must remain unchanged
            check_interval (int): Seconds between size checks
            max_retries (int): Maximum number of stability check attempts
            
        Returns:
            bool: True if file is stable, False otherwise
        """
        for retry in range(max_retries):
            try:
                # Check if file exists and has size > 0
                if not file_path.exists():
                    self.logger.warning(f"File {file_path} no longer exists")
                    return False
                
                initial_size = file_path.stat().st_size
                if initial_size == 0:
                    self.logger.info(f"File {file_path} is empty, waiting for content...")
                    time.sleep(check_interval)
                    continue
                
                self.logger.info(f"Monitoring file {file_path} for stability (size: {initial_size} bytes)")
                
                # Monitor file size for stability_duration
                stable_time = 0
                last_size = initial_size
                
                while stable_time < stability_duration:
                    time.sleep(check_interval)
                    
                    if not file_path.exists():
                        self.logger.warning(f"File {file_path} was deleted during stability check")
                        return False
                    
                    current_size = file_path.stat().st_size
                    
                    if current_size != last_size:
                        self.logger.info(f"File {file_path} size changed: {last_size} -> {current_size} bytes, restarting stability check")
                        stable_time = 0
                        last_size = current_size
                    else:
                        stable_time += check_interval
                        self.logger.debug(f"File {file_path} stable for {stable_time}/{stability_duration} seconds")
                
                self.logger.info(f"File {file_path} is stable (size: {last_size} bytes), ready for processing")
                return True
                
            except OSError as e:
                self.logger.warning(f"Error checking file {file_path} stability (attempt {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(check_interval)
                
        self.logger.error(f"Failed to verify stability of {file_path} after {max_retries} attempts")
        return False


class DirectoryMonitor:
    """
    Monitor a directory for new compressed files.
    """
    
    def __init__(self, input_dir, output_dir, default_passwords=None):
        """
        Initialize the monitor.
        
        Args:
            input_dir (str): Directory to monitor for new compressed files
            output_dir (str): Directory where decompressed files will be saved
            default_passwords (list): List of default passwords to try for password-protected archives
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure input directory exists
        if not self.input_dir.exists():
            self.logger.warning(f"Input directory does not exist: {input_dir}")
            os.makedirs(self.input_dir, exist_ok=True)
            self.logger.info(f"Created input directory: {input_dir}")
        
        # Create event handler and observer
        self.event_handler = CompressedFileHandler(input_dir, output_dir, default_passwords)
        self.observer = Observer()
        
    def start(self):
        """
        Start monitoring the directory.
        """
        self.logger.info(f"Starting to monitor directory: {self.input_dir}")
        self.observer.schedule(self.event_handler, str(self.input_dir), recursive=False)
        self.observer.start()
        
        try:
            # Process any existing files in the directory
            self._process_existing_files()
            
            # Keep the thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in monitor: {str(e)}")
            self.stop()
    
    def stop(self):
        """
        Stop monitoring the directory.
        """
        self.logger.info("Stopping directory monitor")
        self.observer.stop()
        self.observer.join()
    
    def _process_existing_files(self):
        """
        Process any existing compressed files in the input directory.
        """
        self.logger.info(f"Checking for existing compressed files in {self.input_dir}")
        
        for extension in ['.zip', '.rar', '.7z']:
            for file_path in self.input_dir.glob(f'*{extension}'):
                self.logger.info(f"Found existing compressed file: {file_path}")
                self.event_handler._process_file(file_path)
