"""
command_system/ui/widgets/spin_box.py
Command-aware QSpinBox and QDoubleSpinBox
"""

from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Signal, Slot
from .base import CommandWidgetBase


class CommandSpinBox(QSpinBox, CommandWidgetBase[int]):
    """
    Command-aware spin box that automatically integrates with the command system.
    
    Example:
        # Create spin box and connect to model
        spin = CommandSpinBox()
        spin.bind_to_model(my_model, "count_property")
        
        # Use like a normal QSpinBox
        layout.addWidget(spin)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command spin box."""
        QSpinBox.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("value")
        
        # Connect signals
        self.valueChanged.connect(self._on_value_changed)
        self.editingFinished.connect(self._end_edit)
        
        # Store initial state
        self._old_value = self.value()
        self._is_editing = False
        
    def _on_value_changed(self, value):
        """Called when value changes."""
        if not self._is_editing:
            self._is_editing = True
            self._begin_edit()
        
        # Update model via command widget
        self._on_widget_value_changed()
            
    def _end_edit(self):
        """Called when editing is finished."""
        if self._is_editing:
            self._is_editing = False
            self._old_value = self.value()
            
    def _get_widget_value(self) -> int:
        """Get the widget's current value."""
        return self.value()
        
    def _set_widget_value(self, value: int):
        """Set the widget's value."""
        try:
            self.setValue(int(value))
        except (ValueError, TypeError):
            # Use minimum value if conversion fails
            self.setValue(self.minimum())


class CommandDoubleSpinBox(QDoubleSpinBox, CommandWidgetBase[float]):
    """
    Command-aware double spin box that automatically integrates with the command system.
    
    Example:
        # Create spin box and connect to model
        spin = CommandDoubleSpinBox()
        spin.bind_to_model(my_model, "value_property")
        
        # Use like a normal QDoubleSpinBox
        layout.addWidget(spin)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command double spin box."""
        QDoubleSpinBox.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("value")
        
        # Connect signals
        self.valueChanged.connect(self._on_value_changed)
        self.editingFinished.connect(self._end_edit)
        
        # Store initial state
        self._old_value = self.value()
        self._is_editing = False
        
    def _on_value_changed(self, value):
        """Called when value changes."""
        if not self._is_editing:
            self._is_editing = True
            self._begin_edit()
        
        # Update model via command widget
        self._on_widget_value_changed()
            
    def _end_edit(self):
        """Called when editing is finished."""
        if self._is_editing:
            self._is_editing = False
            self._old_value = self.value()
            
    def _get_widget_value(self) -> float:
        """Get the widget's current value."""
        return self.value()
        
    def _set_widget_value(self, value: float):
        """Set the widget's value."""
        try:
            self.setValue(float(value))
        except (ValueError, TypeError):
            # Use minimum value if conversion fails
            self.setValue(self.minimum())