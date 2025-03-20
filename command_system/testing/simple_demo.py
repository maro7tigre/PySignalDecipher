"""
Simple Command System Demo

A minimal demo with just a number input to test the command system.
"""
import sys
import os

# Add parent directory to path for imports to work
# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QSpinBox, QPushButton)

# Import from the simple command system
from command_system import (
    Observable, ObservableProperty, Command, 
    PropertyBinder, get_command_manager
)


class SimpleModel(Observable):
    """Simple model with a single observable property."""
    value = ObservableProperty[int](default=0)
    
    def __init__(self):
        """Initialize with default value."""
        super().__init__()


class ValueChangeCommand(Command):
    """Command for manually changing the value (for testing)."""
    
    def __init__(self, model, new_value):
        self.model = model
        self.new_value = new_value
        self.old_value = model.value
        
    def execute(self):
        self.model.value = self.new_value
        
    def undo(self):
        self.model.value = self.old_value


class MainWindow(QMainWindow):
    """Main window for the simple demo."""
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Simple Command System Demo")
        self.setMinimumSize(300, 200)
        
        # Get command manager
        self.cmd_manager = get_command_manager()
        
        # Create model
        self.model = SimpleModel()
        
        # Create property binder
        self.binder = PropertyBinder()
        
        # Create UI
        self._create_ui()
        
        # Initial update of button states
        self._update_undo_redo_buttons()
        
    def _create_ui(self):
        """Create the UI elements."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Value input
        value_layout = QHBoxLayout()
        value_label = QLabel("Value:")
        self.value_spinbox = QSpinBox()
        self.value_spinbox.setMinimum(0)
        self.value_spinbox.setMaximum(100)
        
        # We need to set the initial value before binding
        # and block signals to avoid false-positive change events
        self.value_spinbox.blockSignals(True)
        self.value_spinbox.setValue(self.model.value)
        self.value_spinbox.blockSignals(False)
        
        value_layout.addWidget(value_label)
        value_layout.addWidget(self.value_spinbox)
        main_layout.addLayout(value_layout)
        
        # Add manual change buttons for testing
        increment_layout = QHBoxLayout()
        increment_label = QLabel("Test Increment:")
        self.increment_button = QPushButton("+5")
        self.increment_button.clicked.connect(self._on_increment)
        self.decrement_button = QPushButton("-5")
        self.decrement_button.clicked.connect(self._on_decrement)
        increment_layout.addWidget(increment_label)
        increment_layout.addWidget(self.increment_button)
        increment_layout.addWidget(self.decrement_button)
        main_layout.addLayout(increment_layout)
        
        # Command buttons
        cmd_layout = QHBoxLayout()
        
        # Undo button
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._on_undo)
        self.undo_button.setEnabled(False)
        cmd_layout.addWidget(self.undo_button)
        
        # Redo button
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._on_redo)
        self.redo_button.setEnabled(False)
        cmd_layout.addWidget(self.redo_button)
        
        main_layout.addLayout(cmd_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Current value display
        self.value_display = QLabel(f"Current model value: {self.model.value}")
        main_layout.addWidget(self.value_display)
        
        # Set main widget
        self.setCentralWidget(main_widget)
        
        # Add observer to update the display label
        self.model.add_property_observer("value", self._on_model_value_changed)
        
        # Create a custom handler for spin box changes to explicitly create commands
        self.value_spinbox.valueChanged.connect(self._on_spinbox_value_changed)
        
        # No longer using the automatic binding since we're handling changes manually
        # self.binder.bind(self.model, "value", self.value_spinbox, "value")
        
    def _on_model_value_changed(self, property_name, old_value, new_value):
        """Update the display when model value changes."""
        self.value_display.setText(f"Current model value: {new_value}")
        
        # Update the spinbox if necessary, blocking signals to prevent loops
        if self.value_spinbox.value() != new_value:
            self.value_spinbox.blockSignals(True)
            self.value_spinbox.setValue(new_value)
            self.value_spinbox.blockSignals(False)
            
        self._update_undo_redo_buttons()
        
    def _on_spinbox_value_changed(self, new_value):
        """Handle changes from the spinbox by creating explicit commands."""
        # Skip if the model already has this value (prevents duplicates)
        if self.model.value == new_value:
            return
            
        # Create and execute a command for this change
        cmd = ValueChangeCommand(self.model, new_value)
        self.cmd_manager.execute(cmd)
        self.status_label.setText(f"Value changed to {new_value}")
        # No need to update buttons here as the model observer will do it
        
    def _on_increment(self):
        """Handle increment button click."""
        new_value = self.model.value + 5
        cmd = ValueChangeCommand(self.model, new_value)
        self.cmd_manager.execute(cmd)
        self.status_label.setText(f"Incremented value by 5")
        
    def _on_decrement(self):
        """Handle decrement button click."""
        new_value = max(0, self.model.value - 5)  # Don't go below 0
        cmd = ValueChangeCommand(self.model, new_value)
        self.cmd_manager.execute(cmd)
        self.status_label.setText(f"Decremented value by 5")
        
    def _update_undo_redo_buttons(self):
        """Update undo/redo button states."""
        self.undo_button.setEnabled(self.cmd_manager.can_undo())
        self.redo_button.setEnabled(self.cmd_manager.can_redo())
        
    def _on_undo(self):
        """Handle undo button click."""
        if self.cmd_manager.undo():
            self.status_label.setText("Undo: Success")
        else:
            self.status_label.setText("Undo: Nothing to undo")
        self._update_undo_redo_buttons()
        
    def _on_redo(self):
        """Handle redo button click."""
        if self.cmd_manager.redo():
            self.status_label.setText("Redo: Success")
        else:
            self.status_label.setText("Redo: Nothing to redo")
        self._update_undo_redo_buttons()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()