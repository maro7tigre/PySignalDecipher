"""
Signal data management for large datasets.
"""
import os
import tempfile
import numpy as np
from command_system.observable import Observable, ObservableProperty
from command_system.internal.storage.hdf5_storage import HDF5Storage


class SignalData(Observable):
    """
    Signal data representation with observable properties.
    Can store data in memory or in a file for large datasets.
    """
    name = ObservableProperty(default="Signal")
    sample_rate = ObservableProperty(default=44100.0)
    
    def __init__(self, name="Signal", data=None, use_file_storage=True, file_path=None):
        """
        Initialize signal data.
        
        Args:
            name (str): Signal name
            data (array-like, optional): Signal data
            use_file_storage (bool): Whether to use file storage for data
            file_path (str, optional): Path to file for storage
        """
        super().__init__()
        self.name = name
        self._use_file_storage = use_file_storage
        self._file_path = file_path
        self._data_cache = None
        self._metadata = {}
        
        # If data provided, store it
        if data is not None:
            self.set_data(data)
            
    def set_data(self, data):
        """
        Set signal data, using file storage if enabled.
        
        Args:
            data: Signal data (array-like)
            
        Returns:
            bool: True if data was set successfully
        """
        if self._use_file_storage:
            return self._store_data_to_file(data)
        else:
            self._data_cache = np.array(data) if not isinstance(data, np.ndarray) else data
            return True
            
    def get_data(self, start=0, end=None):
        """
        Get full signal data or a segment.
        
        Args:
            start (int): Start index
            end (int, optional): End index
            
        Returns:
            numpy.ndarray: Signal data
        """
        if self._use_file_storage and self._file_path:
            return self._load_data_from_file(start, end)
        else:
            if self._data_cache is None:
                return None
                
            if end is None:
                return self._data_cache[start:]
            else:
                return self._data_cache[start:end]
                
    def get_visible_segment(self, start_sample, end_sample, max_points=1000):
        """
        Get a downsampled segment for visualization.
        
        Args:
            start_sample (int): Start sample index
            end_sample (int): End sample index
            max_points (int): Maximum number of points to return
            
        Returns:
            numpy.ndarray: Downsampled segment
        """
        data = self.get_data(start_sample, end_sample)
        
        if data is None:
            return None
            
        # If too many points, downsample
        if len(data) > max_points:
            # Simple downsampling by selecting evenly spaced points
            step = len(data) // max_points
            return data[::step]
        
        return data
        
    def is_file_based(self):
        """
        Check if signal data is stored in a file.
        
        Returns:
            bool: True if data is stored in a file
        """
        return self._use_file_storage and self._file_path is not None
        
    def get_file_path(self):
        """
        Get the file path for file-based storage.
        
        Returns:
            str: File path, or None if not using file storage
        """
        return self._file_path if self._use_file_storage else None
        
    def _store_data_to_file(self, data):
        """
        Store data to file using HDF5.
        
        Args:
            data: Signal data
            
        Returns:
            bool: True if data was stored successfully
        """
        # Create temp file if no file path yet
        if not self._file_path:
            temp_dir = tempfile.gettempdir()
            self._file_path = os.path.join(temp_dir, f"signal_{self.get_id()}.h5")
            
        # Create storage
        storage = HDF5Storage(self._file_path)
        
        # Store data
        success = storage.save(data)
        
        # Store metadata
        if success:
            for key, value in self._metadata.items():
                storage.set_metadata(key, value)
                
        return success
        
    def _load_data_from_file(self, start=0, end=None):
        """
        Load data segment from file.
        
        Args:
            start (int): Start index
            end (int, optional): End index
            
        Returns:
            numpy.ndarray: Signal data
        """
        if not self._file_path:
            return None
            
        storage = HDF5Storage(self._file_path)
        return storage.load(start=start, end=end)
        
    def get_metadata(self, key=None, default=None):
        """
        Get metadata.
        
        Args:
            key (str, optional): Specific metadata key to get.
                                If None, returns all metadata.
            default: Default value if key not found
            
        Returns:
            Metadata value or dict of all metadata
        """
        if key is not None:
            return self._metadata.get(key, default)
        return self._metadata
        
    def set_metadata(self, key, value):
        """
        Set metadata.
        
        Args:
            key (str): Metadata key
            value: Metadata value
            
        Returns:
            bool: True if metadata was set successfully
        """
        self._metadata[key] = value
        
        # Update file if using file storage
        if self._use_file_storage and self._file_path:
            storage = HDF5Storage(self._file_path)
            return storage.set_metadata(key, value)
            
        return True
        
    def serialize(self):
        """
        Serialize signal data.
        
        Returns:
            dict: Serialized state
        """
        state = {
            "name": self.name,
            "sample_rate": self.sample_rate,
            "use_file_storage": self._use_file_storage,
            "file_path": self._file_path,
            "metadata": self._metadata
        }
        
        # Include in-memory data if not using file storage
        if not self._use_file_storage and self._data_cache is not None:
            # Convert numpy array to list for serialization
            state["data"] = self._data_cache.tolist()
            
        return state
        
    def deserialize(self, state, registry):
        """
        Restore signal data from serialized state.
        
        Args:
            state (dict): Serialized state
            registry: Object registry
            
        Returns:
            bool: True if deserialization was successful
        """
        self.name = state.get("name", "Signal")
        self.sample_rate = state.get("sample_rate", 44100.0)
        self._use_file_storage = state.get("use_file_storage", True)
        self._file_path = state.get("file_path")
        self._metadata = state.get("metadata", {})
        
        # Load in-memory data if present
        if "data" in state and not self._use_file_storage:
            self._data_cache = np.array(state["data"])
            
        return True


