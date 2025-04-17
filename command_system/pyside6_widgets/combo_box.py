"""
Command-enabled combo box widget for PySide6 integration.

This module provides a combo box widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional, List, Union
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal, Slot, Qt

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandComboBox(QComboBox, BaseCommandWidget):
    """
    A command-system integrated combo box widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, items: Optional[List[str]] = None):
        """
        Initialize a command combo box.
        
        Args:
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            items: Optional list of items to populate the combo box
        """
        # Initialize QComboBox first
        QComboBox.__init__(self, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.COMBO_BOX, container_id, location)
        
        # Add items if provided
        if items:
            self.addItems(items)
        
        # Connect signals for value changes
        self.currentIndexChanged.connect(self._handle_index_changed)
        self.currentTextChanged.connect(self._handle_text_changed)
        
        # Default to immediate trigger mode for combos
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
        
        if property_name == "currentIndex":
            # Handle None value as -1 (no selection)
            index = -1 if value is None else int(value)
            self.setCurrentIndex(index)
        elif property_name == "currentText":
            # Find the index of the text and set it
            text = str(value) if value is not None else ""
            index = self.findText(text)
            if index >= 0:
                self.setCurrentIndex(index)
            elif self.isEditable():  
                # If editable, we can set text directly
                self.setCurrentText(text)
        elif property_name == "items":
            # Update the entire item list
            self.clear()
            if value:
                if isinstance(value, (list, tuple)):
                    self.addItems(value)
                else:
                    # Try to convert to string and add as single item
                    self.addItem(str(value))
        elif property_name == "enabled":
            self.setEnabled(bool(value))
        else:
            self.blockSignals(False)
            raise ValueError(f"Unsupported property: {property_name}")
        
        # Re-enable signals
        self.blockSignals(False)
    
    # MARK: - Signal Handlers
    @Slot(int)
    def _handle_index_changed(self, index: int):
        """
        Handle index changes from the widget.
        
        Args:
            index: New selected index
        """
        # Delegate to base class
        self._on_widget_value_changed("currentIndex", index)
    
    @Slot(str)
    def _handle_text_changed(self, text: str):
        """
        Handle text changes from the widget.
        
        Args:
            text: New selected or entered text
        """
        # Delegate to base class if text actually changed
        self._on_widget_value_changed("currentText", text)
    
    # MARK: - Custom Methods
    def setItems(self, items: List[str], current_index: int = 0):
        """
        Set all items at once and optionally select an item.
        
        Args:
            items: List of items to set
            current_index: Index to select after setting items
        """
        self.blockSignals(True)
        self.clear()
        self.addItems(items)
        if 0 <= current_index < len(items):
            self.setCurrentIndex(current_index)
        self.blockSignals(False)
        
        # Notify about both changes
        self._on_widget_value_changed("items", items)
        self._on_widget_value_changed("currentIndex", self.currentIndex())
    
    # MARK: - Convenience Methods
    def bind_to_current_index_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind currentIndex property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("currentIndex", observable_id, property_name)
    
    def unbind_current_index_property(self):
        """Convenience method to unbind currentIndex property."""
        self.unbind_property("currentIndex")
    
    def bind_to_current_text_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind currentText property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("currentText", observable_id, property_name)
    
    def unbind_current_text_property(self):
        """Convenience method to unbind currentText property."""
        self.unbind_property("currentText")
    
    def bind_to_items_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind items property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("items", observable_id, property_name)
    
    def unbind_items_property(self):
        """Convenience method to unbind items property."""
        self.unbind_property("items")
        
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QComboBox-specific properties
        items = [self.itemText(i) for i in range(self.count())]
        
        result['combo_box_props'] = {
            'items': items,
            'current_index': self.currentIndex(),
            'editable': self.isEditable(),
            'max_visible_items': self.maxVisibleItems(),
            'insert_policy': int(self.insertPolicy()),
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
            
        # Handle QComboBox-specific properties
        if 'combo_box_props' in data:
            props = data['combo_box_props']
            
            # Block signals during bulk updates
            self.blockSignals(True)
            
            if 'editable' in props:
                self.setEditable(props['editable'])
            
            if 'max_visible_items' in props:
                self.setMaxVisibleItems(props['max_visible_items'])
            
            if 'insert_policy' in props:
                self.setInsertPolicy(QComboBox.InsertPolicy(props['insert_policy']))
            
            # Clear and add items
            if 'items' in props:
                self.clear()
                self.addItems(props['items'])
            
            # Set current index last
            if 'current_index' in props and 'items' in props:
                index = props['current_index']
                if 0 <= index < len(props['items']):
                    self.setCurrentIndex(index)
            
            self.blockSignals(False)
        
        return True