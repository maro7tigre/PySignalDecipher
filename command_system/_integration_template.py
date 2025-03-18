"""
Integration template for PySignalDecipher's command system.

This module provides templates and guidelines for integrating the
command system with the application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QDockWidget, QApplication, QMenuBar, QToolBar, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QObject

import sys
import uuid

# Import command system components
from command_system import CommandManager
from command_system.project import Project, SignalData, WorkspaceState
from command_system.variable_registry import VariableRegistry
from command_system.hardware_manager import HardwareManager
from command_system.workspace_manager import WorkspaceTabManager
from command_system.observable import PropertyChangeCommand
from command_system.commands.workspace_commands import CreateDockCommand
from command_system.command_history import CommandHistory
from command_system.signal_variable import SignalVariable


# Step 1: Create the main application class
class PySignalDecipherApp:
    """
    Main application class integrating all command system components.
    
    This class serves as the central integration point for all
    subsystems including the command system, variable registry,
    hardware manager, and UI components.
    """
    
    def __init__(self):
        # Initialize command manager (central component)
        self.command_manager = CommandManager()
        
        # Get references to subsystems
        self.variable_registry = self.command_manager.get_variable_registry()
        self.hardware_manager = self.command_manager.get_hardware_manager()
        self.workspace_manager = self.command_manager.get_workspace_manager()
        
        # Create a new project
        self.project = Project("Untitled Project")
        self.project.set_command_manager(self.command_manager)
        
        # Register command types
        self._register_commands()
        
        # Initialize UI
        self._init_ui()
    
    def _register_commands(self):
        """Register all command types with the command factory."""
        # Import and register commands
        from command_system.commands import (
            AddSignalCommand, RemoveSignalCommand, RenameSignalCommand,
            ChangeLayoutCommand, SetDockStateCommand, SetWorkspaceSettingCommand,
            RenameProjectCommand, BatchCommand, CreateDockCommand, RemoveDockCommand
        )
        
        # Additional command registrations if needed
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create application and main window
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow(self.command_manager)
        
        # Set up utility groups
        self._setup_utility_groups()
        
        # Create initial workspace if needed
        if not self.workspace_manager.has_workspaces():
            self._create_default_workspace()
        
        # Show the main window
        self.main_window.show()
    
    def _setup_utility_groups(self):
        """Set up the utility groups in the main window."""
        # Create and add hardware connection utility group
        hardware_widget = HardwareConnectionWidget(self.hardware_manager)
        self.main_window.add_utility_group("hardware", hardware_widget)
        
        # Create and add workspace options utility group
        options_widget = WorkspaceOptionsWidget(self.workspace_manager)
        self.main_window.add_utility_group("options", options_widget)
        
        # Create and add third utility group (if needed)
        # third_widget = ThirdUtilityWidget()
        # self.main_window.add_utility_group("third", third_widget)
    
    def _create_default_workspace(self):
        """Create the default workspace."""
        workspace_id = self.workspace_manager.create_workspace("basic", "Basic Analysis")
        
        # Create workspace widget
        workspace_widget = WorkspaceWidget(workspace_id, self.command_manager)
        
        # Add workspace to main window
        self.main_window.add_workspace_tab(workspace_id, "Basic Analysis", workspace_widget)
    
    def run(self):
        """Run the application."""
        return self.app.exec()


# Step 2: Create the main window class
class MainWindow(QMainWindow):
    """
    Main window for PySignalDecipher.
    
    Provides workspace tabs, utility groups, and menu/toolbar integration.
    """
    
    def __init__(self, command_manager):
        super().__init__()
        self.command_manager = command_manager
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher")
        self.resize(1200, 800)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create top layout with utility groups
        self.utility_layout = QHBoxLayout()
        self.main_layout.addLayout(self.utility_layout)
        
        # Dictionary to store utility group widgets
        self.utility_groups = {}
        
        # Create workspace tabs
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setTabsClosable(True)
        self.workspace_tabs.tabCloseRequested.connect(self._close_workspace_tab)
        self.workspace_tabs.currentChanged.connect(self._on_tab_changed)
        self.main_layout.addWidget(self.workspace_tabs)
        
        # Set up menus and toolbar
        self._setup_menu()
        self._setup_toolbar()
    
    def _setup_menu(self):
        """Set up the application menu."""
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New project action
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        # Open project action
        open_action = QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        # Save project action
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        # Save as action
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo action
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self._undo)
        edit_menu.addAction(self.undo_action)
        
        # Redo action
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self._redo)
        edit_menu.addAction(self.redo_action)
        
        # Register for undo/redo state changes
        self.command_manager.register_history_observers(
            lambda can_undo: self.undo_action.setEnabled(can_undo),
            lambda can_redo: self.redo_action.setEnabled(can_redo)
        )
        
        # Workspace menu
        workspace_menu = menubar.addMenu("&Workspace")
        
        # New workspace action
        new_workspace_action = QAction("&New Workspace", self)
        new_workspace_action.triggered.connect(self._create_workspace)
        workspace_menu.addAction(new_workspace_action)
        
        # Add more menus as needed
    
    def _setup_toolbar(self):
        """Set up the application toolbar."""
        # Main toolbar
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Add toolbar actions
        # (similar to menu actions)
    
    def add_utility_group(self, group_id, widget):
        """Add a utility group widget to the top layout."""
        if group_id in self.utility_groups:
            # Replace existing widget
            old_widget = self.utility_groups[group_id]
            self.utility_layout.replaceWidget(old_widget, widget)
            old_widget.deleteLater()
        else:
            # Add new widget
            self.utility_layout.addWidget(widget)
        
        self.utility_groups[group_id] = widget
    
    def add_workspace_tab(self, workspace_id, name, widget):
        """Add a workspace tab."""
        index = self.workspace_tabs.addTab(widget, name)
        widget.setProperty("workspace_id", workspace_id)
        return index
    
    def _on_tab_changed(self, index):
        """Handle tab selection change."""
        if index >= 0:
            workspace_widget = self.workspace_tabs.widget(index)
            workspace_id = workspace_widget.property("workspace_id")
            
            # Notify workspace manager of active workspace change
            workspace_manager = self.command_manager.get_workspace_manager()
            workspace_manager.set_active_workspace(workspace_id)
    
    def _close_workspace_tab(self, index):
        """Handle tab close request."""
        # Don't allow closing the last tab
        if self.workspace_tabs.count() <= 1:
            return
        
        workspace_widget = self.workspace_tabs.widget(index)
        workspace_id = workspace_widget.property("workspace_id")
        
        # Ask for confirmation if necessary
        
        # Remove the tab
        self.workspace_tabs.removeTab(index)
        workspace_widget.deleteLater()
        
        # Clean up workspace resources
        workspace_manager = self.command_manager.get_workspace_manager()
        workspace_manager.remove_workspace(workspace_id)
    
    def _new_project(self):
        """Create a new project."""
        # Confirm if current project has unsaved changes
        
        # Create new project
        project = Project("Untitled Project")
        project.set_command_manager(self.command_manager)
        
        # Close all tabs and create default workspace
        # Reset application state
    
    def _open_project(self):
        """Open a project from file."""
        # Show file dialog
        
        # Load project
        # project = Project.load(filename, self.command_manager)
    
    def _save_project(self):
        """Save the current project."""
        project = self.command_manager.get_active_project()
        # If project has a filename, save directly
        # Otherwise, show save dialog
    
    def _save_project_as(self):
        """Save the current project with a new filename."""
        # Show save dialog
        
        # Save project
        # project.save(filename)
    
    def _create_workspace(self):
        """Create a new workspace."""
        # Show dialog to select workspace type and name
        
        # Create workspace
        # workspace_id = self.workspace_manager.create_workspace(type, name)
    
    def _undo(self):
        """Undo the last command."""
        self.command_manager.undo()
    
    def _redo(self):
        """Redo the last undone command."""
        self.command_manager.redo()


# Step 3: Create a workspace widget
class WorkspaceWidget(QWidget):
    """
    Workspace widget that can contain multiple dock widgets.
    
    Each workspace represents a different analysis environment
    (e.g. Basic Analysis, Protocol Decoder, Pattern Recognition).
    """
    
    def __init__(self, workspace_id, command_manager):
        super().__init__()
        self.workspace_id = workspace_id
        self.command_manager = command_manager
        
        # Set widget properties
        self.setProperty("workspace_id", workspace_id)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Dictionary to track dock widgets
        self.dock_widgets = {}
        
        # Initialize workspace from state
        self._init_from_state()
    
    def _init_from_state(self):
        """Initialize workspace from saved state."""
        project = self.command_manager.get_active_project()
        workspace_state = project.get_workspace_state(self.workspace_id)
        
        # Restore dock widgets
        for dock_id, dock_state in workspace_state.get_dock_states().items():
            self._create_dock_widget(dock_id, dock_state)
    
    def _create_dock_widget(self, dock_id, dock_state):
        """Create a dock widget from state."""
        # Get dock type
        dock_type = dock_state.get("type", "unknown")
        
        # Create appropriate dock widget based on type
        if dock_type == "signal_viewer":
            dock_widget = SignalViewerDock(dock_id, self.command_manager, self)
        elif dock_type == "spectrum_analyzer":
            # Create spectrum analyzer dock
            pass
        else:
            # Create generic dock
            pass
        
        # Set geometry from saved state
        position = dock_state.get("position", {"x": 0, "y": 0, "width": 300, "height": 200})
        dock_widget.setGeometry(
            position.get("x", 0),
            position.get("y", 0),
            position.get("width", 300),
            position.get("height", 200)
        )
        
        # Add to layout
        self.layout.addWidget(dock_widget)
        
        # Store in dictionary
        self.dock_widgets[dock_id] = dock_widget
        
        return dock_widget
    
    def add_dock_widget(self, dock_type):
        """Add a new dock widget to the workspace."""
        # Create command to add the dock
        project = self.command_manager.get_active_project()
        workspace_state = project.get_workspace_state(self.workspace_id)
        
        command = CreateDockCommand(workspace_state, dock_type)
        self.command_manager.execute_command(command)
        
        # Get the dock ID from the command
        dock_id = command.dock_id
        
        # Create the dock widget
        dock_state = workspace_state.get_dock_state(dock_id)
        dock_widget = self._create_dock_widget(dock_id, dock_state)
        
        return dock_widget
    
    def remove_dock_widget(self, dock_id):
        """Remove a dock widget from the workspace."""
        if dock_id in self.dock_widgets:
            # Get the dock widget
            dock_widget = self.dock_widgets[dock_id]
            
            # Remove from layout and dictionary
            self.layout.removeWidget(dock_widget)
            del self.dock_widgets[dock_id]
            
            # Delete the widget
            dock_widget.deleteLater()
            
            # Remove from workspace state
            project = self.command_manager.get_active_project()
            workspace_state = project.get_workspace_state(self.workspace_id)
            
            from command_system.commands.workspace_commands import RemoveDockCommand
            command = RemoveDockCommand(workspace_state, dock_id)
            self.command_manager.execute_command(command)


# Step 4: Create utility group widgets
class HardwareConnectionWidget(QWidget):
    """
    Utility group widget for hardware connection.
    
    Provides UI for discovering, connecting to, and configuring hardware devices.
    """
    
    def __init__(self, hardware_manager):
        super().__init__()
        self.hardware_manager = hardware_manager
        
        # Set up UI
        self.layout = QVBoxLayout(self)
        
        # Create UI elements
        self._create_ui()
        
        # Initialize device list
        self._refresh_devices()
    
    def _create_ui(self):
        """Create UI elements."""
        # Device selection combo box
        # Refresh button
        # Connect button
        # Device status indicator
        # Additional configuration options
        pass
    
    def _refresh_devices(self):
        """Refresh the list of available devices."""
        devices = self.hardware_manager.get_available_devices()
        # Update UI with available devices
        pass
    
    def _connect_selected_device(self):
        """Connect to the selected device."""
        # Get selected device
        # Connect via hardware manager
        # Update UI to show connected state
        pass


class WorkspaceOptionsWidget(QWidget):
    """
    Utility group widget for workspace options.
    
    Provides UI elements specific to the current workspace type.
    """
    
    def __init__(self, workspace_manager):
        super().__init__()
        self.workspace_manager = workspace_manager
        
        # Set up UI
        self.layout = QVBoxLayout(self)
        
        # Create UI elements
        self._create_ui()
        
        # Connect to workspace change events
        self.workspace_manager.workspace_changed.connect(self._update_options)
    
    def _create_ui(self):
        """Create UI elements."""
        # Options will be populated based on active workspace
        pass
    
    def _update_options(self, workspace_id):
        """Update options based on workspace type."""
        # Clear current options
        
        # Get workspace type
        workspace_type = self.workspace_manager.get_workspace_type(workspace_id)
        
        # Add options specific to the workspace type
        if workspace_type == "basic":
            # Add basic analysis options
            pass
        elif workspace_type == "protocol_decoder":
            # Add protocol decoder options
            pass
        elif workspace_type == "pattern_recognition":
            # Add pattern recognition options
            pass
        # Add other workspace types as needed


# Step 5: Create a dock widget example
class SignalViewerDock(QDockWidget):
    """
    Dock widget for viewing signal data.
    
    Provides a graphical display of signal data with zoom, pan, and measurement tools.
    """
    
    def __init__(self, dock_id, command_manager, parent=None):
        super().__init__(parent)
        self.dock_id = dock_id
        self.command_manager = command_manager
        self.variable_registry = command_manager.get_variable_registry()
        
        # Set properties
        self.setWindowTitle("Signal Viewer")
        self.setObjectName(f"signal_viewer_{dock_id}")
        
        # Create widget content
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        self.layout = QVBoxLayout(self.content_widget)
        
        # Create variables associated with this dock
        self._create_variables()
        
        # Create UI elements
        self._create_ui()
    
    def _create_variables(self):
        """Create variables associated with this dock."""
        # Signal data variable
        self.signal_data_var = SignalVariable("signal_data", None, self.dock_id)
        self.variable_registry.register_variable(self.signal_data_var)
        
        # Display settings variables
        self.vertical_scale_var = SignalVariable("vertical_scale", 1.0, self.dock_id)
        self.variable_registry.register_variable(self.vertical_scale_var)
        
        self.horizontal_scale_var = SignalVariable("horizontal_scale", 1.0, self.dock_id)
        self.variable_registry.register_variable(self.horizontal_scale_var)
        
        # Subscribe to our own variables
        self.signal_data_var.subscribe(self.dock_id, self._on_signal_data_changed)
        self.vertical_scale_var.subscribe(self.dock_id, self._on_vertical_scale_changed)
        self.horizontal_scale_var.subscribe(self.dock_id, self._on_horizontal_scale_changed)
    
    def _create_ui(self):
        """Create UI elements."""
        # Create UI elements for the signal viewer
        # (This would include a plotting widget and controls)
        pass
    
    def _on_signal_data_changed(self, data):
        """Handle signal data changes."""
        if data is not None:
            # Update plot
            pass
    
    def _on_vertical_scale_changed(self, value):
        """Handle vertical scale changes."""
        # Update plot scale
        pass
    
    def _on_horizontal_scale_changed(self, value):
        """Handle horizontal scale changes."""
        # Update plot scale
        pass
    
    def closeEvent(self, event):
        """Clean up when dock is closed."""
        # Unsubscribe from variables
        self.signal_data_var.unsubscribe(self.dock_id)
        self.vertical_scale_var.unsubscribe(self.dock_id)
        self.horizontal_scale_var.unsubscribe(self.dock_id)
        
        # Remove the dock widget from the workspace
        parent = self.parent()
        if parent and hasattr(parent, "remove_dock_widget"):
            parent.remove_dock_widget(self.dock_id)
        
        # Let the parent handle the event
        super().closeEvent(event)


# Example implementation of the VariableRegistry class
class VariableRegistry:
    """
    Central registry for all variables in the application.
    
    Manages variable lifecycles and parent-child relationships.
    """
    
    def __init__(self):
        self._variables = {}  # All variables by ID
        self._parent_map = {}  # Dict mapping parent_id to list of variable IDs
    
    def register_variable(self, variable):
        """Register a variable in the system."""
        self._variables[variable.id] = variable
        
        # Add to parent mapping if applicable
        if variable.parent_id:
            if variable.parent_id not in self._parent_map:
                self._parent_map[variable.parent_id] = []
            self._parent_map[variable.parent_id].append(variable.id)
    
    def unregister_variable(self, variable_id):
        """Remove a variable from the registry."""
        if variable_id in self._variables:
            variable = self._variables[variable_id]
            
            # Clean up parent mapping
            if variable.parent_id and variable.parent_id in self._parent_map:
                if variable_id in self._parent_map[variable.parent_id]:
                    self._parent_map[variable.parent_id].remove(variable_id)
            
            # Clear all subscribers
            variable.clear_subscribers()
            
            # Remove from registry
            del self._variables[variable_id]
    
    def unregister_parent(self, parent_id):
        """Unregister all variables belonging to a parent."""
        if parent_id in self._parent_map:
            # Make a copy since we'll be modifying during iteration
            variable_ids = self._parent_map[parent_id].copy()
            for variable_id in variable_ids:
                self.unregister_variable(variable_id)
            
            # Clean up parent mapping
            del self._parent_map[parent_id]
    
    def get_variable(self, variable_id):
        """Get a variable by ID."""
        return self._variables.get(variable_id)
    
    def get_variables_by_parent(self, parent_id):
        """Get all variables belonging to a parent."""
        variable_ids = self._parent_map.get(parent_id, [])
        return [self._variables[vid] for vid in variable_ids if vid in self._variables]


# Example implementation of SignalVariable class
class SignalVariable:
    """
    A variable that can be linked to multiple components and notifies
    subscribers when its value changes.
    """
    
    def __init__(self, name, initial_value=None, parent_id=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.parent_id = parent_id  # Store the parent dock/widget ID
        self.value = initial_value
        self._subscribers = {}  # Dictionary of callback functions keyed by subscriber ID
    
    def subscribe(self, subscriber_id, callback):
        """Register a subscriber to be notified of value changes."""
        self._subscribers[subscriber_id] = callback
        # Immediately notify with current value
        callback(self.value)
    
    def unsubscribe(self, subscriber_id):
        """Remove a subscriber."""
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
    
    def clear_subscribers(self):
        """Remove all subscribers."""
        self._subscribers.clear()
    
    def set_value(self, new_value):
        """Set the variable's value and notify subscribers."""
        if self.value != new_value:
            old_value = self.value
            self.value = new_value
            
            # Notify subscribers
            for callback in self._subscribers.values():
                callback(new_value)


