"""
Improved demo for the simplified command system container architecture.

This demo showcases the registration and instantiation pattern with
full undo/redo support for tab operations, using both existing observables
and dynamic observable creation. Also includes command count tracking.
"""
import sys
import os
from typing import Type, Union, List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QStatusBar
)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.pyside6_widgets.line_edit import CommandLineEdit
from command_system.pyside6_widgets.containers.tab_widget import CommandTabWidget


class Person(Observable):
    """Simple person model with observable properties."""
    name = ObservableProperty("John Doe")
    email = ObservableProperty("john@example.com")


class ImprovedTabsDemo(QMainWindow):
    """Demo of the improved container system with registration pattern."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Tabs Demo")
        self.resize(600, 400)
        
        # Create shared model
        self.person = Person()
        self.cmd_manager = get_command_manager()
        self.cmd_manager._is_initializing = True
        # Set up UI
        self.setup_ui()
        
        # Register tab types
        self.register_tab_types()
        
        # Add initial welcome tab
        self.tab_widget.add_tab(self.welcome_tab_id)
        
        # Set up command tracking
        self.cmd_manager.add_after_execute_callback("tabs_demo", self.update_command_count)
        self.cmd_manager.add_after_undo_callback("tabs_demo", self.update_command_count)
        
        # Initialize command count display
        self.update_command_count()
        
        self.cmd_manager._is_initializing = False
    
    def setup_ui(self):
        """Set up the user interface."""
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(self)
        layout.addWidget(self.tab_widget)
        
        # Create buttons for adding tabs
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add buttons
        shared_btn = QPushButton("Add Tab with Shared Model")
        shared_btn.clicked.connect(self.add_shared_model_tab)
        button_layout.addWidget(shared_btn)
        
        new_btn = QPushButton("Add Tab with New Model")
        new_btn.clicked.connect(self.add_new_model_tab)
        button_layout.addWidget(new_btn)
        
        non_closable_btn = QPushButton("Add Non-Closable Tab")
        non_closable_btn.clicked.connect(self.add_non_closable_tab)
        button_layout.addWidget(non_closable_btn)
        
        # Create undo/redo buttons
        undo_redo_layout = QHBoxLayout()
        layout.addLayout(undo_redo_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        undo_redo_layout.addWidget(undo_btn)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        undo_redo_layout.addWidget(redo_btn)
        
        # Create command count label
        self.count_label = QLabel("Commands: 0")
        undo_redo_layout.addWidget(self.count_label)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def register_tab_types(self):
        """Register all tab types."""
        # Register welcome tab (no observables needed)
        self.welcome_tab_id = self.tab_widget.register_tab(
            self.create_welcome_tab,
            tab_name="Welcome",
            observables=[],
            closable=False
        )
        
        # Register tab that uses an existing observable (shared model)
        self.shared_model_tab_id = self.tab_widget.register_tab(
            self.create_model_tab,
            tab_name="Shared Model Tab",
            observables=[self.person.get_id()],  # Pass the ID of existing observable
            closable=True
        )
        
        # Register tab that creates a new observable instance each time
        self.new_model_tab_id = self.tab_widget.register_tab(
            self.create_model_tab,
            tab_name="New Model Tab",
            observables=[Person],  # Pass the Person class to create new instances
            closable=True
        )
        
        # Register non-closable tab with shared model
        self.non_closable_tab_id = self.tab_widget.register_tab(
            self.create_model_tab,
            tab_name="Non-Closable Tab",
            observables=[self.person.get_id()],
            closable=False
        )
    
    def create_welcome_tab(self):
        """Create welcome tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(
            "Welcome to the Improved Container System Demo\n\n"
            "This demo showcases our improved container architecture with:\n"
            "• Observable registration and instantiation\n"
            "• Both shared and per-tab observable instances\n"
            "• Full undo/redo support for all operations\n"
            "• Selective tab closability\n"
            "• Command history tracking\n\n"
            "Try out the buttons below to add different types of tabs."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        info_label = QLabel(
            "About the tabs:\n"
            "- Shared Model Tab: Uses a single shared observable across all tabs\n"
            "- New Model Tab: Creates a new observable instance for each tab\n"
            "- Non-Closable Tab: Cannot be closed with the close button\n\n"
            "The command count at the bottom shows the number of commands in the history."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return widget
    
    def create_model_tab(self, model):
        """
        Create content for a tab with a model.
        
        Args:
            model: Observable instance (either shared or newly created)
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Show model ID to demonstrate shared vs new instances
        id_label = QLabel(f"Model ID: {model.get_id()}")
        layout.addWidget(id_label)
        
        # Add editable fields bound to the model
        name_label = QLabel("Name:")
        layout.addWidget(name_label)
        
        name_edit = CommandLineEdit()
        # Using the bind_property method from the updated widget system
        name_edit.bind_to_text_property(model.get_id(), "name")
        layout.addWidget(name_edit)
        
        email_label = QLabel("Email:")
        layout.addWidget(email_label)
        
        email_edit = CommandLineEdit()
        # Using the bind_property method from the updated widget system
        email_edit.bind_to_text_property(model.get_id(), "email")
        layout.addWidget(email_edit)
        
        # Info about this tab
        if model.get_id() == self.person.get_id():
            info = QLabel("This tab uses the shared model. Changes here affect all shared model tabs.")
        else:
            info = QLabel("This tab uses its own model instance. Changes here only affect this tab.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        return widget
    
    def add_shared_model_tab(self):
        """Add a tab that uses the shared model."""
        tab_id = self.tab_widget.add_tab(self.shared_model_tab_id)
        self.statusBar.showMessage(f"Added shared model tab (ID: {tab_id})")
    
    def add_new_model_tab(self):
        """Add a tab with a new model instance."""
        tab_id = self.tab_widget.add_tab(self.new_model_tab_id)
        self.statusBar.showMessage(f"Added new model tab (ID: {tab_id})")
    
    def add_non_closable_tab(self):
        """Add a non-closable tab with the shared model."""
        tab_id = self.tab_widget.add_tab(self.non_closable_tab_id)
        self.statusBar.showMessage(f"Added non-closable tab (ID: {tab_id})")
    
    def update_command_count(self, *args):
        """Update command count display in the UI."""
        count = len(self.cmd_manager._history.get_executed_commands())
        self.count_label.setText(f"Commands: {count}")
        
        # Update status bar with undo/redo availability
        if self.cmd_manager.can_undo():
            undo_cmd = self.cmd_manager._history._executed_commands[-1]
            undo_msg = f"Can undo ({undo_cmd.__class__.__name__})"
        else:
            undo_msg = "Cannot undo"
            
        if self.cmd_manager.can_redo():
            redo_cmd = self.cmd_manager._history._undone_commands[-1]
            redo_msg = f"Can redo ({redo_cmd.__class__.__name__})"
        else:
            redo_msg = "Cannot redo"
            
        self.statusBar.showMessage(f"{undo_msg} | {redo_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = ImprovedTabsDemo()
    demo.show()
    sys.exit(app.exec())