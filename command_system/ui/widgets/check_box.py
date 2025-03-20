"""
command_system/ui/widgets/check_box.py
Command-aware QCheckBox
"""

from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Signal, Slot
from .base import CommandWidgetBase


class CommandCheckBox(QCheckBox, CommandWidgetBase[bool]):
    """
    Command-aware check box that automatically integrates with the command system.
    
    Example:
        # Create check box and connect to model
        check = CommandCheckBox("Enable feature")
        check.bind_to_model(my_model, "is_enabled")
        
        # Use like a normal QCheckBox
        layout.addWidget(check)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command check box."""
        QCheckBox.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("checked")
        
        # Connect signals
        self.toggled.connect(self._on_toggled)
        
        # Store initial state
        self._old_value = self.isChecked()
        
    def _on_toggled(self, checked):
        """Called when checked state changes."""
        # Create command immediately for toggle actions
        self._on_widget_value_changed()
        
    def _get_widget_value(self) -> bool:
        """Get the widget's checked state."""
        return self.isChecked()
        
    def _set_widget_value(self, value: bool):
        """Set the widget's checked state."""
        self.setChecked(bool(value))