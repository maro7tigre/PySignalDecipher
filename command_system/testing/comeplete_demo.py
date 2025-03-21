"""
Comprehensive demo of the PySignalDecipher Command System.

This demo combines features from all test files:
1. Widget bindings - from widgets_demo.py
2. File operations - from file_menu_demo.py
3. Dock management - from docks_demo.py
4. Layout management - from layout_demo.py

The demo allows you to:
- Create and edit documents with command-aware widgets
- Save and load documents
- Add and manage dock widgets
- Save and restore UI layouts
"""
import sys
import os
from pathlib import Path
from datetime import date

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGroupBox, QGridLayout, QSplitter, QTabWidget,
    QFileDialog, QMessageBox, QDockWidget, QTextEdit, QInputDialog,
    QListWidget, QStatusBar
)
from PySide6.QtCore import Qt, QSize

# Import from the command system
from command_system import (
    Observable, ObservableProperty, get_command_manager,
    get_project_manager, ProjectSerializer
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


class DocumentModel(Observable):
    """Model for the document with various property types."""
    
    # Document properties
    title = ObservableProperty[str](default="Untitled Document")
    content = ObservableProperty[str](default="")
    
    # Metadata properties
    author = ObservableProperty[str](default="")
    importance = ObservableProperty[int](default=1)
    complexity = ObservableProperty[float](default=3.0)
    is_active = ObservableProperty[bool](default=True)
    category_index = ObservableProperty[int](default=0)
    creation_date = ObservableProperty[date](default=date.today())
    
    # Statistics
    word_count = ObservableProperty[int](default=0)
    
    def __init__(self):
        """Initialize the document model."""
        super().__init__()
        
        # Add observer to update word count when content changes
        self.add_property_observer("content", self._update_word_count)
        
    def _update_word_count(self, property_name, old_value, new_value):
        """Update word count when content changes."""
        # Simple word count calculation
        if new_value:
            words = new_value.split()
            self.word_count = len(words)
        else:
            self.word_count = 0


class ComprehensiveDemoWindow(QMainWindow):
    """Main window for the comprehensive demo."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up window properties
        self.setWindowTitle("Command System Demo")
        self.setMinimumSize(1000, 800)
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.project_manager = get_project_manager()
        self.dock_manager = get_dock_manager()
        self.layout_manager = get_layout_manager()
        
        # Register model factory
        self.project_manager.register_model_type("document", lambda: DocumentModel())
        
        # Set up managers
        self.dock_manager.set_main_window(self)
        self.layout_manager.set_main_window(self)
        
        # Set layout directory
        demo_dir = os.path.dirname(os.path.abspath(__file__))
        layouts_dir = os.path.join(demo_dir, "layouts")
        self.layout_manager.set_layouts_directory(layouts_dir)
        
        # Begin initialization - disable command tracking
        self.cmd_manager.begin_init()
        
        # Create model
        self.model = DocumentModel()
        
        # Create UI
        self._create_ui()
        self._create_menu()
        self._create_initial_docks()
        
        # Register widgets with layout manager
        self._register_widgets()
        
        # Initialize dock counter for new docks
        self.dock_counter = 0
        
        # End initialization - re-enable command tracking
        self.cmd_manager.end_init()
        
        # Update window title
        self._update_window_title()
        
    def _create_ui(self):
        """Create the main UI."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Buttons toolbar
        toolbar_layout = QHBoxLayout()
        
        # Undo/Redo buttons
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._on_undo)
        self.undo_button.setEnabled(False)
        toolbar_layout.addWidget(self.undo_button)
        
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._on_redo)
        self.redo_button.setEnabled(False)
        toolbar_layout.addWidget(self.redo_button)
        
        # Add dock buttons
        toolbar_layout.addWidget(QLabel("Docks:"))
        
        self.add_dock_btn = QPushButton("Add Editor")
        self.add_dock_btn.clicked.connect(self._on_add_editor_dock)
        toolbar_layout.addWidget(self.add_dock_btn)
        
        self.add_stats_btn = QPushButton("Add Stats")
        self.add_stats_btn.clicked.connect(self._on_add_stats_dock)
        toolbar_layout.addWidget(self.add_stats_btn)
        
        # Layout buttons
        toolbar_layout.addWidget(QLabel("Layout:"))
        
        self.save_layout_btn = QPushButton("Save Layout")
        self.save_layout_btn.clicked.connect(self._on_save_layout)
        toolbar_layout.addWidget(self.save_layout_btn)
        
        self.load_layout_btn = QPushButton("Load Layout")
        self.load_layout_btn.clicked.connect(self._on_load_layout)
        toolbar_layout.addWidget(self.load_layout_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Document properties
        self.properties_panel = QGroupBox("Document Properties")
        properties_layout = QGridLayout(self.properties_panel)
        
        # Title
        properties_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_edit = CommandLineEdit()
        self.title_edit.bind_to_model(self.model, "title")
        properties_layout.addWidget(self.title_edit, 0, 1)
        
        # Author
        properties_layout.addWidget(QLabel("Author:"), 1, 0)
        self.author_edit = CommandLineEdit()
        self.author_edit.bind_to_model(self.model, "author")
        properties_layout.addWidget(self.author_edit, 1, 1)
        
        # Category
        properties_layout.addWidget(QLabel("Category:"), 2, 0)
        self.category_combo = CommandComboBox()
        self.category_combo.addItems(["General", "Notes", "Report", "Research"])
        self.category_combo.bind_to_model(self.model, "category_index")
        properties_layout.addWidget(self.category_combo, 2, 1)
        
        # Active
        properties_layout.addWidget(QLabel("Active:"), 3, 0)
        self.active_check = CommandCheckBox()
        self.active_check.bind_to_model(self.model, "is_active")
        properties_layout.addWidget(self.active_check, 3, 1)
        
        # Importance
        properties_layout.addWidget(QLabel("Importance (1-10):"), 4, 0)
        self.importance_spin = CommandSpinBox()
        self.importance_spin.setRange(1, 10)
        self.importance_spin.bind_to_model(self.model, "importance")
        properties_layout.addWidget(self.importance_spin, 4, 1)
        
        # Complexity
        properties_layout.addWidget(QLabel("Complexity:"), 5, 0)
        self.complexity_spin = CommandDoubleSpinBox()
        self.complexity_spin.setRange(1.0, 10.0)
        self.complexity_spin.setSingleStep(0.1)
        self.complexity_spin.bind_to_model(self.model, "complexity")
        properties_layout.addWidget(self.complexity_spin, 5, 1)
        
        # Creation Date
        properties_layout.addWidget(QLabel("Creation Date:"), 6, 0)
        self.date_edit = CommandDateEdit()
        self.date_edit.bind_to_model(self.model, "creation_date")
        properties_layout.addWidget(self.date_edit, 6, 1)
        
        # Word Count (read-only)
        properties_layout.addWidget(QLabel("Word Count:"), 7, 0)
        self.word_count_label = QLabel("0")
        self.model.add_property_observer("word_count", self._on_word_count_changed)
        properties_layout.addWidget(self.word_count_label, 7, 1)
        
        # Add to splitter
        self.main_splitter.addWidget(self.properties_panel)
        
        # Right panel - Content
        self.content_panel = QGroupBox("Document Content")
        content_layout = QVBoxLayout(self.content_panel)
        
        # Content edit
        self.content_edit = CommandTextEdit()
        self.content_edit.bind_to_model(self.model, "content")
        content_layout.addWidget(self.content_edit)
        
        # Add to splitter
        self.main_splitter.addWidget(self.content_panel)
        
        # Set splitter sizes
        self.main_splitter.setSizes([300, 700])
        
        # Add to main layout
        main_layout.addWidget(self.main_splitter)
        
        # Layout presets list
        self.layouts_group = QGroupBox("Saved Layouts")
        layouts_layout = QVBoxLayout(self.layouts_group)
        
        self.layouts_list = QListWidget()
        self.layouts_list.setMaximumHeight(100)
        self._update_layouts_list()
        self.layouts_list.itemDoubleClicked.connect(self._on_layout_double_clicked)
        layouts_layout.addWidget(self.layouts_list)
        
        # Delete layout button
        self.delete_layout_btn = QPushButton("Delete Selected Layout")
        self.delete_layout_btn.clicked.connect(self._on_delete_layout)
        layouts_layout.addWidget(self.delete_layout_btn)
        
        main_layout.addWidget(self.layouts_group)
        
        # Set central widget
        self.setCentralWidget(main_widget)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect model changes to update undo/redo buttons
        for prop_name in dir(self.model.__class__):
            prop = getattr(self.model.__class__, prop_name)
            if isinstance(prop, ObservableProperty):
                self.model.add_property_observer(prop_name, self._on_model_changed)
        
    def _create_menu(self):
        """Create the menu bar."""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
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
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # Dock menu
        dock_menu = menu_bar.addMenu("&Docks")
        
        add_editor_action = dock_menu.addAction("Add Editor Dock")
        add_editor_action.triggered.connect(self._on_add_editor_dock)
        
        add_stats_action = dock_menu.addAction("Add Stats Dock")
        add_stats_action.triggered.connect(self._on_add_stats_dock)
        
        # Layout menu
        layout_menu = menu_bar.addMenu("&Layout")
        
        save_layout_action = layout_menu.addAction("&Save Layout...")
        save_layout_action.triggered.connect(self._on_save_layout)
        
        load_layout_action = layout_menu.addAction("&Load Layout...")
        load_layout_action.triggered.connect(self._on_load_layout)
        
    def _create_initial_docks(self):
        """Create initial dock widgets."""
        # Create properties dock on right side
        self._create_properties_dock("properties_dock", "Properties", Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create overview dock on bottom
        self._create_overview_dock("overview_dock", "Document Overview", Qt.DockWidgetArea.BottomDockWidgetArea)
        
    def _register_widgets(self):
        """Register widgets with the layout manager."""
        # Register splitters and main widgets
        self.layout_manager.register_widget("main_splitter", self.main_splitter)
        self.layout_manager.register_widget("properties_panel", self.properties_panel)
        self.layout_manager.register_widget("content_panel", self.content_panel)
        self.layout_manager.register_widget("layouts_group", self.layouts_group)
        
    def _create_properties_dock(self, dock_id, title, area):
        """Create a properties dock widget with metadata."""
        # Create content widget
        content = QWidget()
        layout = QGridLayout(content)
        
        # Add importance slider
        layout.addWidget(QLabel("Importance:"), 0, 0)
        importance_slider = CommandSlider(Qt.Orientation.Horizontal)
        importance_slider.setRange(1, 10)
        importance_slider.bind_to_model(self.model, "importance")
        layout.addWidget(importance_slider, 0, 1)
        
        # Add complexity slider
        layout.addWidget(QLabel("Complexity:"), 1, 0)
        complexity_slider = CommandSlider(Qt.Orientation.Horizontal)
        complexity_slider.setRange(1, 100)
        complexity_slider.setValue(int(self.model.complexity * 10))
        # Custom mapping of slider values to complexity
        complexity_slider.valueChanged.connect(
            lambda v: setattr(self.model, "complexity", v/10)
        )
        layout.addWidget(complexity_slider, 1, 1)
        
        # Create observable dock with model
        dock = ObservableDockWidget(dock_id, title, self, self.model)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        return dock
        
    def _create_overview_dock(self, dock_id, title, area):
        """Create an overview dock with document summary."""
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Add text display
        overview_text = QTextEdit()
        overview_text.setReadOnly(True)
        layout.addWidget(overview_text)
        
        # Create dock
        dock = CommandDockWidget(dock_id, title, self)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, area)
        self.cmd_manager.execute(cmd)
        
        # Update text when model changes
        def update_overview():
            categories = ["General", "Notes", "Report", "Research"]
            category = categories[self.model.category_index]
            
            text = f"Document: {self.model.title}\n"
            text += f"Author: {self.model.author}\n"
            text += f"Category: {category}\n"
            text += f"Status: {'Active' if self.model.is_active else 'Inactive'}\n"
            text += f"Importance: {self.model.importance}/10\n"
            text += f"Complexity: {self.model.complexity:.1f}/10.0\n"
            text += f"Creation Date: {self.model.creation_date}\n"
            text += f"Word Count: {self.model.word_count}\n\n"
            
            # Add content preview
            preview = self.model.content
            if len(preview) > 200:
                preview = preview[:200] + "..."
            text += f"Preview:\n{preview}"
            
            overview_text.setText(text)
            
        # Connect all model properties to update the overview
        for prop_name in dir(self.model.__class__):
            prop = getattr(self.model.__class__, prop_name)
            if isinstance(prop, ObservableProperty):
                self.model.add_property_observer(prop_name, lambda *args: update_overview())
        
        # Initial update
        update_overview()
        
        return dock
        
    def _on_add_editor_dock(self):
        """Handle add editor dock button click."""
        # Generate a unique ID for the new dock
        self.dock_counter += 1
        dock_id = f"editor_dock_{self.dock_counter}"
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Add a text edit
        text_edit = CommandTextEdit()
        text_edit.bind_to_model(self.model, "content")
        layout.addWidget(text_edit)
        
        # Create dock
        dock = CommandDockWidget(dock_id, f"Editor {self.dock_counter}", self)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, Qt.DockWidgetArea.RightDockWidgetArea)
        self.cmd_manager.execute(cmd)
        
        # Update status
        self.statusBar().showMessage(f"Added editor dock: {dock_id}")
        
    def _on_add_stats_dock(self):
        """Handle add stats dock button click."""
        # Generate a unique ID for the new dock
        self.dock_counter += 1
        dock_id = f"stats_dock_{self.dock_counter}"
        
        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Add stats display
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        layout.addWidget(stats_text)
        
        # Create dock
        dock = CommandDockWidget(dock_id, f"Stats {self.dock_counter}", self)
        dock.setWidget(content)
        dock.closeRequested.connect(self._on_dock_close_requested)
        
        # Create and execute command to add dock
        cmd = CreateDockCommand(dock_id, dock, None, Qt.DockWidgetArea.RightDockWidgetArea)
        self.cmd_manager.execute(cmd)
        
        # Define stats updater
        def update_stats():
            # Count characters, words, sentences
            text = self.model.content
            chars = len(text)
            words = len(text.split())
            sentences = len([s for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()])
            
            stats = f"Document Statistics:\n\n"
            stats += f"Characters: {chars}\n"
            stats += f"Words: {words}\n"
            stats += f"Sentences: {sentences}\n"
            
            if words > 0:
                stats += f"Average word length: {chars/words:.1f} characters\n"
            if sentences > 0:
                stats += f"Average sentence length: {words/sentences:.1f} words\n"
                
            stats_text.setText(stats)
            
        # Connect to content changes
        self.model.add_property_observer("content", lambda *args: update_stats())
        
        # Initial update
        update_stats()
        
        # Update status
        self.statusBar().showMessage(f"Added stats dock: {dock_id}")
        
    def _on_dock_close_requested(self, dock_id):
        """Handle dock close request."""
        # Get the dock
        dock = self.dock_manager.get_dock_widget(dock_id)
        
        if dock:
            # Create and execute command to delete dock
            cmd = DeleteDockCommand(dock_id)
            self.cmd_manager.execute(cmd)
            
            # Update status
            self.statusBar().showMessage(f"Deleted dock: {dock_id}")
            
    def _on_save_layout(self):
        """Handle save layout button click."""
        # Ask for a name
        name, ok = QInputDialog.getText(
            self, "Save Layout", "Enter layout name:"
        )
        
        if ok and name:
            # Save layout
            success = self.layout_manager.save_layout_preset(name)
            
            if success:
                self.statusBar().showMessage(f"Layout saved: {name}")
                self._update_layouts_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to save layout")
                
    def _on_load_layout(self):
        """Handle load layout button click."""
        # Get selected item
        current_item = self.layouts_list.currentItem()
        
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a layout to load")
            return
            
        name = current_item.text()
        
        # Load layout
        success = self.layout_manager.load_layout_preset(name)
        
        if success:
            self.statusBar().showMessage(f"Layout loaded: {name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load layout")
            
    def _on_delete_layout(self):
        """Handle delete layout button click."""
        # Get selected item
        current_item = self.layouts_list.currentItem()
        
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a layout to delete")
            return
            
        name = current_item.text()
        
        # Confirm deletion
        response = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete layout '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if response == QMessageBox.Yes:
            # Delete layout
            success = self.layout_manager.delete_layout_preset(name)
            
            if success:
                self.statusBar().showMessage(f"Layout deleted: {name}")
                self._update_layouts_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete layout")
                
    def _on_layout_double_clicked(self, item):
        """Handle double-click on a layout item."""
        name = item.text()
        
        # Load layout
        success = self.layout_manager.load_layout_preset(name)
        
        if success:
            self.statusBar().showMessage(f"Layout loaded: {name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load layout")
            
    def _update_layouts_list(self):
        """Update the list of available layouts."""
        self.layouts_list.clear()
        
        # Get available presets
        presets = self.layout_manager.get_available_presets()
        
        # Add to list
        for preset in presets:
            self.layouts_list.addItem(preset)
            
    def _on_word_count_changed(self, property_name, old_value, new_value):
        """Handle word count changes."""
        self.word_count_label.setText(str(new_value))
        
    def _on_new(self):
        """Handle New action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Create new model
        self.model = self.project_manager.new_project("document")
        
        # Rebind widgets to new model
        self._rebind_widgets()
        
        # Update window title
        self._update_window_title()
        
    def _on_open(self):
        """Handle Open action."""
        # Check for unsaved changes
        if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
            return
            
        # Show file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "", "Document Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
            
        # Load project
        model = self.project_manager.load_project(filename)
        
        if model is not None:
            # Update model
            self.model = model
            
            # Rebind widgets to new model
            self._rebind_widgets()
            
            # Update window title
            self._update_window_title()
            
            # Update status
            self.statusBar().showMessage(f"Opened: {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to load the document file.")
        
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
                
                # Update status
                self.statusBar().showMessage("Document saved")
            else:
                QMessageBox.critical(self, "Error", "Failed to save the document file.")
        
    def _on_save_as(self):
        """Handle Save As action."""
        # Show file dialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Document", "", "Document Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
            
        # Add extension if not present
        if not filename.lower().endswith(".json"):
            filename += ".json"
            
        # Save project
        if self.project_manager.save_project(self.model, filename):
            # Update window title
            self._update_window_title()
            
            # Update status
            self.statusBar().showMessage(f"Saved as: {filename}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save the document file.")
            
    def _rebind_widgets(self):
        """Rebind all widgets to the current model."""
        # Rebind text fields
        self.title_edit.bind_to_model(self.model, "title")
        self.author_edit.bind_to_model(self.model, "author")
        self.content_edit.bind_to_model(self.model, "content")
        
        # Rebind numeric fields
        self.importance_spin.bind_to_model(self.model, "importance")
        self.complexity_spin.bind_to_model(self.model, "complexity")
        
        # Rebind other fields
        self.category_combo.bind_to_model(self.model, "category_index")
        self.active_check.bind_to_model(self.model, "is_active")
        self.date_edit.bind_to_model(self.model, "creation_date")
        
        # Update word count
        self._on_word_count_changed("word_count", 0, self.model.word_count)
        
        # Connect model changes to update buttons
        for prop_name in dir(self.model.__class__):
            prop = getattr(self.model.__class__, prop_name)
            if isinstance(prop, ObservableProperty):
                self.model.add_property_observer(prop_name, self._on_model_changed)
                
    def _on_undo(self):
        """Handle undo button click."""
        if self.cmd_manager.undo():
            self.statusBar().showMessage("Undo: Success")
        else:
            self.statusBar().showMessage("Undo: Nothing to undo")
            
        self._update_undo_redo_buttons()
        self._update_window_title()
        
    def _on_redo(self):
        """Handle redo button click."""
        if self.cmd_manager.redo():
            self.statusBar().showMessage("Redo: Success")
        else:
            self.statusBar().showMessage("Redo: Nothing to redo")
            
        self._update_undo_redo_buttons()
        self._update_window_title()
        
    def _on_model_changed(self, *args):
        """Called when any model property changes."""
        self._update_undo_redo_buttons()
        self._update_window_title()
        
    def _update_undo_redo_buttons(self):
        """Update undo/redo button states."""
        self.undo_button.setEnabled(self.cmd_manager.can_undo())
        self.redo_button.setEnabled(self.cmd_manager.can_redo())
        
    def _update_window_title(self):
        """Update the window title to show filename and modified status."""
        filename = self.project_manager.get_current_filename()
        
        if filename:
            # Show filename in title
            base_filename = os.path.basename(filename)
            title = f"{base_filename} - Command System Demo"
        else:
            # No filename yet
            title = "Untitled - Command System Demo"
            
        # Add asterisk if modified
        if self.cmd_manager.can_undo():
            title = f"*{title}"
            
        self.setWindowTitle(title)
        
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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        return result == QMessageBox.Yes
        
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
    
    # Create and show the main window
    window = ComprehensiveDemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()