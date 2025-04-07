"""
Minimal demo of the PySignalDecipher command system with different command trigger modes.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFormLayout
)

# Add project root to path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core import Observable, ObservableProperty, get_command_manager
from command_system.pyside6_widgets import CommandLineEdit, CommandTriggerMode

class Person(Observable):
    """Simple model with observable properties for demonstration."""
    name = ObservableProperty("")
    email = ObservableProperty("")
    phone = ObservableProperty("")
    
    def __init__(self):
        """Initialize the person model with default values."""
        super().__init__()
        self.name = "John Doe"
        self.email = "john@example.com"
        self.phone = "123-456-7890"

class SimpleModeDemo(QMainWindow):
    """
    Minimal demo of command trigger modes.
    
    This demo shows how different trigger modes affect when commands
    are created and executed.
    """
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        self.setWindowTitle("Command System Demo")
        self.resize(500, 300)
        
        # Create model and get command manager
        self.person = Person()
        self.person_id = self.person.get_id()
        self.cmd_manager = get_command_manager()
        
        # Setup UI
        self._setup_ui()
        
        # Update command count display
        self.update_count()
        
    def _setup_ui(self):
        """Set up the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create form layout for the input fields
        form = QFormLayout()
        layout.addLayout(form)
        
        # Create and configure the input fields
        
        # Immediate mode input
        self.edit1 = CommandLineEdit()
        self.edit1.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        self.edit1.bind_to_text_property(self.person_id, "name")
        form.addRow("Immediate Mode:", self.edit1)
        
        # Add explanation label for immediate mode
        immediate_label = QLabel("Changes applied with every keystroke")
        immediate_label.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", immediate_label)
        
        # Delayed mode input
        self.edit2 = CommandLineEdit()
        self.edit2.set_command_trigger_mode(CommandTriggerMode.DELAYED, 1000)  # 1 second delay
        self.edit2.bind_to_text_property(self.person_id, "email")
        form.addRow("Delayed Mode:", self.edit2)
        
        # Add explanation label for delayed mode
        delayed_label = QLabel("Changes applied after 1 second of inactivity")
        delayed_label.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", delayed_label)
        
        # On edit finished mode input
        self.edit3 = CommandLineEdit()
        self.edit3.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        self.edit3.bind_to_text_property(self.person_id, "phone")
        form.addRow("On Edit Finished:", self.edit3)
        
        # Add explanation label for edit finished mode
        finished_label = QLabel("Changes applied when focus leaves the field")
        finished_label.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", finished_label)
        
        # Add a separator
        separator = QWidget()
        separator.setFixedHeight(20)
        layout.addWidget(separator)
        
        # Add command count display
        self.count_label = QLabel()
        layout.addWidget(self.count_label)
        
        # Add undo/redo buttons
        btn_layout = QHBoxLayout()
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.setMinimumWidth(100)
        undo_btn.clicked.connect(self.cmd_manager.undo)
        undo_btn.clicked.connect(self.update_count)
        
        redo_btn = QPushButton("Redo")
        redo_btn.setMinimumWidth(100)
        redo_btn.clicked.connect(self.cmd_manager.redo)
        redo_btn.clicked.connect(self.update_count)
        
        btn_layout.addStretch()
        btn_layout.addWidget(undo_btn)
        btn_layout.addWidget(redo_btn)
        btn_layout.addStretch()
        
        # Connect signals for command count update
        self.cmd_manager.add_after_execute_callback("demo", self.update_count)
        self.cmd_manager.add_after_undo_callback("demo", self.update_count)
    
    def update_count(self, *args):
        """Update the command count display."""
        count = len(self.cmd_manager._history.get_executed_commands())
        undo_count = len(self.cmd_manager._history._undone_commands)
        
        self.count_label.setText(f"Command History: {count} commands (Undo stack: {undo_count})")
        
        # Update window title with current values
        self.setWindowTitle(f"Command Demo - {self.person.name}, {self.person.email}, {self.person.phone}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SimpleModeDemo()
    demo.show()
    sys.exit(app.exec())