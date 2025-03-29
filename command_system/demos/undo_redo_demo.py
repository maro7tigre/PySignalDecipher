"""
Minimal demo of the PySignalDecipher command system with different command trigger modes.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFormLayout
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core import Observable, ObservableProperty, get_command_manager
from command_system.pyside6_widgets import CommandLineEdit, CommandTriggerMode

class Person(Observable):
    """Simple model with observable properties."""
    name = ObservableProperty("")
    email = ObservableProperty("")
    phone = ObservableProperty("")
    
    def __init__(self):
        super().__init__()
        self.name = "John Doe"
        self.email = "john@example.com"
        self.phone = "123-456-7890"

class SimpleModeDemo(QMainWindow):
    """Minimal demo of command trigger modes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Demo")
        self.resize(400, 200)
        
        # Create model and get command manager
        self.person = Person()
        self.person_id = self.person.get_id()  # Get ID directly
        self.cmd_manager = get_command_manager()
        
        # Setup UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Form layout for edit fields
        form = QFormLayout()
        layout.addLayout(form)
        
        # Three line edits with different modes
        self.edit1 = CommandLineEdit()
        self.edit1.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        self.edit1.bind_to_text_property(self.person_id, "name")
        form.addRow("Immediate:", self.edit1)
        
        self.edit2 = CommandLineEdit()
        self.edit2.set_command_trigger_mode(CommandTriggerMode.DELAYED)
        self.edit2.bind_to_text_property(self.person_id, "email")
        form.addRow("Delayed:", self.edit2)
        
        self.edit3 = CommandLineEdit()
        self.edit3.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        self.edit3.bind_to_text_property(self.person_id, "phone")
        form.addRow("On Edit Finished:", self.edit3)
        
        # Command count
        self.count_label = QLabel("Commands: 0")
        layout.addWidget(self.count_label)
        
        # Undo/redo buttons
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        
        btn_layout.addWidget(undo_btn)
        btn_layout.addWidget(redo_btn)
        
        # Update UI when commands change
        self.cmd_manager.add_after_execute_callback("demo", self.update_count)
        self.cmd_manager.add_after_undo_callback("demo", self.update_count)
        
    def update_count(self, *args):
        """Update command count display."""
        count = len(self.cmd_manager._history.get_executed_commands())
        self.count_label.setText(f"Commands: {count}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SimpleModeDemo()
    demo.show()
    sys.exit(app.exec())