class SignalDataManager:
    """
    Manager for signal data objects.
    Provides caching and efficient access to signal data.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = SignalDataManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the signal data manager."""
        if SignalDataManager._instance is not None:
            raise RuntimeError("Use SignalDataManager.get_instance() to get the singleton instance")
            
        SignalDataManager._instance = self
        self._signals = {}
        self._cache = LRUCache(max_size=20)
        
    def create_signal(self, name, data=None, use_file_storage=True, file_path=None):
        """
        Create a new signal.
        
        Args:
            name (str): Signal name
            data (array-like, optional): Signal data
            use_file_storage (bool): Whether to use file storage
            file_path (str, optional): Path to file for storage
            
        Returns:
            SignalData: Created signal
        """
        signal = SignalData(name, data, use_file_storage, file_path)
        self._signals[signal.get_id()] = signal
        
        # Register with registry
        from command_system.internal.registry import Registry
        Registry.get_instance().register_object(signal)
        
        return signal
        
    def get_signal(self, signal_id):
        """
        Get a signal by ID.
        
        Args:
            signal_id (str): Signal ID
            
        Returns:
            SignalData: Signal object, or None if not found
        """
        return self._signals.get(signal_id)
        
    def remove_signal(self, signal_id):
        """
        Remove a signal.
        
        Args:
            signal_id (str): Signal ID
            
        Returns:
            bool: True if signal was removed
        """
        if signal_id in self._signals:
            # Remove from registry
            from command_system.internal.registry import Registry
            Registry.get_instance().unregister_object(signal_id)
            
            # Remove from signals
            del self._signals[signal_id]
            
            # Clear cache entries for this signal
            self._cache.remove_by_prefix(signal_id)
            
            return True
        return False
        
    def get_visible_segment(self, signal_id, start, end, max_points=1000):
        """
        Get a visible segment of signal data, using cache if available.
        
        Args:
            signal_id (str): Signal ID
            start (int): Start sample index
            end (int): End sample index
            max_points (int): Maximum number of points
            
        Returns:
            numpy.ndarray: Signal data segment
        """
        # Create cache key
        cache_key = f"{signal_id}:{start}:{end}:{max_points}"
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # Get signal
        signal = self.get_signal(signal_id)
        if not signal:
            return None
            
        # Get data segment
        data = signal.get_visible_segment(start, end, max_points)
        
        # Cache result
        if data is not None:
            self._cache[cache_key] = data
        
        return data
        
    def clear(self):
        """Clear all signals and cache."""
        self._signals.clear()
        self._cache.clear()


