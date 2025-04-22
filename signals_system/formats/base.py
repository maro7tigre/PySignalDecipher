"""
Signal Format Base Class

This module defines the abstract base class for all signal format handlers.
Format handlers are responsible for serializing and deserializing signal data,
reading and writing files, and extracting metadata.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, BinaryIO, Union, Tuple
import numpy as np
import logging
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FormatCapability(Enum):
    """Capabilities that a format may support."""
    PARTIAL_READ = auto()        # Can read portions of a file without loading it all
    METADATA = auto()            # Can store and retrieve metadata
    RANDOM_ACCESS = auto()       # Supports random access to any point in the file
    COMPRESSION = auto()         # Supports data compression
    STREAMING = auto()           # Supports streaming writes (appending data over time)
    MULTI_CHANNEL = auto()       # Supports multiple data channels
    TIME_INDEXING = auto()       # Supports direct access by timestamps
    VARIABLE_SAMPLING = auto()   # Supports variable sampling rates
    BINARY_EFFICIENT = auto()    # Particularly efficient binary encoding


class ReadMode(Enum):
    """Modes for reading signal data."""
    FULL = auto()                # Read the entire file
    TIME_RANGE = auto()          # Read data between start and end times
    SAMPLE_RANGE = auto()        # Read data between start and end sample indices
    CHUNK = auto()               # Read data in chunks of specified size


class SignalFormatError(Exception):
    """Base exception for all signal format related errors."""
    pass


class SignalFormat(ABC):
    """
    Abstract base class for all signal format handlers.
    
    This class defines the interface that all signal format implementations must follow.
    Formats are responsible for:
    - Serializing and deserializing signal data
    - Reading and writing signal files
    - Extracting and managing metadata
    - Providing format-specific capabilities
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the format.
        
        Returns:
            str: The name of the format (e.g., "JSON", "CSV", "HDF5")
        """
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """
        Get the file extensions supported by this format.
        
        Returns:
            List[str]: List of supported file extensions (e.g., [".json", ".jsn"])
        """
        pass
    
    @property
    def default_extension(self) -> str:
        """
        Get the default file extension for this format.
        
        Returns:
            str: The default file extension (e.g., ".json")
        """
        return self.extensions[0] if self.extensions else ""
    
    @property
    @abstractmethod
    def capabilities(self) -> List[FormatCapability]:
        """
        Get the capabilities supported by this format.
        
        Returns:
            List[FormatCapability]: List of supported capabilities
        """
        pass
    
    def has_capability(self, capability: FormatCapability) -> bool:
        """
        Check if this format supports a specific capability.
        
        Args:
            capability (FormatCapability): The capability to check
        
        Returns:
            bool: True if the capability is supported, False otherwise
        """
        return capability in self.capabilities
    
    @abstractmethod
    def serialize(self, 
                 data: np.ndarray, 
                 timestamps: np.ndarray = None, 
                 metadata: Dict[str, Any] = None) -> bytes:
        """
        Serialize signal data to bytes.
        
        Args:
            data (np.ndarray): The signal data to serialize
            timestamps (np.ndarray, optional): Timestamps for the data points
            metadata (Dict[str, Any], optional): Metadata to include
        
        Returns:
            bytes: The serialized data
            
        Raises:
            SignalFormatError: If serialization fails
        """
        pass
    
    @abstractmethod
    def deserialize(self, 
                   data: bytes) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Deserialize bytes to signal data.
        
        Args:
            data (bytes): The serialized data
        
        Returns:
            Tuple containing:
                np.ndarray: The deserialized signal data
                Optional[np.ndarray]: Timestamps if available, otherwise None
                Optional[Dict[str, Any]]: Metadata if available, otherwise None
        
        Raises:
            SignalFormatError: If deserialization fails
        """
        pass
    
    @abstractmethod
    def read_file(self, 
                 file_path: str, 
                 mode: ReadMode = ReadMode.FULL,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 start_sample: Optional[int] = None,
                 end_sample: Optional[int] = None,
                 chunk_size: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """
        Read signal data from a file.
        
        Args:
            file_path (str): Path to the file to read
            mode (ReadMode): Mode for reading the file
            start_time (float, optional): Start time for TIME_RANGE mode
            end_time (float, optional): End time for TIME_RANGE mode
            start_sample (int, optional): Start sample for SAMPLE_RANGE mode
            end_sample (int, optional): End sample for SAMPLE_RANGE mode
            chunk_size (int, optional): Chunk size for CHUNK mode
        
        Returns:
            Tuple containing:
                np.ndarray: The signal data
                Optional[np.ndarray]: Timestamps if available, otherwise None
                Dict[str, Any]: Metadata
        
        Raises:
            SignalFormatError: If reading fails
            FileNotFoundError: If the file does not exist
            ValueError: If invalid parameters are provided
        """
        pass
    
    @abstractmethod
    def write_file(self, 
                  file_path: str, 
                  data: np.ndarray, 
                  timestamps: Optional[np.ndarray] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  append: bool = False,
                  compression: Optional[str] = None) -> None:
        """
        Write signal data to a file.
        
        Args:
            file_path (str): Path to the file to write
            data (np.ndarray): The signal data to write
            timestamps (np.ndarray, optional): Timestamps for the data points
            metadata (Dict[str, Any], optional): Metadata to include
            append (bool): Whether to append to an existing file
            compression (str, optional): Compression method to use
        
        Raises:
            SignalFormatError: If writing fails
            ValueError: If invalid parameters are provided
            PermissionError: If the file cannot be written due to permissions
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a file without loading the entire file.
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            Dict[str, Any]: The extracted metadata
        
        Raises:
            SignalFormatError: If metadata extraction fails
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Get structure information about the file.
        
        This method provides information about the file structure, such as:
        - Number of samples
        - Signal duration
        - Sampling rate
        - Number of channels
        - Data type
        - File layout
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            Dict[str, Any]: Structure information
        
        Raises:
            SignalFormatError: If structure analysis fails
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def write_chunk(self, 
                   file_handle: BinaryIO, 
                   data: np.ndarray,
                   timestamps: Optional[np.ndarray] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Write a chunk of data to an open file.
        
        This method is used for streaming writes, where data is written incrementally.
        
        Args:
            file_handle (BinaryIO): Open file handle to write to
            data (np.ndarray): The chunk of data to write
            timestamps (np.ndarray, optional): Timestamps for the data points
            metadata (Dict[str, Any], optional): Metadata to include
        
        Returns:
            int: Number of bytes written
        
        Raises:
            SignalFormatError: If chunk writing fails
        """
        pass
    
    @abstractmethod
    def read_chunk(self, 
                  file_handle: BinaryIO, 
                  chunk_size: int = 1024,
                  offset: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """
        Read a chunk of data from an open file.
        
        This method is used for streaming reads, where data is read incrementally.
        
        Args:
            file_handle (BinaryIO): Open file handle to read from
            chunk_size (int): Maximum number of samples to read
            offset (int, optional): File offset to seek to before reading
        
        Returns:
            Tuple containing:
                np.ndarray: The chunk of signal data
                Optional[np.ndarray]: Timestamps if available, otherwise None
                Optional[Dict[str, Any]]: Chunk-specific metadata if available, otherwise None
        
        Raises:
            SignalFormatError: If chunk reading fails
        """
        pass
    
    @abstractmethod
    def finalize_file(self, file_handle: BinaryIO) -> None:
        """
        Finalize a file after all chunks are written.
        
        This method is used to update headers, finalize indexes, and perform any other
        operations needed to make the file complete and valid.
        
        Args:
            file_handle (BinaryIO): Open file handle to finalize
        
        Raises:
            SignalFormatError: If finalization fails
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that a file is in the correct format.
        
        Args:
            file_path (str): Path to the file to validate
        
        Returns:
            bool: True if the file is valid, False otherwise
        """
        try:
            # Default implementation tries to extract metadata
            self.extract_metadata(file_path)
            return True
        except Exception as e:
            logger.debug(f"File validation failed: {e}")
            return False
    
    def convert_timestamps_to_samples(self, 
                                     timestamps: np.ndarray, 
                                     sample_rate: float, 
                                     start_time: float) -> np.ndarray:
        """
        Convert timestamps to sample indices.
        
        Args:
            timestamps (np.ndarray): Array of timestamps
            sample_rate (float): Sampling rate in Hz
            start_time (float): Start time of the signal
        
        Returns:
            np.ndarray: Array of sample indices
        """
        return np.round((timestamps - start_time) * sample_rate).astype(int)
    
    def convert_samples_to_timestamps(self, 
                                     samples: np.ndarray, 
                                     sample_rate: float, 
                                     start_time: float) -> np.ndarray:
        """
        Convert sample indices to timestamps.
        
        Args:
            samples (np.ndarray): Array of sample indices
            sample_rate (float): Sampling rate in Hz
            start_time (float): Start time of the signal
        
        Returns:
            np.ndarray: Array of timestamps
        """
        return start_time + (samples / sample_rate)
    
    def __str__(self) -> str:
        """String representation of the format."""
        return f"{self.name} Format ({', '.join(self.extensions)})"


class FormatRegistry:
    """
    Registry for signal formats.
    
    This class maintains a registry of available signal formats and provides
    methods for registering, retrieving, and using formats.
    """
    
    def __init__(self):
        """Initialize an empty format registry."""
        self._formats = {}  # Maps format name to format instance
        self._extension_map = {}  # Maps file extension to format instance
    
    def register_format(self, format_instance: SignalFormat) -> None:
        """
        Register a signal format.
        
        Args:
            format_instance (SignalFormat): The format to register
        
        Raises:
            ValueError: If a format with the same name is already registered
        """
        name = format_instance.name.lower()
        if name in self._formats:
            raise ValueError(f"Format {name} is already registered")
        
        self._formats[name] = format_instance
        
        # Register extensions
        for ext in format_instance.extensions:
            ext_lower = ext.lower()
            if ext_lower in self._extension_map:
                logger.warning(f"Extension {ext} is already registered to {self._extension_map[ext_lower].name}, "
                              f"overriding with {format_instance.name}")
            self._extension_map[ext_lower] = format_instance
    
    def get_format(self, name: str) -> SignalFormat:
        """
        Get a format by name.
        
        Args:
            name (str): The name of the format
        
        Returns:
            SignalFormat: The requested format
        
        Raises:
            KeyError: If no format with the given name is registered
        """
        name_lower = name.lower()
        if name_lower not in self._formats:
            raise KeyError(f"No format registered with name {name}")
        return self._formats[name_lower]
    
    def get_format_for_extension(self, extension: str) -> SignalFormat:
        """
        Get a format for a file extension.
        
        Args:
            extension (str): The file extension (with or without leading dot)
        
        Returns:
            SignalFormat: The format for the extension
        
        Raises:
            KeyError: If no format is registered for the given extension
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        ext_lower = extension.lower()
        if ext_lower not in self._extension_map:
            raise KeyError(f"No format registered for extension {extension}")
        return self._extension_map[ext_lower]
    
    def get_format_for_file(self, file_path: str) -> SignalFormat:
        """
        Get a format for a file based on its extension.
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            SignalFormat: The format for the file
        
        Raises:
            KeyError: If no format is registered for the file's extension
        """
        import os
        _, extension = os.path.splitext(file_path)
        return self.get_format_for_extension(extension)
    
    def list_formats(self) -> List[str]:
        """
        Get a list of all registered format names.
        
        Returns:
            List[str]: List of format names
        """
        return list(self._formats.keys())
    
    def list_extensions(self) -> Dict[str, List[str]]:
        """
        Get a mapping of format names to supported extensions.
        
        Returns:
            Dict[str, List[str]]: Mapping of format names to extensions
        """
        return {name: fmt.extensions for name, fmt in self._formats.items()}
    
    def find_formats_with_capability(self, capability: FormatCapability) -> List[SignalFormat]:
        """
        Find all formats that support a specific capability.
        
        Args:
            capability (FormatCapability): The capability to search for
        
        Returns:
            List[SignalFormat]: Formats that support the capability
        """
        return [fmt for fmt in self._formats.values() if fmt.has_capability(capability)]


# Global format registry instance
format_registry = FormatRegistry()


def register_builtin_formats():
    """Register all built-in format handlers."""
    # This function will be implemented once we have concrete format implementations
    pass