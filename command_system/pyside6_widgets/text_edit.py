"""
Command-enabled text edit widget for PySide6 integration.

This module provides a text edit widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QTextDocument

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandTextEdit(QTextEdit, BaseCommandWidget):
    """
    A command-system integrated text edit widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    # Custom signal for edit completion
    editingFinished = Signal()
    
    def __init__(self, container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, text: str = ""):
        """
        Initialize a command text edit.
        
        Args:
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            text: Initial text
        """
        # Initialize QTextEdit first
        QTextEdit.__init__(self, text, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.TEXT_EDIT, container_id, location)
        
        # Connect signals for value changes
        self.textChanged.connect(self._handle_text_changed)
        
        # Default to DELAYED trigger mode for text edits
        # This provides a good balance between responsiveness and avoiding
        # excessive command generation during rapid typing
        self.set_command_trigger_mode(CommandTriggerMode.DELAYED, 500)  # 500ms delay
        
        # Editing completion timer
        self._editing_timer = QTimer(self)
        self._editing_timer.setSingleShot(True)
        self._editing_timer.timeout.connect(self._on_editing_timeout)
        self._editing_timeout_ms = 1000  # 1 second of inactivity signals editing finished
        
        # Focus handling for editing completion
        self._had_focus = False
    
    # MARK: - Property Implementation
    def _update_widget_property(self, property_name: str, value: Any):
        """
        Update a widget property value.
        
        Args:
            property_name: Name of the property to update
            value: New value for the property
        """
        # Block signals to prevent recursion
        self.blockSignals(True)
        
        if property_name == "plainText":
            self.setPlainText(str(value) if value is not None else "")
        elif property_name == "html":
            self.setHtml(str(value) if value is not None else "")
        elif property_name == "enabled":
            self.setEnabled(bool(value))
        elif property_name == "readOnly":
            self.setReadOnly(bool(value))
        else:
            self.blockSignals(False)
            raise ValueError(f"Unsupported property: {property_name}")
        
        # Re-enable signals
        self.blockSignals(False)
    
    # MARK: - Signal Handlers
    @Slot()
    def _handle_text_changed(self):
        """Handle text changes from the widget."""
        # Restart the editing timeout timer
        self._editing_timer.start(self._editing_timeout_ms)
        
        # Get current text
        plain_text = self.toPlainText()
        html_text = self.toHtml()
        
        # Delegate to base class - update both formats
        self._on_widget_value_changed("plainText", plain_text)
        self._on_widget_value_changed("html", html_text)
    
    def _on_editing_timeout(self):
        """Handle editing timeout - signals that editing is finished."""
        self.editingFinished.emit()
        self._on_widget_editing_finished()
    
    # MARK: - Focus Events
    def focusInEvent(self, event):
        """Handle focus in event to track editing state."""
        self._had_focus = True
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """Handle focus out event to signal editing completed."""
        if self._had_focus:
            self._had_focus = False
            # Stop any pending timer
            if self._editing_timer.isActive():
                self._editing_timer.stop()
            # Signal editing finished
            self.editingFinished.emit()
            self._on_widget_editing_finished()
        super().focusOutEvent(event)
    
    # MARK: - Convenience Methods
    def bind_to_plain_text_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind plainText property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("plainText", observable_id, property_name)
    
    def unbind_plain_text_property(self):
        """Convenience method to unbind plainText property."""
        self.unbind_property("plainText")
    
    def bind_to_html_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind html property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("html", observable_id, property_name)
    
    def unbind_html_property(self):
        """Convenience method to unbind html property."""
        self.unbind_property("html")
    
    def bind_to_read_only_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind readOnly property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("readOnly", observable_id, property_name)
    
    def unbind_read_only_property(self):
        """Convenience method to unbind readOnly property."""
        self.unbind_property("readOnly")
    
    # MARK: - Helper methods for enum conversion
    def _get_line_wrap_mode_value(self):
        """
        Get the integer value of the current line wrap mode.
        
        Returns:
            int: 0 for NoWrap, 1 for WidgetWidth
        """
        mode = self.lineWrapMode()
        if mode == QTextEdit.LineWrapMode.NoWrap:
            return 0
        elif mode == QTextEdit.LineWrapMode.WidgetWidth:
            return 1
        else:
            return 0  # Default to NoWrap
    
    def _get_text_interaction_flags_value(self):
        """
        Get the integer value of the current text interaction flags.
        
        Returns:
            int: Integer representation of the flags
        """
        flags = self.textInteractionFlags()
        
        # Instead of trying to directly convert the flags to int,
        # we'll create a numeric value based on individual flag checks
        value = 0
        
        # Map each flag to a bit position (these need to match Qt's values)
        # These values are from Qt documentation
        if flags & Qt.TextInteractionFlag.NoTextInteraction:
            value |= 0
        if flags & Qt.TextInteractionFlag.TextSelectableByMouse:
            value |= 1
        if flags & Qt.TextInteractionFlag.TextSelectableByKeyboard:
            value |= 2
        if flags & Qt.TextInteractionFlag.LinksAccessibleByMouse:
            value |= 4
        if flags & Qt.TextInteractionFlag.LinksAccessibleByKeyboard:
            value |= 8
        if flags & Qt.TextInteractionFlag.TextEditable:
            value |= 16
        if flags & Qt.TextInteractionFlag.TextEditorInteraction:
            value |= (1 | 2 | 16)  # This is a combination of other flags
        if flags & Qt.TextInteractionFlag.TextBrowserInteraction:
            value |= (1 | 4 | 8)  # This is a combination of other flags
        
        return value
    
    # MARK: - Serialization
    def get_serialization(self):
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QTextEdit-specific properties with safe enum conversions
        result['text_edit_props'] = {
            'plain_text': self.toPlainText(),
            'html': self.toHtml(),
            'read_only': self.isReadOnly(),
            'line_wrap_mode': self._get_line_wrap_mode_value(),
            'text_interaction_flags': self._get_text_interaction_flags_value(),
        }
        
        return result
    
    def deserialize(self, data: dict) -> bool:
        """
        Restore this widget's state from serialized data.

        Args:
            data: Dictionary containing widget state

        Returns:
            True if successful
        """
        # Let the base class handle the common serialization
        if not super().deserialize(data):
            return False
            
        # Handle QTextEdit-specific properties
        if 'text_edit_props' in data:
            props = data['text_edit_props']
            
            self.blockSignals(True)
            
            # Set content-related properties
            if 'html' in props:
                self.setHtml(props['html'])
            elif 'plain_text' in props:
                # Only use plain_text if html is not available
                self.setPlainText(props['plain_text'])
            
            # Set behavior properties
            if 'read_only' in props:
                self.setReadOnly(props['read_only'])
            
            if 'line_wrap_mode' in props:
                mode_value = props['line_wrap_mode']
                if mode_value == 0:
                    self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
                else:
                    self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            
            if 'text_interaction_flags' in props:
                # Convert numeric value back to Qt flags
                flag_value = props['text_interaction_flags']
                
                # For simplicity, just set some common combinations
                if flag_value & 16:  # TextEditable
                    self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                elif flag_value & 4:  # LinksAccessibleByMouse
                    self.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                elif flag_value & 1:  # TextSelectableByMouse
                    self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                else:
                    self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            
            self.blockSignals(False)
        
        return True