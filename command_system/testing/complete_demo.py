"""
Simple test for dock system where parameters are children of the dock.
"""
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

# Import from the command system
from command_system import (
    Observable, ObservableProperty, get_command_manager,
    get_project_manager
)
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandCheckBox
)
from command_system.ui.dock import (
    get_dock_manager, ObservableDockWidget,
    CreateDockCommand, DeleteDockCommand
)
from command_system.layout import get_layout_manager


class ParameterModel(Observable):
    """Simple model for a parameter."""
    name = ObservableProperty[str](default="Parameter")
    value = ObservableProperty[int](default=0)
    enabled = ObservableProperty[bool](default=True)
    
    def __init__(self, name="Parameter", value=0, parent=None):
        """Initialize with optional parent."""
        super().__init__(parent)
        self.name = name
        self.value = value


class SimpleDockTest(QMainWindow):
    """Simple test for dock system."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Set up window
        self.setWindowTitle("Simple Dock Test")
        self.setMinimumSize(800, 600)
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.dock_manager = get_dock_manager()
        self.layout_manager = get_layout_manager()
        self.project_manager = get_project_manager()
        
        # Set main window for managers
        self.dock_manager.set_main_window(self)
        self.layout_manager.set_main_window(self)
        
        # Register model type
        self.project_manager.register_model_type("parameter", lambda: ParameterModel())
        
        # Begin initialization
        self.cmd_manager.begin_init()
        
        # Create main parameter
        self.main_param = ParameterModel(name="Main Parameter", value=50)
        
        # Create UI
        self._create_ui()
        
        # Counter for dock IDs
        self.dock_counter = 0
        
        # End initialization
        self.cmd_manager.end_init()
        
    def _create_ui(self):
        """Create the UI."""
        # Central widget
        central = QWidget()
        main_layout = QVBoxLayout(central)
        
        # Parameter controls
        param_group = QGroupBox("Main Parameter")
        param_layout = QVBoxLayout(param_group)
        
        # Name control
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(self.main_param, "name")
        name_layout.addWidget(name_edit)
        param_layout.addLayout(name_layout)
        
        # Value control
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_spin = CommandSpinBox()
        value_spin.setRange(0, 100)
        value_spin.bind_to_model(self.main_param, "value")
        value_layout.addWidget(value_spin)
        param_layout.addLayout(value_layout)
        
        # Enabled control
        enabled_layout = QHBoxLayout()
        enabled_layout.addWidget(QLabel("Enabled:"))
        enabled_check = CommandCheckBox()
        enabled_check.bind_to_model(self.main_param, "enabled")
        enabled_layout.addWidget(enabled_check)
        param_layout.addLayout(enabled_layout)
        
        # Generation info
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("Generation:"))
        gen_layout.addWidget(QLabel(str(self.main_param.get_generation())))
        param_layout.addLayout(gen_layout)
        
        # Add parameter group to main layout
        main_layout.addWidget(param_group)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        # Undo/Redo buttons
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        buttons_layout.addWidget(undo_btn)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        buttons_layout.addWidget(redo_btn)
        
        # Add dock button
        add_dock_btn = QPushButton("Add Dock")
        add_dock_btn.clicked.connect(self._on_add_dock)
        buttons_layout.addWidget(add_dock_btn)
        
        # Save/Open buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._on_open)
        buttons_layout.addWidget(open_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Set central widget
        self.setCentralWidget(central)
        
    def _create_dock(self):
        """Create a dock with parameters as children of the dock."""
        # Increment dock counter
        self.dock_counter += 1
        
        # Create unique ID
        dock_id = f"dock_{self.dock_counter}"
        
        # Create dock model (will be the parent)
        dock_model = ParameterModel(
            name=f"Dock {self.dock_counter}", 
            value=25
        )
        
        # Create parameter models that are children of the dock
        param1 = ParameterModel(
            name=f"Parameter 1", 
            value=10, 
            parent=dock_model
        )
        
        param2 = ParameterModel(
            name=f"Parameter 2", 
            value=20, 
            parent=dock_model
        )
        
        param3 = ParameterModel(
            name=f"Parameter 3", 
            value=30, 
            parent=dock_model
        )
        
        # Create dock content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Dock label
        layout.addWidget(QLabel(f"Dock Model - Generation {dock_model.get_generation()}"))
        
        # Parameter 1 controls
        param1_group = QGroupBox("Parameter 1")
        param1_layout = QVBoxLayout(param1_group)
        
        # Name control
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(param1, "name")
        name_layout.addWidget(name_edit)
        param1_layout.addLayout(name_layout)
        
        # Value control
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_spin = CommandSpinBox()
        value_spin.setRange(0, 100)
        value_spin.bind_to_model(param1, "value")
        value_layout.addWidget(value_spin)
        param1_layout.addLayout(value_layout)
        
        # Generation info
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("Generation:"))
        gen_layout.addWidget(QLabel(str(param1.get_generation())))
        param1_layout.addLayout(gen_layout)
        
        layout.addWidget(param1_group)
        
        # Parameter 2 controls
        param2_group = QGroupBox("Parameter 2")
        param2_layout = QVBoxLayout(param2_group)
        
        # Name control
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(param2, "name")
        name_layout.addWidget(name_edit)
        param2_layout.addLayout(name_layout)
        
        # Value control
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_spin = CommandSpinBox()
        value_spin.setRange(0, 100)
        value_spin.bind_to_model(param2, "value")
        value_layout.addWidget(value_spin)
        param2_layout.addLayout(value_layout)
        
        # Generation info
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("Generation:"))
        gen_layout.addWidget(QLabel(str(param2.get_generation())))
        param2_layout.addLayout(gen_layout)
        
        layout.addWidget(param2_group)
        
        # Parameter 3 controls
        param3_group = QGroupBox("Parameter 3")
        param3_layout = QVBoxLayout(param3_group)
        
        # Name control
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = CommandLineEdit()
        name_edit.bind_to_model(param3, "name")
        name_layout.addWidget(name_edit)
        param3_layout.addLayout(name_layout)
        
        # Value control
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Value:"))
        value_spin = CommandSpinBox()
        value_spin.setRange(0, 100)
        value_spin.bind_to_model(param3, "value")
        value_layout.addWidget(value_spin)
        param3_layout.addLayout(value_layout)
        
        # Generation info
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("Generation:"))
        gen_layout.addWidget(QLabel(str(param3.get_generation())))
        param3_layout.addLayout(gen_layout)
        
        layout.addWidget(param3_group)
        
        # Create dock with model
        dock = ObservableDockWidget(dock_id, f"Dock {self.dock_counter}", self, dock_model)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Determine dock area based on dock number
        area = Qt.DockWidgetArea.RightDockWidgetArea
        if self.dock_counter % 3 == 0:
            area = Qt.DockWidgetArea.LeftDockWidgetArea
        elif self.dock_counter % 3 == 2:
            area = Qt.DockWidgetArea.BottomDockWidgetArea
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        return dock
        
    def _on_add_dock(self):
        """Handle add dock button click."""
        self._create_dock()
        
    def _on_dock_close_requested(self, dock_id):
        """Handle dock close request."""
        cmd = DeleteDockCommand(dock_id)
        self.cmd_manager.execute(cmd)
        
    def _on_save(self):
        """Handle save button click."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json)"
        )
        
        if filename:
            if not filename.lower().endswith(".json"):
                filename += ".json"
                
            # Save project with layout
            success = self.project_manager.save_project(
                self.main_param, filename, save_layout=True
            )
            
            if success:
                self.statusBar().showMessage(f"Project saved to {filename}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save the project")
                
    def _on_open(self):
        """Handle open button click."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "JSON Files (*.json)"
        )
        
        if filename:
            # Load project with layout
            loaded_model = self.project_manager.load_project(
                filename, load_layout=True
            )
            
            if loaded_model:
                # Update our main parameter
                self.main_param = loaded_model
                
                # Rebind main parameter widgets
                # In a real app, you'd need to handle child models properly
                
                self.statusBar().showMessage(f"Project loaded from {filename}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load the project")


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    window = SimpleDockTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()