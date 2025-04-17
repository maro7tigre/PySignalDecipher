"""
Command-enabled check box widget for PySide6 integration.

This module provides a check box widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Signal, Slot, Qt

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandCheckBox(QCheckBox, BaseCommandWidget):
    """
    A command-system integrated check box widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, text: str = "", container_id: Optional[str] = None, 
                location: Optional[str] = None, parent=None, checked: bool = False):
        """
        Initialize a command check box.
        
        Args:
            text: Text to display next to the checkbox
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            checked: Initial checked state
        """
        # Initialize QCheckBox first
        QCheckBox.__init__(self, text, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.CHECK_BOX, container_id, location)
        
        # Set initial value
        self.setChecked(checked)
        
        # Connect signals for value changes
        self.stateChanged.connect(self._handle_state_changed)
        
        # Default to immediate trigger mode since checkboxes have immediate feedback
        self.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
    
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
        
        if property_name == "checked":
            self.setChecked(bool(value))
        elif property_name == "text":
            self.setText(str(value) if value is not None else "")
        elif property_name == "enabled":
            self.setEnabled(bool(value))
        elif property_name == "checkState":
            # Handle tri-state checkboxes
            if value is None:
                state = Qt.PartiallyChecked
            elif value:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            self.setCheckState(state)
        else:
            self.blockSignals(False)
            raise ValueError(f"Unsupported property: {property_name}")
        
        # Re-enable signals
        self.blockSignals(False)
    
    # MARK: - Signal Handlers
    @Slot(int)
    def _handle_state_changed(self, state: int):
        """
        Handle state changes from the widget.
        
        Args:
            state: New state (Qt.Checked, Qt.Unchecked, or Qt.PartiallyChecked)
        """
        # Convert Qt state to boolean for the "checked" property
        checked = state == Qt.Checked
        
        # Delegate to base class
        self._on_widget_value_changed("checked", checked)
        
        # For tri-state support, also update checkState property if needed
        if self.isTristate():
            # Convert Qt state to Python value (True, False, None)
            check_state = None if state == Qt.PartiallyChecked else checked
            self._on_widget_value_changed("checkState", check_state)
    
    # MARK: - Convenience Methods
    def bind_to_checked_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind checked property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("checked", observable_id, property_name)
    
    def unbind_checked_property(self):
        """Convenience method to unbind checked property."""
        self.unbind_property("checked")
    
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
        
    def bind_to_check_state_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind checkState property for tri-state checkboxes.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        # Enable tri-state mode if not already enabled
        if not self.isTristate():
            self.setTristate(True)
        self.bind_property("checkState", observable_id, property_name)
    
    def unbind_check_state_property(self):
        """Convenience method to unbind checkState property."""
        self.unbind_property("checkState")
        
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QCheckBox-specific properties
        result['check_box_props'] = {
            'text': self.text(),
            'tristate': self.isTristate(),
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
            
        # Handle QCheckBox-specific properties
        if 'check_box_props' in data:
            props = data['check_box_props']
            if 'text' in props:
                self.setText(props['text'])
            if 'tristate' in props:
                self.setTristate(props['tristate'])
        
        return True