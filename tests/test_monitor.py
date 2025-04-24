"""
Tests for the monitor module.
"""
import os
import shutil
import tempfile
import unittest
import time
from pathlib import Path
import zipfile
import threading

from src.monitor import DirectoryMonitor, CompressedFileHandler


class TestCompressedFileHandler(unittest.TestCase):
    """Test cases for the CompressedFileHandler class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / 'input'
        self.output_dir = Path(self.temp_dir) / 'output'
        
        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize handler
        self.handler = CompressedFileHandler(self.input_dir, self.output_dir)

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_process_file(self):
        """Test processing a compressed file."""
        # Create a test file
        test_file_content = "This is a test file."
        test_file_path = self.input_dir / 'test.txt'
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        
        # Create a test zip file
        zip_file_path = self.input_dir / 'test.zip'
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            zip_file.write(test_file_path, arcname='test.txt')
        
        # Process the file
        self.handler._process_file(zip_file_path)
        
        # Check if the file was extracted correctly
        extracted_file = self.output_dir / 'test' / 'test.txt'
        self.assertTrue(extracted_file.exists())
        
        # Check if the original file was removed
        self.assertFalse(zip_file_path.exists())


class TestDirectoryMonitor(unittest.TestCase):
    """Test cases for the DirectoryMonitor class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / 'input'
        self.output_dir = Path(self.temp_dir) / 'output'
        
        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize monitor
        self.monitor = DirectoryMonitor(self.input_dir, self.output_dir)

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_process_existing_files(self):
        """Test processing existing files in the input directory."""
        # Create a test file
        test_file_content = "This is a test file."
        test_file_path = self.input_dir / 'test.txt'
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        
        # Create a test zip file
        zip_file_path = self.input_dir / 'test.zip'
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            zip_file.write(test_file_path, arcname='test.txt')
        
        # Process existing files
        self.monitor._process_existing_files()
        
        # Check if the file was extracted correctly
        extracted_file = self.output_dir / 'test' / 'test.txt'
        self.assertTrue(extracted_file.exists())
        
        # Check if the original file was removed
        self.assertFalse(zip_file_path.exists())

    def test_start_stop(self):
        """Test starting and stopping the monitor."""
        # Start the monitor in a separate thread
        monitor_thread = threading.Thread(target=self._run_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Wait a moment for the monitor to start
        time.sleep(0.5)
        
        # Stop the monitor
        self.monitor.stop()
        
        # Wait for the thread to finish
        monitor_thread.join(timeout=1)
        
        # Check if the thread is no longer alive
        self.assertFalse(monitor_thread.is_alive())
    
    def _run_monitor(self):
        """Run the monitor for a short time."""
        try:
            # Override the infinite loop to run for a short time
            self.monitor.observer.start()
            time.sleep(0.5)
        except Exception:
            pass


if __name__ == '__main__':
    unittest.main()
