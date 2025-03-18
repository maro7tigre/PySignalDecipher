"""
Basic workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Basic Signal Analysis workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class BasicWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Basic Signal Analysis workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the basic workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the basic workspace utility."""
        # Example dropdown control that could affect project settings
        self.add_combo_box(
            id="view_mode",
            label="View Mode:",
            items=["Chart", "Waterfall", "Tabular"],
            callback=self._on_view_mode_changed
        )
        
        # Example numeric control
        self.add_spin_box(
            id="sample_rate",
            label="Sample Rate:",
            minimum=1000,
            maximum=100000,
            value=44100,
            callback=self._on_sample_rate_changed
        )
        
        # Example action button
        self.add_button(
            id="analyze",
            text="Analyze",
            callback=self._on_analyze_clicked
        )
    
    def _on_view_mode_changed(self, mode):
        """
        Handle view mode changes with command system integration.
        
        Args:
            mode: The selected view mode
        """
        if not self._workspace or not self._command_manager:
            return
            
        # Example: create and execute a command to change the view mode
        # This would be saved in command history and project state
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Create a command to change the setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="view_mode", 
                                                        value=mode)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing view mode: {e}")
    
    def _on_sample_rate_changed(self, value):
        """
        Handle sample rate changes with command system integration.
        
        Args:
            value: The new sample rate value
        """
        if not self._workspace or not self._command_manager:
            return
            
        # Example: create and execute a command to change the sample rate
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Create a command to change the setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="sample_rate", 
                                                        value=value)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing sample rate: {e}")
    
    def _on_analyze_clicked(self):
        """Handle analyze button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        # Example: create and execute a batch command for analysis
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for analysis
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Signal Analysis")
                
                # Add individual commands to the batch
                # (In a real implementation, you would add commands to perform analysis steps)
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing analysis: {e}")
    
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        """
        if not self._workspace or not self._command_manager:
            return
            
        # Example: Update controls from workspace state
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Update view mode
                    view_mode = workspace_state.get_setting("view_mode")
                    if view_mode and self.get_control("view_mode"):
                        self.get_control("view_mode").setCurrentText(view_mode)
                        
                    # Update sample rate
                    sample_rate = workspace_state.get_setting("sample_rate")
                    if sample_rate and self.get_control("sample_rate"):
                        self.get_control("sample_rate").setValue(sample_rate)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")