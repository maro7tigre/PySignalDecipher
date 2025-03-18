"""
Advanced workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Advanced Analysis workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class AdvancedWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Advanced Analysis workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the advanced workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the advanced workspace utility."""
        # Transform type selection
        self.add_combo_box(
            id="transform",
            label="Transform:",
            items=["Fourier", "Wavelet", "Hilbert", "Z-Transform"],
            callback=self._on_transform_changed
        )
        
        # Window type selection for applicable transforms
        self.add_combo_box(
            id="window",
            label="Window:",
            items=["Rectangular", "Hamming", "Hanning", "Blackman"],
            callback=self._on_window_changed
        )
        
        # Resolution setting
        self.add_spin_box(
            id="resolution",
            label="Resolution:",
            minimum=64,
            maximum=8192,
            value=1024,
            callback=self._on_resolution_changed
        )
        
        # Analyze button
        self.add_button(
            id="analyze",
            text="Analyze Signal",
            callback=self._on_analyze_clicked
        )
    
    def _on_transform_changed(self, transform):
        """
        Handle transform selection changes with command system integration.
        
        Args:
            transform: The selected transform type
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
                    
                    # Create a command to change the transform setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="transform_type", 
                                                        value=transform)
                    self._command_manager.execute_command(command)
                    
                    # Enable/disable window selection based on transform type
                    is_window_applicable = transform in ["Fourier", "Wavelet"]
                    self.get_control("window").setEnabled(is_window_applicable)
        except Exception as e:
            print(f"Error changing transform type: {e}")
    
    def _on_window_changed(self, window):
        """
        Handle window selection changes with command system integration.
        
        Args:
            window: The selected window type
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
                    
                    # Create a command to change the window setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="window_type", 
                                                        value=window)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing window type: {e}")
    
    def _on_resolution_changed(self, resolution):
        """
        Handle resolution changes with command system integration.
        
        Args:
            resolution: The new resolution value
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
                    
                    # Create a command to change the resolution setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="resolution", 
                                                        value=resolution)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing resolution: {e}")
    
    def _on_analyze_clicked(self):
        """Handle analyze button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for advanced analysis
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Advanced Analysis")
                
                # Example of how to get current settings for the analysis
                workspace_id = getattr(self._workspace, 'workspace_id', None)
                if workspace_id:
                    workspace_state = project.get_workspace_state(workspace_id)
                    transform = workspace_state.get_setting("transform_type", "Fourier")
                    window = workspace_state.get_setting("window_type", "Hamming")
                    resolution = workspace_state.get_setting("resolution", 1024)
                    
                    # We could log this or use it in the batch command
                    print(f"Analyzing with: {transform}, {window}, {resolution}")
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing advanced analysis: {e}")
    
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
                    
                    # Update transform selection
                    transform = workspace_state.get_setting("transform_type")
                    if transform and self.get_control("transform"):
                        self.get_control("transform").setCurrentText(transform)
                        
                    # Update window selection
                    window = workspace_state.get_setting("window_type")
                    if window and self.get_control("window"):
                        self.get_control("window").setCurrentText(window)
                        
                    # Update resolution
                    resolution = workspace_state.get_setting("resolution")
                    if resolution is not None and self.get_control("resolution"):
                        self.get_control("resolution").setValue(resolution)
                        
                    # Also update enabled state based on transform type
                    if transform:
                        is_window_applicable = transform in ["Fourier", "Wavelet"]
                        self.get_control("window").setEnabled(is_window_applicable)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")