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

    def __init__(self, output_dir, default_passwords=None):
        """
        Initialize the decompressor.
        
        Args:
            output_dir (str): Directory where decompressed files will be saved
            default_passwords (list): List of default passwords to try for password-protected archives
        """
        self.output_dir = Path(output_dir)
        self.default_passwords = default_passwords or []
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
        Decompress a ZIP file, trying default passwords if needed.
        
        Args:
            file_path (Path): Path to the ZIP file
            
        Returns:
            bool: True if decompression was successful, False otherwise
        """
        try:
            # Create a directory with the same name as the zip file (without extension)
            extract_dir = self.output_dir / file_path.stem
            os.makedirs(extract_dir, exist_ok=True)
            
            # First try without password
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(path=extract_dir)
                self.logger.info(f"Successfully decompressed ZIP file (no password): {file_path}")
                return True
            except (RuntimeError, zipfile.BadZipFile) as e:
                # Check if it's a password error
                if "Bad password" in str(e) or "password required" in str(e).lower():
                    self.logger.info(f"ZIP file requires password: {file_path}")
                    # Try with default passwords
                    for password in self.default_passwords:
                        try:
                            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                                zip_ref.extractall(path=extract_dir, pwd=password.encode('utf-8'))
                            self.logger.info(f"Successfully decompressed ZIP file with password: {file_path} (password: {password})")
                            return True
                        except (RuntimeError, zipfile.BadZipFile) as pwd_e:
                            if "Bad password" in str(pwd_e):
                                self.logger.debug(f"Failed password attempt for {file_path}: {password}")
                                continue
                            else:
                                raise pwd_e
                    
                    self.logger.warning(f"Failed to decompress ZIP file {file_path}: exhausted all {len(self.default_passwords)} default passwords")
                    return False
                else:
                    raise e
                
        except zipfile.BadZipFile:
            self.logger.error(f"Corrupted ZIP file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error decompressing ZIP file {file_path}: {str(e)}")
            return False

    def _decompress_rar(self, file_path):
        """
        Decompress a RAR file, trying default passwords if needed.
        
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
            
            # First try without password
            try:
                with rarfile.RarFile(file_path) as rar_ref:
                    if not rar_ref.needs_password():
                        rar_ref.extractall(path=extract_dir)
                        self.logger.info(f"Successfully decompressed RAR file (no password): {file_path}")
                        return True
                    else:
                        raise rarfile.PasswordRequired("Password required")
            except (rarfile.PasswordRequired, rarfile.BadRarFile) as e:
                if "password" in str(e).lower() or isinstance(e, rarfile.PasswordRequired):
                    self.logger.info(f"RAR file requires password: {file_path}")
                    # Try with default passwords
                    for password in self.default_passwords:
                        try:
                            with rarfile.RarFile(file_path) as rar_ref:
                                rar_ref.setpassword(password)
                                rar_ref.extractall(path=extract_dir)
                            self.logger.info(f"Successfully decompressed RAR file with password: {file_path} (password: {password})")
                            return True
                        except (rarfile.PasswordRequired, rarfile.BadRarFile) as pwd_e:
                            if "password" in str(pwd_e).lower():
                                self.logger.debug(f"Failed password attempt for {file_path}: {password}")
                                continue
                            else:
                                raise pwd_e
                    
                    self.logger.warning(f"Failed to decompress RAR file {file_path}: exhausted all {len(self.default_passwords)} default passwords")
                    return False
                else:
                    raise e
                
        except rarfile.BadRarFile:
            self.logger.error(f"Corrupted RAR file: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error decompressing RAR file {file_path}: {str(e)}")
            return False

    def _decompress_7z(self, file_path):
        """
        Decompress a 7z file, trying default passwords if needed.
        
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
            
            # First try without password
            try:
                with py7zr.SevenZipFile(file_path, mode='r') as z:
                    if not z.needs_password():
                        z.extractall(path=extract_dir)
                        self.logger.info(f"Successfully decompressed 7z file (no password): {file_path}")
                        return True
                    else:
                        raise py7zr.PasswordRequired("Password required")
            except (py7zr.PasswordRequired, py7zr.Bad7zFile) as e:
                if "password" in str(e).lower() or isinstance(e, py7zr.PasswordRequired):
                    self.logger.info(f"7z file requires password: {file_path}")
                    # Try with default passwords
                    for password in self.default_passwords:
                        try:
                            with py7zr.SevenZipFile(file_path, mode='r', password=password) as z:
                                z.extractall(path=extract_dir)
                            self.logger.info(f"Successfully decompressed 7z file with password: {file_path} (password: {password})")
                            return True
                        except (py7zr.PasswordRequired, py7zr.Bad7zFile) as pwd_e:
                            if "password" in str(pwd_e).lower():
                                self.logger.debug(f"Failed password attempt for {file_path}: {password}")
                                continue
                            else:
                                raise pwd_e
                    
                    self.logger.warning(f"Failed to decompress 7z file {file_path}: exhausted all {len(self.default_passwords)} default passwords")
                    return False
                else:
                    raise e
                
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
