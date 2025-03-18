"""
Usage example for the command system.

This module demonstrates how to use the command system in PySignalDecipher.
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QLabel, QListWidget, QMenu, QInputDialog,
    QComboBox, QDockWidget, QTabWidget
)
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QSize
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import numpy as np
import sys
import uuid

# Import command system components
from command_system import CommandManager
from command_system.project import Project, SignalData, WorkspaceState
from command_system.observable import SignalVariable, PropertyChangeCommand
from command_system.variable_registry import VariableRegistry
from command_system.hardware_manager import HardwareManager
from command_system.workspace_manager import WorkspaceTabManager
from command_system.commands import (
    AddSignalCommand, RenameSignalCommand, RemoveSignalCommand,
    RenameProjectCommand, CreateDockCommand
)


class MainWindow(QMainWindow):
    """Example main window demonstrating the command system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySignalDecipher - Command System Example")
        self.resize(1200, 800)
        
        # Set up the command manager and related components
        self._command_manager = CommandManager()
        self._variable_registry = self._command_manager.get_variable_registry()
        self._hardware_manager = self._command_manager.get_hardware_manager()
        self._workspace_manager = self._command_manager.get_workspace_manager()
        
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
        
        # Add utility group section at top
        utility_layout = QHBoxLayout()
        main_layout.addLayout(utility_layout)
        
        # Hardware utility group
        hardware_group = QWidget()
        hardware_layout = QVBoxLayout(hardware_group)
        
        hardware_label = QLabel("Hardware Utility Group")
        hardware_layout.addWidget(hardware_label)
        
        self._device_combo = QComboBox()
        hardware_layout.addWidget(self._device_combo)
        
        refresh_button = QPushButton("Refresh Devices")
        refresh_button.clicked.connect(self._refresh_devices)
        hardware_layout.addWidget(refresh_button)
        
        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self._connect_device)
        hardware_layout.addWidget(connect_button)
        
        utility_layout.addWidget(hardware_group)
        
        # Options utility group
        options_group = QWidget()
        options_layout = QVBoxLayout(options_group)
        
        options_label = QLabel("Workspace Options")
        options_layout.addWidget(options_label)
        
        # Add workspace-specific options here
        self._options_widget = QWidget()
        self._options_layout = QVBoxLayout(self._options_widget)
        options_layout.addWidget(self._options_widget)
        
        utility_layout.addWidget(options_group)
        
        # Add a third utility group placeholder
        third_group = QWidget()
        third_layout = QVBoxLayout(third_group)
        
        third_label = QLabel("Third Utility Group")
        third_layout.addWidget(third_label)
        
        utility_layout.addWidget(third_group)
        
        # Add workspace tabs
        self._workspace_tabs = QTabWidget()
        self._workspace_tabs.setTabsClosable(True)
        self._workspace_tabs.tabCloseRequested.connect(self._close_workspace_tab)
        self._workspace_tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self._workspace_tabs)
        
        # Create default workspace
        self._create_default_workspace()
        
        # Create buttons for workspace manipulation
        workspace_buttons_layout = QHBoxLayout()
        
        new_workspace_button = QPushButton("New Workspace")
        new_workspace_button.clicked.connect(self._create_new_workspace)
        workspace_buttons_layout.addWidget(new_workspace_button)
        
        main_layout.addLayout(workspace_buttons_layout)
        
        # Project manipulation section
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
        
        # Buttons for signal manipulation
        signal_buttons_layout = QHBoxLayout()
        
        add_signal_button = QPushButton("Add Signal")
        add_signal_button.clicked.connect(self._add_signal)
        signal_buttons_layout.addWidget(add_signal_button)
        
        remove_signal_button = QPushButton("Remove Signal")
        remove_signal_button.clicked.connect(self._remove_selected_signal)
        signal_buttons_layout.addWidget(remove_signal_button)
        
        rename_signal_button = QPushButton("Rename Signal")
        rename_signal_button.clicked.connect(self._rename_selected_signal)
        signal_buttons_layout.addWidget(rename_signal_button)
        
        main_layout.addLayout(signal_buttons_layout)
        
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
    
    def _create_default_workspace(self):
        """Create the default workspace."""
        # Create the basic workspace
        workspace_id = uuid.uuid4().hex
        
        # Create a workspace widget
        workspace_widget = WorkspaceWidget(workspace_id, self._command_manager)
        
        # Add to tabs
        self._workspace_tabs.addTab(workspace_widget, "Basic Analysis")
        workspace_widget.setProperty("workspace_id", workspace_id)
        
        # Register with workspace manager
        self._workspace_manager.create_workspace("basic", "Basic Analysis")
        self._workspace_manager.set_active_workspace(workspace_id)
    
    def _create_new_workspace(self):
        """Create a new workspace tab."""
        # Get workspace type and name
        workspace_types = ["basic", "protocol_decoder", "pattern_recognition", "signal_separation"]
        
        # In a real app, this would be a dialog
        workspace_type = workspace_types[0]  # Default to basic
        workspace_name = f"Workspace {self._workspace_tabs.count() + 1}"
        
        # Create workspace in the manager
        workspace_id = self._workspace_manager.create_workspace(workspace_type, workspace_name)
        
        # Create workspace widget
        workspace_widget = WorkspaceWidget(workspace_id, self._command_manager)
        
        # Add to tabs
        index = self._workspace_tabs.addTab(workspace_widget, workspace_name)
        workspace_widget.setProperty("workspace_id", workspace_id)
        
        # Select the new tab
        self._workspace_tabs.setCurrentIndex(index)
    
    def _close_workspace_tab(self, index):
        """Handle tab close request."""
        # Don't allow closing the last tab
        if self._workspace_tabs.count() <= 1:
            return
        
        workspace_widget = self._workspace_tabs.widget(index)
        workspace_id = workspace_widget.property("workspace_id")
        
        # Remove the tab
        self._workspace_tabs.removeTab(index)
        workspace_widget.deleteLater()
        
        # Clean up workspace resources
        self._workspace_manager.remove_workspace(workspace_id)
    
    def _on_tab_changed(self, index):
        """Handle tab selection change."""
        if index >= 0:
            workspace_widget = self._workspace_tabs.widget(index)
            workspace_id = workspace_widget.property("workspace_id")
            
            # Notify workspace manager of active workspace change
            self._workspace_manager.set_active_workspace(workspace_id)
            
            # Update options UI based on workspace type
            self._update_workspace_options(workspace_id)
    
    def _update_workspace_options(self, workspace_id):
        """Update options UI based on workspace type."""
        # Clear current options
        for i in reversed(range(self._options_layout.count())): 
            widget = self._options_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Get workspace type
        workspace_type = self._workspace_manager.get_workspace_type(workspace_id)
        
        # Add options based on workspace type
        if workspace_type == "basic":
            # Add basic analysis options
            self._options_layout.addWidget(QLabel("Basic Analysis Options"))
            
            add_signal_viewer = QPushButton("Add Signal Viewer")
            add_signal_viewer.clicked.connect(
                lambda: self._add_dock_to_current_workspace("signal_viewer")
            )
            self._options_layout.addWidget(add_signal_viewer)
            
            add_measurement = QPushButton("Add Measurement Panel")
            self._options_layout.addWidget(add_measurement)
            
        elif workspace_type == "protocol_decoder":
            # Add protocol decoder options
            self._options_layout.addWidget(QLabel("Protocol Decoder Options"))
            
            protocol_combo = QComboBox()
            protocol_combo.addItems(["UART", "I2C", "SPI", "CAN"])
            self._options_layout.addWidget(protocol_combo)
            
            decode_button = QPushButton("Add Decoder")
            self._options_layout.addWidget(decode_button)
            
        elif workspace_type == "pattern_recognition":
            # Add pattern recognition options
            self._options_layout.addWidget(QLabel("Pattern Recognition Options"))
            
            learn_button = QPushButton("Learn Pattern")
            self._options_layout.addWidget(learn_button)
            
            match_button = QPushButton("Match Patterns")
            self._options_layout.addWidget(match_button)
    
    def _add_dock_to_current_workspace(self, dock_type):
        """Add a dock widget to the current workspace."""
        index = self._workspace_tabs.currentIndex()
        if index >= 0:
            workspace_widget = self._workspace_tabs.widget(index)
            workspace_widget.add_dock_widget(dock_type)
    
    def _refresh_devices(self):
        """Refresh the list of available devices."""
        self._device_combo.clear()
        
        # Get available devices
        devices = self._hardware_manager.get_available_devices()
        
        # Add to combo box
        for device in devices:
            self._device_combo.addItem(device)
    
    def _connect_device(self):
        """Connect to the selected device."""
        selected_device = self._device_combo.currentText()
        if selected_device:
            # Connect to the device
            device_id = self._hardware_manager.connect_device(selected_device)
            
            if device_id:
                # Get device variables
                variables = self._variable_registry.get_variables_by_parent(device_id)
                
                # Show connected status
                self._device_combo.setToolTip(f"Connected: {device_id}")
                
                # For demo purposes, print the variables
                print(f"Connected to device: {device_id}")
                print(f"Variables: {[var.name for var in variables]}")
    
    def _update_ui(self):
        """Update the UI to reflect the current state."""
        # Update project name
        self._project_name_label.setText(self._project.name)
        
        # Update signals list
        self._update_signals_list()
        
        # Update undo/redo buttons
        self._update_undo_button(self._command_manager.can_undo())
        self._update_redo_button(self._command_manager.can_redo())
    
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
        # Create a simple test signal
        t = np.linspace(0, 10, 1000)
        data = np.sin(t) + 0.1 * np.random.randn(len(t))
        
        # Create a signal with the data
        signal = SignalData(f"Signal {len(self._project.get_all_signals()) + 1}")
        signal.set_data(data)
        
        # Create and execute the command
        command = AddSignalCommand(self._project, signal)
        self._command_manager.execute_command(command)
        
        # Update UI
        self._update_ui()
        
        # Notify any signal viewers about the new signal
        if signal.id in self._project.get_all_signals():
            # Link signal to any signal viewers that might be interested
            self._link_signal_to_viewers(signal)
    
    def _link_signal_to_viewers(self, signal):
        """Link a signal to any interested signal viewers."""
        # Iterate through all workspaces and find signal viewer docks
        for i in range(self._workspace_tabs.count()):
            workspace = self._workspace_tabs.widget(i)
            if hasattr(workspace, 'dock_widgets'):
                for dock_id, dock in workspace.dock_widgets.items():
                    if hasattr(dock, 'signal_data_var'):
                        # This is a signal viewer dock, offer to link the signal
                        dock.set_signal(signal)
    
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


