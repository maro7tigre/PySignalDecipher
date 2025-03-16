"""
Widget utility manager for PySignalDecipher.

This module provides a manager for widget-specific utilities
that dynamically changes based on the selected widget.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot

from core.service_registry import ServiceRegistry


class WidgetUtilityManager(QWidget):
    """
    Manager for widget-specific utilities.
    
    Dynamically changes the displayed utilities based on the currently selected widget.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the widget utility manager.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get theme manager from registry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        
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
        
    def register_widget_utility(self, widget_type, utility_widget):
        """
        Register a utility panel for a specific widget type.
        
        Args:
            widget_type: Type identifier for the widget
            utility_widget: Utility panel widget for this type
        """
        self._widget_utilities[widget_type] = utility_widget
        self._stacked_widget.addWidget(utility_widget)
        
    def set_selected_widget(self, widget_type, widget):
        """
        Update the displayed utilities based on the selected widget.
        
        Args:
            widget_type: Type of the selected widget
            widget: Reference to the selected widget
        """
        self._selected_widget = widget
        self._selected_widget_type = widget_type
        
        if widget_type in self._widget_utilities:
            utility = self._widget_utilities[widget_type]
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
        
        # Apply theme to all widget utilities
        for utility in self._widget_utilities.values():
            if hasattr(utility, 'apply_theme') and callable(utility.apply_theme):
                utility.apply_theme(self._theme_manager)