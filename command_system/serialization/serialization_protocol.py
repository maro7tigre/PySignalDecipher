class SerializationProtocol:
    """Protocol for serializable components."""
    
    def get_serialization_data(self) -> dict:
        """
        Return serialization data for this component.
        
        The returned dictionary should contain all information needed
        to reconstruct this component, including:
        - Component ID
        - Type information
        - Property values
        - Children (for containers)
        
        Returns:
            Dict containing serializable component state
        """
        raise NotImplementedError()
    
    @classmethod
    def from_serialization_data(cls, data: dict):
        """
        Create component from serialization data.
        
        This is the first phase of deserialization that creates
        the component with its ID and basic properties.
        
        Args:
            data: Dictionary containing serialized component state
            
        Returns:
            Newly created component instance
        """
        raise NotImplementedError()
    
    def restore_relationships(self, serialized_state: dict) -> None:
        """
        Restore relationships after creation (second phase).
        
        This method is called after all components have been created
        to establish relationships between them, including:
        - Parent-child relationships
        - Property bindings
        - Observer connections
        
        Args:
            serialized_state: Complete serialized state containing all components
        """
        raise NotImplementedError()