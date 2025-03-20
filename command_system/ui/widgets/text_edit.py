"""
command_system/ui/widgets/text_edit.py
Command-aware QTextEdit with cursor position preservation
"""

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QTextCursor
from typing import Any
from .base import CommandWidgetBase


class CommandTextEdit(QTextEdit, CommandWidgetBase[str]):
    """
    Command-aware text edit that automatically integrates with the command system.
    
    Example:
        # Create text edit and connect to model
        text_edit = CommandTextEdit()
        text_edit.bind_to_model(my_model, "content_property")
        
        # Use like a normal QTextEdit
        layout.addWidget(text_edit)
    """
    
    # Custom signal to detect focus changes
    focusLost = Signal()
    
    def __init__(self, *args, **kwargs):
        """Initialize command text edit."""
        QTextEdit.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("text")
        
        # Connect signals for real-time updates
        self.textChanged.connect(self._on_content_changed)
        
        # Store initial state
        self._old_value = self.toPlainText()
        self._current_value = self._old_value
        self._is_editing = False
        self._update_timer_id = None
        
    def focusInEvent(self, event):
        """Handle focus in event."""
        QTextEdit.focusInEvent(self, event)
        self._is_editing = True
        self._begin_edit()
        
    def focusOutEvent(self, event):
        """Handle focus out event."""
        QTextEdit.focusOutEvent(self, event)
        self._is_editing = False
        self._end_edit()
        self.focusLost.emit()
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Call parent implementation first
        QTextEdit.keyPressEvent(self, event)
        
        # Start or restart the timer for delayed command creation
        if self._update_timer_id is not None:
            self.killTimer(self._update_timer_id)
        self._update_timer_id = self.startTimer(300)  # 300ms delay
        
    def timerEvent(self, event):
        """Handle timer events."""
        if event.timerId() == self._update_timer_id:
            self.killTimer(self._update_timer_id)
            self._update_timer_id = None
            
            # Get current text
            current_text = self.toPlainText()
            
            # Only create a command if text changed
            if current_text != self._current_value:
                # Save cursor position
                cursor_position = self.textCursor().position()
                
                # Update model via command
                if self._command_enabled and self._observable_model and self._observable_property:
                    self._on_widget_value_changed()
                
                # Update current value for next change
                self._current_value = current_text
                
                # Restore cursor position after command execution
                self._restore_cursor_position(cursor_position)
        
    def _on_content_changed(self):
        """Called when content changes."""
        pass  # We handle changes via the timer instead
        
    def _begin_edit(self):
        """Called when editing begins."""
        self._old_value = self.toPlainText()
        self._current_value = self._old_value
        
    def _end_edit(self):
        """Called when editing is finished."""
        # Final check for changes
        current_text = self.toPlainText()
        if current_text != self._current_value:
            # Save cursor position
            cursor_position = self.textCursor().position()
            
            # Update model via command
            if self._command_enabled and self._observable_model and self._observable_property:
                self._on_widget_value_changed()
                
            # Restore cursor position after command execution
            self._restore_cursor_position(cursor_position)
            
    def _restore_cursor_position(self, position):
        """Restore cursor to the specified position."""
        # Create a cursor and set its position
        cursor = self.textCursor()
        
        # Make sure position is valid for the current text
        text_length = len(self.toPlainText())
        valid_position = min(position, text_length)
        
        # Set the cursor position and update the text cursor
        cursor.setPosition(valid_position)
        self.setTextCursor(cursor)
            
    def _get_widget_value(self) -> str:
        """Get the widget's current text."""
        return self.toPlainText()
        
    def _set_widget_value(self, value: str):
        """Set the widget's text while preserving cursor position when appropriate."""
        current_text = self.toPlainText()
        new_text = str(value) if value is not None else ""
        
        # Only update if the text is different
        if current_text != new_text:
            # If we're updating from the model in response to our own changes,
            # we want to preserve the cursor position
            if self.hasFocus() and self._is_updating:
                # Save the cursor position
                cursor_position = self.textCursor().position()
                
                # Set the new text
                self.setPlainText(new_text)
                
                # Restore cursor position
                self._restore_cursor_position(cursor_position)
            else:
                # We're not editing, so just set the text normally
                self.setPlainText(new_text)
                
    def _on_model_property_changed(self, property_name: str, old_value: Any, new_value: Any):
        """Override the base method to add cursor position preservation."""
        # Save cursor position if we have focus
        cursor_position = None
        if self.hasFocus():
            cursor_position = self.textCursor().position()
            
        # Call the parent implementation
        super()._on_model_property_changed(property_name, old_value, new_value)
        
        # Restore cursor position if we saved it
        if cursor_position is not None:
            self._restore_cursor_position(cursor_position)