#!/usr/bin/env python3
"""
Create a test zip file for testing the file auto-decompressor.
"""
import zipfile
import os

# Ensure the test_downloads directory exists
os.makedirs('test_downloads', exist_ok=True)

# Create a test zip file
with zipfile.ZipFile('test_downloads/test_archive.zip', 'w') as zip_file:
    zip_file.write('test_file.txt')

print("Test zip file created at test_downloads/test_archive.zip")
