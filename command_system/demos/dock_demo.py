"""
Demo for the dock widget system with command-enabled functionality.

This demo showcases the dock registration and instantiation pattern with
full undo/redo support for dock operations, using both existing observables
and dynamic observable creation. Also includes command count tracking.
"""
import sys
import os
from typing import Type, Union, List
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QStatusBar,
    QLineEdit, QTextEdit, QMainWindow, QSlider
)
from PySide6.QtCore import Qt

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.pyside6_widgets.line_edit import CommandLineEdit
from command_system.pyside6_widgets.containers.dock_widget import CommandDockWidget, DockArea


class Person(Observable):
    """Simple person model with observable properties."""
    name = ObservableProperty("John Doe")
    email = ObservableProperty("john@example.com")
    notes = ObservableProperty("Additional notes about this person")


class Project(Observable):
    """Project model with observable properties."""
    title = ObservableProperty("New Project")
    description = ObservableProperty("Project description")
    priority = ObservableProperty(5)  # 1-10 scale


class DockWidgetDemo(QMainWindow):
    """Demo of the dock widget system with registration pattern."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dock Widget Demo")
        self.resize(1000, 700)
        
        # Create shared models
        self.person = Person()
        self.project = Project()
        
        # Get command manager
        self.cmd_manager = get_command_manager()
        self.cmd_manager._is_initializing = True
        
        # Set up UI
        self.setup_ui()
        
        # Register dock types
        self.register_dock_types()
        
        # Add initial docks
        self.dock_widget.add_dock(self.info_dock_id)
        
        # Set up command tracking
        self.cmd_manager.add_after_execute_callback("docks_demo", self.update_command_count)
        self.cmd_manager.add_after_undo_callback("docks_demo", self.update_command_count)
        
        # Initialize command count display
        self.update_command_count()
        
        self.cmd_manager._is_initializing = False
    
    def setup_ui(self):
        """Set up the user interface."""
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create dock widget container
        self.dock_widget = CommandDockWidget(self)
        layout.addWidget(self.dock_widget)
        
        # Create buttons for adding docks
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add buttons for different types of docks
        person_dock_btn = QPushButton("Add Person Dock")
        person_dock_btn.clicked.connect(self.add_person_dock)
        button_layout.addWidget(person_dock_btn)
        
        project_dock_btn = QPushButton("Add Project Dock")
        project_dock_btn.clicked.connect(self.add_project_dock)
        button_layout.addWidget(project_dock_btn)
        
        new_person_dock_btn = QPushButton("Add New Person Dock")
        new_person_dock_btn.clicked.connect(self.add_new_person_dock)
        button_layout.addWidget(new_person_dock_btn)
        
        floating_dock_btn = QPushButton("Add Floating Dock")
        floating_dock_btn.clicked.connect(self.add_floating_dock)
        button_layout.addWidget(floating_dock_btn)
        
        # Create buttons for specific areas
        area_layout = QHBoxLayout()
        layout.addLayout(area_layout)
        
        left_dock_btn = QPushButton("Add Left Dock")
        left_dock_btn.clicked.connect(self.add_left_dock)
        area_layout.addWidget(left_dock_btn)
        
        right_dock_btn = QPushButton("Add Right Dock")
        right_dock_btn.clicked.connect(self.add_right_dock)
        area_layout.addWidget(right_dock_btn)
        
        top_dock_btn = QPushButton("Add Top Dock")
        top_dock_btn.clicked.connect(self.add_top_dock)
        area_layout.addWidget(top_dock_btn)
        
        bottom_dock_btn = QPushButton("Add Bottom Dock")
        bottom_dock_btn.clicked.connect(self.add_bottom_dock)
        area_layout.addWidget(bottom_dock_btn)
        
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
    
    def register_dock_types(self):
        """Register all dock types."""
        # Register info dock (no observables needed)
        self.info_dock_id = self.dock_widget.register_dock(
            self.create_info_dock,
            dock_title="Information",
            observables=[],
            closable=False,
            default_area=DockArea.TOP
        )
        
        # Register person dock with shared model
        self.person_dock_id = self.dock_widget.register_dock(
            self.create_person_dock,
            dock_title="Person Details",
            observables=[self.person.get_id()],
            closable=True,
            default_area=DockArea.LEFT
        )
        
        # Register project dock with shared model
        self.project_dock_id = self.dock_widget.register_dock(
            self.create_project_dock,
            dock_title="Project Details",
            observables=[self.project.get_id()],
            closable=True,
            default_area=DockArea.RIGHT
        )
        
        # Register new person dock that creates a new model instance
        self.new_person_dock_id = self.dock_widget.register_dock(
            self.create_person_dock,
            dock_title="New Person",
            observables=[Person],  # Pass the Person class to create new instances
            closable=True,
            default_area=DockArea.BOTTOM
        )
        
        # Register floating dock with unique content
        self.floating_dock_id = self.dock_widget.register_dock(
            self.create_floating_dock,
            dock_title="Floating Dock",
            observables=[],
            closable=True,
            floating=True,
            default_area=DockArea.RIGHT
        )
    
    def create_info_dock(self):
        """Create info dock content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(
            "Dock Widget System Demo\n\n"
            "This demo showcases the dock widget system with:\n"
            "• Dock registration and instantiation\n"
            "• Both shared and per-dock observable instances\n"
            "• Full undo/redo support for all operations\n"
            "• Docks at different positions and areas\n"
            "• Floating and non-closable docks\n"
            "• Command tracking for all actions\n\n"
            "Try adding different docks, moving them around, and using undo/redo."
        )
        label.setWordWrap(True)
        layout.addWidget(label)
        
        info_label = QLabel(
            "The dock system automatically tracks:\n"
            "- Dock positions and areas\n"
            "- Floating state changes\n"
            "- Dock visibility\n"
            "- Content changes within docks\n\n"
            "All changes are captured for undo/redo with a 500ms delay after position changes settle."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return widget
    
    def create_person_dock(self, model):
        """
        Create content for a person dock.
        
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
        name_edit.bind_to_text_property(model.get_id(), "name")
        layout.addWidget(name_edit)
        
        email_label = QLabel("Email:")
        layout.addWidget(email_label)
        
        email_edit = CommandLineEdit()
        email_edit.bind_to_text_property(model.get_id(), "email")
        layout.addWidget(email_edit)
        
        notes_label = QLabel("Notes:")
        layout.addWidget(notes_label)
        
        notes_edit = QTextEdit()
        notes_edit.setPlainText(model.notes)
        notes_edit.textChanged.connect(lambda: self.update_notes(model, notes_edit))
        layout.addWidget(notes_edit)
        
        # Info about this dock
        if model.get_id() == self.person.get_id():
            info = QLabel("This dock uses the shared Person model. Changes here affect all Person docks.")
        else:
            info = QLabel("This dock uses its own Person model instance. Changes here only affect this dock.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        return widget
    
    def create_project_dock(self, model):
        """
        Create content for a project dock.
        
        Args:
            model: Observable instance
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Show model ID
        id_label = QLabel(f"Project Model ID: {model.get_id()}")
        layout.addWidget(id_label)
        
        # Add editable fields bound to the model
        title_label = QLabel("Project Title:")
        layout.addWidget(title_label)
        
        title_edit = CommandLineEdit()
        title_edit.bind_to_text_property(model.get_id(), "title")
        layout.addWidget(title_edit)
        
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        desc_edit = QTextEdit()
        desc_edit.setPlainText(model.description)
        desc_edit.textChanged.connect(lambda: self.update_description(model, desc_edit))
        layout.addWidget(desc_edit)
        
        priority_label = QLabel(f"Priority: {model.priority}")
        layout.addWidget(priority_label)
        
        priority_slider = QSlider(Qt.Horizontal)
        priority_slider.setMinimum(1)
        priority_slider.setMaximum(10)
        priority_slider.setValue(model.priority)
        priority_slider.valueChanged.connect(lambda v: self.update_priority(model, v, priority_label))
        layout.addWidget(priority_slider)
        
        return widget
    
    def create_floating_dock(self):
        """Create content for a floating dock."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("This is a floating dock that can be moved freely around the screen.")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        info = QLabel(
            "The dock system tracks floating state changes and will create commands when:\n"
            "• A dock is moved between different areas\n"
            "• A dock is changed between docked and floating states\n"
            "• A dock's position or size is changed\n\n"
            "Commands are created 500ms after the changes settle to avoid creating too many commands."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        note = QLabel("Try moving this dock around and then using undo/redo to see how position is restored.")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        return widget
    
    def update_notes(self, model, notes_edit):
        """Update the notes property of a Person model."""
        # Only create commands when not already updating
        if not self.cmd_manager.is_updating():
            new_text = notes_edit.toPlainText()
            if model.notes != new_text:
                property_id = model._get_property_id("notes")
                self.cmd_manager.execute_property_command(property_id, new_text)
    
    def update_description(self, model, desc_edit):
        """Update the description property of a Project model."""
        # Only create commands when not already updating
        if not self.cmd_manager.is_updating():
            new_text = desc_edit.toPlainText()
            if model.description != new_text:
                property_id = model._get_property_id("description")
                self.cmd_manager.execute_property_command(property_id, new_text)
    
    def update_priority(self, model, value, label):
        """Update the priority property of a Project model."""
        # Only create commands when not already updating
        if not self.cmd_manager.is_updating():
            if model.priority != value:
                property_id = model._get_property_id("priority")
                self.cmd_manager.execute_property_command(property_id, value)
                label.setText(f"Priority: {value}")
    
    def add_person_dock(self):
        """Add a person dock with the shared model."""
        dock_id = self.dock_widget.add_dock(self.person_dock_id)
        self.statusBar.showMessage(f"Added person dock (ID: {dock_id})")
    
    def add_project_dock(self):
        """Add a project dock with the shared model."""
        dock_id = self.dock_widget.add_dock(self.project_dock_id)
        self.statusBar.showMessage(f"Added project dock (ID: {dock_id})")
    
    def add_new_person_dock(self):
        """Add a dock with a new Person model instance."""
        dock_id = self.dock_widget.add_dock(self.new_person_dock_id)
        self.statusBar.showMessage(f"Added new person dock (ID: {dock_id})")
    
    def add_floating_dock(self):
        """Add a floating dock."""
        dock_id = self.dock_widget.add_dock(self.floating_dock_id)
        self.statusBar.showMessage(f"Added floating dock (ID: {dock_id})")
    
    def add_left_dock(self):
        """Add a person dock to the left area."""
        dock_id = self.dock_widget.add_dock(self.person_dock_id, area=DockArea.LEFT)
        self.statusBar.showMessage(f"Added left dock (ID: {dock_id})")
    
    def add_right_dock(self):
        """Add a project dock to the right area."""
        dock_id = self.dock_widget.add_dock(self.project_dock_id, area=DockArea.RIGHT)
        self.statusBar.showMessage(f"Added right dock (ID: {dock_id})")
    
    def add_top_dock(self):
        """Add a person dock to the top area."""
        dock_id = self.dock_widget.add_dock(self.person_dock_id, area=DockArea.TOP)
        self.statusBar.showMessage(f"Added top dock (ID: {dock_id})")
    
    def add_bottom_dock(self):
        """Add a project dock to the bottom area."""
        dock_id = self.dock_widget.add_dock(self.project_dock_id, area=DockArea.BOTTOM)
        self.statusBar.showMessage(f"Added bottom dock (ID: {dock_id})")
    
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
    demo = DockWidgetDemo()
    demo.show()
    sys.exit(app.exec())