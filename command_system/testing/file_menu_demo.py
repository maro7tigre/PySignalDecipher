"""
Example implementation of save/load functionality in a Qt application.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QMenuBar, QMenu, QFileDialog, 
    QMessageBox
)
from PySide6.QtCore import Qt

# Import from the command system
from command_system import (
    Observable, ObservableProperty, get_command_manager,
    get_project_manager, ProjectSerializer
)
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandTextEdit
)


class NoteModel(Observable):
    """Simple model for the demo."""
    
    title = ObservableProperty[str](default="Untitled Note")
    content = ObservableProperty[str](default="")
    importance = ObservableProperty[int](default=1)


class FileMenuWindow(QMainWindow):
    """Example window with file menu save/load functionality."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Save/Load Demo")
        self.setMinimumSize(600, 400)
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.project_manager = get_project_manager()
        
        # Register model factory
        self.project_manager.register_model_type("note", lambda: NoteModel())
        
        # Create model
        self.model = NoteModel()
        
        # Create status bar
        self.statusBar()
        
        # Create UI
        self._create_ui()
        self._create_menu()
        
        # Update window title
        self._update_window_title()
        
    def _create_ui(self):
        """Create the UI elements."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Title edit
        title_label = QLabel("Title:")
        self.title_edit = CommandLineEdit()
        self.title_edit.bind_to_model(self.model, "title")
        self.title_edit.textChanged.connect(self._on_content_changed)
        
        # Importance slider
        importance_label = QLabel("Importance (1-10):")
        self.importance_spin = CommandSpinBox()
        self.importance_spin.setRange(1, 10)
        self.importance_spin.bind_to_model(self.model, "importance")
        self.importance_spin.valueChanged.connect(self._on_content_changed)
        
        # Content edit
        content_label = QLabel("Content:")
        self.content_edit = CommandTextEdit()
        self.content_edit.bind_to_model(self.model, "content")
        self.content_edit.textChanged.connect(self._on_content_changed)
        
        # Add widgets to layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.title_edit)
        main_layout.addWidget(importance_label)
        main_layout.addWidget(self.importance_spin)
        main_layout.addWidget(content_label)
        main_layout.addWidget(self.content_edit)
        
        # Set main widget
        self.setCentralWidget(main_widget)
        
    def _create_menu(self):
        """Create the menu bar."""
        # Create menu bar
        menu_bar = QMenuBar()
        
        # File menu
        file_menu = QMenu("&File", self)
        
        # Add file actions
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
        
        xml_action = format_menu.addAction("&XML")
        xml_action.setCheckable(True)
        xml_action.setChecked(self.project_manager.get_default_format() == "xml")
        xml_action.triggered.connect(lambda: self._set_format("xml"))
        
        yaml_action = format_menu.addAction("&YAML")
        yaml_action.setCheckable(True)
        yaml_action.setChecked(self.project_manager.get_default_format() == "yaml")
        yaml_action.triggered.connect(lambda: self._set_format("yaml"))
        
        # Store format actions for updating checkable state
        self.format_actions = {
            "json": json_action,
            "bin": binary_action,
            "xml": xml_action,
            "yaml": yaml_action
        }
        
        file_menu.addMenu(format_menu)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # Add file menu to menu bar
        menu_bar.addMenu(file_menu)
        
        # Set menu bar
        self.setMenuBar(menu_bar)
        
    def _set_format(self, format_type):
        """Set the project file format."""
        # Update project manager
        self.project_manager.set_default_format(format_type)
        
        # Update checkable state of menu items
        for fmt, action in self.format_actions.items():
            action.setChecked(fmt == format_type)
            
        # Show status message
        extension = self.project_manager.get_default_extension()
        self.statusBar().showMessage(f"File format set to {format_type.upper()} ({extension})", 3000)
        
    def _on_new(self):
        """Handle New action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Create new model
        self.model = self.project_manager.new_project("note")
        
        # Rebind widgets to new model
        self.title_edit.bind_to_model(self.model, "title")
        self.importance_spin.bind_to_model(self.model, "importance")
        self.content_edit.bind_to_model(self.model, "content")
        
        # Update window title
        self._update_window_title()
        
    def _on_open(self):
        """Handle Open action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Get current format and extension
        current_format = self.project_manager.get_default_format()
        extension = self.project_manager.get_default_extension()
        
        # Create filter string based on format
        if current_format == "json":
            filter_str = "JSON Files (*" + extension + ");;All Files (*)"
        elif current_format == "bin":
            filter_str = "Binary Files (*" + extension + ");;All Files (*)"
        elif current_format == "xml":
            filter_str = "XML Files (*" + extension + ");;All Files (*)"
        elif current_format == "yaml":
            filter_str = "YAML Files (*" + extension + ");;All Files (*)"
        else:
            filter_str = "Project Files (*" + extension + ");;All Files (*)"
            
        # Show file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Note", "", filter_str
        )
        
        if not filename:
            return
            
        # Load project
        model = self.project_manager.load_project(filename)
        
        if model is not None:
            # Update model
            self.model = model
            
            # Rebind widgets to new model
            self.title_edit.bind_to_model(self.model, "title")
            self.importance_spin.bind_to_model(self.model, "importance")
            self.content_edit.bind_to_model(self.model, "content")
            
            # Update window title
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Error", "Failed to load the note file.")
        
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
            else:
                QMessageBox.critical(self, "Error", "Failed to save the note file.")
        
    def _on_save_as(self):
        """Handle Save As action."""
        # Get current format and extension
        current_format = self.project_manager.get_default_format()
        extension = self.project_manager.get_default_extension()
        
        # Create filter string based on format
        if current_format == "json":
            filter_str = "JSON Files (*" + extension + ");;All Files (*)"
        elif current_format == "bin":
            filter_str = "Binary Files (*" + extension + ");;All Files (*)"
        elif current_format == "xml":
            filter_str = "XML Files (*" + extension + ");;All Files (*)"
        elif current_format == "yaml":
            filter_str = "YAML Files (*" + extension + ");;All Files (*)"
        else:
            filter_str = "Project Files (*" + extension + ");;All Files (*)"
            
        # Show file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Note", "", filter_str
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
        else:
            QMessageBox.critical(self, "Error", "Failed to save the note file.")
        
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
        
    def _update_window_title(self):
        """Update the window title to show filename and modified status."""
        filename = self.project_manager.get_current_filename()
        
        if filename:
            # Show filename in title
            base_filename = os.path.basename(filename)
            title = f"{base_filename} - Note Editor"
        else:
            # No filename yet
            title = "Untitled - Note Editor"
            
        # Add asterisk if modified
        if self.cmd_manager.can_undo():
            title = f"*{title}"
            
        self.setWindowTitle(title)
        
    def _on_content_changed(self):
        """Called when content changes to update window title."""
        self._update_window_title()
        
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
    window = FileMenuWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()