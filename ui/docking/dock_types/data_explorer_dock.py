"""
Data Explorer Dock for PySignalDecipher.

This dock provides a user interface for exploring data available in the data registry,
seeing what data is available, and monitoring changes.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QApplication,
    QPushButton, QLineEdit, QMenu, QTextEdit, QSplitter, QComboBox,
    QCheckBox, QTabWidget
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize, QTimer

from .dockable_widget import DockableWidget
from core.service_registry import ServiceRegistry
from core.data_registry import get_data_registry


class DataExplorerDock(DockableWidget):
    """
    Dock widget for exploring and monitoring the data registry.
    
    Provides a tree view of all available data, details about selected data,
    and a live view of data changes.
    """
    
    def __init__(self, title="Data Explorer", parent=None, widget_id=None):
        """
        Initialize the data explorer dock.
        
        Args:
            title: Title for the dock widget
            parent: Parent widget
            widget_id: Unique identifier for this widget
        """
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"data_explorer_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Access application services through ServiceRegistry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._data_registry = get_data_registry()
        
        # Set up the content widget
        self._setup_content()
        
        # Register our own data
        self.register_data(
            data_id="selected_data_path",
            description="Currently selected data path in the explorer",
            initial_value=None
        )
        
        # Update the tree on a timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_data_tree)
        self._update_timer.start(2000)  # Update every 2 seconds
        
        # Initialize the data tree
        self._update_data_tree()
        
        # Subscribe to data changed events
        self._data_registry._notifier.data_changed.connect(self._on_data_changed)
    
    def _setup_content(self):
        """Set up the content widget for the data explorer."""
        # Create a layout for the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create a splitter for tree and details
        splitter = QSplitter(Qt.Vertical)
        
        # Create the top panel (tree and search)
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search controls
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search data...")
        self._search_input.textChanged.connect(self._on_search_changed)
        
        self._search_description_check = QCheckBox("Description")
        self._search_description_check.setChecked(True)
        self._search_description_check.stateChanged.connect(self._on_search_options_changed)
        
        self._search_metadata_check = QCheckBox("Metadata")
        self._search_metadata_check.setChecked(False)
        self._search_metadata_check.stateChanged.connect(self._on_search_options_changed)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._update_data_tree)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self._search_input, 1)
        search_layout.addWidget(self._search_description_check)
        search_layout.addWidget(self._search_metadata_check)
        search_layout.addWidget(refresh_button)
        
        # Add search controls to top layout
        top_layout.addLayout(search_layout)
        
        # Create the data tree
        self._data_tree = QTreeWidget()
        self._data_tree.setHeaderLabels(["Data Path", "Type", "Provider"])
        self._data_tree.setColumnWidth(0, 200)
        self._data_tree.setColumnWidth(1, 80)
        self._data_tree.setColumnWidth(2, 120)
        self._data_tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._data_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._data_tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        
        # Add the tree to the top layout
        top_layout.addWidget(self._data_tree, 1)
        
        # Create the bottom panel (details and monitoring)
        bottom_panel = QTabWidget()
        
        # Details tab
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(4, 4, 4, 4)
        
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        details_layout.addWidget(self._details_text)
        
        # Monitoring tab
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        monitor_layout.setContentsMargins(4, 4, 4, 4)
        
        self._monitor_text = QTextEdit()
        self._monitor_text.setReadOnly(True)
        monitor_layout.addWidget(self._monitor_text)
        
        # Add tabs
        bottom_panel.addTab(details_widget, "Details")
        bottom_panel.addTab(monitor_widget, "Monitor")
        
        # Add panels to splitter
        splitter.addWidget(top_panel)
        splitter.addWidget(bottom_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        # Add splitter to main layout
        layout.addWidget(splitter)
    
    def _update_data_tree(self):
        """Update the data tree with the current state of the registry."""
        # Get all available data
        available_data = self._data_registry.get_available_data()
        
        # Apply search filter if needed
        search_text = self._search_input.text().strip().lower()
        if search_text:
            # Get search options
            include_description = self._search_description_check.isChecked()
            include_metadata = self._search_metadata_check.isChecked()
            
            # Search for matching data paths
            matching_paths = self._data_registry.search_data(
                search_text, include_description, include_metadata
            )
            
            # Filter available data
            filtered_data = {}
            for path in matching_paths:
                if path in available_data:
                    filtered_data[path] = available_data[path]
                    
            available_data = filtered_data
        
        # Remember the currently selected item
        selected_path = None
        selected_items = self._data_tree.selectedItems()
        if selected_items:
            selected_path = selected_items[0].text(0)
        
        # Clear the tree
        self._data_tree.clear()
        
        # Get all component IDs
        component_ids = set()
        for data_path in available_data.keys():
            if '.' in data_path:
                component_id = data_path.split('.')[0]
                component_ids.add(component_id)
        
        # Create component items
        component_items = {}
        for component_id in sorted(component_ids):
            item = QTreeWidgetItem([component_id, "", ""])
            item.setExpanded(True)
            self._data_tree.addTopLevelItem(item)
            component_items[component_id] = item
        
        # Add data items to components
        for data_path, metadata in available_data.items():
            if '.' not in data_path:
                continue
                
            component_id, data_id = data_path.split('.', 1)
            
            if component_id in component_items:
                parent_item = component_items[component_id]
                
                # Create the data item
                data_item = QTreeWidgetItem(parent_item, [
                    data_path,
                    self._get_type_string(self._data_registry.get_data(data_path)),
                    metadata["provider"]
                ])
                
                # Restore selection if this was the selected item
                if data_path == selected_path:
                    self._data_tree.setCurrentItem(data_item)
    
    def _get_type_string(self, value):
        """
        Get a string representation of the type of a value.
        
        Args:
            value: Value to get the type of
            
        Returns:
            String representation of the type
        """
        if value is None:
            return "None"
            
        if isinstance(value, (int, float, bool, str, list, dict, tuple, set)):
            return type(value).__name__
            
        # For other types, use the class name
        return value.__class__.__name__
    
    def _on_search_changed(self, text):
        """
        Handle changes to the search input.
        
        Args:
            text: New search text
        """
        # Update the tree
        self._update_data_tree()
    
    def _on_search_options_changed(self, state):
        """
        Handle changes to the search options.
        
        Args:
            state: New checkbox state
        """
        # Only update if there's search text
        if self._search_input.text().strip():
            self._update_data_tree()
    
    def _on_selection_changed(self):
        """Handle changes to the selected item in the tree."""
        # Get the selected item
        selected_items = self._data_tree.selectedItems()
        if not selected_items:
            # Clear details
            self._details_text.clear()
            # Update our data
            self.update_data("selected_data_path", None)
            return
            
        # Get the selected data path
        data_path = selected_items[0].text(0)
        
        # Only process actual data paths (not component headers)
        if '.' not in data_path:
            # Clear details
            self._details_text.clear()
            # Update our data
            self.update_data("selected_data_path", None)
            return
        
        # Update our data
        self.update_data("selected_data_path", data_path)
        
        # Get data metadata
        metadata = self._data_registry.get_data_metadata(data_path)
        if not metadata:
            # This shouldn't happen, but just in case
            self._details_text.setPlainText(f"No metadata available for {data_path}")
            return
            
        # Get the data value
        value = self._data_registry.get_data(data_path)
        
        # Create details text
        details = f"Data Path: {data_path}\n"
        details += f"Description: {metadata['description']}\n"
        details += f"Provider: {metadata['provider']}\n"
        details += f"Type: {self._get_type_string(value)}\n"
        details += f"Has Custom Getter: {metadata['has_custom_getter']}\n"
        details += f"Has Custom Setter: {metadata['has_custom_setter']}\n"
        
        # Add metadata if available
        if metadata['metadata']:
            details += "\nMetadata:\n"
            for key, value in metadata['metadata'].items():
                details += f"  {key}: {value}\n"
        
        # Add current value
        details += f"\nCurrent Value:\n{self._format_value(value)}"
        
        # Set details text
        self._details_text.setPlainText(details)
    
    def _format_value(self, value):
        """
        Format a value for display.
        
        Args:
            value: Value to format
            
        Returns:
            Formatted string representation of the value
        """
        import pprint
        return pprint.pformat(value, indent=2)
    
    def _on_data_changed(self, data_path, new_value):
        """
        Handle data changed signals from the registry.
        
        Args:
            data_path: Path of the data that changed
            new_value: New value of the data
        """
        # Add to the monitor log
        timestamp = self._get_timestamp()
        log_entry = f"{timestamp} - {data_path}: {self._format_value(new_value)}\n\n"
        
        # Add to the beginning of the monitor text
        current_text = self._monitor_text.toPlainText()
        self._monitor_text.setPlainText(log_entry + current_text)
        
        # Update details if this is the selected item
        selected_items = self._data_tree.selectedItems()
        if selected_items and selected_items[0].text(0) == data_path:
            self._on_selection_changed()
    
    def _get_timestamp(self):
        """
        Get a formatted timestamp for the current time.
        
        Returns:
            Formatted timestamp string
        """
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    def _show_tree_context_menu(self, position):
        """
        Show a context menu for the data tree.
        
        Args:
            position: Position where the menu should be shown
        """
        # Get the selected item
        selected_items = self._data_tree.selectedItems()
        if not selected_items:
            return
            
        # Get the selected data path
        data_path = selected_items[0].text(0)
        
        # Only show menu for actual data paths (not component headers)
        if '.' not in data_path:
            return
            
        # Create the menu
        menu = QMenu(self)
        
        # Add "Copy Path" action
        copy_path_action = QAction("Copy Path", menu)
        copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(data_path))
        menu.addAction(copy_path_action)
        
        # Add "Copy Value" action
        value = self._data_registry.get_data(data_path)
        copy_value_action = QAction("Copy Value", menu)
        copy_value_action.triggered.connect(lambda: self._copy_to_clipboard(str(value)))
        menu.addAction(copy_value_action)
        
        # Show the menu
        menu.exec_(self._data_tree.mapToGlobal(position))
    
    def _copy_to_clipboard(self, text):
        """
        Copy text to the clipboard.
        
        Args:
            text: Text to copy
        """
        QApplication.clipboard().setText(text)
    
    def sizeHint(self):
        """
        Provide a size hint for the dock widget.
        
        Returns:
            QSize: Suggested size for the dock
        """
        return QSize(500, 600)
    
    def save_state(self):
        """
        Save the dock state for serialization.
        
        Returns:
            dict: State dictionary
        """
        # Get the base state from the parent class
        state = super().save_state()
        
        # Add dock-specific state
        state["dock_type"] = "data_explorer"  # Important for restoring the dock
        
        return state
    
    def closeEvent(self, event):
        """
        Handle close events.
        
        Args:
            event: Close event
        """
        # Stop the update timer
        self._update_timer.stop()
        
        # Call the parent class method
        super().closeEvent(event)