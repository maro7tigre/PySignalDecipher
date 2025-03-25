"""
Command-aware line edit widget.

This module provides a line edit that integrates with the command system,
enabling undo/redo and property binding.
"""
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from .base import CommandWidgetBase, CommandExecutionMode
from ..core.observable import Observable


class CommandLineEdit(QLineEdit, CommandWidgetBase):
    """
    A line edit widget that creates commands when its value changes.
    Supports binding to Observable model properties.
    """
    
    def __init__(self, parent=None, execution_mode=CommandExecutionMode.ON_EDIT_END):
        """
        Initialize the command-aware line edit.
        
        Args:
            parent: Parent widget
            execution_mode: When to execute commands (default: ON_EDIT_END)
        """
        QLineEdit.__init__(self, parent)
        CommandWidgetBase.__init__(self)
        
        # Setup command widget tracking for the text property
        self._setup_command_widget("text")
        
        # Set command execution mode
        self.set_command_execution_mode(execution_mode)
        
        # Connect signals based on execution mode
        if execution_mode == CommandExecutionMode.ON_CHANGE:
            self.textChanged.connect(self._on_widget_value_changed)
        elif execution_mode == CommandExecutionMode.DELAYED:
            self.textChanged.connect(self._on_widget_value_changed)
            self.editingFinished.connect(self._end_edit)
        else:  # ON_EDIT_END
            self.editingFinished.connect(self._end_edit)
        
        # Track if we're in a focused editing state
        self._is_editing = False
        
    def _get_widget_value(self) -> str:
        """
        Get the widget's current value.
        
        Returns:
            Current text value
        """
        return self.text()
        
    def _set_widget_value(self, value: Any) -> None:
        """
        Set the widget's value.
        
        Args:
            value: New text value
        """
        # Handle None values gracefully
        if value is None:
            value = ""
            
        # Try to convert to string
        try:
            text_value = str(value)
        except Exception:
            text_value = ""
            
        # Set the text
        self.setText(text_value)
    
    def focusInEvent(self, event):
        """Handle focus in to track editing state."""
        if not self._is_editing:
            self._is_editing = True
            self._begin_edit()
        QLineEdit.focusInEvent(self, event)
    
    def focusOutEvent(self, event):
        """Handle focus out to finalize edits."""
        if self._is_editing:
            self._is_editing = False
            # _end_edit will be called by the editingFinished signal
        QLineEdit.focusOutEvent(self, event)

    def keyPressEvent(self, event):
        """Handle key press events for special keys."""
        # Handle Escape key to cancel edit
        if event.key() == Qt.Key_Escape:
            # Revert to original value
            if self._is_editing and hasattr(self, '_old_value'):
                self._is_updating = True
                try:
                    self.setText(self._old_value if self._old_value is not None else "")
                finally:
                    self._is_updating = False
            self._is_editing = False
            self.clearFocus()
            event.accept()
        # Handle Enter/Return key to confirm edit and remove focus
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            # End editing immediately rather than waiting for focusOut
            if self._is_editing:
                self._end_edit()
                self._is_editing = False
            self.clearFocus()
            event.accept()
        else:
            # Pass other keys to parent class
            QLineEdit.keyPressEvent(self, event)