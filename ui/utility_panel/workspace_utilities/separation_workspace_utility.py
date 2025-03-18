"""
Separation workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Signal Separation workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class SeparationWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Signal Separation workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the separation workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the separation workspace utility."""
        # Separation method selection
        self.add_combo_box(
            id="method",
            label="Method:",
            items=["Filtering", "ICA", "Wavelet", "Neural"],
            callback=self._on_method_changed
        )
        
        # Components control
        self.add_spin_box(
            id="components",
            label="Components:",
            minimum=2,
            maximum=10,
            value=3,
            callback=self._on_components_changed
        )
        
        # Auto-detect option
        self.add_check_box(
            id="auto_detect",
            text="Auto-detect Components",
            checked=True,
            callback=self._on_auto_detect_changed
        )
        
        # Separate button
        self.add_button(
            id="separate",
            text="Separate Signals",
            callback=self._on_separate_clicked
        )
    
    def _on_method_changed(self, method):
        """
        Handle method selection changes with command system integration.
        
        Args:
            method: The selected separation method
        """
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Create a command to change the method setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="sep_method", 
                                                        value=method)
                    self._command_manager.execute_command(command)
                    
                    # Enable/disable components control based on method
                    is_auto_compatible = method in ["ICA", "Neural"]
                    self.get_control("auto_detect").setEnabled(is_auto_compatible)
        except Exception as e:
            print(f"Error changing separation method: {e}")
    
    def _on_components_changed(self, components):
        """
        Handle components changes with command system integration.
        
        Args:
            components: The new components value
        """
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Create a command to change the components setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="components", 
                                                        value=components)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing components: {e}")
    
    def _on_auto_detect_changed(self, state):
        """
        Handle auto-detect checkbox changes with command system integration.
        
        Args:
            state: The checkbox state
        """
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Create a command to change the auto-detect setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="auto_detect", 
                                                        value=bool(state))
                    self._command_manager.execute_command(command)
                    
                    # Enable/disable components control based on auto-detect
                    self.get_control("components").setEnabled(not bool(state))
        except Exception as e:
            print(f"Error changing auto-detect setting: {e}")
    
    def _on_separate_clicked(self):
        """Handle separate button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for signal separation
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Signal Separation")
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing signal separation: {e}")
    
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        """
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project and workspace state
            project = self._command_manager.get_active_project()
            if project and self._workspace:
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    
                    # Update method selection
                    method = workspace_state.get_setting("sep_method")
                    if method and self.get_control("method"):
                        self.get_control("method").setCurrentText(method)
                        
                    # Update components
                    components = workspace_state.get_setting("components")
                    if components is not None and self.get_control("components"):
                        self.get_control("components").setValue(components)
                        
                    # Update auto-detect checkbox
                    auto_detect = workspace_state.get_setting("auto_detect")
                    if auto_detect is not None and self.get_control("auto_detect"):
                        self.get_control("auto_detect").setChecked(auto_detect)
                        # Enable/disable components control based on auto-detect
                        self.get_control("components").setEnabled(not auto_detect)
                        
                    # Also update enabled state based on method
                    if method:
                        is_auto_compatible = method in ["ICA", "Neural"]
                        self.get_control("auto_detect").setEnabled(is_auto_compatible)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")