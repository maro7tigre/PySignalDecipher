"""
Demonstration of the layout management system.

This example shows how to use the layout system to save and restore UI layouts.
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
    QLabel, QPushButton, QDockWidget, QTextEdit, QSplitter,
    QInputDialog, QMessageBox, QListWidget, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize

# Import from the command system
from command_system import get_command_manager, get_project_manager
from command_system.layout import get_layout_manager, extend_project_manager


class LayoutDemoWindow(QMainWindow):
    """Main window for the layout demo."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Layout System Demo")
        self.setMinimumSize(900, 700)
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.layout_manager = get_layout_manager()
        
        # Set layout manager's main window
        self.layout_manager.set_main_window(self)
        
        # Set layout directory
        demo_dir = os.path.dirname(os.path.abspath(__file__))
        layouts_dir = os.path.join(demo_dir, "layouts")
        self.layout_manager.set_layouts_directory(layouts_dir)
        
        # Create UI
        self._create_ui()
        
        # Initialize dock counter
        self.dock_counter = 0
        
        # Register widgets with layout manager
        self._register_widgets()
        
        # Register widget factories
        self._register_widget_factories()
        
    def _create_ui(self):
        """Create the UI elements."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Layout controls at top
        layout_group = QGroupBox("Layout Controls")
        layout_controls = QHBoxLayout(layout_group)
        
        # Save layout button
        self.save_layout_btn = QPushButton("Save Layout Preset")
        self.save_layout_btn.clicked.connect(self._on_save_layout)
        layout_controls.addWidget(self.save_layout_btn)
        
        # Load layout button
        self.load_layout_btn = QPushButton("Load Layout Preset")
        self.load_layout_btn.clicked.connect(self._on_load_layout)
        layout_controls.addWidget(self.load_layout_btn)
        
        # Delete layout button
        self.delete_layout_btn = QPushButton("Delete Layout Preset")
        self.delete_layout_btn.clicked.connect(self._on_delete_layout)
        layout_controls.addWidget(self.delete_layout_btn)
        
        # Available layouts list
        self.layouts_list = QListWidget()
        self.layouts_list.setMaximumHeight(80)
        self._update_layouts_list()
        self.layouts_list.itemDoubleClicked.connect(self._on_layout_double_clicked)
        
        layout_controls.addWidget(self.layouts_list)
        
        main_layout.addWidget(layout_group)
        
        # Create a splitter for the main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel for dock controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Dock controls group
        dock_group = QGroupBox("Dock Controls")
        dock_controls = QVBoxLayout(dock_group)
        
        # Add dock button
        self.add_dock_btn = QPushButton("Add New Dock")
        self.add_dock_btn.clicked.connect(self._on_add_dock)
        dock_controls.addWidget(self.add_dock_btn)
        
        # Add fixed dock buttons
        self.add_left_dock_btn = QPushButton("Add Left Dock")
        self.add_left_dock_btn.clicked.connect(lambda: self._on_add_fixed_dock("left", Qt.LeftDockWidgetArea))
        dock_controls.addWidget(self.add_left_dock_btn)
        
        self.add_right_dock_btn = QPushButton("Add Right Dock")
        self.add_right_dock_btn.clicked.connect(lambda: self._on_add_fixed_dock("right", Qt.RightDockWidgetArea))
        dock_controls.addWidget(self.add_right_dock_btn)
        
        self.add_bottom_dock_btn = QPushButton("Add Bottom Dock")
        self.add_bottom_dock_btn.clicked.connect(lambda: self._on_add_fixed_dock("bottom", Qt.BottomDockWidgetArea))
        dock_controls.addWidget(self.add_bottom_dock_btn)
        
        left_layout.addWidget(dock_group)
        
        # Size controls group
        size_group = QGroupBox("Window Size")
        size_layout = QVBoxLayout(size_group)
        
        self.resize_small_btn = QPushButton("Small Window")
        self.resize_small_btn.clicked.connect(lambda: self.resize(800, 600))
        size_layout.addWidget(self.resize_small_btn)
        
        self.resize_large_btn = QPushButton("Large Window")
        self.resize_large_btn.clicked.connect(lambda: self.resize(1200, 900))
        size_layout.addWidget(self.resize_large_btn)
        
        left_layout.addWidget(size_group)
        
        # Add to splitter
        self.main_splitter.addWidget(left_panel)
        
        # Right content area - another splitter
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("content_splitter")
        
        # Top text area
        self.top_text = QTextEdit()
        self.top_text.setObjectName("top_text")
        self.top_text.setPlainText("Top text area - try rearranging the UI and saving a layout")
        self.content_splitter.addWidget(self.top_text)
        
        # Bottom text area
        self.bottom_text = QTextEdit()
        self.bottom_text.setObjectName("bottom_text")
        self.bottom_text.setPlainText("Bottom text area - layouts will be saved with correct splitter positions")
        self.content_splitter.addWidget(self.bottom_text)
        
        # Add to main splitter
        self.main_splitter.addWidget(self.content_splitter)
        
        # Set splitter sizes
        self.main_splitter.setSizes([300, 600])
        self.content_splitter.setSizes([300, 300])
        
        main_layout.addWidget(self.main_splitter)
        
        # Set main widget
        self.setCentralWidget(main_widget)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def _register_widgets(self):
        """Register widgets with the layout manager."""
        # Register splitters
        self.layout_manager.register_widget("main_splitter", self.main_splitter)
        self.layout_manager.register_widget("content_splitter", self.content_splitter)
        
        # Register text editors
        self.layout_manager.register_widget("top_text", self.top_text)
        self.layout_manager.register_widget("bottom_text", self.bottom_text)
        
    def _register_widget_factories(self):
        """Register widget factory functions for creating widgets during layout restoration."""
        # Factory for creating dock widgets
        def create_dock_widget():
            # Generate a unique ID
            dock_id = f"dock_{self.dock_counter}"
            self.dock_counter += 1
            
            # Create dock
            dock = QDockWidget(f"Dock {self.dock_counter}", self)
            dock.setObjectName(dock_id)
            
            # Create content
            text_edit = QTextEdit()
            text_edit.setPlainText(f"Content for {dock_id}")
            dock.setWidget(text_edit)
            
            # Setup close event
            dock.closeEvent = lambda event, d=dock: self._on_dock_closed(d, event)
            
            # Add to main window
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
            
            # Register with layout manager
            self.layout_manager.register_widget(dock_id, dock)
            
            return dock
            
        # Register factories
        self.layout_manager.register_widget_factory("QDockWidget", create_dock_widget)
        
    def _on_add_dock(self):
        """Handle add dock button click."""
        # Generate a unique ID
        dock_id = f"dock_{self.dock_counter}"
        self.dock_counter += 1
        
        # Create dock
        dock = QDockWidget(f"Dock {self.dock_counter}", self)
        dock.setObjectName(dock_id)
        
        # Create content
        text_edit = QTextEdit()
        text_edit.setPlainText(f"Content for {dock_id}")
        dock.setWidget(text_edit)
        
        # Setup close event
        dock.closeEvent = lambda event, d=dock: self._on_dock_closed(d, event)
        
        # Add to main window
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        
        # Register with layout manager
        self.layout_manager.register_widget(dock_id, dock)
        
        self.statusBar().showMessage(f"Added dock: {dock_id}")
        
    def _on_add_fixed_dock(self, position, area):
        """Add a fixed-position dock."""
        # Create a fixed dock
        dock_id = f"{position}_dock"
        
        # Check if it already exists
        for widget_id in self.findChildren(QDockWidget):
            if widget_id.objectName() == dock_id:
                # Just show it if it exists
                widget_id.show()
                self.statusBar().showMessage(f"Showed existing dock: {dock_id}")
                return
        
        # Create new dock
        dock = QDockWidget(f"{position.title()} Dock", self)
        dock.setObjectName(dock_id)
        
        # Create content
        text_edit = QTextEdit()
        text_edit.setPlainText(f"This is the {position} dock")
        dock.setWidget(text_edit)
        
        # Setup close event
        dock.closeEvent = lambda event, d=dock: self._on_dock_closed(d, event)
        
        # Add to main window
        self.addDockWidget(area, dock)
        
        # Register with layout manager
        self.layout_manager.register_widget(dock_id, dock)
        
        self.statusBar().showMessage(f"Added dock: {dock_id}")
        
    def _on_dock_closed(self, dock, event):
        """Handle dock close event."""
        # Unregister from layout manager
        dock_id = dock.objectName()
        self.layout_manager.unregister_widget(dock_id)
        
        # Accept the close
        event.accept()
        
        self.statusBar().showMessage(f"Closed dock: {dock_id}")
        
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


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    # Extend the project manager with layout capabilities
    extend_project_manager()
    
    window = LayoutDemoWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()