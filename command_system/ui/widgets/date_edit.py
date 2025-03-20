"""
command_system/ui/widgets/date_edit.py
Command-aware QDateEdit
"""

from PySide6.QtWidgets import QDateEdit
from PySide6.QtCore import Signal, Slot, QDate
from datetime import date
from .base import CommandWidgetBase


class CommandDateEdit(QDateEdit, CommandWidgetBase[date]):
    """
    Command-aware date edit that automatically integrates with the command system.
    
    Example:
        # Create date edit and connect to model
        date_edit = CommandDateEdit()
        date_edit.bind_to_model(my_model, "date_property")
        
        # Use like a normal QDateEdit
        layout.addWidget(date_edit)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command date edit."""
        QDateEdit.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("date")
        
        # Connect signals
        self.dateChanged.connect(self._on_date_changed)
        self.editingFinished.connect(self._end_edit)
        
        # Store initial state
        self._old_value = self.date().toPython()
        self._is_editing = False
        
    def _on_date_changed(self, qdate):
        """Called when date changes."""
        if not self._is_editing:
            self._is_editing = True
            self._begin_edit()
        
        # Update model via command widget
        self._on_widget_value_changed()
            
    def _end_edit(self):
        """Called when editing is finished."""
        if self._is_editing:
            self._is_editing = False
            self._old_value = self.date().toPython()
            
    def _get_widget_value(self) -> date:
        """Get the widget's current date as Python date."""
        return self.date().toPython()
        
    def _set_widget_value(self, value: date):
        """Set the widget's date."""
        if isinstance(value, date):
            self.setDate(QDate(value))
        elif isinstance(value, QDate):
            self.setDate(value)
        else:
            try:
                # Try to parse as ISO format date string
                d = date.fromisoformat(str(value))
                self.setDate(QDate(d))
            except (ValueError, TypeError):
                # Use current date if conversion fails
                self.setDate(QDate.currentDate())