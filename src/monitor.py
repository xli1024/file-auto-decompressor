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
    
    def __init__(self, input_dir, output_dir):
        """
        Initialize the handler.
        
        Args:
            input_dir (str): Directory to monitor for new compressed files
            output_dir (str): Directory where decompressed files will be saved
        """
        self.input_dir = Path(input_dir)
        self.decompressor = Decompressor(output_dir)
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = ['.zip', '.rar', '.7z']
        
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
            
            # Wait a short time to ensure the file is fully written
            # This helps avoid processing partially written files
            time.sleep(1)
            
            # Process the file
            self._process_file(file_path)
    
    def _process_file(self, file_path):
        """
        Process a compressed file.
        
        Args:
            file_path (Path): Path to the compressed file
        """
        try:
            # Attempt to decompress the file
            success = self.decompressor.decompress(file_path)
            
            # If decompression was successful, remove the original file
            if success:
                self.decompressor.remove_original(file_path)
            else:
                self.logger.warning(f"Failed to decompress {file_path}, original file not removed")
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")


class DirectoryMonitor:
    """
    Monitor a directory for new compressed files.
    """
    
    def __init__(self, input_dir, output_dir):
        """
        Initialize the monitor.
        
        Args:
            input_dir (str): Directory to monitor for new compressed files
            output_dir (str): Directory where decompressed files will be saved
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
        self.event_handler = CompressedFileHandler(input_dir, output_dir)
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