class WorkspaceWidget(QWidget):
    """
    Widget representing a workspace.
    
    Contains dock widgets and provides workspace-specific functionality.
    """
    
    def __init__(self, workspace_id, command_manager):
        super().__init__()
        self.workspace_id = workspace_id
        self.command_manager = command_manager
        
        # Set up layout
        self.layout = QVBoxLayout(self)
        self.setProperty("workspace_id", workspace_id)
        
        # Store dock widgets
        self.dock_widgets = {}
        
        # Get workspace state from project
        project = command_manager.get_active_project()
        self.workspace_state = project.get_workspace_state(workspace_id)
    
    def add_dock_widget(self, dock_type):
        """Add a dock widget to the workspace."""
        # Create command to add dock
        command = CreateDockCommand(self.workspace_state, dock_type)
        self.command_manager.execute_command(command)
        
        # Get dock ID from command
        dock_id = command.dock_id
        
        # Create appropriate dock widget
        if dock_type == "signal_viewer":
            dock = SignalViewerDock(dock_id, self.command_manager, self)
        else:
            # Generic dock widget for other types
            dock = QDockWidget(f"Dock {dock_id}", self)
            content = QWidget()
            layout = QVBoxLayout(content)
            layout.addWidget(QLabel(f"Content for {dock_type}"))
            dock.setWidget(content)
        
        # Add to layout
        self.layout.addWidget(dock)
        
        # Store in dictionary
        self.dock_widgets[dock_id] = dock
        
        return dock
    
    def remove_dock_widget(self, dock_id):
        """Remove a dock widget."""
        if dock_id in self.dock_widgets:
            # Get the dock widget
            dock = self.dock_widgets[dock_id]
            
            # Remove from layout
            self.layout.removeWidget(dock)
            
            # Delete the widget
            dock.deleteLater()
            
            # Remove from dictionary
            del self.dock_widgets[dock_id]
            
            # Update workspace state
            from command_system.commands.workspace_commands import RemoveDockCommand
            command = RemoveDockCommand(self.workspace_state, dock_id)
            self.command_manager.execute_command(command)


