"""
Core decompression logic for handling different compressed file formats.
"""
import os
import zipfile
import shutil
import logging
from pathlib import Path

# These will be imported conditionally to handle cases where they might not be installed
# Import for RAR files
try:
    import rarfile
    RARFILE_AVAILABLE = True
except ImportError:
    RARFILE_AVAILABLE = False
    logging.warning("rarfile module not available. RAR decompression will be disabled.")

# Import for 7z files
try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False
    logging.warning("py7zr module not available. 7z decompression will be disabled.")


class Decompressor:
    """Class to handle decompression of various file formats."""

    def __init__(self, output_dir):
        """
        Initialize the decompressor.
        
        Args:
            output_dir (str): Directory where decompressed files will be saved
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def decompress(self, file_path):
        """
        Decompress a file based on its extension.
        
        Args:
            file_path (str): Path to the compressed file
            
        Returns:
            bool: True if decompression was successful, False otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
            
        try:
            extension = file_path.suffix.lower()
            
            if extension == '.zip':
                return self._decompress_zip(file_path)
            elif extension == '.rar':
                return self._decompress_rar(file_path)
            elif extension == '.7z':
                return self._decompress_7z(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {extension}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error decompressing {file_path}: {str(e)}")
            return False

    def _decompress_zip(self, file_path):
        """
        Decompress a ZIP file.
        
        Args:
            file_path (Path): Path to the ZIP file
            
        Returns:
            bool: True if decompression was successful, False otherwise
        """
        try:
            # Create a directory with the same name as the zip file (without extension)
            extract_dir = self.output_dir / file_path.stem
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Check if the zip file is password protected
                for zip_info in zip_ref.infolist():
                    if zip_info.flag_bits & 0x1:
                        self.logger.warning(f"ZIP file is password protected: {file_path}")
                        return False
                
                # Extract all contents
                zip_ref.extractall(path=extract_dir)
                
            self.logger.info(f"Successfully decompressed ZIP file: {file_path}")
            return True
            
        except zipfile.BadZipFile:
            self.logger.error(f"Corrupted ZIP file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error decompressing ZIP file {file_path}: {str(e)}")
            return False

    def _decompress_rar(self, file_path):
        """
        Decompress a RAR file.
        
        Args:
            file_path (Path): Path to the RAR file
            
        Returns:
            bool: True if decompression was successful, False otherwise
        """
        if not RARFILE_AVAILABLE:
            self.logger.error("RAR decompression is not available. Please install rarfile module.")
            return False
            
        try:
            # Create a directory with the same name as the rar file (without extension)
            extract_dir = self.output_dir / file_path.stem
            os.makedirs(extract_dir, exist_ok=True)
            
            with rarfile.RarFile(file_path) as rar_ref:
                # Check if the rar file is password protected
                if rar_ref.needs_password():
                    self.logger.warning(f"RAR file is password protected: {file_path}")
                    return False
                
                # Extract all contents
                rar_ref.extractall(path=extract_dir)
                
            self.logger.info(f"Successfully decompressed RAR file: {file_path}")
            return True
            
        except rarfile.BadRarFile:
            self.logger.error(f"Corrupted RAR file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error decompressing RAR file {file_path}: {str(e)}")
            return False

    def _decompress_7z(self, file_path):
        """
        Decompress a 7z file.
        
        Args:
            file_path (Path): Path to the 7z file
            
        Returns:
            bool: True if decompression was successful, False otherwise
        """
        if not PY7ZR_AVAILABLE:
            self.logger.error("7z decompression is not available. Please install py7zr module.")
            return False
            
        try:
            # Create a directory with the same name as the 7z file (without extension)
            extract_dir = self.output_dir / file_path.stem
            os.makedirs(extract_dir, exist_ok=True)
            
            with py7zr.SevenZipFile(file_path, mode='r') as z:
                # Check if the 7z file is password protected
                if z.needs_password():
                    self.logger.warning(f"7z file is password protected: {file_path}")
                    return False
                
                # Extract all contents
                z.extractall(path=extract_dir)
                
            self.logger.info(f"Successfully decompressed 7z file: {file_path}")
            return True
            
        except py7zr.Bad7zFile:
            self.logger.error(f"Corrupted 7z file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error decompressing 7z file {file_path}: {str(e)}")
            return False

    def remove_original(self, file_path):
        """
        Remove the original compressed file after successful decompression.
        
        Args:
            file_path (str): Path to the compressed file
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        try:
            os.remove(file_path)
            self.logger.info(f"Removed original compressed file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error removing original file {file_path}: {str(e)}")
            return False
