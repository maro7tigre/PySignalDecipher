"""
Command-enabled line edit widget for PySide6 integration.

This module provides a line edit widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal, Slot

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandLineEdit(QLineEdit, BaseCommandWidget):
    """
    A command-system integrated line edit widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, text: str = ""):
        """
        Initialize a command line edit.
        
        Args:
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            text: Initial text
        """
        # Initialize QLineEdit first
        QLineEdit.__init__(self, text, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.LINE_EDIT, container_id, location)
        
        # Connect signals for value changes
        self.textChanged.connect(self._handle_text_changed)
        self.editingFinished.connect(self._handle_editing_finished)
        
        # Default to edit finished trigger mode for better user experience
        self.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
    
    # MARK: - Property Implementation
    def _update_widget_property(self, property_name: str, value: Any):
        """
        Update a widget property value.
        
        Args:
            property_name: Name of the property to update
            value: New value for the property
        """
        if property_name == "text":
            # Block signals to prevent recursion
            self.blockSignals(True)
            self.setText(str(value) if value is not None else "")
            self.blockSignals(False)
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    
    # MARK: - Signal Handlers
    @Slot(str)
    def _handle_text_changed(self, text: str):
        """
        Handle text changes from the widget.
        
        Args:
            text: New text value
        """
        # Delegate to base class
        self._on_widget_value_changed("text", text)
    
    @Slot()
    def _handle_editing_finished(self):
        """Handle the completion of editing."""
        # Delegate to base class
        self._on_widget_editing_finished()
    
    # MARK: - Convenience Methods
    def bind_to_text_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind text property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("text", observable_id, property_name)
    
    def unbind_text_property(self):
        """Convenience method to unbind text property."""
        self.unbind_property("text")
        
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add any QLineEdit-specific properties here if needed
        # For example:
        # result['line_edit_props'] = {
        #     'placeholder_text': self.placeholderText(),
        #     'max_length': self.maxLength(),
        #     'read_only': self.isReadOnly()
        # }
        
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
            
        # Handle any QLineEdit-specific properties here if needed
        # if 'line_edit_props' in data:
        #     props = data['line_edit_props']
        #     if 'placeholder_text' in props:
        #         self.setPlaceholderText(props['placeholder_text'])
        #     if 'max_length' in props:
        #         self.setMaxLength(props['max_length'])
        #     if 'read_only' in props:
        #         self.setReadOnly(props['read_only'])
        
        return True