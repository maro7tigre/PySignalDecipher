"""
Signal Processing System - Core Implementation

This module defines the primary components of a modular signal processing system
capable of handling both file-based and live signal sources with configurable 
averaging, serialization, and change detection.
"""

from abc import ABC, abstractmethod
import numpy as np
import time
from typing import Dict, Any, List, Callable, Optional, Union, Tuple
from dataclasses import dataclass
import threading
from queue import Queue
import json
import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- Data Structures ----------
# MARK: - Data Structures

@dataclass
class SignalFrame:
    """Container for signal data with timestamp information."""
    data: np.ndarray
    timestamp_start: float
    timestamp_end: float
    sample_rate: float
    metadata: Dict[str, Any] = None
    
    @property
    def duration(self) -> float:
        """Duration of the signal frame in seconds."""
        return self.timestamp_end - self.timestamp_start
    
    @property
    def num_samples(self) -> int:
        """Number of samples in the frame."""
        return len(self.data)


class SignalEventType(Enum):
    """Types of events that can be dispatched by the system."""
    NEW_FRAME = "new_frame"
    AVERAGE_UPDATED = "average_updated"
    SIGNAL_CHANGED = "signal_changed"
    CONNECTION_STATUS = "connection_status"
    ERROR = "error"


# ---------- Configuration ----------
# MARK: - Configuration

class SignalConfig:
    """Configuration parameters for the signal processing system."""
    
    def __init__(self, 
                 mode: str = "file",
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 duration: Optional[float] = None,
                 full_signal: bool = False,
                 frame_rate: float = 30.0,
                 buffer_size: int = 1000,
                 connection_params: Dict[str, Any] = None,
                 window_size: Union[float, int] = 1.0,
                 window_type: str = "rolling",
                 overlap: float = 0.0,
                 serialization_format: str = "json",
                 compression: str = "none",
                 change_threshold: float = 0.1):
        
        # General settings
        self.mode = mode
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.full_signal = full_signal
        
        # Live mode settings
        self.frame_rate = frame_rate
        self.buffer_size = buffer_size
        self.connection_params = connection_params or {}
        
        # Averaging settings
        self.window_size = window_size
        self.window_type = window_type
        self.overlap = overlap
        
        # Serialization settings
        self.serialization_format = serialization_format
        self.compression = compression
        
        # Signal processing settings
        self.change_threshold = change_threshold
        
        self._validate()
    
    def _validate(self):
        """Validate configuration parameters."""
        if self.mode not in ["file", "live"]:
            raise ValueError("Mode must be 'file' or 'live'")
        
        if not self.full_signal:
            if self.start_time is None and self.end_time is None and self.duration is None:
                raise ValueError("Must specify at least one of: start_time, end_time, duration, or set full_signal=True")
            
            if self.duration is not None and self.end_time is not None:
                logger.warning("Both duration and end_time specified; end_time takes precedence")
        
        if self.window_type not in ["rolling", "fixed", "exponential"]:
            raise ValueError("Window type must be 'rolling', 'fixed', or 'exponential'")
        
        if self.serialization_format not in ["json", "protobuf", "hdf5"]:
            raise ValueError("Serialization format must be 'json', 'protobuf', or 'hdf5'")
        
        if self.compression not in ["none", "gzip", "lzma"]:
            raise ValueError("Compression must be 'none', 'gzip', or 'lzma'")


# ---------- Signal Providers ----------
#  MARK: - Signal Providers

class SignalProvider(ABC):
    """Abstract base class for signal data sources."""
    
    def __init__(self, config: SignalConfig):
        self.config = config
        self._is_open = False
    
    @abstractmethod
    def open(self) -> bool:
        """Initialize and open the signal source."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the signal source and release resources."""
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[SignalFrame]:
        """Get the next frame of signal data."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the signal source."""
        pass
    
    @property
    def is_open(self) -> bool:
        """Check if the signal source is open."""
        return self._is_open


