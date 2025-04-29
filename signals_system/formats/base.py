"""
Signal Format Base Module

This module defines the base interfaces for all signal format handlers.
Formats are responsible for reading, writing and manipulating signal data.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
import logging
from typing import Dict, Any, List, Optional, Tuple, Union, BinaryIO
import numpy as np
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FormatCapability(Enum):
    """Capabilities that a format may support."""
    RANDOM_ACCESS = auto()      # Can read arbitrary time ranges efficiently
    STREAMING = auto()          # Supports incremental writing/reading
    COMPRESSION = auto()        # Supports data compression
    METADATA = auto()           # Supports rich metadata
    MULTI_CHANNEL = auto()      # Supports multiple data channels


class TimeRange:
    """Represents a time range for signal data."""
    
    def __init__(self, start: Optional[float] = None, end: Optional[float] = None):
        self.start = start
        self.end = end
    
    def __repr__(self):
        return f"TimeRange(start={self.start}, end={self.end})"


@dataclass
class SignalData:
    """Container for signal data with associated metadata."""
    
    # The signal values as a numpy array
    values: np.ndarray
    
    # Timestamps for each data point (optional)
    timestamps: Optional[np.ndarray] = None
    
    # Metadata associated with the signal
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize defaults and validate structure."""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def num_samples(self) -> int:
        """Get the number of samples in the signal."""
        return len(self.values)
    
    @property
    def num_channels(self) -> int:
        """Get the number of channels in the signal."""
        if len(self.values.shape) > 1:
            return self.values.shape[1]
        return 1
    
    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the signal if timestamps are available."""
        if self.timestamps is not None and len(self.timestamps) > 1:
            return float(self.timestamps[-1] - self.timestamps[0])
        return None
    
    @property
    def sample_rate(self) -> Optional[float]:
        """Get or estimate the sample rate."""
        # Try to get from metadata
        if 'sample_rate' in self.metadata:
            return float(self.metadata['sample_rate'])
        
        # Try to estimate from timestamps
        if self.timestamps is not None and len(self.timestamps) > 1:
            return (len(self.timestamps) - 1) / (self.timestamps[-1] - self.timestamps[0])
        
        return None
    
    def slice(self, start_idx: int, end_idx: Optional[int] = None) -> 'SignalData':
        """Extract a slice of the signal by sample indices."""
        end_idx = end_idx or len(self.values)
        
        values_slice = self.values[start_idx:end_idx]
        timestamps_slice = None
        if self.timestamps is not None:
            timestamps_slice = self.timestamps[start_idx:end_idx]
        
        return SignalData(
            values=values_slice,
            timestamps=timestamps_slice,
            metadata=self.metadata.copy()  # Copy metadata to the slice
        )
    
    def time_slice(self, time_range: TimeRange) -> 'SignalData':
        """Extract a slice of the signal by time range."""
        if self.timestamps is None:
            raise ValueError("Cannot slice by time: no timestamps available")
        
        # Create mask for time range
        mask = np.ones(len(self.timestamps), dtype=bool)
        if time_range.start is not None:
            mask &= (self.timestamps >= time_range.start)
        if time_range.end is not None:
            mask &= (self.timestamps <= time_range.end)
        
        values_slice = self.values[mask]
        timestamps_slice = self.timestamps[mask]
        
        return SignalData(
            values=values_slice,
            timestamps=timestamps_slice,
            metadata=self.metadata.copy()
        )


class SignalFormatError(Exception):
    """Base exception for all signal format related errors."""
    pass


class SignalFormat(ABC):
    """
    Base class for all signal format handlers.
    
    This class defines the interface that all signal format implementations must follow.
    Formats are responsible for reading and writing signal data.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the format."""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """Get the file extensions supported by this format."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[FormatCapability]:
        """Get the capabilities supported by this format."""
        pass
    
    def has_capability(self, capability: FormatCapability) -> bool:
        """Check if this format supports a specific capability."""
        return capability in self.capabilities
    
    @abstractmethod
    def read(self, source: Union[str, Path, BinaryIO], time_range: Optional[TimeRange] = None) -> SignalData:
        """
        Read signal data from a source.
        
        Args:
            source: File path or file-like object to read from
            time_range: Optional time range to filter the data
            
        Returns:
            SignalData object containing the signal values, timestamps, and metadata
            
        Raises:
            SignalFormatError: If reading fails
        """
        pass
    
    @abstractmethod
    def write(self, destination: Union[str, Path, BinaryIO], data: SignalData, append: bool = False) -> None:
        """
        Write signal data to a destination.
        
        Args:
            destination: File path or file-like object to write to
            data: SignalData object containing the signal to write
            append: Whether to append to existing data
            
        Raises:
            SignalFormatError: If writing fails
        """
        pass
    
    def get_metadata(self, source: Union[str, Path, BinaryIO]) -> Dict[str, Any]:
        """
        Extract metadata from a source without loading all data.
        
        The default implementation reads the full file and extracts metadata.
        Formats should override this with more efficient implementations when possible.
        
        Args:
            source: File path or file-like object to read from
            
        Returns:
            Dictionary of metadata
            
        Raises:
            SignalFormatError: If metadata extraction fails
        """
        data = self.read(source)
        return data.metadata
    
    def validate(self, source: Union[str, Path, BinaryIO]) -> bool:
        """
        Validate whether a source contains valid data for this format.
        
        Args:
            source: File path or file-like object to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.get_metadata(source)
            return True
        except Exception as e:
            logger.debug(f"Validation failed: {str(e)}")
            return False
    
    # --- Methods for streaming capability ---
    
    def supports_streaming(self) -> bool:
        """Check if this format supports streaming operations."""
        return FormatCapability.STREAMING in self.capabilities
    
    def open_stream(self, destination: Union[str, Path], mode: str = 'w') -> BinaryIO:
        """
        Open a stream for writing or reading.
        
        Args:
            destination: File path to open
            mode: File mode ('w' for write, 'r' for read, 'a' for append)
            
        Returns:
            File handle
            
        Raises:
            SignalFormatError: If the format doesn't support streaming
        """
        if not self.supports_streaming():
            raise SignalFormatError(f"{self.name} format does not support streaming")
        
        try:
            if isinstance(destination, (str, Path)):
                return open(destination, f"{mode}b")
            return destination
        except Exception as e:
            raise SignalFormatError(f"Failed to open stream: {str(e)}")
    
    def write_chunk(self, stream: BinaryIO, data: SignalData) -> None:
        """
        Write a chunk of data to an open stream.
        
        Args:
            stream: Open file handle
            data: Signal data chunk to write
            
        Raises:
            SignalFormatError: If the format doesn't support streaming
        """
        if not self.supports_streaming():
            raise SignalFormatError(f"{self.name} format does not support streaming")
        
        raise NotImplementedError("This format hasn't implemented streaming support")
    
    def read_chunk(self, stream: BinaryIO) -> Optional[SignalData]:
        """
        Read a chunk of data from an open stream.
        
        Args:
            stream: Open file handle
            
        Returns:
            Signal data chunk or None if end of stream
            
        Raises:
            SignalFormatError: If the format doesn't support streaming
        """
        if not self.supports_streaming():
            raise SignalFormatError(f"{self.name} format does not support streaming")
        
        raise NotImplementedError("This format hasn't implemented streaming support")
    
    def close_stream(self, stream: BinaryIO) -> None:
        """
        Close a stream and perform any necessary finalization.
        
        Args:
            stream: Open file handle
            
        Raises:
            SignalFormatError: If closing fails
        """
        try:
            stream.close()
        except Exception as e:
            raise SignalFormatError(f"Failed to close stream: {str(e)}")
    
    # --- Methods for random access capability ---
    
    def supports_random_access(self) -> bool:
        """Check if this format supports random access operations."""
        return FormatCapability.RANDOM_ACCESS in self.capabilities
    
    def read_time_range(self, source: Union[str, Path, BinaryIO], time_range: TimeRange) -> SignalData:
        """
        Read a specific time range from a source.
        
        The default implementation reads all data and then filters.
        Formats should override this with more efficient implementations when possible.
        
        Args:
            source: File path or file-like object to read from
            time_range: Time range to read
            
        Returns:
            SignalData for the specified time range
            
        Raises:
            SignalFormatError: If the format doesn't support random access
        """
        if not self.supports_random_access():
            raise SignalFormatError(f"{self.name} format does not support random access")
        
        # Default implementation: read all and filter
        data = self.read(source)
        return data.time_slice(time_range)


class FormatRegistry:
    """
    Registry for managing signal formats.
    
    This class keeps track of available formats and provides methods
    for finding and creating format instances.
    """
    
    def __init__(self):
        """Initialize an empty format registry."""
        self._formats = {}  # Maps format name to class
        self._extensions = {}  # Maps file extension to format class
    
    def register(self, format_class):
        """
        Register a format class.
        
        Args:
            format_class: The format class to register
            
        Raises:
            ValueError: If a format with the same name is already registered
        """
        # Create an instance to get properties
        format_instance = format_class()
        name = format_instance.name.lower()
        
        if name in self._formats:
            raise ValueError(f"Format '{name}' is already registered")
        
        # Register the class
        self._formats[name] = format_class
        
        # Register extensions
        for ext in format_instance.extensions:
            ext = ext.lower()
            if ext in self._extensions:
                logger.warning(f"Extension '{ext}' is already registered to {self._extensions[ext].__name__}, "
                               f"now mapping to {format_class.__name__}")
            self._extensions[ext] = format_class
    
    def get_format(self, name: str) -> SignalFormat:
        """
        Get a format instance by name.
        
        Args:
            name: Format name
            
        Returns:
            SignalFormat instance
            
        Raises:
            KeyError: If no format with that name is registered
        """
        name = name.lower()
        if name not in self._formats:
            raise KeyError(f"No format registered with name '{name}'")
        return self._formats[name]()
    
    def get_for_extension(self, extension: str) -> SignalFormat:
        """
        Get a format instance for a file extension.
        
        Args:
            extension: File extension (with or without leading dot)
            
        Returns:
            SignalFormat instance
            
        Raises:
            KeyError: If no format is registered for that extension
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        extension = extension.lower()
        
        if extension not in self._extensions:
            raise KeyError(f"No format registered for extension '{extension}'")
        return self._extensions[extension]()
    
    def get_for_file(self, file_path: Union[str, Path]) -> SignalFormat:
        """
        Get a format instance for a file path based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SignalFormat instance
            
        Raises:
            KeyError: If no format is registered for the file's extension
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        extension = '.' + file_path.suffix.lstrip('.')
        return self.get_for_extension(extension)
    
    def find_with_capability(self, capability: FormatCapability) -> List[SignalFormat]:
        """
        Find all formats that support a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of SignalFormat instances
        """
        result = []
        for format_class in self._formats.values():
            format_instance = format_class()
            if format_instance.has_capability(capability):
                result.append(format_instance)
        return result


# Global registry instance
registry = FormatRegistry()

def register_builtin_formats():
    """Register all built-in format handlers."""
    # Import and register formats to avoid circular imports
    from .json_format import JsonFormat
    from .csv_format import CsvFormat
    
    registry.register(JsonFormat)
    registry.register(CsvFormat)
    
    # TODO: Register other built-in formats when implemented
    # from .numpy_format import NumpyFormat
    # from .hdf5_format import Hdf5Format
    # from .protobuf_format import ProtobufFormat
    # 
    # registry.register(NumpyFormat)
    # registry.register(Hdf5Format)
    # registry.register(ProtobufFormat)

# Call register_builtin_formats to populate the registry
# This fixes the empty registry issue
register_builtin_formats()