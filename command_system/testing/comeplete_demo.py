"""
Comprehensive demonstration of the command system.

This demo shows all key features:
- Observable properties
- Command-aware widgets
- Undo/redo functionality
- Dock management
- Layout management
- Project save/load
"""
import sys
import os
from datetime import date
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QGridLayout, QFileDialog,
    QMessageBox, QSplitter, QTabWidget, QMenu, QMenuBar, QStatusBar, QInputDialog
)
from PySide6.QtCore import Qt, QSize

# Import from the command system
from command_system import (
    Observable, ObservableProperty, get_command_manager,
    get_project_manager
)
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandDoubleSpinBox,
    CommandComboBox, CommandCheckBox, CommandSlider,
    CommandDateEdit, CommandTextEdit
)
from command_system.ui.dock import (
    get_dock_manager, CommandDockWidget, ObservableDockWidget,
    CreateDockCommand, DeleteDockCommand
)
from command_system.layout import get_layout_manager, extend_project_manager


class ProjectModel(Observable):
    """Main model for the demonstration project."""
    
    # Text properties
    name = ObservableProperty[str](default="Untitled Project")
    description = ObservableProperty[str](default="")
    
    # Number properties
    priority = ObservableProperty[int](default=3)
    budget = ObservableProperty[float](default=1000.0)
    progress = ObservableProperty[int](default=0)
    
    # Selection properties
    category_index = ObservableProperty[int](default=0)
    is_active = ObservableProperty[bool](default=True)
    
    # Date property
    deadline = ObservableProperty[date](default=date.today())


