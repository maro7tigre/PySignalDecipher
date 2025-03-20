"""
command_system/ui/widgets/combo_box.py
Command-aware QComboBox
"""

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal, Slot, Qt
from typing import Any, Union, List, Dict, Optional
from .base import CommandWidgetBase


class CommandComboBox(QComboBox, CommandWidgetBase[int]):
    """
    Command-aware combo box that automatically integrates with the command system.
    
    By default, binds to the currentIndex property. Can be set to use
    currentData or currentText instead with the value_mode parameter.
    
    Example:
        # Create combo box and connect to model
        combo = CommandComboBox()
        combo.addItems(["Option 1", "Option 2"])
        combo.bind_to_model(my_model, "option_index")
        
        # Using data mode
        combo = CommandComboBox(value_mode="data")
        combo.addItem("Option 1", userData=100)
        combo.addItem("Option 2", userData=200)
        combo.bind_to_model(my_model, "option_value")
    """
    
    MODE_INDEX = "index"
    MODE_TEXT = "text"
    MODE_DATA = "data"
    
    def __init__(self, value_mode="index", *args, **kwargs):
        """
        Initialize command combo box.
        
        Args:
            value_mode: Mode for getting/setting values:
                        "index": Use currentIndex
                        "text": Use currentText
                        "data": Use currentData
        """
        QComboBox.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set value mode
        self._value_mode = value_mode
        if value_mode == self.MODE_INDEX:
            self._setup_command_widget("currentIndex")
        elif value_mode == self.MODE_TEXT:
            self._setup_command_widget("currentText")
        elif value_mode == self.MODE_DATA:
            self._setup_command_widget("currentData")
        else:
            raise ValueError(f"Invalid value_mode: {value_mode}")
            
        # Connect signals
        if value_mode == self.MODE_INDEX:
            self.currentIndexChanged.connect(self._on_index_changed)
        elif value_mode == self.MODE_TEXT:
            self.currentTextChanged.connect(self._on_text_changed)
        else:  # MODE_DATA
            self.currentIndexChanged.connect(self._on_data_changed)
            
        # Store initial state
        self._old_value = self._get_widget_value()
            
    def _on_index_changed(self, index):
        """Called when current index changes."""
        self._on_widget_value_changed()
        
    def _on_text_changed(self, text):
        """Called when current text changes."""
        self._on_widget_value_changed()
        
    def _on_data_changed(self, index):
        """Called when index changes, affecting current data."""
        self._on_widget_value_changed()
        
    def _get_widget_value(self) -> Any:
        """Get the widget's current value."""
        if self._value_mode == self.MODE_INDEX:
            return self.currentIndex()
        elif self._value_mode == self.MODE_TEXT:
            return self.currentText()
        else:  # MODE_DATA
            return self.currentData(Qt.ItemDataRole.UserRole)
        
    def _set_widget_value(self, value: Any):
        """Set the widget's value."""
        if self._value_mode == self.MODE_INDEX:
            try:
                index = int(value)
                if 0 <= index < self.count():
                    self.setCurrentIndex(index)
            except (ValueError, TypeError):
                pass
        elif self._value_mode == self.MODE_TEXT:
            # Try to find matching text
            index = self.findText(str(value))
            if index >= 0:
                self.setCurrentIndex(index)
        else:  # MODE_DATA
            # Try to find matching data
            index = self.findData(value, Qt.ItemDataRole.UserRole)
            if index >= 0:
                self.setCurrentIndex(index)