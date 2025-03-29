"""
Simple demo for selective tab closability.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel
)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.widgets.line_edit import CommandLineEdit
from command_system.widgets.containers.tab_widget import CommandTabWidget


class Person(Observable):
    """Simple person model with observable properties."""
    name = ObservableProperty[str]("John Doe")
    email = ObservableProperty[str]("john@example.com")
    address = ObservableProperty[str]("123 Main St")


class SimpleTabsDemo(QMainWindow):
    """Demo of dynamic tabs with command system integration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Dynamic Tabs Demo")
        self.resize(500, 300)
        
        # Create model and command manager
        self.person = Person()
        self.cmd_manager = get_command_manager()
        
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(self)
        # Enable tab close buttons for all tabs
        layout.addWidget(self.tab_widget)
        
        # Register tab types with different closability
        self.closable_tab_type = self.tab_widget.register_tab(
            self.create_closable_tab,
            tab_name="Closable Tab",
            dynamic=True,
            closable=True
        )
        
        self.non_closable_tab_type = self.tab_widget.register_tab(
            self.create_non_closable_tab,
            tab_name="Non-Closable Tab",
            dynamic=True,
            closable=False
        )
        
        self.welcome_tab = self.tab_widget.register_tab(
            self.add_welcome_tab,
            tab_name="Welcome",
            dynamic=True,
            closable=False
        )
        
        # Create buttons for adding tabs
        tab_btn_layout = QHBoxLayout()
        layout.addLayout(tab_btn_layout)
        
        add_closable_btn = QPushButton("Add Closable Tab")
        add_closable_btn.clicked.connect(self.add_closable_tab)
        
        add_non_closable_btn = QPushButton("Add Non-Closable Tab")
        add_non_closable_btn.clicked.connect(self.add_non_closable_tab)
        
        tab_btn_layout.addWidget(add_closable_btn)
        tab_btn_layout.addWidget(add_non_closable_btn)
        
        # Create undo/redo buttons
        cmd_btn_layout = QHBoxLayout()
        layout.addLayout(cmd_btn_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        
        cmd_btn_layout.addWidget(undo_btn)
        cmd_btn_layout.addWidget(redo_btn)
        
        # Add initial welcome tab
        self.tab_widget.add_tab(self.welcome_tab)
    
    def create_closable_tab(self):
        """Create content for a closable tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label explaining tab type
        label = QLabel("This is a closable tab.\nYou can close this tab with the X button.")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Add an editable field to test undo/redo
        name_label = QLabel("Edit this field and use undo/redo:")
        layout.addWidget(name_label)
        
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(self.person, "name")
        layout.addWidget(name_edit)
        
        return widget
    
    def create_non_closable_tab(self):
        """Create content for a non-closable tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label explaining tab type
        label = QLabel("This is a non-closable tab.\nThe X button is disabled for this tab.")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Add an editable field to test undo/redo
        email_label = QLabel("Edit this field and use undo/redo:")
        layout.addWidget(email_label)
        
        email_edit = CommandLineEdit()
        email_edit.bind_to_model(self.person, "email")
        layout.addWidget(email_edit)
        
        return widget
    
    def add_welcome_tab(self):
        """Add a welcome tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(
            "Welcome to the Tab Closability Demo\n\n"
            "This demo shows how to create tabs with different closability settings.\n"
            "- Closable tabs allow you to click the X button\n"
            "- Non-closable tabs ignore clicks on the X button\n\n"
            "Use the buttons below to add different types of tabs."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Add the tab directly (not using the dynamic system)
        return widget
    
    def add_closable_tab(self):
        """Add a closable tab."""
        self.tab_widget.add_tab(self.closable_tab_type)
    
    def add_non_closable_tab(self):
        """Add a non-closable tab."""
        self.tab_widget.add_tab(self.non_closable_tab_type)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SimpleTabsDemo()
    demo.show()
    sys.exit(app.exec())