class ComprehensiveDemo(QMainWindow):
    """Main window for the comprehensive demo."""
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Command System Demo")
        self.setMinimumSize(1000, 700)
        
        # Get all managers
        self.cmd_manager = get_command_manager()
        self.dock_manager = get_dock_manager()
        self.layout_manager = get_layout_manager()
        self.project_manager = get_project_manager()
        
        # Register model types for project manager
        self.project_manager.register_model_type("project", lambda: ProjectModel())
        
        # Set main window for dock and layout managers
        self.dock_manager.set_main_window(self)
        self.layout_manager.set_main_window(self)
        
        # Set layouts directory
        demo_dir = os.path.dirname(os.path.abspath(__file__))
        layouts_dir = os.path.join(demo_dir, "layouts")
        self.layout_manager.set_layouts_directory(layouts_dir)
        
        # Begin initialization (disable command tracking)
        self.cmd_manager.begin_init()
        
        # Create the model
        self.model = ProjectModel()
        
        # Create the UI components
        self._create_menu()
        self._create_status_bar()
        self._create_central_widget()
        self._create_docks()
        
        # Initialize dock counter
        self.dock_counter = 1
        
        # Register widgets with layout manager
        self._register_layout_widgets()
        
        # Connect model observers
        self._connect_model_observers()
        
        # End initialization (re-enable command tracking)
        self.cmd_manager.end_init()
        
        # Update window title
        self._update_window_title()
    
    def _create_menu(self):
        """Create the menu bar."""
        menu_bar = QMenuBar(self)
        
        # File menu
        file_menu = QMenu("&File", self)
        
        new_action = file_menu.addAction("&New")
        new_action.triggered.connect(self._on_new)
        
        open_action = file_menu.addAction("&Open...")
        open_action.triggered.connect(self._on_open)
        
        save_action = file_menu.addAction("&Save")
        save_action.triggered.connect(self._on_save)
        
        save_as_action = file_menu.addAction("Save &As...")
        save_as_action.triggered.connect(self._on_save_as)
        
        file_menu.addSeparator()
        
        # Format submenu
        format_menu = QMenu("File &Format", self)
        
        json_action = format_menu.addAction("&JSON")
        json_action.setCheckable(True)
        json_action.setChecked(self.project_manager.get_default_format() == "json")
        json_action.triggered.connect(lambda: self._set_format("json"))
        
        binary_action = format_menu.addAction("&Binary")
        binary_action.setCheckable(True)
        binary_action.setChecked(self.project_manager.get_default_format() == "bin")
        binary_action.triggered.connect(lambda: self._set_format("bin"))
        
        yaml_action = format_menu.addAction("&YAML")
        yaml_action.setCheckable(True)
        yaml_action.setChecked(self.project_manager.get_default_format() == "yaml")
        yaml_action.triggered.connect(lambda: self._set_format("yaml"))
        
        # Store format actions for updating
        self.format_actions = {
            "json": json_action,
            "bin": binary_action,
            "yaml": yaml_action
        }
        
        file_menu.addMenu(format_menu)
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = QMenu("&Edit", self)
        
        undo_action = edit_menu.addAction("&Undo")
        undo_action.triggered.connect(self._on_undo)
        self.undo_action = undo_action
        
        redo_action = edit_menu.addAction("&Redo")
        redo_action.triggered.connect(self._on_redo)
        self.redo_action = redo_action
        
        # View menu
        view_menu = QMenu("&View", self)
        
        # Layout submenu
        layout_menu = QMenu("&Layouts", self)
        
        save_layout_action = layout_menu.addAction("&Save Layout...")
        save_layout_action.triggered.connect(self._on_save_layout)
        
        load_layout_action = layout_menu.addAction("&Load Layout...")
        load_layout_action.triggered.connect(self._on_load_layout)
        
        view_menu.addMenu(layout_menu)
        view_menu.addSeparator()
        
        add_dock_action = view_menu.addAction("Add &Dock")
        add_dock_action.triggered.connect(self._on_add_dock)
        
        # Add menus to menu bar
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(view_menu)
        
        self.setMenuBar(menu_bar)
    
    def _create_status_bar(self):
        """Create the status bar."""
        status_bar = QStatusBar(self)
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        self.setStatusBar(status_bar)
    
    def _create_central_widget(self):
        """Create the central widget."""
        # Main container widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter for resizable panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("main_splitter")
        
        # Left panel - Project Properties
        left_panel = QGroupBox("Project Properties")
        left_layout = QGridLayout(left_panel)
        
        # Add project property widgets
        row = 0
        
        # Name field
        left_layout.addWidget(QLabel("Name:"), row, 0)
        self.name_edit = CommandLineEdit()
        self.name_edit.bind_to_model(self.model, "name")
        left_layout.addWidget(self.name_edit, row, 1)
        row += 1
        
        # Category field
        left_layout.addWidget(QLabel("Category:"), row, 0)
        self.category_combo = CommandComboBox()
        self.category_combo.addItems(["Development", "Design", "Marketing", "Research"])
        self.category_combo.bind_to_model(self.model, "category_index")
        left_layout.addWidget(self.category_combo, row, 1)
        row += 1
        
        # Priority field
        left_layout.addWidget(QLabel("Priority (1-5):"), row, 0)
        self.priority_spin = CommandSpinBox()
        self.priority_spin.setRange(1, 5)
        self.priority_spin.bind_to_model(self.model, "priority")
        left_layout.addWidget(self.priority_spin, row, 1)
        row += 1
        
        # Budget field
        left_layout.addWidget(QLabel("Budget:"), row, 0)
        self.budget_spin = CommandDoubleSpinBox()
        self.budget_spin.setRange(0, 1000000)
        self.budget_spin.setPrefix("$")
        self.budget_spin.bind_to_model(self.model, "budget")
        left_layout.addWidget(self.budget_spin, row, 1)
        row += 1
        
        # Progress field
        left_layout.addWidget(QLabel("Progress:"), row, 0)
        self.progress_slider = CommandSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.bind_to_model(self.model, "progress")
        left_layout.addWidget(self.progress_slider, row, 1)
        row += 1
        
        # Active field
        left_layout.addWidget(QLabel("Active:"), row, 0)
        self.active_check = CommandCheckBox()
        self.active_check.bind_to_model(self.model, "is_active")
        left_layout.addWidget(self.active_check, row, 1)
        row += 1
        
        # Deadline field
        left_layout.addWidget(QLabel("Deadline:"), row, 0)
        self.deadline_edit = CommandDateEdit()
        self.deadline_edit.bind_to_model(self.model, "deadline")
        left_layout.addWidget(self.deadline_edit, row, 1)
        row += 1
        
        # Right panel - Description + Command controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Description field
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        
        self.desc_edit = CommandTextEdit()
        self.desc_edit.bind_to_model(self.model, "description")
        desc_layout.addWidget(self.desc_edit)
        
        right_layout.addWidget(desc_group)
        
        # Command controls
        cmd_group = QGroupBox("Commands")
        cmd_layout = QHBoxLayout(cmd_group)
        
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._on_undo)
        cmd_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self._on_redo)
        cmd_layout.addWidget(self.redo_btn)
        
        right_layout.addWidget(cmd_group)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # Set initial sizes
        main_splitter.setSizes([400, 600])
        
        # Add to main layout
        main_layout.addWidget(main_splitter)
        
        # Set as central widget
        self.setCentralWidget(central_widget)
    
    def _create_docks(self):
        """Create the initial dock widgets."""
        # Project Summary dock
        self._create_summary_dock("summary_dock", "Project Summary", 
                                  Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Notes dock
        self._create_notes_dock("notes_dock", "Project Notes", 
                               Qt.DockWidgetArea.BottomDockWidgetArea)
    
    def _create_summary_dock(self, dock_id, title, area):
        """Create a summary dock widget."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Summary label
        self.summary_label = QLabel()
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.summary_label)
        
        # Create dock with associated model
        dock = ObservableDockWidget(dock_id, title, self, self.model)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        # Update summary
        self._update_summary()
        
        return dock
    
    def _create_notes_dock(self, dock_id, title, area):
        """Create a notes dock widget."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Add a command-aware text edit
        notes_edit = CommandTextEdit()
        # We can't bind this to a model property since it's not part of our main model
        # But it will still track changes for undo/redo
        layout.addWidget(notes_edit)
        
        # Create dock
        dock = CommandDockWidget(dock_id, title, self)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        return dock
    
    def _register_layout_widgets(self):
        """Register widgets with the layout manager."""
        # Register main UI components
        for widget in self.findChildren(QSplitter):
            if widget.objectName():
                self.layout_manager.register_widget(widget.objectName(), widget)
    
    def _connect_model_observers(self):
        """Connect observers to model properties."""
        # Connect to all properties
        properties = ["name", "description", "priority", "budget", 
                     "progress", "category_index", "is_active", "deadline"]
        
        for prop in properties:
            self.model.add_property_observer(prop, self._on_model_changed)
    
    def _on_model_changed(self, property_name, old_value, new_value):
        """Handle model property changes."""
        # Update UI
        self._update_window_title()
        self._update_summary()
        self._update_button_states()
        
        # Update status
        self.status_label.setText(f"Property '{property_name}' changed")
    
    def _update_window_title(self):
        """Update the window title."""
        filename = self.project_manager.get_current_filename()
        
        if filename:
            # Show filename in title
            base_filename = os.path.basename(filename)
            title = f"{base_filename} - Command System Demo"
        else:
            # No filename yet
            title = f"{self.model.name} - Command System Demo"
            
        # Add asterisk if modified
        if self.cmd_manager.can_undo():
            title = f"*{title}"
            
        self.setWindowTitle(title)
    
    def _update_summary(self):
        """Update the project summary display."""
        if not hasattr(self, 'summary_label'):
            return
            
        html = "<table width='100%'>"
        html += f"<tr><td><b>Name:</b></td><td>{self.model.name}</td></tr>"
        
        categories = ["Development", "Design", "Marketing", "Research"]
        category = categories[self.model.category_index]
        html += f"<tr><td><b>Category:</b></td><td>{category}</td></tr>"
        
        html += f"<tr><td><b>Priority:</b></td><td>{self.model.priority}</td></tr>"
        html += f"<tr><td><b>Budget:</b></td><td>${self.model.budget:,.2f}</td></tr>"
        html += f"<tr><td><b>Progress:</b></td><td>{self.model.progress}%</td></tr>"
        html += f"<tr><td><b>Active:</b></td><td>{'Yes' if self.model.is_active else 'No'}</td></tr>"
        html += f"<tr><td><b>Deadline:</b></td><td>{self.model.deadline.strftime('%Y-%m-%d')}</td></tr>"
        html += "</table>"
        
        # Add description excerpt if available
        if self.model.description:
            excerpt = self.model.description[:100]
            if len(self.model.description) > 100:
                excerpt += "..."
            html += f"<p><b>Description:</b><br>{excerpt}</p>"
        
        self.summary_label.setText(html)
    
    def _update_button_states(self):
        """Update button states based on command availability."""
        can_undo = self.cmd_manager.can_undo()
        can_redo = self.cmd_manager.can_redo()
        
        # Update undo/redo buttons
        self.undo_btn.setEnabled(can_undo)
        self.redo_btn.setEnabled(can_redo)
        
        # Update menu actions
        self.undo_action.setEnabled(can_undo)
        self.redo_action.setEnabled(can_redo)
    
    def _on_undo(self):
        """Handle undo action."""
        if self.cmd_manager.undo():
            self.status_label.setText("Undo: Success")
        else:
            self.status_label.setText("Undo: Nothing to undo")
            
        self._update_button_states()
    
    def _on_redo(self):
        """Handle redo action."""
        if self.cmd_manager.redo():
            self.status_label.setText("Redo: Success")
        else:
            self.status_label.setText("Redo: Nothing to redo")
            
        self._update_button_states()
    
    def _on_add_dock(self):
        """Handle add dock action."""
        # Generate a unique ID
        dock_id = f"custom_dock_{self.dock_counter}"
        self.dock_counter += 1
        
        # Alternate between notes and summary docks
        if self.dock_counter % 2 == 0:
            dock = self._create_notes_dock(dock_id, f"Notes {self.dock_counter}", 
                                          Qt.DockWidgetArea.RightDockWidgetArea)
        else:
            dock = self._create_summary_dock(dock_id, f"Summary {self.dock_counter}",
                                            Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.status_label.setText(f"Added new dock: {dock_id}")
    
    def _on_dock_close_requested(self, dock_id):
        """Handle dock close request."""
        dock = self.dock_manager.get_dock_widget(dock_id)
        
        if dock:
            # Create and execute command to delete dock
            cmd = DeleteDockCommand(dock_id)
            self.cmd_manager.execute(cmd)
            
            self.status_label.setText(f"Closed dock: {dock_id}")
    
    def _set_format(self, format_type):
        """Set the project file format."""
        # Update project manager
        self.project_manager.set_default_format(format_type)
        
        # Update checkable state of menu items
        for fmt, action in self.format_actions.items():
            action.setChecked(fmt == format_type)
            
        # Show status message
        extension = self.project_manager.get_default_extension()
        self.status_label.setText(f"File format set to {format_type.upper()} ({extension})")
    
    def _on_new(self):
        """Handle New action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Create new model
        self.model = self.project_manager.new_project("project")
        
        # Rebind widgets to new model
        self.name_edit.bind_to_model(self.model, "name")
        self.category_combo.bind_to_model(self.model, "category_index")
        self.priority_spin.bind_to_model(self.model, "priority")
        self.budget_spin.bind_to_model(self.model, "budget")
        self.progress_slider.bind_to_model(self.model, "progress")
        self.active_check.bind_to_model(self.model, "is_active")
        self.deadline_edit.bind_to_model(self.model, "deadline")
        self.desc_edit.bind_to_model(self.model, "description")
        
        # Reconnect model observers
        self._connect_model_observers()
        
        # Update UI
        self._update_window_title()
        self._update_summary()
        
        self.status_label.setText("New project created")
    
    def _on_open(self):
        """Handle Open action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Get file format details
        extension = self.project_manager.get_default_extension()
        
        # Show file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", f"Project Files (*{extension});;All Files (*)"
        )
        
        if not filename:
            return
            
        # Load project
        model = self.project_manager.load_project(filename)
        
        if model is not None:
            # Update model
            self.model = model
            
            # Rebind widgets to new model
            self.name_edit.bind_to_model(self.model, "name")
            self.category_combo.bind_to_model(self.model, "category_index")
            self.priority_spin.bind_to_model(self.model, "priority")
            self.budget_spin.bind_to_model(self.model, "budget")
            self.progress_slider.bind_to_model(self.model, "progress")
            self.active_check.bind_to_model(self.model, "is_active")
            self.deadline_edit.bind_to_model(self.model, "deadline")
            self.desc_edit.bind_to_model(self.model, "description")
            
            # Reconnect model observers
            self._connect_model_observers()
            
            # Update UI
            self._update_window_title()
            self._update_summary()
            
            self.status_label.setText(f"Project loaded: {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to load the project file.")
    
    def _on_save(self):
        """Handle Save action."""
        # Check if we have a filename
        if self.project_manager.get_current_filename() is None:
            # No filename, do Save As instead
            self._on_save_as()
        else:
            # Save to current filename
            if self.project_manager.save_project(self.model):
                # Update window title to reflect saved state
                self._update_window_title()
                self.status_label.setText("Project saved")
            else:
                QMessageBox.critical(self, "Error", "Failed to save the project file.")
    
    def _on_save_as(self):
        """Handle Save As action."""
        # Get file format details
        extension = self.project_manager.get_default_extension()
        
        # Show file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", f"Project Files (*{extension});;All Files (*)"
        )
        
        if not filename:
            return
            
        # Add extension if not present
        if not filename.lower().endswith(extension):
            filename += extension
            
        # Save project
        if self.project_manager.save_project(self.model, filename):
            # Update window title
            self._update_window_title()
            self.status_label.setText(f"Project saved as: {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save the project file.")
    
    def _on_save_layout(self):
        """Handle save layout action."""
        # Ask for a name
        name, ok = QInputDialog.getText(
            self, "Save Layout", "Enter layout name:"
        )
        
        if ok and name:
            # Save layout
            success = self.layout_manager.save_layout_preset(name)
            
            if success:
                self.status_label.setText(f"Layout saved: {name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save layout")
    
    def _on_load_layout(self):
        """Handle load layout action."""
        # Get available presets
        presets = self.layout_manager.get_available_presets()
        
        if not presets:
            QMessageBox.information(self, "No Layouts", "No saved layouts found")
            return
            
        # Show dialog with presets
        from PySide6.QtWidgets import QInputDialog
        preset, ok = QInputDialog.getItem(
            self, "Load Layout", "Select layout:", presets, 0, False
        )
        
        if ok and preset:
            # Load layout
            success = self.layout_manager.load_layout_preset(preset)
            
            if success:
                self.status_label.setText(f"Layout loaded: {preset}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load layout")
    
    def _confirm_discard_changes(self):
        """
        Ask user to confirm discarding unsaved changes.
        
        Returns:
            True if changes can be discarded, False otherwise
        """
        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return result == QMessageBox.StandardButton.Yes
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            # Cancel close
            event.ignore()
        else:
            # Accept close
            event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    # Extend the project manager with layout capabilities
    extend_project_manager()
    
    window = ComprehensiveDemo()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()