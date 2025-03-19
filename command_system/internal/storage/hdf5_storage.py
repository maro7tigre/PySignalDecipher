"""
HDF5 storage implementation for signal data.
"""
import os
import numpy as np
import h5py
from command_system.internal.storage.storage_interface import StorageInterface


class HDF5Storage(StorageInterface):
    """
    Storage implementation that saves data as HDF5 files.
    Optimized for large signal data.
    """
    
    def __init__(self, file_path):
        """
        Initialize HDF5 storage.
        
        Args:
            file_path (str): Path to the HDF5 file
        """
        self.file_path = file_path
        
    def save(self, data, dataset_name="data", compression="gzip", compression_opts=9):
        """
        Save data to HDF5 file.
        
        Args:
            data: Data to save (numpy array or compatible)
            dataset_name (str): Name of the dataset within the HDF5 file
            compression (str): Compression type
            compression_opts (int): Compression options
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Convert to numpy array if needed
            if not isinstance(data, np.ndarray):
                data = np.array(data)
                
            # Write to file
            with h5py.File(self.file_path, 'w') as f:
                f.create_dataset(
                    dataset_name,
                    data=data,
                    compression=compression,
                    compression_opts=compression_opts
                )
                
            return True
        except Exception as e:
            print(f"Error saving HDF5 data: {e}")
            return False
            
    def load(self, dataset_name="data", start=None, end=None):
        """
        Load data from HDF5 file.
        
        Args:
            dataset_name (str): Name of the dataset within the HDF5 file
            start (int, optional): Start index for partial loading
            end (int, optional): End index for partial loading
            
        Returns:
            Data loaded from HDF5, or None if load failed
        """
        if not self.exists():
            return None
            
        try:
            with h5py.File(self.file_path, 'r') as f:
                if dataset_name in f:
                    if start is not None or end is not None:
                        # Default values for start and end
                        if start is None:
                            start = 0
                        if end is None:
                            end = f[dataset_name].shape[0]
                            
                        # Load partial data
                        return f[dataset_name][start:end]
                    else:
                        # Load full data
                        return f[dataset_name][:]
                else:
                    return None
        except Exception as e:
            print(f"Error loading HDF5 data: {e}")
            return None
            
    def exists(self):
        """
        Check if the HDF5 file exists.
        
        Returns:
            bool: True if file exists
        """
        return os.path.exists(self.file_path)
        
    def get_metadata(self, key=None):
        """
        Get metadata from HDF5 file.
        
        Args:
            key (str, optional): Specific metadata key to get.
                                If None, returns all metadata.
                                
        Returns:
            Metadata value or dict of all metadata
        """
        if not self.exists():
            return None if key else {}
            
        try:
            with h5py.File(self.file_path, 'r') as f:
                if key is not None:
                    # Get specific metadata
                    return f.attrs.get(key)
                else:
                    # Get all metadata
                    return dict(f.attrs)
        except Exception as e:
            print(f"Error getting HDF5 metadata: {e}")
            return None if key else {}
            
    def set_metadata(self, key, value):
        """
        Set metadata in HDF5 file.
        
        Args:
            key (str): Metadata key
            value: Metadata value
            
        Returns:
            bool: True if metadata was set successfully
        """
        if not self.exists():
            return False
            
        try:
            with h5py.File(self.file_path, 'r+') as f:
                f.attrs[key] = value
            return True
        except Exception as e:
            print(f"Error setting HDF5 metadata: {e}")
            return False
            
    def get_dataset_info(self, dataset_name="data"):
        """
        Get information about a dataset.
        
        Args:
            dataset_name (str): Name of the dataset
            
        Returns:
            dict: Dataset information (shape, dtype, etc.)
        """
        if not self.exists():
            return None
            
        try:
            with h5py.File(self.file_path, 'r') as f:
                if dataset_name in f:
                    dataset = f[dataset_name]
                    return {
                        "shape": dataset.shape,
                        "dtype": dataset.dtype.name,
                        "size_bytes": dataset.size * dataset.dtype.itemsize,
                        "chunks": dataset.chunks,
                        "compression": dataset.compression,
                        "compression_opts": dataset.compression_opts
                    }
                else:
                    return None
        except Exception as e:
            print(f"Error getting dataset info: {e}")
            return None