"""
Tests for the decompressor module.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import zipfile

from src.decompressor import Decompressor


class TestDecompressor(unittest.TestCase):
    """Test cases for the Decompressor class."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / 'input'
        self.output_dir = Path(self.temp_dir) / 'output'
        
        # Create directories
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create a test zip file
        self.test_file_content = "This is a test file."
        self.test_file_path = self.input_dir / 'test.txt'
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_file_content)
        
        self.zip_file_path = self.input_dir / 'test.zip'
        with zipfile.ZipFile(self.zip_file_path, 'w') as zip_file:
            zip_file.write(self.test_file_path, arcname='test.txt')
        
        # Initialize decompressor
        self.decompressor = Decompressor(self.output_dir)

    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)

    def test_decompress_zip(self):
        """Test decompressing a ZIP file."""
        # Decompress the test zip file
        result = self.decompressor.decompress(self.zip_file_path)
        
        # Check if decompression was successful
        self.assertTrue(result)
        
        # Check if the file was extracted correctly
        extracted_file = self.output_dir / 'test' / 'test.txt'
        self.assertTrue(extracted_file.exists())
        
        # Check if the content is correct
        with open(extracted_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, self.test_file_content)

    def test_remove_original(self):
        """Test removing the original compressed file."""
        # Create a dummy file to remove
        dummy_file = self.input_dir / 'dummy.txt'
        with open(dummy_file, 'w') as f:
            f.write("Dummy file")
        
        # Remove the file
        result = self.decompressor.remove_original(dummy_file)
        
        # Check if removal was successful
        self.assertTrue(result)
        self.assertFalse(dummy_file.exists())


if __name__ == '__main__':
    unittest.main()
