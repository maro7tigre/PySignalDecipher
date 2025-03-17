"""
Usage example for the command system.

This module demonstrates how to use the command system in a simple application.
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QListWidget, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QSize

import sys
import random

# Import command system components
from command_system import CommandManager, Project, SignalData
from command_system.commands import (
    AddSignalCommand, RenameSignalCommand, RemoveSignalCommand,
    RenameProjectCommand
)


class MainWindow(QMainWindow):
    """Example main window demonstrating the command system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command System Example")
        self.resize(800, 600)
        
        # Set up the command manager
        self._command_manager = CommandManager()
        
        # Create a new project
        self._project = Project("Example Project")
        self._project.set_command_manager(self._command_manager)
        
        # Set up the UI
        self._setup_ui()
        
        # Update UI state
        self._update_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Project name section
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project Name:"))
        self._project_name_label = QLabel(self._project.name)
        project_layout.addWidget(self._project_name_label)
        self._rename_project_button = QPushButton("Rename")
        self._rename_project_button.clicked.connect(self._rename_project)
        project_layout.addWidget(self._rename_project_button)
        project_layout.addStretch()
        main_layout.addLayout(project_layout)
        
        # Signals list
        main_layout.addWidget(QLabel("Signals:"))
        self._signals_list = QListWidget()
        self._signals_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._signals_list.customContextMenuRequested.connect(self._show_signal_context_menu)
        main_layout.addWidget(self._signals_list)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add signal button
        add_button = QPushButton("Add Signal")
        add_button.clicked.connect(self._add_signal)
        buttons_layout.addWidget(add_button)
        
        # Remove signal button
        remove_button = QPushButton("Remove Signal")
        remove_button.clicked.connect(self._remove_selected_signal)
        buttons_layout.addWidget(remove_button)
        
        # Rename signal button
        rename_button = QPushButton("Rename Signal")
        rename_button.clicked.connect(self._rename_selected_signal)
        buttons_layout.addWidget(rename_button)
        
        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)
        
        # Undo/Redo layout
        history_layout = QHBoxLayout()
        
        # Undo button
        self._undo_button = QPushButton("Undo")
        self._undo_button.clicked.connect(self._undo)
        history_layout.addWidget(self._undo_button)
        
        # Redo button
        self._redo_button = QPushButton("Redo")
        self._redo_button.clicked.connect(self._redo)
        history_layout.addWidget(self._redo_button)
        
        # Add history layout to main layout
        main_layout.addLayout(history_layout)
        
        # Connect to command manager signals
        self._command_manager.register_history_observers(
            self._update_undo_button,
            self._update_redo_button
        )
    
    def _update_ui(self):
        """Update the UI to reflect the current state."""
        # Update project name
        self._project_name_label.setText(self._project.name)
        
        # Update signals list
        self._update_signals_list()
    
    def _update_signals_list(self):
        """Update the signals list."""
        # Save the current selection
        selected_items = self._signals_list.selectedItems()
        selected_ids = [item.data(Qt.UserRole) for item in selected_items]
        
        # Clear the list
        self._signals_list.clear()
        
        # Add all signals
        for signal_id, signal in self._project.get_all_signals().items():
            item = self._signals_list.addItem(signal.name)
            # Store the signal ID in the item's user data
            self._signals_list.item(self._signals_list.count() - 1).setData(Qt.UserRole, signal_id)
        
        # Restore selection if possible
        for i in range(self._signals_list.count()):
            item = self._signals_list.item(i)
            if item.data(Qt.UserRole) in selected_ids:
                item.setSelected(True)
    
    def _update_undo_button(self, can_undo):
        """Update the undo button state."""
        self._undo_button.setEnabled(can_undo)
    
    def _update_redo_button(self, can_redo):
        """Update the redo button state."""
        self._redo_button.setEnabled(can_redo)
    
    def _add_signal(self):
        """Add a new signal to the project."""
        # Generate a random signal
        signal = SignalData(f"Signal {random.randint(1, 1000)}")
        
        # Create and execute the command
        command = AddSignalCommand(self._project, signal)
        self._command_manager.execute_command(command)
        
        # Update UI
        self._update_ui()
    
    def _remove_selected_signal(self):
        """Remove the selected signal."""
        selected_items = self._signals_list.selectedItems()
        if not selected_items:
            return
            
        # Get the signal ID
        signal_id = selected_items[0].data(Qt.UserRole)
        
        # Create and execute the command
        command = RemoveSignalCommand(self._project, signal_id)
        self._command_manager.execute_command(command)
        
        # Update UI
        self._update_ui()
    
    def _rename_selected_signal(self):
        """Rename the selected signal."""
        selected_items = self._signals_list.selectedItems()
        if not selected_items:
            return
            
        # Get the signal ID
        signal_id = selected_items[0].data(Qt.UserRole)
        signal = self._project.get_signal(signal_id)
        
        # Get the new name
        new_name, ok = QInputDialog.getText(
            self, "Rename Signal", 
            "Enter new name:", text=signal.name
        )
        
        if ok and new_name:
            # Create and execute the command
            command = RenameSignalCommand(signal, new_name)
            self._command_manager.execute_command(command)
            
            # Update UI
            self._update_ui()
    
    def _rename_project(self):
        """Rename the project."""
        # Get the new name
        new_name, ok = QInputDialog.getText(
            self, "Rename Project", 
            "Enter new name:", text=self._project.name
        )
        
        if ok and new_name:
            # Create and execute the command
            command = RenameProjectCommand(self._project, new_name)
            self._command_manager.execute_command(command)
            
            # Update UI
            self._update_ui()
    
    def _undo(self):
        """Undo the last command."""
        if self._command_manager.undo():
            # Update UI
            self._update_ui()
    
    def _redo(self):
        """Redo the last undone command."""
        if self._command_manager.redo():
            # Update UI
            self._update_ui()
    
    def _show_signal_context_menu(self, pos):
        """Show a context menu for the signals list."""
        selected_items = self._signals_list.selectedItems()
        if not selected_items:
            return
            
        # Create the menu
        menu = QMenu(self)
        
        # Add actions
        rename_action = menu.addAction("Rename")
        remove_action = menu.addAction("Remove")
        
        # Show the menu and get the selected action
        action = menu.exec_(self._signals_list.mapToGlobal(pos))
        
        if action == rename_action:
            self._rename_selected_signal()
        elif action == remove_action:
            self._remove_selected_signal()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())