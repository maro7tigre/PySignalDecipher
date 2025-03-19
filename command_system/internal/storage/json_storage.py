"""
JSON storage implementation.
"""
import os
import json
from command_system.internal.storage.storage_interface import StorageInterface


class JsonStorage(StorageInterface):
    """
    Storage implementation that saves data as JSON files.
    """
    
    def __init__(self, file_path):
        """
        Initialize JSON storage.
        
        Args:
            file_path (str): Path to the JSON file
        """
        self.file_path = file_path
        
    def save(self, data):
        """
        Save data as JSON.
        
        Args:
            data: Data to save (must be JSON serializable)
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            # Custom JSON encoder to handle objects with serialize method
            class CommandSystemJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if hasattr(obj, 'serialize') and callable(getattr(obj, 'serialize')):
                        return obj.serialize()
                    # Let the base class handle other types or raise TypeError
                    return super().default(obj)
                    
            # Write to file with custom encoder
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2, cls=CommandSystemJSONEncoder)
                
            return True
        except Exception as e:
            print(f"Error saving JSON data: {e}")
            return False
            
    def load(self):
        """
        Load data from JSON file.
        
        Returns:
            Data loaded from JSON, or None if load failed
        """
        if not self.exists():
            return None
            
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return None
            
    def exists(self):
        """
        Check if the JSON file exists.
        
        Returns:
            bool: True if file exists
        """
        return os.path.exists(self.file_path)