"""
Protocol workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Protocol Decoder workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class ProtocolWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Protocol Decoder workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the protocol workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the protocol workspace utility."""
        # Protocol selection dropdown
        self.add_combo_box(
            id="protocol",
            label="Protocol:",
            items=["UART", "SPI", "I2C", "CAN"],
            callback=self._on_protocol_changed
        )
        
        # Protocol parameter
        self.add_spin_box(
            id="baudrate",
            label="Baudrate:",
            minimum=1200,
            maximum=1000000,
            value=9600,
            callback=self._on_baudrate_changed
        )
        
        # Decode button
        self.add_button(
            id="decode",
            text="Decode",
            callback=self._on_decode_clicked
        )
    
    def _on_protocol_changed(self, protocol):
        """
        Handle protocol selection changes with command system integration.
        
        Args:
            protocol: The selected protocol
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
                    
                    # Create a command to change the protocol setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="protocol", 
                                                        value=protocol)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing protocol: {e}")
    
    def _on_baudrate_changed(self, baudrate):
        """
        Handle baudrate changes with command system integration.
        
        Args:
            baudrate: The new baudrate value
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
                    
                    # Create a command to change the baudrate setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="baudrate", 
                                                        value=baudrate)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing baudrate: {e}")
    
    def _on_decode_clicked(self):
        """Handle decode button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for protocol decoding
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Protocol Decoding")
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing protocol decoding: {e}")
    
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
                    
                    # Update protocol selection
                    protocol = workspace_state.get_setting("protocol")
                    if protocol and self.get_control("protocol"):
                        self.get_control("protocol").setCurrentText(protocol)
                        
                    # Update baudrate
                    baudrate = workspace_state.get_setting("baudrate")
                    if baudrate and self.get_control("baudrate"):
                        self.get_control("baudrate").setValue(baudrate)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")