# Example implementation of the HardwareManager class
class HardwareManager:
    """
    Manages hardware connections via PyVISA and integrates with the command system.
    """
    
    def __init__(self, variable_registry):
        self.variable_registry = variable_registry
        self.resource_manager = None
        self.devices = {}  # Connected devices
        self.device_variables = {}  # Variables linked to device parameters
    
    def initialize(self):
        """Initialize the hardware manager."""
        import pyvisa
        self.resource_manager = pyvisa.ResourceManager()
    
    def get_available_devices(self):
        """Get list of available devices."""
        if not self.resource_manager:
            self.initialize()
        return list(self.resource_manager.list_resources())
    
    def connect_device(self, resource_name, alias=None):
        """Connect to a device and create variables for its parameters."""
        if not self.resource_manager:
            self.initialize()
            
        try:
            # Connect to device
            device = self.resource_manager.open_resource(resource_name)
            device.timeout = 30000
            device.read_termination = '\n'
            device.write_termination = '\n'
            
            # Store device with optional alias
            device_id = alias or resource_name
            self.devices[device_id] = device
            
            # Create device-specific variables
            self._create_device_variables(device_id, device)
            
            return device_id
        except Exception as e:
            print(f"Error connecting to device: {e}")
            return None
    
    def disconnect_device(self, device_id):
        """Disconnect a device and clean up associated variables."""
        if device_id in self.devices:
            # Close connection
            try:
                self.devices[device_id].close()
            except:
                pass
            
            # Remove device
            del self.devices[device_id]
            
            # Unregister associated variables
            if device_id in self.device_variables:
                for var_id in self.device_variables[device_id]:
                    self.variable_registry.unregister_variable(var_id)
                del self.device_variables[device_id]
    
    def _create_device_variables(self, device_id, device):
        """Create variables for device parameters."""
        self.device_variables[device_id] = []
        
        # Example: create standard oscilloscope variables
        if self._is_oscilloscope(device):
            # Create common oscilloscope variables
            for channel in range(1, 5):  # Assuming 4 channels
                # Channel enable variable
                ch_enable_var = SignalVariable(
                    f"CH{channel}_ENABLE", 
                    False, 
                    device_id
                )
                self.variable_registry.register_variable(ch_enable_var)
                self.device_variables[device_id].append(ch_enable_var.id)
                
                # Subscribe to changes to update hardware
                ch_enable_var.subscribe(
                    f"{device_id}_ch{channel}_enable_hw",
                    lambda value, ch=channel: self._set_channel_enable(device_id, ch, value)
                )
                
                # Add more variables like vertical scale, coupling, etc.
    
    def _is_oscilloscope(self, device):
        """Determine if device is an oscilloscope."""
        try:
            idn = device.query("*IDN?")
            # Check for known oscilloscope manufacturers
            return any(name in idn.lower() for name in ["rigol", "tektronix", "keysight", "agilent"])
        except:
            return False
    
    def _set_channel_enable(self, device_id, channel, enable):
        """Set channel enable state on hardware."""
        if device_id in self.devices:
            device = self.devices[device_id]
            try:
                device.write(f":CHAN{channel}:DISP {'ON' if enable else 'OFF'}")
            except Exception as e:
                print(f"Error setting channel {channel} enable to {enable}: {e}")