class SignalViewerDock(QWidget):
    """
    Dock widget for viewing signal data.
    
    Uses PyQtGraph for plotting and demonstrates variable linking.
    """
    
    def __init__(self, dock_id, command_manager, parent=None):
        super().__init__(parent)
        self.dock_id = dock_id
        self.command_manager = command_manager
        self.variable_registry = command_manager.get_variable_registry()
        
        # Set up widget
        self.layout = QVBoxLayout(self)
        
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("Signal View")
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(self.chart_view)

        # Create axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Samples")
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Amplitude")
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Signal selector
        self.signal_combo = QComboBox()
        self.signal_combo.currentIndexChanged.connect(self._on_signal_selected)
        controls_layout.addWidget(QLabel("Signal:"))
        controls_layout.addWidget(self.signal_combo)
        
        # Vertical scale control
        v_scale_label = QLabel("V Scale:")
        controls_layout.addWidget(v_scale_label)
        
        self.v_scale_spinner = QComboBox()
        self.v_scale_spinner.addItems(["0.1", "0.2", "0.5", "1.0", "2.0", "5.0"])
        self.v_scale_spinner.setCurrentText("1.0")
        self.v_scale_spinner.currentTextChanged.connect(self._on_v_scale_changed)
        controls_layout.addWidget(self.v_scale_spinner)
        
        # Horizontal scale control
        h_scale_label = QLabel("H Scale:")
        controls_layout.addWidget(h_scale_label)
        
        self.h_scale_spinner = QComboBox()
        self.h_scale_spinner.addItems(["0.1", "0.2", "0.5", "1.0", "2.0", "5.0"])
        self.h_scale_spinner.setCurrentText("1.0")
        self.h_scale_spinner.currentTextChanged.connect(self._on_h_scale_changed)
        controls_layout.addWidget(self.h_scale_spinner)
        
        self.layout.addLayout(controls_layout)
        
        # Create variables
        self._create_variables()
        
        # Populate signal list
        self._update_signal_list()
    
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
    
    def _update_signal_list(self):
        """Update the signal selection combo box."""
        self.signal_combo.clear()
        
        project = self.command_manager.get_active_project()
        signals = project.get_all_signals()
        
        # Add "None" option
        self.signal_combo.addItem("None", None)
        
        # Add all signals
        for signal_id, signal in signals.items():
            self.signal_combo.addItem(signal.name, signal_id)
    
    def _on_signal_selected(self, index):
        """Handle signal selection."""
        if index <= 0:  # None selected
            self.signal_data_var.set_value(None)
            return
        
        signal_id = self.signal_combo.currentData()
        project = self.command_manager.get_active_project()
        signal = project.get_signal(signal_id)
        
        if signal:
            # Set signal data
            self.set_signal(signal)
    
    def set_signal(self, signal):
        """Set the signal to display."""
        # Set the signal data variable
        self.signal_data_var.set_value({
            'data': signal.get_data(),
            'name': signal.name,
            'id': signal.id
        })
        
        # Update combo box selection
        for i in range(self.signal_combo.count()):
            if self.signal_combo.itemData(i) == signal.id:
                self.signal_combo.setCurrentIndex(i)
                break
    
    def _on_v_scale_changed(self, value_text):
        """Handle vertical scale UI change."""
        try:
            value = float(value_text)
            if value != self.vertical_scale_var.value:
                self.vertical_scale_var.set_value(value)
        except ValueError:
            pass
    
    def _on_h_scale_changed(self, value_text):
        """Handle horizontal scale UI change."""
        try:
            value = float(value_text)
            if value != self.horizontal_scale_var.value:
                self.horizontal_scale_var.set_value(value)
        except ValueError:
            pass
    
    def _on_signal_data_changed(self, data):
        """Handle signal data changes."""
        self.plot_widget.clear()
        
        if data is None:
            return
            
        # Plot the data
        signal_data = data.get('data')
        if signal_data is not None and len(signal_data) > 0:
            self.plot_widget.plot(signal_data)
            
            # Update scales
            self._on_vertical_scale_changed(self.v_scale_spinner.currentText())
            self._on_horizontal_scale_changed(self.h_scale_spinner.currentText())
    
    def _on_vertical_scale_changed(self, value):
        """Handle vertical scale changes."""
        # Update plot scale
        if hasattr(self.plot_widget, 'getViewBox'):
            data = self.signal_data_var.value
            if data is not None and 'data' in data:
                signal_data = data['data']
                if len(signal_data) > 0:
                    max_val = max(abs(np.max(signal_data)), abs(np.min(signal_data)))
                    self.plot_widget.getViewBox().setYRange(-max_val * value, max_val * value)
    
    def _on_horizontal_scale_changed(self, value):
        """Handle horizontal scale changes."""
        # Update plot scale
        if hasattr(self.plot_widget, 'getViewBox'):
            data = self.signal_data_var.value
            if data is not None and 'data' in data:
                signal_data = data['data']
                if len(signal_data) > 0:
                    self.plot_widget.getViewBox().setXRange(0, len(signal_data) * value)
    
    def closeEvent(self, event):
        """Handle close event."""
        # Unsubscribe from variables
        self.signal_data_var.unsubscribe(self.dock_id)
        self.vertical_scale_var.unsubscribe(self.dock_id)
        self.horizontal_scale_var.unsubscribe(self.dock_id)
        
        # Unregister variables
        variable_registry = self.variable_registry
        variable_registry.unregister_parent(self.dock_id)
        
        # Remove from parent workspace if applicable
        parent = self.parent()
        if parent and hasattr(parent, "remove_dock_widget"):
            parent.remove_dock_widget(self.dock_id)
        
        # Accept the event
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set app style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())