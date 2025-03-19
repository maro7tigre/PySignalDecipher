"""
Storage manager for different storage types.
"""
import os


class StorageManager:
    """
    Manager for different storage implementations.
    Provides factory methods for creating appropriate storage based on file extension.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = StorageManager()
        return cls._instance
    
    def __init__(self):
        """Initialize storage manager."""
        if StorageManager._instance is not None:
            raise RuntimeError("Use StorageManager.get_instance() to get the singleton instance")
            
        StorageManager._instance = self
        
    def get_storage(self, file_path):
        """
        Get appropriate storage for a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            StorageInterface: Storage implementation
        """
        # Determine file type by extension
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.json':
            from command_system.internal.storage.json_storage import JsonStorage
            return JsonStorage(file_path)
        elif ext in ('.h5', '.hdf5'):
            from command_system.internal.storage.hdf5_storage import HDF5Storage
            return HDF5Storage(file_path)
        else:
            # Default to JSON storage
            from command_system.internal.storage.json_storage import JsonStorage
            return JsonStorage(file_path)