"""
Storage interface for saving and loading data.
"""
from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """
    Abstract base class for storage implementations.
    """
    
    @abstractmethod
    def save(self, data):
        """
        Save data to storage.
        
        Args:
            data: Data to save
            
        Returns:
            bool: True if save was successful
        """
        pass
        
    @abstractmethod
    def load(self):
        """
        Load data from storage.
        
        Returns:
            Data loaded from storage, or None if load failed
        """
        pass
        
    @abstractmethod
    def exists(self):
        """
        Check if storage exists.
        
        Returns:
            bool: True if storage exists
        """
        pass