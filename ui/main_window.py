"""
Main application window for PySignalDecipher.

This module provides the main window implementation that integrates with the command system.
"""

from PySide6.QtWidgets import QMainWindow, QApplication, QStatusBar, QWidget, QVBoxLayout
from PySide6.QtCore import QSize, Qt

from command_system.command_manager import CommandManager
from command_system.project import Project
from command_system.command import CommandContext
from command_system.ui_integration import CommandButton, CommandAction
from utils.preferences_manager import PreferencesManager
from core.hardware.device_manager import DeviceManager
from .layout_manager import LayoutManager
from .docking.dock_manager  import DockManager

from ui.theme.theme_manager import ThemeManager
from ui.menus import MenuManager, MenuActionHandler
from ui.themed_widgets import ThemedTab
from ui.utility_panel import UtilityPanel
from ui.workspaces import (
    BasicSignalWorkspace,
    ProtocolDecoderWorkspace,
    PatternRecognitionWorkspace,
    SignalSeparationWorkspace,
    SignalOriginWorkspace,
    AdvancedAnalysisWorkspace
)


class MainWindow(QMainWindow):
    """
    Main application window with support for theme and preferences.
    
    Handles window state restoration, theme application, and menu system.
    Integrates with the command system for all state changes.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get command manager
        self._command_manager = CommandManager.instance()
        
        # Create command context
        self._context = CommandContext(self._command_manager)
        
        # Get managers from command manager
        self._theme_manager = self._command_manager.get_service(ThemeManager)
        self._preferences_manager = self._command_manager.get_service(PreferencesManager)
        self._device_manager = self._command_manager.get_service(DeviceManager)
        self._layout_manager = self._command_manager.get_service(LayoutManager)
        self._dock_manager = self._command_manager.get_service(DockManager)
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher")
        self.setMinimumSize(QSize(800, 600))
        
        # Set up the menu system
        self._setup_menus()
        
        # Set up the UI
        self._setup_ui()
        
        # Restore window state
        self._restore_window_state()
        
        # Connect command manager signals
        self._command_manager.command_executed.connect(self._on_command_executed)
        self._command_manager.command_undone.connect(self._on_command_undone)
        self._command_manager.command_redone.connect(self._on_command_redone)
        
    def _setup_menus(self):
        """Set up the application menu system."""
        # Create menu manager
        self._menu_manager = MenuManager(self, self._theme_manager, self._preferences_manager)
        
        # Create menu action handler
        self._menu_action_handler = MenuActionHandler(self, self._theme_manager, self._preferences_manager)
        
        # Connect menu actions to handler
        self._menu_manager.action_triggered.connect(self._menu_action_handler.handle_action)
        
        # Set the menu bar
        self.setMenuBar(self._menu_manager.menu_bar)
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Create status bar
        self.setStatusBar(QStatusBar(self))
        
        # Create a central container widget
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        
        # Create layout for central widget
        self._main_layout = QVBoxLayout(self._central_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # Set up utility panel (above tabs)
        self._setup_utility_panel()
        
        # Create tab widget for workspaces (below utility panel)
        self._tab_widget = ThemedTab(self)
        self._main_layout.addWidget(self._tab_widget, 1)  # Add with stretch to fill available space
        
        # Set up workspace tabs
        self._setup_workspaces()
        
        # Set up utility panel with initial workspace
        initial_workspace_index = self._preferences_manager.get_preference("ui/active_workspace_tab", 0)
        if 0 <= initial_workspace_index < self._tab_widget.count():
            workspace = self._tab_widget.widget(initial_workspace_index)
            if hasattr(workspace, 'get_workspace_id'):
                workspace_id = workspace.get_workspace_id()
                self._utility_panel.set_active_workspace(workspace_id, workspace)
        
        # Apply theme to tab widget
        self._tab_widget.set_theme(self._theme_manager)
        
    def _setup_utility_panel(self):
        """Set up the utility panel above the tabs."""
        self._utility_panel = UtilityPanel(self)
        
        # Provide command manager to utility panel
        self._utility_panel.set_command_manager(self._command_manager)
        
        # Provide preferences manager to utility panel for height persistence
        self._utility_panel.set_preferences_manager(self._preferences_manager)
        
        # Add utility panel to the main layout (at the top)
        self._main_layout.addWidget(self._utility_panel)
        
    def _setup_workspaces(self):
        """Set up workspace tabs."""
        # Create and add each workspace
        self._basic_workspace = BasicSignalWorkspace(self._command_manager, self)
        self._protocol_workspace = ProtocolDecoderWorkspace(self._command_manager, self)
        self._pattern_workspace = PatternRecognitionWorkspace(self._command_manager, self)
        self._separation_workspace = SignalSeparationWorkspace(self._command_manager, self)
        self._origin_workspace = SignalOriginWorkspace(self._command_manager, self)
        self._advanced_workspace = AdvancedAnalysisWorkspace(self._command_manager, self)
        
        # Apply theme to workspaces
        for workspace in [
            self._basic_workspace,
            self._protocol_workspace,
            self._pattern_workspace,
            self._separation_workspace,
            self._origin_workspace,
            self._advanced_workspace
        ]:
            workspace.apply_theme(self._theme_manager)
        
        # Add workspaces to tab widget
        self._tab_widget.addTab(self._basic_workspace, "Basic Signal Analysis")
        self._tab_widget.addTab(self._protocol_workspace, "Protocol Decoder")
        self._tab_widget.addTab(self._pattern_workspace, "Pattern Recognition")
        self._tab_widget.addTab(self._separation_workspace, "Signal Separation")
        self._tab_widget.addTab(self._origin_workspace, "Signal Origin")
        self._tab_widget.addTab(self._advanced_workspace, "Advanced Analysis")
        
        # Connect tab changed signal
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # After all workspaces are set up, set the main window for dock manager
        # This directs dock operations to the current active workspace
        current_workspace = self._tab_widget.currentWidget()
        if hasattr(current_workspace, 'get_main_window'):
            self._dock_manager.set_main_window(current_workspace.get_main_window())
        
    def _on_tab_changed(self, index):
        """
        Handle tab change event.
        
        Args:
            index: Index of the new active tab
        """
        # Update the active workspace in the context
        workspace_id = None
        workspace = None
        
        if 0 <= index < self._tab_widget.count():
            workspace = self._tab_widget.widget(index)
            if hasattr(workspace, 'get_workspace_id'):
                workspace_id = workspace.get_workspace_id()
                
                # Update the command context with active workspace
                self._context.active_workspace = workspace_id
                
        # Update workspace menu if we have a valid workspace ID
        if workspace_id and hasattr(self._menu_manager, '_workspace_menu'):
            self._menu_manager._workspace_menu.update_active_workspace(workspace_id)
            
        # Update utility panel with the active workspace
        if workspace_id:
            self._utility_panel.set_active_workspace(workspace_id, workspace)
            
        # Update dock manager with the new workspace's main window
        if workspace and hasattr(workspace, 'get_main_window'):
            self._dock_manager.set_main_window(workspace.get_main_window())
            
        # Save the active tab preference
        self._preferences_manager.set_preference("ui/active_workspace_tab", index)
    
    def _restore_window_state(self):
        """Restore window state from preferences."""
        self._preferences_manager.restore_window_state(self)
        
        # Restore active tab
        active_tab = self._preferences_manager.get_preference("ui/active_workspace_tab", 0)
        if isinstance(active_tab, int) and 0 <= active_tab < self._tab_widget.count():
            self._tab_widget.setCurrentIndex(active_tab)
            
    def _on_command_executed(self, command):
        """
        Handle command execution event.
        
        Args:
            command: Command that was executed
        """
        # Update UI state based on command
        self._update_ui_state()
        
    def _on_command_undone(self, _):
        """
        Handle command undo event.
        
        Args:
            _: Ignored parameter
        """
        # Update UI state after undo
        self._update_ui_state()
        
    def _on_command_redone(self, _):
        """
        Handle command redo event.
        
        Args:
            _: Ignored parameter
        """
        # Update UI state after redo
        self._update_ui_state()
        
    def _update_ui_state(self):
        """Update UI state based on current application state."""
        # Update window title with project name
        project = self._command_manager.get_active_project()
        if project:
            self.setWindowTitle(f"PySignalDecipher - {project.name}")
            
        # Update undo/redo actions
        if hasattr(self._menu_manager, 'get_action'):
            undo_action = self._menu_manager.get_action("edit.undo")
            if undo_action:
                undo_action.setEnabled(self._command_manager.can_undo())
                
            redo_action = self._menu_manager.get_action("edit.redo")
            if redo_action:
                redo_action.setEnabled(self._command_manager.can_redo())
        
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Save window state
        self._preferences_manager.save_window_state(self)
        
        # Accept the event to close the window
        event.accept()