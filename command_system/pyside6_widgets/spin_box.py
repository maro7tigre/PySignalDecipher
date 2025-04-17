"""
Command-enabled spin box widget for PySide6 integration.

This module provides a spin box widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QSpinBox
from PySide6.QtCore import Signal, Slot

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandSpinBox(QSpinBox, BaseCommandWidget):
    """
    A command-system integrated spin box widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, value: int = 0):
        """
        Initialize a command spin box.
        
        Args:
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            value: Initial value
        """
        # Initialize QSpinBox first
        QSpinBox.__init__(self, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.SPIN_BOX, container_id, location)
        
        # Set initial value
        self.setValue(value)
        
        # Connect signals for value changes
        self.valueChanged.connect(self._handle_value_changed)
        self.editingFinished.connect(self._handle_editing_finished)
        
        # Default to immediate trigger mode for better user experience with spin box
        # Since users typically expect immediate feedback from increment/decrement
        self.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
    
    # MARK: - Property Implementation
    def _update_widget_property(self, property_name: str, value: Any):
        """
        Update a widget property value.
        
        Args:
            property_name: Name of the property to update
            value: New value for the property
        """
        if property_name == "value":
            # Block signals to prevent recursion
            self.blockSignals(True)
            self.setValue(int(value) if value is not None else 0)
            self.blockSignals(False)
        elif property_name == "enabled":
            # Block signals to prevent recursion
            self.blockSignals(True)
            self.setEnabled(bool(value))
            self.blockSignals(False)
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    
    # MARK: - Signal Handlers
    @Slot(int)
    def _handle_value_changed(self, value: int):
        """
        Handle value changes from the widget.
        
        Args:
            value: New value
        """
        # Delegate to base class
        self._on_widget_value_changed("value", value)
    
    @Slot()
    def _handle_editing_finished(self):
        """Handle the completion of editing."""
        # Delegate to base class
        self._on_widget_editing_finished()
    
    # MARK: - Convenience Methods
    def bind_to_value_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind value property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("value", observable_id, property_name)
    
    def unbind_value_property(self):
        """Convenience method to unbind value property."""
        self.unbind_property("value")
        
    def bind_to_enabled_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind enabled property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("enabled", observable_id, property_name)
    
    def unbind_enabled_property(self):
        """Convenience method to unbind enabled property."""
        self.unbind_property("enabled")
        
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QSpinBox-specific properties
        result['spin_box_props'] = {
            'minimum': self.minimum(),
            'maximum': self.maximum(),
            'single_step': self.singleStep(),
            'prefix': self.prefix(),
            'suffix': self.suffix()
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
            
        # Handle QSpinBox-specific properties
        if 'spin_box_props' in data:
            props = data['spin_box_props']
            if 'minimum' in props:
                self.setMinimum(props['minimum'])
            if 'maximum' in props:
                self.setMaximum(props['maximum'])
            if 'single_step' in props:
                self.setSingleStep(props['single_step'])
            if 'prefix' in props:
                self.setPrefix(props['prefix'])
            if 'suffix' in props:
                self.setSuffix(props['suffix'])
        
        return True