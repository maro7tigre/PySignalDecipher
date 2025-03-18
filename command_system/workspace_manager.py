import uuid


class WorkspaceTabManager:
    """
    Manages different workspace tabs and their associated commands/variables.
    """
    
    def __init__(self, command_manager, variable_registry):
        self.command_manager = command_manager
        self.variable_registry = variable_registry
        self.workspaces = {}  # Workspace objects by ID
        self.active_workspace_id = None
    
    def create_workspace(self, workspace_type, name):
        """Create a new workspace tab"""
        # Create a workspace ID
        workspace_id = str(uuid.uuid4())
        
        # Create workspace state in project
        project = self.command_manager.get_active_project()
        workspace_state = project.get_workspace_state(workspace_id)
        
        # Set workspace type and name
        workspace_state.set_setting("type", workspace_type)
        workspace_state.set_setting("name", name)
        
        # Set as active if it's the first workspace
        if not self.active_workspace_id:
            self.active_workspace_id = workspace_id
        
        return workspace_id
    
    def set_active_workspace(self, workspace_id):
        """Set the active workspace"""
        if workspace_id in self.workspaces:
            self.active_workspace_id = workspace_id
            # Update available options based on active workspace
            self._update_workspace_options(workspace_id)
    
    def _update_workspace_options(self, workspace_id):
        """Update available options based on workspace type"""
        project = self.command_manager.get_active_project()
        workspace_state = project.get_workspace_state(workspace_id)
        workspace_type = workspace_state.get_setting("type")
        
        # Update the utility group based on workspace type
        # This would emit signals to update the UI