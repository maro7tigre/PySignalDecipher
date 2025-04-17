"""
PySide6 integration for command system.

This package provides PySide6 widgets and containers that integrate with the command system
for automatic undo/redo support, property binding, and serialization.
"""

from .base_widget import BaseCommandWidget, CommandTriggerMode
from .line_edit import CommandLineEdit
from .spin_box import CommandSpinBox
from .check_box import CommandCheckBox
from .slider import CommandSlider
from .combo_box import CommandComboBox
from .text_edit import CommandTextEdit
from .date_edit import CommandDateEdit
from .double_spin_box import CommandDoubleSpinBox

# Import container classes
from .containers.base_container import BaseCommandContainer
from .containers.tab_widget import CommandTabWidget

__all__ = [
    # Base classes
    'BaseCommandWidget',
    'CommandTriggerMode',
    'BaseCommandContainer',
    
    # Widgets
    'CommandLineEdit',
    'CommandSpinBox',
    'CommandCheckBox',
    'CommandSlider',
    'CommandComboBox',
    'CommandTextEdit',
    'CommandDateEdit',
    'CommandDoubleSpinBox',
    
    # Containers
    'CommandTabWidget',
]