"""
Origin workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Signal Origin workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class OriginWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Signal Origin workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the origin workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the origin workspace utility."""
        # Localization method selection
        self.add_combo_box(
            id="method",
            label="Method:",
            items=["Direction Finding", "Triangulation", "TDOA"],
            callback=self._on_method_changed
        )
        
        # Frequency setting
        self.add_double_spin_box(
            id="frequency",
            label="Frequency:",
            minimum=1.0,
            maximum=6000.0,
            value=433.92,
            decimals=2,
            suffix=" MHz",
            callback=self._on_frequency_changed
        )
        
        # Continuous monitoring option
        self.add_check_box(
            id="continuous",
            text="Continuous Monitoring",
            checked=False,
            callback=self._on_continuous_changed
        )
        
        # Locate button
        self.add_button(
            id="locate",
            text="Locate Signal",
            callback=self._on_locate_clicked
        )
    
    def _on_method_changed(self, method):
        """
        Handle method selection changes with command system integration.
        
        Args:
            method: The selected localization method
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
                                                        key="location_method", 
                                                        value=method)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing localization method: {e}")
    
    def _on_frequency_changed(self, frequency):
        """
        Handle frequency changes with command system integration.
        
        Args:
            frequency: The new frequency value
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
                    
                    # Create a command to change the frequency setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="frequency", 
                                                        value=frequency)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing frequency: {e}")
    
    def _on_continuous_changed(self, state):
        """
        Handle continuous monitoring checkbox changes with command system integration.
        
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
                    
                    # Create a command to change the continuous monitoring setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="continuous_monitoring", 
                                                        value=bool(state))
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing continuous monitoring setting: {e}")
    
    def _on_locate_clicked(self):
        """Handle locate button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for signal localization
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Signal Localization")
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing signal localization: {e}")
    
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
                    method = workspace_state.get_setting("location_method")
                    if method and self.get_control("method"):
                        self.get_control("method").setCurrentText(method)
                        
                    # Update frequency
                    frequency = workspace_state.get_setting("frequency")
                    if frequency is not None and self.get_control("frequency"):
                        self.get_control("frequency").setValue(frequency)
                        
                    # Update continuous monitoring checkbox
                    continuous = workspace_state.get_setting("continuous_monitoring")
                    if continuous is not None and self.get_control("continuous"):
                        self.get_control("continuous").setChecked(continuous)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")