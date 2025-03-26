"""
Simple demo of the PySignalDecipher command system with tab navigation.

This demo shows how the command system can automatically navigate between
tabs during undo/redo operations, making it clear which field changed.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFormLayout, QTabWidget
)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.widgets.line_edit import CommandLineEdit
from command_system.widgets.base_widget import CommandExecutionMode
from command_system.widgets.containers.tab_widget import CommandTabWidget
from command_system.core.widget_context import get_widget_context_registry


class Person(Observable):
    """Simple model with observable properties for a person."""
    # Tab 1 properties
    first_name = ObservableProperty[str]("John")
    last_name = ObservableProperty[str]("Doe")
    
    # Tab 2 properties
    email = ObservableProperty[str]("john.doe@example.com")
    phone = ObservableProperty[str]("555-123-4567")
    
    # Tab 3 properties
    address = ObservableProperty[str]("123 Main St")
    city = ObservableProperty[str]("Anytown")


class TabDemo(QMainWindow):
    """Demo application showing tabs with command-aware widgets."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tab Navigation Demo")
        self.resize(500, 300)
        
        # Create model and command manager
        self.person = Person()
        self.cmd_manager = get_command_manager()
        
        # Set up central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(self, "main_tabs")
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_personal_tab()
        self.create_contact_tab()
        self.create_address_tab()
        
        # Command count and buttons
        self.count_label = QLabel("Commands: 0")
        main_layout.addWidget(self.count_label)
        
        btn_layout = QHBoxLayout()
        main_layout.addLayout(btn_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        
        btn_layout.addWidget(undo_btn)
        btn_layout.addWidget(redo_btn)
        
        # Update UI when commands change
        self.cmd_manager.add_after_execute_callback("demo", self.update_count)
        self.cmd_manager.add_after_undo_callback("demo", self.update_count)
        
    def create_personal_tab(self):
        """Create tab for personal information."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # First name field
        first_name_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_EDIT_END)
        first_name_edit.bind_to_model(self.person, "first_name")
        layout.addRow("First Name:", first_name_edit)
        
        # Last name field
        last_name_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_EDIT_END)
        last_name_edit.bind_to_model(self.person, "last_name")
        layout.addRow("Last Name:", last_name_edit)
        
        self.tab_widget.addTab(tab, "Personal")
        
    def create_contact_tab(self):
        """Create tab for contact information."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Email field
        email_edit = CommandLineEdit(execution_mode=CommandExecutionMode.DELAYED)
        email_edit.bind_to_model(self.person, "email")
        layout.addRow("Email:", email_edit)
        
        # Phone field
        phone_edit = CommandLineEdit(execution_mode=CommandExecutionMode.DELAYED)
        phone_edit.bind_to_model(self.person, "phone")
        layout.addRow("Phone:", phone_edit)
        
        self.tab_widget.addTab(tab, "Contact")
        
    def create_address_tab(self):
        """Create tab for address information."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Address field
        address_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_CHANGE)
        address_edit.bind_to_model(self.person, "address")
        layout.addRow("Address:", address_edit)
        
        # City field
        city_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_CHANGE)
        city_edit.bind_to_model(self.person, "city")
        layout.addRow("City:", city_edit)
        
        self.tab_widget.addTab(tab, "Address")
    
    def update_count(self, *args):
        """Update command count display."""
        if hasattr(self.cmd_manager, "_history") and hasattr(self.cmd_manager._history, "_executed_commands"):
            count = len(self.cmd_manager._history._executed_commands)
            self.count_label.setText(f"Commands: {count}")
            
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up any registrations to prevent memory leaks
        registry = get_widget_context_registry()
        # In a real app, you would unregister all widgets here
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = TabDemo()
    demo.show()
    sys.exit(app.exec())