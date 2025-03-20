"""
command_system/ui/widgets/slider.py
Command-aware QSlider
"""

from PySide6.QtWidgets import QSlider
from PySide6.QtCore import Signal, Slot
from .base import CommandWidgetBase


class CommandSlider(QSlider, CommandWidgetBase[int]):
    """
    Command-aware slider that automatically integrates with the command system.
    
    Example:
        # Create slider and connect to model
        slider = CommandSlider()
        slider.setRange(0, 100)
        slider.bind_to_model(my_model, "value_property")
        
        # Use like a normal QSlider
        layout.addWidget(slider)
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize command slider."""
        QSlider.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("value")
        
        # Connect signals for both real-time and final edits
        self.valueChanged.connect(self._on_value_changed)
        self.sliderReleased.connect(self._end_edit)
        self.sliderPressed.connect(self._begin_edit)
        
        # Store flags for tracking editing state
        self._is_sliding = False
        
    def _on_value_changed(self, value):
        """Called when value changes."""
        # Only create commands when slider isn't being dragged
        # to avoid excessive command history
        if not self._is_sliding:
            self._on_widget_value_changed()
        
    def _begin_edit(self):
        """Called when slider is pressed."""
        self._is_sliding = True
        super()._begin_edit()
        
    def _end_edit(self):
        """Called when slider is released."""
        if self._is_sliding:
            self._is_sliding = False
            # Now create a single command for the entire drag operation
            self._on_widget_value_changed()
            
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