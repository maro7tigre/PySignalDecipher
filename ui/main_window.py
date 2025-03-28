from PySide6.QtWidgets import QMainWindow, QApplication, QStatusBar, QWidget, QVBoxLayout
from PySide6.QtCore import QSize, Qt

from core.service_registry import ServiceRegistry
from .theme import ThemeManager
from .menus import MenuManager, MenuActionHandler
from .themed_widgets import ThemedTab
from .utility_panel import UtilityPanel
from .workspaces import (
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
    """
    
    def __init__(self, parent=None):
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get managers from registry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._preferences_manager = ServiceRegistry.get_preferences_manager()
        self._device_manager = ServiceRegistry.get_device_manager()
        self._layout_manager = ServiceRegistry.get_layout_manager()
        self._dock_manager = ServiceRegistry.get_dock_manager()
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher")
        self.setMinimumSize(QSize(800, 600))
        
        # Set up the menu system
        self._setup_menus()
        
        # Set up the UI
        self._setup_ui()
        
        # Restore window state
        self._restore_window_state()
        
        # Apply the current theme
        self._theme_manager.apply_theme()
        
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
        
        # Provide preferences manager to utility panel for height persistence
        self._utility_panel.set_preferences_manager(self._preferences_manager)
        
        # Add utility panel to the main layout (at the top)
        self._main_layout.addWidget(self._utility_panel)
        
    def _setup_workspaces(self):
        """Set up workspace tabs."""
        # Create and add each workspace
        self._basic_workspace = BasicSignalWorkspace(self)
        self._protocol_workspace = ProtocolDecoderWorkspace(self)
        self._pattern_workspace = PatternRecognitionWorkspace(self)
        self._separation_workspace = SignalSeparationWorkspace(self)
        self._origin_workspace = SignalOriginWorkspace(self)
        self._advanced_workspace = AdvancedAnalysisWorkspace(self)
        
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
            workspace.set_preferences_manager(self._preferences_manager)
            workspace.set_layout_manager(self._layout_manager)
            workspace.set_dock_manager(self._dock_manager)
        
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
        # Update the active workspace in the menu
        workspace_id = None
        workspace = None
        
        if 0 <= index < self._tab_widget.count():
            workspace = self._tab_widget.widget(index)
            if hasattr(workspace, 'get_workspace_id'):
                workspace_id = workspace.get_workspace_id()
                
        # Update workspace menu if we have a valid workspace ID
        if workspace_id and hasattr(self._menu_manager, '_workspace_menu'):
            self._menu_manager._workspace_menu.update_active_workspace(workspace_id)
            
        # Update utility panel with the active workspace
        if workspace_id:
            self._utility_panel.set_active_workspace(workspace_id, workspace)
            
        # Update dock manager with the new workspace's main window
        if workspace and hasattr(workspace, 'get_main_window'):
            self._dock_manager.set_main_window(workspace.get_main_window())
        
    def _restore_window_state(self):
        """Restore window state from preferences."""
        self._preferences_manager.restore_window_state(self)
        
        # Restore active tab
        active_tab = self._preferences_manager.get_preference("ui/active_workspace_tab", 0)
        if isinstance(active_tab, int) and 0 <= active_tab < self._tab_widget.count():
            self._tab_widget.setCurrentIndex(active_tab)
        
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Save active tab
        self._preferences_manager.set_preference("ui/active_workspace_tab", self._tab_widget.currentIndex())
        
        # Save window state
        self._preferences_manager.save_window_state(self)
        
        # Accept the event to close the window
        event.accept()