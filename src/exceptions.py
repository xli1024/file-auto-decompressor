"""
Custom exceptions for the file auto-decompressor.
"""


class DecompressionError(Exception):
    """
    Exception raised when there is an error during decompression.
    """
    pass


class PasswordProtectedError(DecompressionError):
    """
    Exception raised when a compressed file is password protected.
    """
    pass


class CorruptedFileError(DecompressionError):
    """
    Exception raised when a compressed file is corrupted.
    """
    pass


class UnsupportedFormatError(Exception):
    """
    Exception raised when a file format is not supported.
    """
    pass


class FileRemovalError(Exception):
    """
    Exception raised when there is an error removing a file.
    """
    pass
