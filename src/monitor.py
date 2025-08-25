"""
File system monitoring for detecting new compressed files.
"""
import os
import time
import logging
import threading
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
        
        # Companion file extensions used by various downloaders
        self.companion_extensions = [
            '.aria2',      # aria2 downloader
            '.part',       # wget, curl, Firefox
            '.tmp',        # various tools
            '.crdownload', # Chrome downloads
            '.download',   # Safari, some tools  
            '.partial',    # some downloaders
            '.!ut',        # µTorrent
            '.bc!',        # BitComet
        ]
        
        # Parking queue for files waiting for download completion
        self.parked_files = {}  # {file_path: park_timestamp}
        self.max_parked_files = 50
        self.park_check_interval = 30  # seconds
        self.parked_files_lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
        # Start background thread for monitoring parked files
        self.parked_monitor_thread = threading.Thread(target=self._monitor_parked_files, daemon=True)
        self.parked_monitor_thread.start()
        
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
        Process a compressed file with non-blocking logic for downloads.
        
        Args:
            file_path (Path): Path to the compressed file
        """
        try:
            # Check if file exists and has content
            if not file_path.exists():
                self.logger.warning(f"File {file_path} no longer exists")
                return
            
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.logger.info(f"File {file_path} is empty, skipping")
                return
            
            # Grace period: wait for companion files to potentially appear
            self.logger.info(f"Waiting 10 seconds for potential companion files to appear for {file_path}")
            time.sleep(10)
            
            # Check if file still exists after grace period
            if not file_path.exists():
                self.logger.warning(f"File {file_path} was deleted during grace period")
                return
            
            # Check for companion files
            companion_files = self._get_companion_files(file_path)
            
            if companion_files:
                # File has companions - park it for later processing
                self._park_file(file_path)
            else:
                # No companions - process immediately
                self.logger.info(f"No companion files found for {file_path}, processing immediately")
                self._decompress_file(file_path)
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def _decompress_file(self, file_path):
        """
        Decompress a file and remove the original.
        
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
            self.logger.error(f"Error decompressing file {file_path}: {str(e)}")
    
    def _park_file(self, file_path):
        """
        Park a file that has companion files (download in progress).
        
        Args:
            file_path (Path): Path to the file to park
        """
        with self.parked_files_lock:
            # Check if parking queue is full
            if len(self.parked_files) >= self.max_parked_files:
                # Remove oldest parked file to make room
                oldest_file = min(self.parked_files.items(), key=lambda x: x[1])
                del self.parked_files[oldest_file[0]]
                self.logger.warning(f"Parking queue full, removed oldest file: {oldest_file[0]}")
            
            # Park the file with current timestamp
            current_time = time.time()
            self.parked_files[file_path] = current_time
            
            companion_files = self._get_companion_files(file_path)
            self.logger.info(f"Parked file {file_path} (companions: {[str(f) for f in companion_files]}) - queue size: {len(self.parked_files)}")
    
    def _monitor_parked_files(self):
        """
        Background thread to monitor parked files and process completed downloads.
        """
        self.logger.info("Started background thread for monitoring parked files")
        
        while not self.shutdown_event.is_set():
            try:
                # Wait for check interval or shutdown signal
                if self.shutdown_event.wait(self.park_check_interval):
                    break
                
                # Check parked files
                self._check_parked_files()
                
            except Exception as e:
                self.logger.error(f"Error in parked files monitor: {str(e)}")
                time.sleep(5)  # Brief pause before retrying
        
        self.logger.info("Background parked files monitor stopped")
    
    def _check_parked_files(self):
        """
        Check all parked files and process any that are ready.
        """
        with self.parked_files_lock:
            if not self.parked_files:
                return
            
            # Create a copy to avoid modification during iteration
            parked_files_copy = dict(self.parked_files)
        
        files_to_unpark = []
        current_time = time.time()
        max_wait_seconds = 3 * 3600  # 3 hours
        
        # Check each parked file (in chronological order - oldest first)
        for file_path, park_time in sorted(parked_files_copy.items(), key=lambda x: x[1]):
            try:
                # Check if file still exists
                if not file_path.exists():
                    self.logger.info(f"Parked file {file_path} was deleted, removing from queue")
                    files_to_unpark.append(file_path)
                    continue
                
                # Check if timeout reached
                elapsed_seconds = current_time - park_time
                if elapsed_seconds > max_wait_seconds:
                    self.logger.warning(f"Parked file {file_path} timed out after {elapsed_seconds/3600:.1f} hours, removing from queue")
                    files_to_unpark.append(file_path)
                    continue
                
                # Check if companions still exist
                companion_files = self._get_companion_files(file_path)
                
                if not companion_files:
                    # Download completed - unpark and process
                    self.logger.info(f"Parked file {file_path} download completed (parked for {elapsed_seconds:.1f} seconds)")
                    files_to_unpark.append(file_path)
                    
                    # Process the file in a separate thread to avoid blocking the monitor
                    processing_thread = threading.Thread(target=self._decompress_file, args=(file_path,))
                    processing_thread.start()
                else:
                    # Still downloading, log progress if significant time elapsed
                    if elapsed_seconds > 300 and int(elapsed_seconds) % 300 == 0:  # Every 5 minutes
                        remaining_hours = (max_wait_seconds - elapsed_seconds) / 3600
                        self.logger.info(f"Parked file {file_path} still downloading (companions: {len(companion_files)}, remaining: {remaining_hours:.1f}h)")
                
            except Exception as e:
                self.logger.error(f"Error checking parked file {file_path}: {str(e)}")
                files_to_unpark.append(file_path)  # Remove problematic files
        
        # Remove unparked files from the queue
        with self.parked_files_lock:
            for file_path in files_to_unpark:
                self.parked_files.pop(file_path, None)
        
        if files_to_unpark:
            self.logger.info(f"Unparked {len(files_to_unpark)} files, {len(self.parked_files)} remain in queue")
    
    def shutdown(self):
        """
        Shutdown the handler and stop background threads.
        """
        self.logger.info("Shutting down compressed file handler")
        self.shutdown_event.set()
        if self.parked_monitor_thread.is_alive():
            self.parked_monitor_thread.join(timeout=5)
    
    def _get_companion_files(self, file_path):
        """
        Find companion files that indicate a download is in progress.
        
        Args:
            file_path (Path): Path to the target compressed file
            
        Returns:
            list: List of companion file paths that exist
        """
        companion_files = []
        
        for extension in self.companion_extensions:
            # Correct: append extension to full filename (e.g., movie.zip + .aria2 = movie.zip.aria2)
            companion_path = Path(str(file_path) + extension)
            if companion_path.exists():
                companion_files.append(companion_path)
        
        return companion_files
    


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
        
        # Shutdown the event handler and background threads
        self.event_handler.shutdown()
        
        # Stop the observer
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
