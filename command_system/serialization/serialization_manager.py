from command_system.id_system import (
    get_id_registry, extract_type_code, extract_unique_id,
    is_widget_id, is_observable_id, is_observable_property_id
)

class SerializationManager:
    """
    Central manager for serialization operations.
    
    This singleton class coordinates all serialization and deserialization
    operations, handling the two-phase process and ensuring proper
    relationship restoration. It leverages the existing ID system utilities
    for ID-related operations.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = SerializationManager()
        return cls._instance
    
    def serialize_component(self, component) -> dict:
        """
        Serialize a single component.
        
        Args:
            component: Component to serialize
            
        Returns:
            Dictionary containing serialized state
        """
        # Get component ID
        id_registry = get_id_registry()
        component_id = id_registry.get_id(component)
        
        # Use protocol if implemented
        if hasattr(component, 'get_serialization_data'):
            data = component.get_serialization_data()
            data['id'] = component_id  # Ensure ID is included
            return data
            
        # Fall back to default implementation
        return self._default_serialize(component)
    
    def serialize_container(self, container) -> dict:
        """
        Serialize a container and all its children.
        
        This creates a complete representation of the container hierarchy,
        all contained observables, and their relationships.
        
        Args:
            container: Container component to serialize
            
        Returns:
            Dictionary containing serialized container state
        """
        # Implementation details using ID system utilities...
    
    def deserialize_component(self, data: dict, parent=None):
        """
        Deserialize a component using the two-phase approach.
        
        Args:
            data: Serialized component data
            parent: Optional parent component
            
        Returns:
            Reconstructed component
        """
        # Phase 1: Create components
        components = self._create_components_phase(data)
        
        # Phase 2: Restore relationships
        self._restore_relationships_phase(components, data)
        
        # Return the root component
        return components.get(data.get('root_id'))
    
    def _create_components_phase(self, data: dict) -> dict:
        """
        First phase: Create all components with correct IDs.
        
        Args:
            data: Serialized state
            
        Returns:
            Dictionary mapping component IDs to created components
        """
        # Implementation using ID system utilities...
    
    def _restore_relationships_phase(self, components: dict, data: dict) -> None:
        """
        Second phase: Restore relationships between components.
        
        Args:
            components: Dictionary of created components (ID -> component)
            data: Complete serialized state
        """
        # Implementation using ID system utilities...
    
    def _default_serialize(self, component) -> dict:
        """Default serialization for components without protocol implementation."""
        # Implementation details...
        
    # Helper methods for serialization-specific tasks
    def _collect_component_ids(self, serialized_state: dict) -> list:
        """Collect all component IDs from a serialized state."""
        # Implementation using ID system utilities...