class FileSignalProvider(SignalProvider):
    """Reads signal data from pre-recorded files."""
    
    def __init__(self, config: SignalConfig, file_path: str):
        super().__init__(config)
        self.file_path = file_path
        self.file_handle = None
        self.deserializer = None
        self.metadata = None
        self.current_position = 0
        self.total_samples = 0
        self.sample_rate = 0
        
    def open(self) -> bool:
        """Open the file and initialize the deserializer."""
        try:
            self.file_handle = open(self.file_path, 'rb')
            self._is_open = True
            
            # Create deserializer based on config
            if self.config.serialization_format == "json":
                self.deserializer = JsonDeserializer()
            elif self.config.serialization_format == "protobuf":
                # Not implemented yet
                raise NotImplementedError("Protobuf deserialization not implemented")
            elif self.config.serialization_format == "hdf5":
                # Not implemented yet
                raise NotImplementedError("HDF5 deserialization not implemented")
            
            # Read metadata from the beginning of the file
            self.metadata = self._read_metadata()
            self.sample_rate = self.metadata.get('sample_rate', 0)
            self.total_samples = self.metadata.get('total_samples', 0)
            
            # Set initial position based on config
            self._set_initial_position()
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening file {self.file_path}: {e}")
            self.close()
            return False
    
    def _read_metadata(self) -> Dict[str, Any]:
        """Read metadata from the beginning of the file."""
        # Implementation depends on file format
        # For simplicity, assume JSON format with a metadata block
        self.file_handle.seek(0)
        header_size_bytes = self.file_handle.read(4)
        header_size = int.from_bytes(header_size_bytes, byteorder='little')
        header_bytes = self.file_handle.read(header_size)
        
        try:
            return json.loads(header_bytes.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Failed to parse metadata as JSON")
            return {}
    
    def _set_initial_position(self) -> None:
        """Set the initial file position based on configuration."""
        if self.config.full_signal:
            # Position after metadata
            self.current_position = self.file_handle.tell()
            return
        
        if self.config.start_time is not None and self.sample_rate > 0:
            # Calculate position from start_time
            start_sample = int(self.config.start_time * self.sample_rate)
            # Get header size and sample size from metadata or guess
            sample_size_bytes = self.metadata.get('sample_size_bytes', 8)  # Default to 8 bytes per sample
            header_size = self.file_handle.tell()
            
            self.current_position = header_size + (start_sample * sample_size_bytes)
            self.file_handle.seek(self.current_position)
    
    def close(self) -> None:
        """Close the file and clean up resources."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self._is_open = False
    
    def get_frame(self) -> Optional[SignalFrame]:
        """Read the next frame of signal data from the file."""
        if not self._is_open or not self.file_handle:
            return None
        
        try:
            # Determine how much data to read
            # For simplicity, read a fixed chunk size
            chunk_size = 1024  # Could be configured or based on window_size
            
            # Check if we've reached the end time
            if self.config.end_time is not None:
                current_time = self.current_position / (self.sample_rate * 8)  # Assuming 8 bytes per sample
                if current_time >= self.config.end_time:
                    return None
            
            # Read data
            raw_data = self.file_handle.read(chunk_size * 8)  # Assuming 8 bytes per sample
            if not raw_data:
                return None
            
            # Deserialize
            frame_data = self.deserializer.deserialize(raw_data)
            
            # Update position
            self.current_position = self.file_handle.tell()
            
            # Calculate timestamps
            start_time = (self.current_position - len(raw_data)) / (self.sample_rate * 8)
            end_time = self.current_position / (self.sample_rate * 8)
            
            return SignalFrame(
                data=frame_data,
                timestamp_start=start_time,
                timestamp_end=end_time,
                sample_rate=self.sample_rate,
                metadata=self.metadata
            )
            
        except Exception as e:
            logger.error(f"Error reading frame from file: {e}")
            return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return the metadata for the signal source."""
        return self.metadata or {}


class LiveSignalProvider(SignalProvider):
    """Connects to a live signal source (e.g., socket, API, hardware)."""
    
    def __init__(self, config: SignalConfig, connection_factory: Callable):
        super().__init__(config)
        self.connection_factory = connection_factory
        self.connection = None
        self.buffer = Queue(maxsize=config.buffer_size)
        self.stop_flag = threading.Event()
        self.receiver_thread = None
        self.deserializer = None
        self.metadata = None
        
    def open(self) -> bool:
        """Establish connection to the live signal source."""
        try:
            # Create connection
            self.connection = self.connection_factory(**self.config.connection_params)
            
            # Create deserializer based on config
            if self.config.serialization_format == "json":
                self.deserializer = JsonDeserializer()
            elif self.config.serialization_format == "protobuf":
                # Not implemented yet
                raise NotImplementedError("Protobuf deserialization not implemented")
            elif self.config.serialization_format == "hdf5":
                # Not implemented yet
                raise NotImplementedError("HDF5 deserialization not implemented")
            
            # Read initial metadata
            self.metadata = self._read_metadata()
            
            # Start receiver thread
            self.stop_flag.clear()
            self.receiver_thread = threading.Thread(
                target=self._receive_data_loop,
                daemon=True
            )
            self.receiver_thread.start()
            
            self._is_open = True
            return True
            
        except Exception as e:
            logger.error(f"Error opening live connection: {e}")
            self.close()
            return False
    
    def _read_metadata(self) -> Dict[str, Any]:
        """Read metadata from the live connection."""
        # Implementation depends on protocol
        # For simplicity, assume metadata is received as a special message
        try:
            metadata_message = self.connection.receive_metadata()
            return json.loads(metadata_message.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to read metadata from live source: {e}")
            return {}
    
    def _receive_data_loop(self) -> None:
        """Background thread to continuously receive data from the live source."""
        last_frame_time = time.time()
        target_frame_interval = 1.0 / self.config.frame_rate
        
        while not self.stop_flag.is_set():
            try:
                # Rate limiting
                elapsed = time.time() - last_frame_time
                if elapsed < target_frame_interval:
                    time.sleep(target_frame_interval - elapsed)
                
                # Receive data
                raw_data = self.connection.receive_data()
                if not raw_data:
                    continue
                
                # Deserialize
                frame_data = self.deserializer.deserialize(raw_data)
                
                # Create frame
                current_time = time.time()
                frame = SignalFrame(
                    data=frame_data,
                    timestamp_start=last_frame_time,
                    timestamp_end=current_time,
                    sample_rate=self.config.frame_rate,
                    metadata=self.metadata
                )
                
                # Update last frame time
                last_frame_time = current_time
                
                # Add to buffer (non-blocking, drop if full)
                if not self.buffer.full():
                    self.buffer.put_nowait(frame)
                else:
                    logger.warning("Buffer full, dropping frame")
                
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                # Add backoff/reconnect logic here
                time.sleep(1.0)
    
    def close(self) -> None:
        """Close the connection and stop the receiver thread."""
        self.stop_flag.set()
        
        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=2.0)
        
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            self.connection = None
        
        self._is_open = False
    
    def get_frame(self) -> Optional[SignalFrame]:
        """Get the next frame from the buffer."""
        if not self._is_open:
            return None
        
        try:
            # Non-blocking get with timeout
            return self.buffer.get(block=True, timeout=1.0)
        except Exception:
            return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return the metadata for the signal source."""
        return self.metadata or {}


# ---------- Serialization ----------
# MARK: -Serialization

class Serializer(ABC):
    """Base class for serializing signal data."""
    
    @abstractmethod
    def serialize(self, frame: SignalFrame) -> bytes:
        """Serialize a signal frame to bytes."""
        pass


class Deserializer(ABC):
    """Base class for deserializing signal data."""
    
    @abstractmethod
    def deserialize(self, data: bytes) -> np.ndarray:
        """Deserialize bytes to a numpy array."""
        pass


class JsonSerializer(Serializer):
    """JSON serializer for signal data."""
    
    def serialize(self, frame: SignalFrame) -> bytes:
        """Serialize a signal frame to JSON."""
        # Convert numpy array to list for JSON serialization
        data_list = frame.data.tolist()
        
        # Create dictionary with frame data
        frame_dict = {
            'data': data_list,
            'timestamp_start': frame.timestamp_start,
            'timestamp_end': frame.timestamp_end,
            'sample_rate': frame.sample_rate,
            'metadata': frame.metadata or {}
        }
        
        # Serialize to JSON
        json_str = json.dumps(frame_dict)
        return json_str.encode('utf-8')


class JsonDeserializer(Deserializer):
    """JSON deserializer for signal data."""
    
    def deserialize(self, data: bytes) -> np.ndarray:
        """Deserialize JSON bytes to a numpy array."""
        try:
            # Parse JSON
            json_str = data.decode('utf-8')
            frame_dict = json.loads(json_str)
            
            # Extract data and convert to numpy array
            data_list = frame_dict.get('data', [])
            return np.array(data_list, dtype=np.float64)
            
        except Exception as e:
            logger.error(f"Error deserializing JSON: {e}")
            return np.array([], dtype=np.float64)


# ---------- Averaging Engine ----------
# MARK: -Averaging Engine

class AveragingEngine:
    """Performs windowed or rolling average on signal data."""
    
    def __init__(self, config: SignalConfig):
        self.config = config
        self.buffer = []
        self.last_average = None
        self.window_samples = 0
        
        # Calculate window size in samples if specified in seconds
        if isinstance(config.window_size, float) and config.window_size > 0:
            # We'll update this when we get the first frame with sample_rate
            self.window_samples = 0
        else:
            # Window size is already in samples
            self.window_samples = int(config.window_size)
    
    def add_frame(self, frame: SignalFrame) -> Optional[np.ndarray]:
        """Add a frame to the averaging buffer and compute average if ready."""
        # Update window size in samples if needed
        if self.window_samples == 0 and frame.sample_rate > 0:
            self.window_samples = int(self.config.window_size * frame.sample_rate)
        
        # Add frame data to buffer
        self.buffer.append(frame.data)
        
        # Check if we have enough data to compute an average
        if len(self.buffer) >= 1:  # Always compute for now
            return self._compute_average()
        
        return None
    
    def _compute_average(self) -> np.ndarray:
        """Compute the average based on configured window type."""
        if self.config.window_type == "rolling":
            return self._compute_rolling_average()
        elif self.config.window_type == "fixed":
            return self._compute_fixed_average()
        elif self.config.window_type == "exponential":
            return self._compute_exponential_average()
        else:
            # Default to simple average
            return self._compute_simple_average()
    
    def _compute_rolling_average(self) -> np.ndarray:
        """Compute a rolling (moving) average."""
        # Keep only the most recent window_samples
        if len(self.buffer) > self.window_samples:
            self.buffer = self.buffer[-self.window_samples:]
        
        # Compute average
        avg = np.mean(self.buffer, axis=0)
        self.last_average = avg
        return avg
    
    def _compute_fixed_average(self) -> np.ndarray:
        """Compute average over fixed, non-overlapping windows."""
        if len(self.buffer) >= self.window_samples:
            # Take only complete windows
            window_count = len(self.buffer) // self.window_samples
            data_to_average = self.buffer[:window_count * self.window_samples]
            
            # Reshape and average
            data_array = np.array(data_to_average)
            reshaped = data_array.reshape(window_count, self.window_samples, -1)
            avg = np.mean(reshaped, axis=1)
            
            # Keep remainder
            self.buffer = self.buffer[window_count * self.window_samples:]
            
            # Save last average
            self.last_average = avg[-1]
            return avg[-1]
        
        return self.last_average if self.last_average is not None else np.array([])
    
    def _compute_exponential_average(self) -> np.ndarray:
        """Compute exponential moving average with smoothing factor."""
        # Default alpha (smoothing factor)
        alpha = 0.2
        
        if self.last_average is None:
            # First average is simple mean
            self.last_average = np.mean(self.buffer, axis=0)
        else:
            # Exponential average formula: avg = alpha * new_data + (1 - alpha) * prev_avg
            newest_data = self.buffer[-1]
            self.last_average = alpha * newest_data + (1 - alpha) * self.last_average
        
        return self.last_average
    
    def _compute_simple_average(self) -> np.ndarray:
        """Compute simple average of all data in buffer."""
        avg = np.mean(self.buffer, axis=0)
        self.last_average = avg
        return avg
    
    def reset(self) -> None:
        """Reset the averaging engine."""
        self.buffer = []
        self.last_average = None


# ---------- Signal Processor ----------
# MARK: -Signal Processor

class SignalProcessor:
    """Processes and manipulates signal data, detecting significant changes."""
    
    def __init__(self, config: SignalConfig):
        self.config = config
        self.previous_result = None
        self.callbacks = []
    
    def process(self, data: np.ndarray) -> np.ndarray:
        """Apply processing to the signal data."""
        # Basic implementation - apply placeholder processing
        # In practice, this would include filters, transforms, etc.
        processed_data = data.copy()
        
        # Check for significant changes
        if self.previous_result is not None:
            change = self._calculate_change(processed_data, self.previous_result)
            if change > self.config.change_threshold:
                self._notify_change(processed_data, change)
        
        # Store result for change detection
        self.previous_result = processed_data
        
        return processed_data
    
    def _calculate_change(self, new_data: np.ndarray, old_data: np.ndarray) -> float:
        """Calculate the magnitude of change between two signals."""
        # Basic implementation - mean absolute difference
        # Could be replaced with more sophisticated metrics
        if len(new_data) == 0 or len(old_data) == 0:
            return 0.0
        
        # Ensure same length by truncating the longer one
        min_length = min(len(new_data), len(old_data))
        diff = np.abs(new_data[:min_length] - old_data[:min_length])
        return np.mean(diff)
    
    def register_change_callback(self, callback: Callable[[np.ndarray, float], None]) -> None:
        """Register a callback to be called when significant changes are detected."""
        self.callbacks.append(callback)
    
    def _notify_change(self, data: np.ndarray, change_magnitude: float) -> None:
        """Notify all registered callbacks about a significant change."""
        for callback in self.callbacks:
            try:
                callback(data, change_magnitude)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    def reset(self) -> None:
        """Reset the signal processor."""
        self.previous_result = None


# ---------- Event Dispatcher ----------
# MARK: -Event Dispatcher

class EventDispatcher:
    """Handles event registration and dispatching."""
    
    def __init__(self):
        self.listeners = {}
    
    def register_listener(self, event_type: SignalEventType, callback: Callable) -> None:
        """Register a listener for a specific event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(callback)
    
    def dispatch_event(self, event_type: SignalEventType, data: Any = None) -> None:
        """Dispatch an event to all registered listeners."""
        if event_type not in self.listeners:
            return
        
        for callback in self.listeners[event_type]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type}: {e}")
    
    def remove_listener(self, event_type: SignalEventType, callback: Callable) -> bool:
        """Remove a listener for a specific event type."""
        if event_type not in self.listeners:
            return False
        
        try:
            self.listeners[event_type].remove(callback)
            return True
        except ValueError:
            return False