# Example implementation of the WorkspaceTabManager class
class WorkspaceTabManager(QObject):
    """
    Manages different workspace tabs and their associated commands/variables.
    """
    
    # Signals
    workspace_changed = Signal(str)  # Emitted when active workspace changes
    
    def __init__(self, command_manager, variable_registry):
        super().__init__()
        self.command_manager = command_manager
        self.variable_registry = variable_registry
        self.workspaces = {}  # Workspace objects by ID
        self.active_workspace_id = None
    
    def create_workspace(self, workspace_type, name):
        """Create a new workspace tab."""
        # Create a workspace ID
        workspace_id = str(uuid.uuid4())
        
        # Create workspace state in project
        project = self.command_manager.get_active_project()
        workspace_state = project.get_workspace_state(workspace_id)
        
        # Set workspace type and name
        workspace_state.set_setting("type", workspace_type)
        workspace_state.set_setting("name", name)
        
        # Store workspace info
        self.workspaces[workspace_id] = {
            "type": workspace_type,
            "name": name
        }
        
        # Set as active if it's the first workspace
        if not self.active_workspace_id:
            self.set_active_workspace(workspace_id)
        
        return workspace_id
    
    def has_workspaces(self):
        """Check if any workspaces exist."""
        return len(self.workspaces) > 0
    
    def get_workspace_type(self, workspace_id):
        """Get the type of a workspace."""
        if workspace_id in self.workspaces:
            return self.workspaces[workspace_id].get("type")
        return None
    
    def set_active_workspace(self, workspace_id):
        """Set the active workspace."""
        if workspace_id in self.workspaces:
            self.active_workspace_id = workspace_id
            # Update available options based on active workspace
            self._update_workspace_options(workspace_id)
            # Emit signal
            self.workspace_changed.emit(workspace_id)
    
    def get_active_workspace_id(self):
        """Get the active workspace ID."""
        return self.active_workspace_id
    
    def remove_workspace(self, workspace_id):
        """Remove a workspace and clean up resources."""
        if workspace_id in self.workspaces:
            # Unregister associated variables
            self.variable_registry.unregister_parent(workspace_id)
            
            # Remove workspace
            del self.workspaces[workspace_id]
            
            # Update active workspace if needed
            if self.active_workspace_id == workspace_id:
                if self.workspaces:
                    # Set first available workspace as active
                    self.set_active_workspace(next(iter(self.workspaces)))
                else:
                    self.active_workspace_id = None
    
    def _update_workspace_options(self, workspace_id):
        """Update available options based on workspace type."""
        workspace_type = self.get_workspace_type(workspace_id)
        
        # This would emit signals to update the UI or notify other components
        # about the workspace type change


