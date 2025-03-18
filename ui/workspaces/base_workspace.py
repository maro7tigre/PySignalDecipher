"""
Base workspace implementation for PySignalDecipher.

This module provides the base workspace class that integrates with the command system.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMenu, QMainWindow
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from command_system.command_manager import CommandManager
from command_system.command import CommandContext
from command_system.ui_integration import CommandConnector, CommandAction

from ui.theme.theme_manager import ThemeManager
from ui.layout_manager import LayoutManager
from ui.docking.dock_manager import DockManager
from utils.preferences_manager import PreferencesManager


class BaseWorkspace(QWidget):
    """
    Base class for all workspace tabs.
    
    Provides common functionality for workspaces such as layout management,
    state persistence, and integration with the command system.
    """
    
    # Signal emitted when the workspace state changes
    state_changed = Signal()
    
    def __init__(self, command_manager=None, parent=None):
        """
        Initialize the base workspace.
        
        Args:
            command_manager: CommandManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Command system integration
        self._command_manager = command_manager or CommandManager.instance()
        self._context = CommandContext(self._command_manager)
        self._context.active_workspace = self.get_workspace_id()
        
        # Get services from command manager
        self._theme_manager = self._get_service(ThemeManager)
        self._preferences_manager = self._get_service(PreferencesManager)
        self._layout_manager = self._get_service(LayoutManager)
        self._dock_manager = self._get_service(DockManager)
        
        # Set up the main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setLayout(self._main_layout)
        
        # Create an internal QMainWindow to support dock widgets
        self._main_window = QMainWindow()
        self._main_window.setContextMenuPolicy(Qt.CustomContextMenu)
        self._main_window.customContextMenuRequested.connect(self._show_context_menu)
        self._main_layout.addWidget(self._main_window)
        
        # Set a central widget for the main window
        self._central_widget = QWidget()
        self._main_window.setCentralWidget(self._central_widget)
        self._central_layout = QVBoxLayout(self._central_widget)
        self._central_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize the workspace
        self._initialize_workspace()
        
        # Connect to command manager signals
        self._command_manager.command_executed.connect(self._on_command_executed)
        self._command_manager.command_undone.connect(self._on_command_undone)
        self._command_manager.command_redone.connect(self._on_command_redone)
    
    def _get_service(self, service_type):
        """
        Get a service from the command manager.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            The service instance or None if not available
        """
        if not self._command_manager:
            return None
            
        try:
            return self._command_manager.get_service(service_type)
        except Exception as e:
            print(f"Error getting service {service_type.__name__}: {e}")
            return None
    
    def _initialize_workspace(self):
        """
        Initialize the workspace components.
        
        To be overridden by subclasses.
        """
        pass
        
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to this workspace.
        
        Args:
            theme_manager: Optional reference to theme manager
        """
        # Store reference if provided
        if theme_manager:
            self._theme_manager = theme_manager
            
        # Apply theme to all child widgets that support it
        for child in self.findChildren(QWidget):
            if hasattr(child, 'apply_theme') and callable(child.apply_theme):
                child.apply_theme(self._theme_manager)
                
    def get_main_window(self):
        """
        Get the internal QMainWindow for dock widgets.
        
        Returns:
            The internal QMainWindow instance
        """
        return self._main_window
        
    def _show_context_menu(self, pos):
        """
        Show context menu for the workspace.
        
        Args:
            pos: Position to show the menu
        """
        if not self._dock_manager:
            return
        
        menu = QMenu(self)
        
        # Add layout submenu
        if self._layout_manager:
            layouts_menu = QMenu("Layouts", menu)
            
            # Get available layouts
            workspace_id = self.get_workspace_id()
            layouts = self._layout_manager.get_layouts_for_workspace(workspace_id)
            
            # Add actions for each layout
            if layouts:
                for layout_id, layout in layouts.items():
                    # Create action using CommandAction instead of QAction
                    from command_system.commands.workspace_commands import ApplyLayoutCommand
                    action = CommandAction(
                        ApplyLayoutCommand,
                        layout.name,
                        layouts_menu,
                        workspace_id=workspace_id,
                        layout_id=layout_id,
                        main_window=self._main_window
                    )
                    layouts_menu.addAction(action)
                    
                layouts_menu.addSeparator()
            
            # Add save layout action
            from command_system.commands.workspace_commands import SaveLayoutCommand
            save_action = CommandAction(
                SaveLayoutCommand,
                "Save Current Layout...",
                layouts_menu,
                workspace_id=workspace_id,
                main_window=self._main_window
            )
            layouts_menu.addAction(save_action)
            
            # Add manage layouts action
            from command_system.commands.workspace_commands import ManageLayoutsCommand
            manage_action = CommandAction(
                ManageLayoutsCommand,
                "Manage Layouts...",
                layouts_menu,
                workspace_id=workspace_id
            )
            layouts_menu.addAction(manage_action)
            
            menu.addMenu(layouts_menu)
            menu.addSeparator()
            
        # Add dock widgets submenu
        widgets_menu = self._dock_manager.create_dock_context_menu(self.get_workspace_id())
        menu.addMenu(widgets_menu)
        
        # Show the menu
        menu.exec_(self._main_window.mapToGlobal(pos))
        
    def _on_command_executed(self, command):
        """
        Handle command execution.
        
        Args:
            command: Command that was executed
        """
        # Check if the command is relevant to this workspace
        if hasattr(command, 'context') and command.context:
            if command.context.active_workspace == self.get_workspace_id():
                self._update_ui_state()
                
    def _on_command_undone(self, _):
        """
        Handle command undo.
        
        Args:
            _: Ignored parameter
        """
        # Update UI state
        self._update_ui_state()
        
    def _on_command_redone(self, _):
        """
        Handle command redo.
        
        Args:
            _: Ignored parameter
        """
        # Update UI state
        self._update_ui_state()
        
    def _update_ui_state(self):
        """
        Update UI state based on current application state.
        
        To be overridden by subclasses.
        """
        pass
        
    def _load_workspace_state(self):
        """
        Load workspace state from preferences.
        
        This is called during initialization and when the workspace is activated.
        To be extended by subclasses.
        """
        # Apply the active layout if layout manager is available
        if self._layout_manager and self._main_window:
            workspace_id = self.get_workspace_id()
            layout = self._layout_manager.get_active_layout(workspace_id)
            
            if layout:
                from command_system.commands.workspace_commands import ApplyLayoutCommand
                cmd = ApplyLayoutCommand(
                    self._context,
                    workspace_id=workspace_id,
                    layout_id=layout.id,
                    main_window=self._main_window
                )
                self._command_manager.execute_command(cmd)
        
    def _save_workspace_state(self):
        """
        Save workspace state to preferences.
        
        This is called when the workspace is deactivated or the application is closed.
        To be extended by subclasses.
        """
        pass
        
    def get_workspace_id(self):
        """
        Get the unique identifier for this workspace.
        
        To be overridden by subclasses.
        
        Returns:
            str: Unique ID for this workspace
        """
        return "base"