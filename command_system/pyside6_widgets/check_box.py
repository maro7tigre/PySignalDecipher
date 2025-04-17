"""
Command-enabled check box widget for PySide6 integration using click detection.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt, QEvent, QTimer

from command_system.id_system import WidgetTypeCodes
from .base_widget import BaseCommandWidget
from command_system.core import PropertyCommand, get_command_manager

class CommandCheckBox(QCheckBox, BaseCommandWidget):
    """A command-system integrated check box widget that responds to clicks."""
    
    def __init__(self, text: str = "", container_id: Optional[str] = None, 
                location: Optional[str] = None, parent=None, checked: bool = False):
        """Initialize a command check box."""
        # Initialize QCheckBox first
        QCheckBox.__init__(self, text, parent)
        
        # Initialize the command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.CHECK_BOX, container_id, location)
        
        # Set initial value
        self.setChecked(checked)
        
        # Initialize tracking variables
        self._was_checked = checked
        self._suppress_events = False
        
        # Install click handler
        self.clicked.connect(self._handle_clicked)
    
    def _update_widget_property(self, property_name: str, value: Any):
        """Update a widget property value."""
        # Suppress event handling while updating
        old_suppress = self._suppress_events
        self._suppress_events = True
        
        try:
            if property_name == "checked":
                boolean_value = bool(value)
                self.setChecked(boolean_value)
                self._was_checked = boolean_value
            elif property_name == "text":
                self.setText(str(value) if value is not None else "")
            elif property_name == "enabled":
                self.setEnabled(bool(value))
            elif property_name == "checkState":
                if not self.isTristate():
                    self.setTristate(True)
                    
                if value is None:
                    self.setCheckState(Qt.PartiallyChecked)
                elif value:
                    self.setCheckState(Qt.Checked)
                else:
                    self.setCheckState(Qt.Unchecked)
                self._was_checked = (value == True)
        finally:
            # Restore previous suppress state
            self._suppress_events = old_suppress
    
    def _handle_clicked(self, checked):
        """Direct handler for checkbox clicks."""
        # Skip if events are suppressed
        if self._suppress_events:
            return
            
        # Only create command if state actually changed
        if checked != self._was_checked:
            # Store new state
            self._was_checked = checked
            
            # Create command for checked property if bound
            if "checked" in self._controlled_properties:
                property_id = self._controlled_properties.get("checked")
                if property_id:
                    cmd = PropertyCommand(property_id, checked)
                    cmd.set_trigger_widget(self.get_id())
                    get_command_manager().execute(cmd)
            
            # Handle tri-state if needed
            if self.isTristate() and "checkState" in self._controlled_properties:
                current_state = self.checkState()
                check_state = None if current_state == Qt.PartiallyChecked else checked
                
                property_id = self._controlled_properties.get("checkState")
                if property_id:
                    cmd = PropertyCommand(property_id, check_state)
                    cmd.set_trigger_widget(self.get_id())
                    get_command_manager().execute(cmd)
    
    def bind_to_checked_property(self, observable_id: str, property_name: str):
        """Bind to checked property."""
        self.bind_property("checked", observable_id, property_name)
    
    def unbind_checked_property(self):
        """Unbind checked property."""
        self.unbind_property("checked")
    
    def bind_to_text_property(self, observable_id: str, property_name: str):
        """Bind to text property."""
        self.bind_property("text", observable_id, property_name)
    
    def unbind_text_property(self):
        """Unbind text property."""
        self.unbind_property("text")
        
    def bind_to_check_state_property(self, observable_id: str, property_name: str):
        """Bind to checkState property."""
        if not self.isTristate():
            self.setTristate(True)
        self.bind_property("checkState", observable_id, property_name)
    
    def unbind_check_state_property(self):
        """Unbind checkState property."""
        self.unbind_property("checkState")