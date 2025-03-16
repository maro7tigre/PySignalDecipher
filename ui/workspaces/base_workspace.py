from PySide6.QtWidgets import QWidget, QVBoxLayout, QMenu, QMainWindow
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from ..themed_widgets.base_themed_widget import BaseThemedWidget
from core.service_registry import ServiceRegistry


class BaseWorkspace(BaseThemedWidget):
    """
    Base class for all workspace tabs.
    
    Provides common functionality for workspaces such as layout management,
    state persistence, and interaction with the main application.
    """
    
    # Signal emitted when the workspace state changes
    state_changed = Signal()
    
    def __init__(self, parent=None):
        """
        Initialize the base workspace.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
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
        
        # References to managers (set by appropriate methods)
        self._preferences_manager = None
        self._layout_manager = None
        self._dock_manager = None
        
        # Initialize the workspace
        self._initialize_workspace()
        
    def _initialize_workspace(self):
        """
        Initialize the workspace components.
        
        To be overridden by subclasses.
        """
        pass
        
    def _apply_theme_impl(self):
        """
        Apply the current theme to this workspace.
        
        Implementation of the method from BaseThemedWidget.
        """
        # Apply theme to all child widgets that support it
        for child in self.findChildren(BaseThemedWidget):
            if hasattr(child, 'apply_theme') and callable(child.apply_theme):
                child.apply_theme(self._theme_manager)
                
    def set_preferences_manager(self, preferences_manager):
        """
        Set the preferences manager.
        
        Args:
            preferences_manager: Reference to the PreferencesManager
        """
        self._preferences_manager = preferences_manager
        
        # Load workspace state
        self._load_workspace_state()
        
    def set_layout_manager(self, layout_manager):
        """
        Set the layout manager.
        
        Args:
            layout_manager: Reference to the LayoutManager
        """
        self._layout_manager = layout_manager
        
    def set_dock_manager(self, dock_manager):
        """
        Set the dock manager.
        
        Args:
            dock_manager: Reference to the DockManager
        """
        self._dock_manager = dock_manager
        
        # Set main window for dock manager (if not already set)
        if self._dock_manager and self._main_window:
            self._dock_manager.set_main_window(self._main_window)
            
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
                    action = QAction(layout.name, layouts_menu)
                    action.triggered.connect(
                        lambda checked=False, lid=layout_id: 
                        self._layout_manager.apply_layout(workspace_id, lid, self._main_window)
                    )
                    layouts_menu.addAction(action)
                    
                layouts_menu.addSeparator()
            
            # Add save layout action
            save_action = QAction("Save Current Layout...", layouts_menu)
            save_action.triggered.connect(self._save_current_layout)
            layouts_menu.addAction(save_action)
            
            # Add manage layouts action
            manage_action = QAction("Manage Layouts...", layouts_menu)
            manage_action.triggered.connect(self._manage_layouts)
            layouts_menu.addAction(manage_action)
            
            menu.addMenu(layouts_menu)
            menu.addSeparator()
            
        # Add dock widgets submenu
        widgets_menu = self._dock_manager.create_dock_context_menu(self.get_workspace_id())
        menu.addMenu(widgets_menu)
        
        # Show the menu
        menu.exec_(self._main_window.mapToGlobal(pos))
        
    def _save_current_layout(self):
        """Save the current layout."""
        if not self._layout_manager:
            return
            
        # Show dialog to get layout name
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, 
            "Save Layout", 
            "Enter a name for this layout:"
        )
        
        if ok and name:
            # Create a new layout
            self._layout_manager.create_layout(
                self.get_workspace_id(),
                name,
                self._main_window
            )
            
    def _manage_layouts(self):
        """Manage layouts for this workspace."""
        if not self._layout_manager:
            return
            
        # Show layout manager dialog
        from ui.layout_manager import LayoutManagerDialog
        dialog = LayoutManagerDialog(
            self,
            self._layout_manager,
            self.get_workspace_id()
        )
        dialog.exec_()
        
    def _load_workspace_state(self):
        """
        Load workspace state from preferences.
        
        To be overridden by subclasses.
        """
        # Apply the active layout if layout manager is available
        if self._layout_manager and self._main_window:
            workspace_id = self.get_workspace_id()
            layout = self._layout_manager.get_active_layout(workspace_id)
            
            if layout:
                self._layout_manager.apply_layout(
                    workspace_id,
                    layout.id,
                    self._main_window
                )
        
    def _save_workspace_state(self):
        """
        Save workspace state to preferences.
        
        To be overridden by subclasses.
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