class LRUCache:
    """
    Least Recently Used Cache.
    Stores items with limited capacity, removing least recently used items when full.
    """
    def __init__(self, max_size=100):
        """
        Initialize LRU cache.
        
        Args:
            max_size (int): Maximum number of items to store
        """
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        
    def __getitem__(self, key):
        """
        Get item from cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            Cached item
            
        Raises:
            KeyError: If key not in cache
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        """
        Set item in cache.
        
        Args:
            key (str): Cache key
            value: Item to cache
        """
        if key in self.cache:
            # Update existing item
            self.cache[key] = value
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new item
            self.cache[key] = value
            self.access_order.append(key)
            
            # Remove oldest if over size
            if len(self.cache) > self.max_size:
                oldest = self.access_order.pop(0)
                del self.cache[oldest]
                
    def __contains__(self, key):
        """
        Check if key in cache.
        
        Args:
            key (str): Cache key
            
        Returns:
            bool: True if key in cache
        """
        return key in self.cache
        
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()
        
    def remove_by_prefix(self, prefix):
        """
        Remove all items with keys starting with prefix.
        
        Args:
            prefix (str): Key prefix to match
            
        Returns:
            int: Number of items removed
        """
        # Find keys to remove
        keys_to_remove = [key for key in self.cache if key.startswith(prefix)]
        
        # Remove from cache and access order
        for key in keys_to_remove:
            del self.cache[key]
            self.access_order.remove(key)
            
        return len(keys_to_remove)


class AdaptiveSampler:
    """
    Provides adaptive sampling based on zoom level.
    Different sampling strategies are used depending on zoom level.
    """
    
    def __init__(self, max_display_points=2000):
        """
        Initialize adaptive sampler.
        
        Args:
            max_display_points (int): Maximum number of points to display
        """
        self.max_display_points = max_display_points
        
    def sample(self, data, start, end, zoom_level):
        """
        Sample data adaptively based on zoom level.
        
        Args:
            data (numpy.ndarray): Data to sample
            start (int): Start index
            end (int): End index
            zoom_level (float): Zoom level (0-1)
            
        Returns:
            numpy.ndarray: Sampled data
        """
        segment = data[start:end]
        segment_length = len(segment)
        
        if segment_length <= self.max_display_points:
            # Detail mode: show all samples
            return segment
            
        if zoom_level < 0.1:
            # Overview mode: maximum downsampling
            # Use min-max sampling to preserve peaks
            return self._min_max_downsample(segment, self.max_display_points)
            
        elif zoom_level < 0.5:
            # Navigation mode: moderate downsampling
            # Use more points for better fidelity
            target_points = min(segment_length, self.max_display_points * 2)
            return self._min_max_downsample(segment, target_points)
            
        else:
            # Detail mode with downsampling
            # Use standard downsampling
            step = segment_length // self.max_display_points
            return segment[::step]
            
    def _min_max_downsample(self, data, target_points):
        """
        Downsample using min-max method to preserve peaks.
        Each output point represents the min and max of a bucket.
        
        Args:
            data (numpy.ndarray): Data to downsample
            target_points (int): Target number of points
            
        Returns:
            numpy.ndarray: Downsampled data
        """
        if len(data) <= target_points:
            return data
            
        # Ensure even target for min-max pairs
        if target_points % 2 != 0:
            target_points -= 1
            
        result = []
        bucket_size = len(data) / (target_points / 2)
        
        for i in range(0, int(target_points / 2)):
            start_idx = int(i * bucket_size)
            end_idx = int((i + 1) * bucket_size)
            
            if end_idx > len(data):
                end_idx = len(data)
                
            if start_idx == end_idx:
                if start_idx < len(data):
                    result.append(data[start_idx])
                    result.append(data[start_idx])
                continue
                
            bucket = data[start_idx:end_idx]
            
            # Add min and max from each bucket
            result.append(min(bucket))
            result.append(max(bucket))
            
        return np.array(result)