"""
command_system/ui/widgets/line_edit.py
Command-aware QLineEdit
"""

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal, Slot
from .base import CommandWidgetBase


class CommandLineEdit(QLineEdit, CommandWidgetBase[str]):
    """
    Command-aware line edit that automatically integrates with the command system.
    
    Example:
        # Create edit and connect to model
        edit = CommandLineEdit()
        edit.bind_to_model(my_model, "text_property")
        
        # Use like a normal QLineEdit
        layout.addWidget(edit)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command line edit."""
        QLineEdit.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("text")
        
        # Connect editing signals
        self.editingFinished.connect(self._end_edit)
        self.textEdited.connect(self._on_text_edited)
        
        # Store initial state
        self._old_value = self.text()
        self._text_changed = False
        
    def _on_text_edited(self, text):
        """Called when text is being edited."""
        if not self._text_changed:
            # First edit, store initial value
            self._begin_edit()
            self._text_changed = True
        
        # Create a command immediately for each text change
        # This ensures even single-character changes are captured
        if self._command_enabled and self._observable_model and self._observable_property:
            self._on_widget_value_changed()
            # Update old value to current value for next change
            self._old_value = self.text()
            
    @Slot()
    def _end_edit(self):
        """Called when editing is finished."""
        self._text_changed = False
            
    def _get_widget_value(self) -> str:
        """Get the widget's current text."""
        return self.text()
        
    def _set_widget_value(self, value: str):
        """Set the widget's text."""
        self.setText(str(value) if value is not None else "")