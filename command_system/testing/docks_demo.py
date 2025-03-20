"""
Simple demonstration of the dock management system with undo/redo functionality.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, QSize

# Import from the command system
from command_system import Observable, ObservableProperty, get_command_manager
from command_system.ui.dock import (
    get_dock_manager, CommandDockWidget, ObservableDockWidget,
    CreateDockCommand, DeleteDockCommand
)
from command_system.ui.widgets import CommandLineEdit, CommandSpinBox


class SimpleModel(Observable):
    """Simple model for the demo."""
    name = ObservableProperty[str](default="Untitled")
    value = ObservableProperty[int](default=0)


class DocksDemoWindow(QMainWindow):
    """Main window for the docks demo."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Docks Demo")
        self.setMinimumSize(800, 600)
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.dock_manager = get_dock_manager()
        
        # Begin initialization - disable command tracking
        self.cmd_manager.begin_init()
        
        # Set dock manager's main window
        self.dock_manager.set_main_window(self)
        
        # Create UI
        self._create_ui()
        
        # Initialize dock counter
        self.dock_counter = 0
        
        # End initialization - re-enable command tracking
        self.cmd_manager.end_init()
        
    def _create_ui(self):
        """Create the UI elements."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Controls at top
        controls_layout = QHBoxLayout()
        
        # Add dock button
        self.add_dock_btn = QPushButton("Add New Dock")
        self.add_dock_btn.clicked.connect(self._on_add_dock)
        controls_layout.addWidget(self.add_dock_btn)
        
        # Undo button
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._on_undo)
        controls_layout.addWidget(self.undo_btn)
        
        # Redo button
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self._on_redo)
        controls_layout.addWidget(self.redo_btn)
        
        # Status label
        self.status_label = QLabel("Ready")
        controls_layout.addWidget(self.status_label)
        
        main_layout.addLayout(controls_layout)
        
        # Info area
        info_group = QGroupBox("Docks Information")
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        main_layout.addWidget(info_group)
        
        # Set main widget
        self.setCentralWidget(main_widget)
        
        # Initialize with some docks
        self._create_initial_docks()
        
        # Update buttons
        self._update_buttons()
        
    def _create_initial_docks(self):
        """Create initial dock widgets to demonstrate functionality."""
        # First dock - text editor
        text_dock = self._create_text_dock("left_dock", "Text Editor", Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Second dock - parameters
        params_dock = self._create_params_dock("right_dock", "Parameters", Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Update status
        self._update_dock_info()
        
    def _create_text_dock(self, dock_id, title, area):
        """Create a text editor dock."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Add a text edit
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        # Create dock
        dock = CommandDockWidget(dock_id, title, self)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        return dock
        
    def _create_params_dock(self, dock_id, title, area):
        """Create a parameters dock with observable properties."""
        # Create model
        model = SimpleModel()
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Name field
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(model, "name")
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # Value field
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_spin = CommandSpinBox()
        value_spin.setRange(0, 100)
        value_spin.bind_to_model(model, "value")
        value_layout.addWidget(value_spin)
        layout.addLayout(value_layout)
        
        # Create dock with model
        dock = ObservableDockWidget(dock_id, title, self, model)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        # Watch for model changes
        model.add_property_observer("name", self._on_model_changed)
        model.add_property_observer("value", self._on_model_changed)
        
        return dock
        
    def _on_add_dock(self):
        """Handle add dock button click."""
        # Generate a unique ID for the new dock
        self.dock_counter += 1
        dock_id = f"dock_{self.dock_counter}"
        
        # Alternate between text and params docks
        if self.dock_counter % 2 == 0:
            dock = self._create_text_dock(dock_id, f"Text Editor {self.dock_counter}", 
                                         Qt.DockWidgetArea.RightDockWidgetArea)
        else:
            dock = self._create_params_dock(dock_id, f"Parameters {self.dock_counter}",
                                           Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Update status
        self.status_label.setText(f"Added new dock: {dock_id}")
        self._update_dock_info()
        self._update_buttons()
        
    def _on_dock_close_requested(self, dock_id):
        """Handle dock close request."""
        # Get the dock
        dock = self.dock_manager.get_dock_widget(dock_id)
        
        if dock:
            # Create and execute command to delete dock
            cmd = DeleteDockCommand(dock_id)
            self.cmd_manager.execute(cmd)
            
            # Update status
            self.status_label.setText(f"Deleted dock: {dock_id}")
            self._update_dock_info()
            self._update_buttons()
        
    def _on_undo(self):
        """Handle undo button click."""
        if self.cmd_manager.undo():
            self.status_label.setText("Undo: Success")
        else:
            self.status_label.setText("Undo: Nothing to undo")
            
        self._update_dock_info()
        self._update_buttons()
        
    def _on_redo(self):
        """Handle redo button click."""
        if self.cmd_manager.redo():
            self.status_label.setText("Redo: Success")
        else:
            self.status_label.setText("Redo: Nothing to redo")
            
        self._update_dock_info()
        self._update_buttons()
        
    def _on_model_changed(self, property_name, old_value, new_value):
        """Handle model property changes."""
        self.status_label.setText(f"Model changed: {property_name} = {new_value}")
        self._update_buttons()
        
    def _update_dock_info(self):
        """Update the dock information display."""
        # Get all dock IDs
        dock_ids = list(self.dock_manager._dock_states.keys())
        
        # Build info text
        info = "Current Docks:\n\n"
        
        for dock_id in dock_ids:
            dock_data = self.dock_manager._dock_states[dock_id]
            dock_widget = dock_data["widget"]
            
            info += f"Dock ID: {dock_id}\n"
            info += f"  Title: {dock_widget.windowTitle()}\n"
            info += f"  Floating: {dock_widget.isFloating()}\n"
            info += f"  Visible: {dock_widget.isVisible()}\n"
            
            # Add model info if available
            model = dock_data.get("model")
            if model:
                info += "  Model:\n"
                for attr_name in dir(model.__class__):
                    attr = getattr(model.__class__, attr_name)
                    if isinstance(attr, ObservableProperty):
                        value = getattr(model, attr_name)
                        info += f"    {attr_name}: {value}\n"
            
            info += "\n"
        
        self.info_text.setText(info)
        
    def _update_buttons(self):
        """Update button states."""
        self.undo_btn.setEnabled(self.cmd_manager.can_undo())
        self.redo_btn.setEnabled(self.cmd_manager.can_redo())
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Accept the close
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = DocksDemoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()