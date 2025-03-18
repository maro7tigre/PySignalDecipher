"""
Pattern workspace utility for PySignalDecipher with simplified implementation.

This module provides a minimal implementation of utilities for the Pattern Recognition workspace
that integrates with the command system.
"""

from .base_workspace_utility import BaseWorkspaceUtility
from command_system.observable import PropertyChangeCommand


class PatternWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Pattern Recognition workspace.
    
    Provides minimal example controls that integrate with the command system.
    """
    
    def __init__(self, theme_manager=None, parent=None):
        """
        Initialize the pattern workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
    
    def register_controls(self):
        """Register example controls for the pattern workspace utility."""
        # Pattern matching algorithm selection
        self.add_combo_box(
            id="algorithm",
            label="Algorithm:",
            items=["Correlation", "Template", "Neural Network"],
            callback=self._on_algorithm_changed
        )
        
        # Threshold setting
        self.add_spin_box(
            id="threshold",
            label="Threshold %:",
            minimum=50,
            maximum=100,
            value=75,
            callback=self._on_threshold_changed
        )
        
        # Normalization option
        self.add_check_box(
            id="normalize",
            text="Normalize Signals",
            checked=True,
            callback=self._on_normalize_changed
        )
        
        # Detect button
        self.add_button(
            id="detect",
            text="Detect Patterns",
            callback=self._on_detect_clicked
        )
    
    def _on_algorithm_changed(self, algorithm):
        """
        Handle algorithm selection changes with command system integration.
        
        Args:
            algorithm: The selected algorithm
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
                    
                    # Create a command to change the algorithm setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="algorithm", 
                                                        value=algorithm)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing algorithm: {e}")
    
    def _on_threshold_changed(self, threshold):
        """
        Handle threshold changes with command system integration.
        
        Args:
            threshold: The new threshold value
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
                    
                    # Create a command to change the threshold setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="threshold", 
                                                        value=threshold)
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing threshold: {e}")
    
    def _on_normalize_changed(self, state):
        """
        Handle normalize checkbox changes with command system integration.
        
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
                    
                    # Create a command to change the normalize setting
                    from command_system.commands.workspace_commands import SetWorkspaceSettingCommand
                    command = SetWorkspaceSettingCommand(workspace_state=workspace_state, 
                                                        key="normalize", 
                                                        value=bool(state))
                    self._command_manager.execute_command(command)
        except Exception as e:
            print(f"Error changing normalize setting: {e}")
    
    def _on_detect_clicked(self):
        """Handle detect button click with command system integration."""
        if not self._workspace or not self._command_manager:
            return
            
        try:
            # Get the project
            project = self._command_manager.get_active_project()
            if project:
                # Create a batch command for pattern detection
                from command_system.commands.project_commands import BatchCommand
                batch_command = BatchCommand(project, "Pattern Detection")
                
                # Execute the batch command
                self._command_manager.execute_command(batch_command)
        except Exception as e:
            print(f"Error performing pattern detection: {e}")
    
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
                    
                    # Update algorithm selection
                    algorithm = workspace_state.get_setting("algorithm")
                    if algorithm and self.get_control("algorithm"):
                        self.get_control("algorithm").setCurrentText(algorithm)
                        
                    # Update threshold
                    threshold = workspace_state.get_setting("threshold")
                    if threshold is not None and self.get_control("threshold"):
                        self.get_control("threshold").setValue(threshold)
                        
                    # Update normalize checkbox
                    normalize = workspace_state.get_setting("normalize")
                    if normalize is not None and self.get_control("normalize"):
                        self.get_control("normalize").setChecked(normalize)
        except Exception as e:
            print(f"Error updating workspace controls: {e}")