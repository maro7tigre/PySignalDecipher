class VariableRegistry:
    """
    Central registry for all variables in the application.
    Manages variable lifecycles and parent-child relationships.
    """
    
    def __init__(self):
        self._variables = {}  # All variables by ID
        self._parent_map = {}  # Dict mapping parent_id to list of variable IDs
    
    def register_variable(self, variable):
        """Register a variable in the system"""
        self._variables[variable.id] = variable
        
        # Add to parent mapping if applicable
        if variable.parent_id:
            if variable.parent_id not in self._parent_map:
                self._parent_map[variable.parent_id] = []
            self._parent_map[variable.parent_id].append(variable.id)
    
    def unregister_variable(self, variable_id):
        """Remove a variable from the registry"""
        if variable_id in self._variables:
            variable = self._variables[variable_id]
            
            # Clean up parent mapping
            if variable.parent_id and variable.parent_id in self._parent_map:
                if variable_id in self._parent_map[variable.parent_id]:
                    self._parent_map[variable.parent_id].remove(variable_id)
            
            # Clear all subscribers
            variable.clear_subscribers()
            
            # Remove from registry
            del self._variables[variable_id]
    
    def unregister_parent(self, parent_id):
        """Unregister all variables belonging to a parent"""
        if parent_id in self._parent_map:
            # Make a copy since we'll be modifying during iteration
            variable_ids = self._parent_map[parent_id].copy()
            for variable_id in variable_ids:
                self.unregister_variable(variable_id)
            
            # Clean up parent mapping
            del self._parent_map[parent_id]
    
    def get_variable(self, variable_id):
        """Get a variable by ID"""
        return self._variables.get(variable_id)
    
    def get_variables_by_parent(self, parent_id):
        """Get all variables belonging to a parent"""
        variable_ids = self._parent_map.get(parent_id, [])
        return [self._variables[vid] for vid in variable_ids if vid in self._variables]