# Example of extending the CommandManager to include the new subsystems
class CommandManager(QObject):
    """
    Central manager for the command system.
    
    Coordinates command execution, history, and provides signals
    for command-related events to update the UI.
    """
    
    # Signals
    command_executed = Signal(object)  # Emitted when a command is executed
    command_undone = Signal(object)    # Emitted when a command is undone
    command_redone = Signal(object)    # Emitted when a command is redone
    history_changed = Signal()         # Emitted when the history state changes
    
    def __init__(self):
        """Initialize the command manager."""
        super().__init__()
        
        self._command_history = CommandHistory()
        self._active_project = None  # Will be set later
        
        # New components
        self._variable_registry = VariableRegistry()
        self._hardware_manager = HardwareManager(self._variable_registry)
        self._workspace_manager = WorkspaceTabManager(self, self._variable_registry)
        
        # Register for internal signals
        self.command_executed.connect(self._on_history_change)
        self.command_undone.connect(self._on_history_change)
        self.command_redone.connect(self._on_history_change)
    
    def get_variable_registry(self):
        """Get the variable registry."""
        return self._variable_registry
    
    def get_hardware_manager(self):
        """Get the hardware manager."""
        return self._hardware_manager
    
    def get_workspace_manager(self):
        """Get the workspace manager."""
        return self._workspace_manager
    
    # Rest of the CommandManager methods...
    # (execute_command, undo, redo, etc.)


# This completes the integration template with examples of all the major components