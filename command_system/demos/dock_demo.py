"""
Demo for the command-aware dock widget container system.

This demo showcases the registration and instantiation pattern with
full undo/redo support for dock operations, using both existing observables
and dynamic observable creation. Also includes command count tracking.
"""
import sys
import os
from typing import Type, Union, List
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QStatusBar,
    QToolBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.pyside6_widgets.line_edit import CommandLineEdit
from command_system.pyside6_widgets.text_edit import CommandTextEdit
from command_system.pyside6_widgets.containers.dock_widget import CommandDockWidget


class Task(Observable):
    """Simple task model with observable properties."""
    title = ObservableProperty("New Task")
    description = ObservableProperty("Task description goes here")
    priority = ObservableProperty("Medium")


class DocksDemo(CommandDockWidget):
    """
    Demo of the dock container system with registration pattern.
    
    This demo inherits directly from CommandDockWidget to ensure proper
    dock management, as CommandDockWidget extends QMainWindow.
    """
    
    def __init__(self, parent=None):
        # Initialize as CommandDockWidget (which is a QMainWindow)
        super().__init__(parent)
        
        self.setWindowTitle("Docks Demo")
        self.resize(800, 600)
        
        # Create shared model
        self.task = Task()
        self.cmd_manager = get_command_manager()
        self.cmd_manager._is_initializing = True
        
        # Set up UI
        self.setup_ui()
        
        # Register dock types
        self.register_dock_types()
        
        # Add initial info dock
        self.add_dock(self.info_dock_id)
        
        # Set up command tracking
        self.cmd_manager.add_after_execute_callback("docks_demo", self.update_command_count)
        self.cmd_manager.add_after_undo_callback("docks_demo", self.update_command_count)
        
        # Initialize command count display
        self.update_command_count()
        
        self.cmd_manager._is_initializing = False
    
    def setup_ui(self):
        """Set up the user interface."""
        # Create central widget with welcome content
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        central_layout = QVBoxLayout(self.central_widget)
        
        # Add welcome content
        welcome_label = QLabel(
            "<h1>Welcome to the Dock Container Demo</h1>"
            "<p>This demo showcases the command-aware dock widget system with:</p>"
            "<ul>"
            "<li>Observable registration and instantiation</li>"
            "<li>Both shared and per-dock observable instances</li>"
            "<li>Full undo/redo support for all operations</li>"
            "<li>Selective dock closability</li>"
            "<li>Floating dock support</li>"
            "<li>Command history tracking</li>"
            "</ul>"
            "<p>Use the buttons or toolbar to add different types of docks.</p>"
        )
        welcome_label.setTextFormat(Qt.TextFormat.RichText)
        welcome_label.setWordWrap(True)
        central_layout.addWidget(welcome_label)
        
        # Create toolbar
        toolbar = QToolBar("Dock Controls")
        self.addToolBar(toolbar)
        
        # Add dock actions
        shared_action = QAction("Add Shared Model Dock", self)
        shared_action.triggered.connect(self.add_shared_model_dock)
        toolbar.addAction(shared_action)
        
        new_action = QAction("Add New Model Dock", self)
        new_action.triggered.connect(self.add_new_model_dock)
        toolbar.addAction(new_action)
        
        floating_action = QAction("Add Floating Dock", self)
        floating_action.triggered.connect(self.add_floating_dock)
        toolbar.addAction(floating_action)
        
        non_closable_action = QAction("Add Non-Closable Dock", self)
        non_closable_action.triggered.connect(self.add_non_closable_dock)
        toolbar.addAction(non_closable_action)
        
        toolbar.addSeparator()
        
        # Add undo/redo actions
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.cmd_manager.undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.cmd_manager.redo)
        toolbar.addAction(redo_action)
        
        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create dock buttons
        shared_btn = QPushButton("Add Shared Dock")
        shared_btn.clicked.connect(self.add_shared_model_dock)
        control_layout.addWidget(shared_btn)
        
        new_btn = QPushButton("Add New Dock")
        new_btn.clicked.connect(self.add_new_model_dock)
        control_layout.addWidget(new_btn)
        
        floating_btn = QPushButton("Add Floating Dock")
        floating_btn.clicked.connect(self.add_floating_dock)
        control_layout.addWidget(floating_btn)
        
        non_closable_btn = QPushButton("Add Non-Closable Dock")
        non_closable_btn.clicked.connect(self.add_non_closable_dock)
        control_layout.addWidget(non_closable_btn)
        
        # Create command count label
        self.count_label = QLabel("Commands: 0")
        control_layout.addWidget(self.count_label)
        
        # Add control panel to central widget
        central_layout.addWidget(control_panel)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def register_dock_types(self):
        """Register all dock types."""
        # Register information dock (no observables needed)
        self.info_dock_id = self.register_dock(
            self.create_info_dock,
            dock_name="Information",
            observables=[],
            closable=False
        )
        
        # Register dock that uses an existing observable (shared model)
        self.shared_model_dock_id = self.register_dock(
            self.create_task_dock,
            dock_name="Shared Task",
            observables=[self.task.get_id()],  # Pass the ID of existing observable
            closable=True
        )
        
        # Register dock that creates a new observable instance each time
        self.new_model_dock_id = self.register_dock(
            self.create_task_dock,
            dock_name="New Task",
            observables=[Task],  # Pass the Task class to create new instances
            closable=True
        )
        
        # Register non-closable dock with shared model
        self.non_closable_dock_id = self.register_dock(
            self.create_task_dock,
            dock_name="Fixed Task",
            observables=[self.task.get_id()],
            closable=False
        )
    
    def create_info_dock(self):
        """Create information dock content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel(
            "<h3>About the docks:</h3>"
            "<ul>"
            "<li><b>Shared Task</b>: Uses a single shared observable across all docks</li>"
            "<li><b>New Task</b>: Creates a new observable instance for each dock</li>"
            "<li><b>Floating Dock</b>: Opens initially as a floating window</li>"
            "<li><b>Fixed Task</b>: Cannot be closed with the close button</li>"
            "</ul>"
            "<p>The command count at the bottom shows the number of commands in the history.</p>"
            "<p>Try undoing and redoing dock operations!</p>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return widget
    
    def create_task_dock(self, task):
        """
        Create content for a dock with a task model.
        
        Args:
            task: Observable instance (either shared or newly created)
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Show model ID to demonstrate shared vs new instances
        id_label = QLabel(f"Model ID: {task.get_id()}")
        layout.addWidget(id_label)
        
        # Add editable fields bound to the model
        title_label = QLabel("Title:")
        layout.addWidget(title_label)
        
        title_edit = CommandLineEdit()
        title_edit.bind_to_text_property(task.get_id(), "title")
        layout.addWidget(title_edit)
        
        description_label = QLabel("Description:")
        layout.addWidget(description_label)
        
        description_edit = CommandTextEdit()
        description_edit.bind_to_plain_text_property(task.get_id(), "description")
        layout.addWidget(description_edit)
        
        priority_label = QLabel("Priority:")
        layout.addWidget(priority_label)
        
        priority_edit = CommandLineEdit()
        priority_edit.bind_to_text_property(task.get_id(), "priority")
        layout.addWidget(priority_edit)
        
        # Info about this dock
        if task.get_id() == self.task.get_id():
            info = QLabel("This dock uses the shared model. Changes here affect all shared model docks.")
        else:
            info = QLabel("This dock uses its own model instance. Changes here only affect this dock.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Add spacer to bottom to make layout nicer
        layout.addStretch()
        
        return widget
    
    def add_shared_model_dock(self):
        """Add a dock that uses the shared model."""
        dock_id = self.add_dock(self.shared_model_dock_id)
        self.statusBar.showMessage(f"Added shared model dock (ID: {dock_id})")
    
    def add_new_model_dock(self):
        """Add a dock with a new model instance."""
        dock_id = self.add_dock(self.new_model_dock_id)
        self.statusBar.showMessage(f"Added new model dock (ID: {dock_id})")
    
    def add_floating_dock(self):
        """Add a floating dock with a shared model."""
        dock_id = self.add_dock(self.shared_model_dock_id, floating=True)
        self.statusBar.showMessage(f"Added floating dock (ID: {dock_id})")
    
    def add_non_closable_dock(self):
        """Add a non-closable dock with the shared model."""
        dock_id = self.add_dock(self.non_closable_dock_id)
        self.statusBar.showMessage(f"Added non-closable dock (ID: {dock_id})")
    
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
    demo = DocksDemo()
    demo.show()
    sys.exit(app.exec())