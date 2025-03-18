"""
Template for creating new dock widgets in PySignalDecipher.

This file serves as a template for creating new dock widgets. Simply copy this
file, rename it, and modify the content to create a new dock widget type.

Steps to create a new dock widget:
1. Copy this file to a new file in the 'ui/docking/dock_types/' directory
2. Rename the file to match your dock widget type (e.g., 'my_dock.py')
3. Rename the class to match your dock widget type (e.g., 'MyDock')
4. Implement the required methods
5. Add your dock-specific UI components and logic

The dock will be automatically discovered and registered with the DockManager
at application startup.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize

from command_system.command_manager import CommandManager
from ..dockable_widget import DockableWidget


class TemplateDock(DockableWidget):
    """
    Template for creating new dock widgets.
    
    This template includes all the standard functionality that a dock widget
    should implement, along with detailed comments explaining how to customize
    each part.
    """
    
    # Define any signals your dock needs to communicate with other components
    # Example: content_changed = Signal(object)  # Signal emitted when content changes
    
    def __init__(self, title="Template Dock", parent=None, widget_id=None):
        """
        Initialize the dock widget.
        
        Args:
            title: Title for the dock widget
            parent: Parent widget
            widget_id: Unique identifier for this widget
        """
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"template_dock_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Initialize dock-specific properties here
        self._config = {
            "example_setting": True,
            "example_value": 100
        }
        
        # Access application services through CommandManager if needed
        self._command_manager = CommandManager.instance()
        
        # Get necessary services
        if self._command_manager:
            try:
                from ui.theme.theme_manager import ThemeManager
                self._theme_manager = self._command_manager.get_service(ThemeManager)
            except Exception as e:
                print(f"Error getting ThemeManager: {e}")
                
            try:
                from utils.preferences_manager import PreferencesManager
                self._preferences_manager = self._command_manager.get_service(PreferencesManager)
            except Exception as e:
                print(f"Error getting PreferencesManager: {e}")
                
            try:
                from core.hardware.device_manager import DeviceManager
                self._device_manager = self._command_manager.get_service(DeviceManager)
            except Exception as e:
                print(f"Error getting DeviceManager: {e}")
        
        # Set up the content widget
        self._setup_content()
    
    def _setup_content(self):
        """Set up the content widget for this dock."""
        # Create a layout for the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Add your UI components here
        # This is a placeholder label - replace with your actual content
        info_label = QLabel("Template Dock - Replace with your content")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Example: Add more complex UI components
        # self._chart_view = ChartView()
        # layout.addWidget(self._chart_view)
        
    def sizeHint(self):
        """
        Provide a size hint for the dock widget.
        
        Returns:
            QSize: Suggested size for the dock
        """
        return QSize(300, 200)
    
    def _add_context_menu_items(self, menu):
        """
        Add dock-specific items to the context menu.
        
        Override this method to add custom menu items for your dock.
        
        Args:
            menu: Menu to add items to
        """
        # Add a separator before dock-specific actions
        menu.addSeparator()
        
        # Example: Add a custom action
        example_action = QAction("Example Action", menu)
        example_action.triggered.connect(self._on_example_action)
        menu.addAction(example_action)
        
        # Example: Add a submenu
        submenu = QMenu("Options", menu)
        
        option1 = QAction("Option 1", submenu)
        option1.setCheckable(True)
        option1.setChecked(self._config["example_setting"])
        option1.triggered.connect(lambda checked: self._set_example_setting(checked))
        submenu.addAction(option1)
        
        menu.addMenu(submenu)
    
    def _on_example_action(self):
        """Handle example action from the context menu."""
        # Implement your action logic here
        pass
    
    def _set_example_setting(self, value):
        """
        Update an example setting.
        
        Args:
            value: New value for the setting
        """
        self._config["example_setting"] = value
        
        # Update UI based on the new setting if needed
        # self._update_ui_for_setting()
    
    def save_state(self):
        """
        Save the dock state for serialization.
        
        Returns:
            dict: State dictionary
        """
        # Get the base state from the parent class
        state = super().save_state()
        
        # Add dock-specific state
        state["config"] = self._config.copy()
        state["dock_type"] = "template_dock"  # Important for restoring the dock
        
        # Add any other state that needs to be saved
        # state["custom_state"] = self._custom_state
        
        return state
    
    def restore_state(self, state):
        """
        Restore the dock state from serialization.
        
        Args:
            state: State dictionary
            
        Returns:
            bool: True if the state was restored successfully
        """
        # Restore the base state from the parent class
        result = super().restore_state(state)
        
        # Restore dock-specific state
        if "config" in state:
            self._config.update(state["config"])
            
        # Restore any other state
        # if "custom_state" in state:
        #     self._custom_state = state["custom_state"]
        
        # Update UI based on restored state if needed
        # self._update_ui_from_config()
        
        return result

    def set_data(self, data):
        """
        Set data to be displayed by this dock.
        
        This is an example method for receiving data from other components.
        Customize it based on the specific needs of your dock.
        
        Args:
            data: Data to display
        """
        # Process and display the data
        # Example: self._chart_view.set_data(data)
        pass
    
    def get_data(self):
        """
        Get the data currently displayed by this dock.
        
        This is an example method for sharing data with other components.
        Customize it based on the specific needs of your dock.
        
        Returns:
            The current data
        """
        # Return the current data
        # Example: return self._chart_view.get_data()
        return None
    
    def clear(self):
        """Clear the dock content."""
        # Implement clearing logic for your dock
        # Example: self._chart_view.clear()
        pass