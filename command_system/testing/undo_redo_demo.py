"""
Minimal demo of the PySignalDecipher command system with different command execution modes.
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
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.widgets.line_edit import CommandLineEdit
from command_system.widgets.base_widget import CommandExecutionMode


class Person(Observable):
    """Simple model with observable properties."""
    name = ObservableProperty[str]("John Doe")
    email = ObservableProperty[str]("john@example.com")
    phone = ObservableProperty[str]("123-456-7890")


class SimpleModeDemo(QMainWindow):
    """Minimal demo of command execution modes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Demo")
        self.resize(400, 200)
        
        # Create model and get command manager
        self.person = Person()
        self.cmd_manager = get_command_manager()
        
        # Setup UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Form layout for edit fields
        form = QFormLayout()
        layout.addLayout(form)
        
        # Three line edits with different modes
        self.edit1 = CommandLineEdit(execution_mode=CommandExecutionMode.ON_CHANGE)
        self.edit1.bind_to_model(self.person, "name")
        form.addRow("On Change:", self.edit1)
        
        self.edit2 = CommandLineEdit(execution_mode=CommandExecutionMode.DELAYED)
        self.edit2.bind_to_model(self.person, "email")
        form.addRow("Delayed:", self.edit2)
        
        self.edit3 = CommandLineEdit(execution_mode=CommandExecutionMode.ON_EDIT_END)
        self.edit3.bind_to_model(self.person, "phone")
        form.addRow("On Edit End:", self.edit3)
        
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
        if hasattr(self.cmd_manager, "_history") and hasattr(self.cmd_manager._history, "_executed_commands"):
            count = len(self.cmd_manager._history._executed_commands)
            self.count_label.setText(f"Commands: {count}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SimpleModeDemo()
    demo.show()
    sys.exit(app.exec())