# ---------- Signal Processing System ----------
# MARK: -Processing System

class SignalProcessingSystem:
    """Main class that coordinates all components of the signal processing system."""
    
    def __init__(self, config: SignalConfig):
        self.config = config
        self.provider = None
        self.averaging_engine = AveragingEngine(config)
        self.signal_processor = SignalProcessor(config)
        self.event_dispatcher = EventDispatcher()
        self.running = False
        self.processing_thread = None
        self.stop_flag = threading.Event()
    
    def initialize(self, provider_factory: Callable[[], SignalProvider]) -> bool:
        """Initialize the system with a signal provider."""
        try:
            # Create provider
            self.provider = provider_factory()
            
            # Open provider
            if not self.provider.open():
                logger.error("Failed to open signal provider")
                return False
            
            # Set up signal processor callback
            self.signal_processor.register_change_callback(self._on_signal_changed)
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing signal processing system: {e}")
            return False
    
    def start(self) -> bool:
        """Start the signal processing system."""
        if self.running or not self.provider:
            return False
        
        self.stop_flag.clear()
        self.running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        
        return True
    
    def stop(self) -> None:
        """Stop the signal processing system."""
        if not self.running:
            return
        
        self.stop_flag.set()
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        if self.provider:
            self.provider.close()
        
        self.running = False
    
    def _processing_loop(self) -> None:
        """Main processing loop that runs in a background thread."""
        while not self.stop_flag.is_set() and self.provider.is_open:
            try:
                # Get next frame
                frame = self.provider.get_frame()
                if frame is None:
                    # No data available, wait a bit
                    time.sleep(0.01)
                    continue
                
                # Dispatch new frame event
                self.event_dispatcher.dispatch_event(
                    SignalEventType.NEW_FRAME, 
                    frame
                )
                
                # Process through averaging engine
                averaged_data = self.averaging_engine.add_frame(frame)
                if averaged_data is not None:
                    # Dispatch average updated event
                    self.event_dispatcher.dispatch_event(
                        SignalEventType.AVERAGE_UPDATED, 
                        averaged_data
                    )
                    
                    # Process through signal processor
                    processed_data = self.signal_processor.process(averaged_data)
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                self.event_dispatcher.dispatch_event(
                    SignalEventType.ERROR, 
                    str(e)
                )
                time.sleep(1.0)  # Avoid tight error loop
    
    def _on_signal_changed(self, data: np.ndarray, change_magnitude: float) -> None:
        """Callback for when the signal processor detects a significant change."""
        # Dispatch signal changed event
        self.event_dispatcher.dispatch_event(
            SignalEventType.SIGNAL_CHANGED,
            {
                'data': data,
                'change_magnitude': change_magnitude
            }
        )
    
    def register_event_listener(self, event_type: SignalEventType, callback: Callable) -> None:
        """Register a listener for a specific event type."""
        self.event_dispatcher.register_listener(event_type, callback)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from the signal provider."""
        if self.provider:
            return self.provider.get_metadata()
        return {}


# ---------- Factory Functions ----------
# MARK: - Factory Functions

def create_file_signal_provider(config: SignalConfig, file_path: str) -> FileSignalProvider:
    """Factory function to create a FileSignalProvider."""
    return FileSignalProvider(config, file_path)


def create_live_signal_provider(config: SignalConfig, connection_factory: Callable) -> LiveSignalProvider:
    """Factory function to create a LiveSignalProvider."""
    return LiveSignalProvider(config, connection_factory)


# ---------- Utility Functions ----------
# MARK: - Utility Functions

def setup_file_processing_system(file_path: str, config: Optional[SignalConfig] = None) -> SignalProcessingSystem:
    """Set up a signal processing system for file-based processing."""
    if config is None:
        config = SignalConfig(mode="file", full_signal=True)
    
    system = SignalProcessingSystem(config)
    system.initialize(lambda: create_file_signal_provider(config, file_path))
    return system


def setup_live_processing_system(connection_factory: Callable, config: Optional[SignalConfig] = None) -> SignalProcessingSystem:
    """Set up a signal processing system for live signal processing."""
    if config is None:
        config = SignalConfig(mode="live", frame_rate=30.0)
    
    system = SignalProcessingSystem(config)
    system.initialize(lambda: create_live_signal_provider(config, connection_factory))
    return system