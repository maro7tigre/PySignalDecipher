"""
Command-enabled date edit widget for PySide6 integration.

This module provides a date edit widget that integrates with the command system
for automatic undo/redo support and property binding.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import Signal, Slot, QDate

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget, CommandTriggerMode

class CommandDateEdit(QDateEdit, BaseCommandWidget):
    """
    A command-system integrated date edit widget.
    
    Supports binding to observable properties with automatic command generation
    for undo/redo functionality.
    """
    
    def __init__(self, container_id: Optional[str] = None, location: Optional[str] = None, 
                parent=None, date: Optional[QDate] = None):
        """
        Initialize a command date edit.
        
        Args:
            container_id: Optional ID of the parent container
            location: Optional location within the container
            parent: Qt parent widget
            date: Initial date (defaults to current date if None)
        """
        # Initialize QDateEdit first
        QDateEdit.__init__(self, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.DATE_EDIT, container_id, location)
        
        # Set initial date
        if date:
            self.setDate(date)
        
        # Connect signals for value changes
        self.dateChanged.connect(self._handle_date_changed)
        self.editingFinished.connect(self._handle_editing_finished)
        
        # Default to ON_EDIT_FINISHED for date edits
        # This ensures we only generate commands when the user has confirmed their selection
        self.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
    
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
        
        if property_name == "date":
            if isinstance(value, QDate):
                self.setDate(value)
            elif isinstance(value, str):
                # Try to parse date from string (yyyy-MM-dd format)
                qdate = QDate.fromString(value, "yyyy-MM-dd")
                if qdate.isValid():
                    self.setDate(qdate)
            elif value is None:
                # Reset to current date
                self.setDate(QDate.currentDate())
        elif property_name == "enabled":
            self.setEnabled(bool(value))
        elif property_name == "calendarPopup":
            self.setCalendarPopup(bool(value))
        elif property_name == "displayFormat":
            self.setDisplayFormat(str(value) if value else "yyyy-MM-dd")
        else:
            self.blockSignals(False)
            raise ValueError(f"Unsupported property: {property_name}")
        
        # Re-enable signals
        self.blockSignals(False)
    
    # MARK: - Signal Handlers
    @Slot(QDate)
    def _handle_date_changed(self, date: QDate):
        """
        Handle date changes from the widget.
        
        Args:
            date: New date value
        """
        # We'll represent the date as an ISO string in our property system
        # for better interoperability
        date_str = date.toString("yyyy-MM-dd")
        
        # Delegate to base class
        self._on_widget_value_changed("date", date_str)
    
    @Slot()
    def _handle_editing_finished(self):
        """Handle the completion of editing."""
        # Delegate to base class
        self._on_widget_editing_finished()
    
    # MARK: - Convenience Methods
    def bind_to_date_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind date property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("date", observable_id, property_name)
    
    def unbind_date_property(self):
        """Convenience method to unbind date property."""
        self.unbind_property("date")
    
    def bind_to_display_format_property(self, observable_id: str, property_name: str):
        """
        Convenience method to bind displayFormat property.
        
        Args:
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        self.bind_property("displayFormat", observable_id, property_name)
    
    def unbind_display_format_property(self):
        """Convenience method to unbind displayFormat property."""
        self.unbind_property("displayFormat")
    
    # MARK: - Serialization
    def get_serialization(self) -> dict:
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get base serialization
        result = super().get_serialization()
        
        # Add QDateEdit-specific properties
        result['date_edit_props'] = {
            'date': self.date().toString("yyyy-MM-dd"),
            'minimum_date': self.minimumDate().toString("yyyy-MM-dd"),
            'maximum_date': self.maximumDate().toString("yyyy-MM-dd"),
            'display_format': self.displayFormat(),
            'calendar_popup': self.calendarPopup(),
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
            
        # Handle QDateEdit-specific properties
        if 'date_edit_props' in data:
            props = data['date_edit_props']
            
            self.blockSignals(True)
            
            # Set range first
            if 'minimum_date' in props:
                min_date = QDate.fromString(props['minimum_date'], "yyyy-MM-dd")
                if min_date.isValid():
                    self.setMinimumDate(min_date)
            
            if 'maximum_date' in props:
                max_date = QDate.fromString(props['maximum_date'], "yyyy-MM-dd")
                if max_date.isValid():
                    self.setMaximumDate(max_date)
            
            # Set format before date to ensure proper display
            if 'display_format' in props:
                self.setDisplayFormat(props['display_format'])
            
            # Set date within the range
            if 'date' in props:
                date = QDate.fromString(props['date'], "yyyy-MM-dd")
                if date.isValid():
                    self.setDate(date)
            
            if 'calendar_popup' in props:
                self.setCalendarPopup(props['calendar_popup'])
            
            self.blockSignals(False)
        
        return True