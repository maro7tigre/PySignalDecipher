"""
Data Registry for PySignalDecipher.

This module provides a centralized registry for sharing data between components.
Components can register as data providers, making their data available to other
components, and access data from other components through a simple interface.
"""

from typing import Dict, Any, List, Callable, Optional, Set, Tuple
from PySide6.QtCore import QObject, Signal


class DataChangeNotifier(QObject):
    """
    Notifier for data changes.
    
    Used to emit signals when registered data changes.
    """
    
    # Signal emitted when data changes
    data_changed = Signal(str, object)  # data_path, new_value


class DataRegistry:
    """
    Centralized registry for sharing data between components.
    
    Allows components to expose their data and access data from other components
    in a standardized way, with automatic notification of changes.
    """
    
    # Singleton instance
    _instance = None
    
    # Data registry structure:
    # {
    #     "component_id.data_id": {
    #         "value": actual_value,
    #         "description": "Description of the data",
    #         "provider": provider_object_or_reference,
    #         "getter": custom_getter_function (optional),
    #         "setter": custom_setter_function (optional),
    #         "metadata": { additional metadata dict }
    #     }
    # }
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the DataRegistry.
        
        Returns:
            DataRegistry: The singleton instance
        """
        if cls._instance is None:
            cls._instance = DataRegistry()
        return cls._instance
    
    def __init__(self):
        """
        Initialize the data registry.
        
        Note: Use get_instance() instead of creating instances directly.
        """
        # Only allow instantiation if we don't have an instance yet
        if DataRegistry._instance is not None:
            raise RuntimeError("Use DataRegistry.get_instance() instead of creating new instances")
            
        # Dictionary of registered data
        self._registry = {}
        
        # Change notifier for signaling data changes
        self._notifier = DataChangeNotifier()
        
        # Dictionary of data subscriptions
        # {data_path: set(callback_functions)}
        self._subscriptions = {}
        
        # Dictionary of data providers
        # {component_id: set(data_paths)}
        self._providers = {}
        
        # Dictionary of data accessors by component
        # {component_id: set(data_paths)}
        self._accessors = {}
        
        # Set DataRegistry._instance to self
        DataRegistry._instance = self
    
    def register_data(self, data_path: str, description: str, provider: Any,
                     initial_value: Any = None, getter: Callable = None, 
                     setter: Callable = None, metadata: Dict = None) -> bool:
        """
        Register data in the registry.
        
        Args:
            data_path: Path identifier for the data (e.g., "component_id.data_id")
            description: Human-readable description of the data
            provider: Object or reference to the provider of this data
            initial_value: Initial value of the data
            getter: Optional custom function to get the current value
            setter: Optional custom function to set the value
            metadata: Optional additional metadata dictionary
            
        Returns:
            bool: True if registration succeeded, False if the data path already exists
        """
        # Check if data path already exists
        if data_path in self._registry:
            return False
            
        # Extract component ID from data path
        component_id = data_path.split('.')[0] if '.' in data_path else data_path
        
        # Create registry entry
        self._registry[data_path] = {
            "value": initial_value,
            "description": description,
            "provider": provider,
            "getter": getter,
            "setter": setter,
            "metadata": metadata or {}
        }
        
        # Register as provider
        if component_id not in self._providers:
            self._providers[component_id] = set()
        self._providers[component_id].add(data_path)
        
        return True
    
    def unregister_data(self, data_path: str) -> bool:
        """
        Unregister data from the registry.
        
        Args:
            data_path: Path identifier for the data
            
        Returns:
            bool: True if unregistration succeeded, False if the data path does not exist
        """
        if data_path not in self._registry:
            return False
            
        # Extract component ID from data path
        component_id = data_path.split('.')[0] if '.' in data_path else data_path
        
        # Remove from registry
        del self._registry[data_path]
        
        # Remove from providers
        if component_id in self._providers:
            self._providers[component_id].discard(data_path)
            if not self._providers[component_id]:
                del self._providers[component_id]
                
        # Remove any subscriptions
        if data_path in self._subscriptions:
            del self._subscriptions[data_path]
            
        return True
    
    def unregister_component(self, component_id: str) -> int:
        """
        Unregister all data provided by a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            int: Number of data paths unregistered
        """
        # Check if component is a provider
        if component_id not in self._providers:
            return 0
            
        # Get all data paths for this component
        data_paths = list(self._providers[component_id])
        
        # Unregister each data path
        count = 0
        for data_path in data_paths:
            if self.unregister_data(data_path):
                count += 1
                
        # Remove component from accessors
        if component_id in self._accessors:
            del self._accessors[component_id]
                
        return count
    
    def get_data(self, data_path: str, default: Any = None) -> Any:
        """
        Get data from the registry.
        
        Args:
            data_path: Path identifier for the data
            default: Default value to return if the data path does not exist
            
        Returns:
            The data value, or the default if not found
        """
        # Check if data path exists
        if data_path not in self._registry:
            return default
        
        # Get registry entry
        entry = self._registry[data_path]
        
        # Use custom getter if available
        if entry["getter"] is not None:
            try:
                return entry["getter"]()
            except Exception as e:
                print(f"Error in custom getter for {data_path}: {e}")
                return entry["value"]
        
        # Return the value
        return entry["value"]
    
    def set_data(self, data_path: str, value: Any) -> bool:
        """
        Set data in the registry.
        
        Args:
            data_path: Path identifier for the data
            value: New value for the data
            
        Returns:
            bool: True if the data was set, False if the data path does not exist
            or the data is not settable
        """
        # Check if data path exists
        if data_path not in self._registry:
            return False
        
        # Get registry entry
        entry = self._registry[data_path]
        
        # Use custom setter if available
        if entry["setter"] is not None:
            try:
                entry["setter"](value)
                # The custom setter is responsible for notifying subscribers
                return True
            except Exception as e:
                print(f"Error in custom setter for {data_path}: {e}")
                return False
        
        # Update the value
        entry["value"] = value
        
        # Notify subscribers
        self._notify_data_changed(data_path, value)
        
        return True
    
    def _notify_data_changed(self, data_path: str, new_value: Any) -> None:
        """
        Notify subscribers of data changes.
        
        Args:
            data_path: Path identifier for the data
            new_value: New value of the data
        """
        # Emit signal for direct signal-slot connections
        self._notifier.data_changed.emit(data_path, new_value)
        
        # Call individual callbacks
        if data_path in self._subscriptions:
            for callback in self._subscriptions[data_path]:
                try:
                    callback(data_path, new_value)
                except Exception as e:
                    print(f"Error in data change callback for {data_path}: {e}")
    
    def subscribe_to_data(self, data_path: str, callback: Callable[[str, Any], None]) -> bool:
        """
        Subscribe to changes in data.
        
        Args:
            data_path: Path identifier for the data
            callback: Function to call when the data changes
            
        Returns:
            bool: True if subscription succeeded, False if the data path does not exist
        """
        # Check if data path exists
        if data_path not in self._registry:
            return False
            
        # Create subscription set if not exists
        if data_path not in self._subscriptions:
            self._subscriptions[data_path] = set()
            
        # Add callback to subscription set
        self._subscriptions[data_path].add(callback)
        
        return True
    
    def unsubscribe_from_data(self, data_path: str, callback: Callable[[str, Any], None]) -> bool:
        """
        Unsubscribe from changes in data.
        
        Args:
            data_path: Path identifier for the data
            callback: Function to unsubscribe
            
        Returns:
            bool: True if unsubscription succeeded, False if the data path or
            subscription does not exist
        """
        # Check if subscription exists
        if (data_path not in self._subscriptions or
            callback not in self._subscriptions[data_path]):
            return False
            
        # Remove callback from subscription set
        self._subscriptions[data_path].remove(callback)
        
        # Remove subscription set if empty
        if not self._subscriptions[data_path]:
            del self._subscriptions[data_path]
            
        return True
    
    def connect_to_data_changed(self, data_path: str, slot: Callable[[str, Any], None]) -> bool:
        """
        Connect a slot to the data_changed signal for a specific data path.
        
        This uses Qt's signal-slot mechanism for more direct integration with Qt components.
        
        Args:
            data_path: Path identifier for the data
            slot: Slot to connect to the signal
            
        Returns:
            bool: True if connection succeeded, False if the data path does not exist
        """
        # Check if data path exists
        if data_path not in self._registry:
            return False
            
        # Create a filter to only emit for this data path
        def filtered_slot(changed_path, value):
            if changed_path == data_path:
                slot(changed_path, value)
                
        # Connect to the signal
        self._notifier.data_changed.connect(filtered_slot)
        
        return True
    
    def register_accessor(self, component_id: str, data_path: str) -> bool:
        """
        Register a component as an accessor of data.
        
        This is used for tracking which components access which data.
        
        Args:
            component_id: ID of the component
            data_path: Path identifier for the data
            
        Returns:
            bool: True if registration succeeded, False if the data path does not exist
        """
        # Check if data path exists
        if data_path not in self._registry:
            return False
            
        # Create accessor set if not exists
        if component_id not in self._accessors:
            self._accessors[component_id] = set()
            
        # Add data path to accessor set
        self._accessors[component_id].add(data_path)
        
        return True
    
    def get_data_for_component(self, component_id: str) -> Dict[str, Any]:
        """
        Get all data provided by a component.
        
        Args:
            component_id: ID of the component
            
        Returns:
            Dictionary mapping data paths to values
        """
        result = {}
        
        # Check if component is a provider
        if component_id not in self._providers:
            return result
            
        # Get all data for this component
        for data_path in self._providers[component_id]:
            result[data_path] = self.get_data(data_path)
            
        return result
    
    def get_data_providers(self) -> Dict[str, Set[str]]:
        """
        Get a dictionary of all data providers.
        
        Returns:
            Dictionary mapping component IDs to sets of data paths
        """
        return self._providers.copy()
    
    def get_data_metadata(self, data_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a data path.
        
        Args:
            data_path: Path identifier for the data
            
        Returns:
            Dictionary of metadata, or None if the data path does not exist
        """
        # Check if data path exists
        if data_path not in self._registry:
            return None
            
        # Get registry entry
        entry = self._registry[data_path]
        
        return {
            "description": entry["description"],
            "provider": str(entry["provider"]),
            "metadata": entry["metadata"].copy() if entry["metadata"] else {},
            "has_custom_getter": entry["getter"] is not None,
            "has_custom_setter": entry["setter"] is not None
        }
    
    def get_available_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available data in the registry.
        
        Returns:
            Dictionary mapping data paths to metadata dictionaries
        """
        result = {}
        
        for data_path, entry in self._registry.items():
            result[data_path] = {
                "description": entry["description"],
                "provider": str(entry["provider"]),
                "metadata": entry["metadata"].copy() if entry["metadata"] else {},
                "has_custom_getter": entry["getter"] is not None,
                "has_custom_setter": entry["setter"] is not None
            }
            
        return result
    
    def get_registered_data_paths(self) -> List[str]:
        """
        Get a list of all registered data paths.
        
        Returns:
            List of data path strings
        """
        return list(self._registry.keys())
    
    def search_data(self, search_term: str, include_description: bool = True,
                   include_metadata: bool = False) -> List[str]:
        """
        Search the registry for data paths matching a search term.
        
        Args:
            search_term: Term to search for
            include_description: Whether to search in descriptions
            include_metadata: Whether to search in metadata
            
        Returns:
            List of matching data paths
        """
        result = []
        search_term = search_term.lower()
        
        for data_path, entry in self._registry.items():
            # Search in data path
            if search_term in data_path.lower():
                result.append(data_path)
                continue
                
            # Search in description if requested
            if include_description and search_term in entry["description"].lower():
                result.append(data_path)
                continue
                
            # Search in metadata if requested
            if include_metadata and entry["metadata"]:
                for key, value in entry["metadata"].items():
                    if (search_term in str(key).lower() or 
                        search_term in str(value).lower()):
                        result.append(data_path)
                        break
        
        return result


# Create an alias for easy access to the singleton instance
def get_data_registry():
    """
    Get the singleton instance of the DataRegistry.
    
    Returns:
        DataRegistry: The singleton instance
    """
    return DataRegistry.get_instance()