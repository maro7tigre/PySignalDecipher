"""
Widget utility manager for PySignalDecipher with command system integration.

This module provides a manager for widget-specific utilities
that dynamically changes based on the selected widget.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot

from command_system.command_manager import CommandManager
from command_system.command import CommandContext


class WidgetUtilityManager(QWidget):
    """
    Manager for widget-specific utilities.
    
    Dynamically changes the displayed utilities based on the currently selected widget.
    Integrated with the command system.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the widget utility manager.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Command system integration
        self._command_manager = None
        self._command_context = None
        
        # Theme manager will be set by command manager
        self._theme_manager = None
        
        # Dictionary to map widget types to utility panels
        self._widget_utilities = {}
        
        # Currently selected widget
        self._selected_widget = None
        self._selected_widget_type = None
        
        # Set up the manager UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the widget utility manager."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a stacked widget to switch between widget utilities
        self._stacked_widget = QStackedWidget()
        
        # Create a default widget for when no widget is selected
        self._default_widget = QWidget()
        default_layout = QVBoxLayout(self._default_widget)
        default_label = QLabel("No element selected")
        default_label.setAlignment(Qt.AlignCenter)
        default_layout.addWidget(default_label)
        
        # Add the default widget to the stacked widget
        self._stacked_widget.addWidget(self._default_widget)
        
        # Add the stacked widget to the main layout
        self._main_layout.addWidget(self._stacked_widget)
        
    def set_command_manager(self, command_manager):
        """
        Set the command manager for this utility manager.
        
        Args:
            command_manager: Reference to the CommandManager
        """
        self._command_manager = command_manager
        
        # Create command context
        self._command_context = CommandContext(command_manager)
        
        # Get theme manager from command manager
        try:
            # Try service-based approach first
            from ui.theme.theme_manager import ThemeManager
            self._theme_manager = command_manager.get_service(ThemeManager)
        except (AttributeError, KeyError, ImportError):
            # Fall back to legacy getter
            if hasattr(command_manager, 'get_theme_manager'):
                self._theme_manager = command_manager.get_theme_manager()
        
        # Initialize utilities with available theme manager
        if self._theme_manager:
            self._initialize_widget_utilities()
            self.apply_theme(self._theme_manager)
    
    def _initialize_widget_utilities(self):
        """Initialize widget utilities as needed."""
        # This would create utility panels for different widget types
        # For example:
        #
        # from .widget_utilities.signal_viewer_utility import SignalViewerUtility
        # from .widget_utilities.plot_utility import PlotUtility
        #
        # self._widget_utilities["signal_viewer"] = SignalViewerUtility(self._theme_manager)
        # self._widget_utilities["plot"] = PlotUtility(self._theme_manager)
        #
        # for utility in self._widget_utilities.values():
        #     self._stacked_widget.addWidget(utility)
        #     if hasattr(utility, 'set_command_manager'):
        #         utility.set_command_manager(self._command_manager)
        
        # The actual implementation will depend on what widget utility classes exist
        pass
        
    def register_widget_utility(self, widget_type, utility_widget):
        """
        Register a utility panel for a specific widget type.
        
        Args:
            widget_type: Type identifier for the widget
            utility_widget: Utility panel widget for this type
        """
        self._widget_utilities[widget_type] = utility_widget
        self._stacked_widget.addWidget(utility_widget)
        
        # Pass command manager to the utility if it supports it
        if hasattr(utility_widget, 'set_command_manager') and callable(getattr(utility_widget, 'set_command_manager')):
            utility_widget.set_command_manager(self._command_manager)
        
    def set_selected_widget(self, widget_type, widget):
        """
        Update the displayed utilities based on the selected widget.
        
        Args:
            widget_type: Type of the selected widget
            widget: Reference to the selected widget
        """
        self._selected_widget = widget
        self._selected_widget_type = widget_type
        
        # Update command context with selected widget
        if self._command_context:
            self._command_context.add_parameter("selected_widget_type", widget_type)
            self._command_context.add_parameter("selected_widget", widget)
        
        if widget_type in self._widget_utilities:
            utility = self._widget_utilities[widget_type]
            if hasattr(utility, 'set_widget') and callable(getattr(utility, 'set_widget')):
                utility.set_widget(widget)
            self._stacked_widget.setCurrentWidget(utility)
        else:
            # Show the default widget if no specific utility is available
            self._stacked_widget.setCurrentWidget(self._default_widget)
            
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to all widget utilities.
        
        Args:
            theme_manager: Optional theme manager reference (uses registry if None)
        """
        if theme_manager:
            self._theme_manager = theme_manager
        
        # Apply theme to the default widget
        if self._theme_manager:
            bg_color = self._theme_manager.get_color("background.utility", "#F5F5F5")
            text_color = self._theme_manager.get_color("text.secondary", "#505050")
            self._default_widget.setStyleSheet(f"""
                background-color: {bg_color};
                color: {text_color};
            """)
        
        # Apply theme to all widget utilities
        for utility in self._widget_utilities.values():
            if hasattr(utility, 'apply_theme') and callable(utility.apply_theme):
                utility.apply_theme(self._theme_manager)