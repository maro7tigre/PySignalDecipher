"""
Command-enabled slider widget for PySide6 integration.

This module provides a slider widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Signal, Slot, Qt

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandSlider(QSlider, BaseCommandWidget):
    """
    A command-system integrated slider widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal, 
                container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, value: int = 0):
        """
        Initialize a command slider.
        
        Args:
            orientation: Qt.Horizontal or Qt.Vertical
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            value: Initial value
        """
        # Initialize QSlider first
        QSlider.__init__(self, orientation, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.SLIDER, container_id, location)
        
        # Set initial value
        self.setValue(value)
        
        # Connect signals for value changes
        self.valueChanged.connect(self._handle_value_changed)
        self.sliderReleased.connect(self._handle_slider_released)
        
        # Default to DELAYED trigger mode for sliders
        # This prevents generating too many commands during sliding
        # while still providing visual feedback
        self.set_command_trigger_mode(CommandTriggerMode.DELAYED, 100)  # 100ms delay
    
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
        
        if property_name == "value":
            self.setValue(int(value) if value is not None else 0)
        elif property_name == "enabled":
            self.setEnabled(bool(value))
        elif property_name == "minimum":
            self.setMinimum(int(value))
        elif property_name == "maximum":
            self.setMaximum(int(value))
        else:
            self.blockSignals(False)
            raise ValueError(f"Unsupported property: {property_name}")
        
        # Re-enable signals
        self.blockSignals(False)
    
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
    def _handle_slider_released(self):
        """Handle the slider being released."""
        # When slider is released, commit any pending changes
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
        
    def bind_to_minimum_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind minimum property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("minimum", observable_id, property_name)
    
    def unbind_minimum_property(self):
        """Convenience method to unbind minimum property."""
        self.unbind_property("minimum")
        
    def bind_to_maximum_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind maximum property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("maximum", observable_id, property_name)
    
    def unbind_maximum_property(self):
        """Convenience method to unbind maximum property."""
        self.unbind_property("maximum")
        
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QSlider-specific properties
        result['slider_props'] = {
            'minimum': self.minimum(),
            'maximum': self.maximum(),
            'single_step': self.singleStep(),
            'page_step': self.pageStep(),
            'tick_position': self.tickPosition(),
            'tick_interval': self.tickInterval(),
            'orientation': int(self.orientation()),  # Convert Qt.Orientation to int
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
            
        # Handle QSlider-specific properties
        if 'slider_props' in data:
            props = data['slider_props']
            if 'minimum' in props:
                self.setMinimum(props['minimum'])
            if 'maximum' in props:
                self.setMaximum(props['maximum'])
            if 'single_step' in props:
                self.setSingleStep(props['single_step'])
            if 'page_step' in props:
                self.setPageStep(props['page_step'])
            if 'tick_position' in props:
                self.setTickPosition(props['tick_position'])
            if 'tick_interval' in props:
                self.setTickInterval(props['tick_interval'])
            if 'orientation' in props:
                # Convert int back to Qt.Orientation
                self.setOrientation(Qt.Orientation(props['orientation']))
        
        return True