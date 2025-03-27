"""
Simple demo of the PySignalDecipher dynamic container system.

This demo shows how to register tab types, create tabs dynamically,
and integrate with the command system for undo/redo navigation.
"""
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFormLayout
)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core.observable import Observable, ObservableProperty
from command_system.core.command_manager import get_command_manager
from command_system.widgets.line_edit import CommandLineEdit
from command_system.widgets.base_widget import CommandExecutionMode
from command_system.widgets.containers.tab_widget import CommandTabWidget


class Person(Observable):
    """Simple person model with observable properties."""
    name = ObservableProperty[str]("John Doe")
    email = ObservableProperty[str]("john@example.com")
    address = ObservableProperty[str]("123 Main St")


class SimpleTabsDemo(QMainWindow):
    """Demo of dynamic tabs with command system integration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Dynamic Tabs Demo")
        self.resize(500, 300)
        
        # Create model and command manager
        self.person = Person()
        self.cmd_manager = get_command_manager()
        
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create buttons
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        
        add_info_btn = QPushButton("Add Info Tab")
        add_info_btn.clicked.connect(self.add_info_tab)
        
        add_contact_btn = QPushButton("Add Contact Tab")
        add_contact_btn.clicked.connect(self.add_contact_tab)
        
        add_address_btn = QPushButton("Add Address Tab")
        add_address_btn.clicked.connect(self.add_address_tab)
        
        btn_layout.addWidget(add_info_btn)
        btn_layout.addWidget(add_contact_btn)
        btn_layout.addWidget(add_address_btn)
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(self, "main_tabs")
        self.tab_widget.setTabsClosable(True)
        layout.addWidget(self.tab_widget)
        
        # Register tab types with different closable settings
        self.info_tab_type = self.tab_widget.register_tab(
            self.create_info_tab,
            tab_name="Info",
            dynamic=True,
            closable=False  # Not closable
        )
        
        self.contact_tab_type = self.tab_widget.register_tab(
            self.create_contact_tab,
            tab_name="Contact",
            dynamic=True,
            closable=True  # Closable
        )
        
        self.address_tab_type = self.tab_widget.register_tab(
            self.create_address_tab,
            tab_name="Address",
            dynamic=True,
            closable=True  # Closable
        )
        
        # Connect tab close signal
        self.tab_widget.tabCloseRequested.connect(self.handle_tab_close)
        
        # Create command buttons
        cmd_layout = QHBoxLayout()
        layout.addLayout(cmd_layout)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.cmd_manager.undo)
        
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.cmd_manager.redo)
        
        cmd_layout.addWidget(undo_btn)
        cmd_layout.addWidget(redo_btn)
        
        # Add welcome tab
        self.create_welcome_tab()
        
        # Store tab IDs
        self.tab_ids = {
            "info": None,
            "contact": None,
            "address": None
        }
        
        # Reverse mapping from tab_id to tab_type
        self.tab_id_to_type = {}
    
    def create_welcome_tab(self):
        """Create a welcome tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel(
            "Welcome to the Simple Dynamic Tabs Demo!\n\n"
            "Use the buttons above to add different types of tabs.\n"
            "Edit the fields and use Undo/Redo to see automatic navigation."
        )
        label.setWordWrap(True)
        
        layout.addWidget(label)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Welcome")
    
    def create_info_tab(self):
        """Factory function to create an info tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        name_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_EDIT_END)
        name_edit.bind_to_model(self.person, "name")
        layout.addRow("Name:", name_edit)
        
        return tab
    
    def create_contact_tab(self):
        """Factory function to create a contact tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        email_edit = CommandLineEdit(execution_mode=CommandExecutionMode.DELAYED)
        email_edit.bind_to_model(self.person, "email")
        layout.addRow("Email:", email_edit)
        
        return tab
    
    def create_address_tab(self):
        """Factory function to create an address tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        address_edit = CommandLineEdit(execution_mode=CommandExecutionMode.ON_CHANGE)
        address_edit.bind_to_model(self.person, "address")
        layout.addRow("Address:", address_edit)
        
        return tab
    
    def add_info_tab(self):
        """Add an info tab if it doesn't exist."""
        if self.tab_ids["info"] is None:
            tab_id = self.tab_widget.add_tab(self.info_tab_type)
            self.tab_ids["info"] = tab_id
            self.tab_id_to_type[tab_id] = "info"
    
    def add_contact_tab(self):
        """Add a contact tab if it doesn't exist."""
        if self.tab_ids["contact"] is None:
            tab_id = self.tab_widget.add_tab(self.contact_tab_type)
            self.tab_ids["contact"] = tab_id
            self.tab_id_to_type[tab_id] = "contact"
    
    def add_address_tab(self):
        """Add an address tab if it doesn't exist."""
        if self.tab_ids["address"] is None:
            tab_id = self.tab_widget.add_tab(self.address_tab_type)
            self.tab_ids["address"] = tab_id
            self.tab_id_to_type[tab_id] = "address"
    
    def handle_tab_close(self, index):
        """Handle tab closing and update tracking."""
        # Skip welcome tab (index 0)
        if index == 0:
            return
        
        # Find which tab type this is
        widget = self.tab_widget.widget(index)
        tab_id_to_remove = None
        
        # Find the tab ID that corresponds to this widget
        for tab_id, instances in self.tab_widget._content_instances.items():
            if instances.get('widget') == widget:
                tab_id_to_remove = tab_id
                break
        
        if tab_id_to_remove:
            # Check if this tab type is closable
            tab_type = self.tab_id_to_type.get(tab_id_to_remove)
            
            if tab_type:
                # Get tab type info
                content_type_id = self.tab_widget._content_instances[tab_id_to_remove].get('type_id')
                content_type = self.tab_widget._content_types.get(content_type_id, {})
                
                # Only allow closing if the tab is closable
                if content_type.get('closable', True):
                    self.tab_ids[tab_type] = None
                    del self.tab_id_to_type[tab_id_to_remove]
                    
                    # Let the tab widget close it properly
                    self.tab_widget.close_content(tab_id_to_remove)
                else:
                    # This tab is not closable - don't close it
                    print(f"Tab '{content_type.get('display_name', 'Unknown')}' is not closable")
        else:
            # Fallback to direct removal for non-tracked tabs
            self.tab_widget.removeTab(index)# Find the tab ID that corresponds to this widget
        for tab_id, instances in self.tab_widget._content_instances.items():
            if instances.get('widget') == widget:
                tab_id_to_remove = tab_id
                break
        
        if tab_id_to_remove:
            # Update our tracking
            tab_type = self.tab_id_to_type.get(tab_id_to_remove)
            if tab_type:
                self.tab_ids[tab_type] = None
                del self.tab_id_to_type[tab_id_to_remove]
            
            # Let the tab widget close it properly
            self.tab_widget.close_content(tab_id_to_remove)
        else:
            # Fallback to direct removal
            self.tab_widget.removeTab(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SimpleTabsDemo()
    demo.show()
    sys.exit(app.exec())