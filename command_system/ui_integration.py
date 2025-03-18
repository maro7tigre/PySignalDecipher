"""
UI integration for the command system.

This module provides classes for integrating UI components with the command system,
allowing for automatic command creation and execution from UI events.
"""

from typing import Dict, Any, Type, Optional, Callable, Union, List
from PySide6.QtWidgets import (
    QPushButton, QToolButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QListWidget, QTableWidget, QRadioButton, QSlider,
    QWidget, QMenu, QAction
)
from PySide6.QtCore import QObject, Signal, Slot

from .command import Command, CommandFactory, CommandContext
from .command_manager import CommandManager
from .observable import Observable, ObservableProperty


class CommandConnector:
    """
    Connects UI widget events to commands.
    
    This utility class helps connect widget signals to command creation and execution.
    """
    
    @staticmethod
    def connect_button(button: Union[QPushButton, QToolButton], 
                      command_class: Type[Command], **kwargs) -> None:
        """
        Connect a button click to execute a command.
        
        Args:
            button: The button widget
            command_class: Command class to create and execute
            **kwargs: Additional parameters to pass to the command constructor
        """
        button.clicked.connect(
            lambda checked=False: 
            CommandManager.instance().execute_command(
                CommandFactory.create(command_class, **kwargs)
            )
        )
    
    @staticmethod
    def connect_action(action: QAction, command_class: Type[Command], **kwargs) -> None:
        """
        Connect a menu action to execute a command.
        
        Args:
            action: The menu action
            command_class: Command class to create and execute
            **kwargs: Additional parameters to pass to the command constructor
        """
        action.triggered.connect(
            lambda checked=False: 
            CommandManager.instance().execute_command(
                CommandFactory.create(command_class, **kwargs)
            )
        )
    
    @staticmethod
    def connect_property(widget: QWidget, widget_signal: str, 
                        target: Observable, property_name: str) -> None:
        """
        Connect a widget signal to update an observable property.
        
        Args:
            widget: Widget emitting the signal
            widget_signal: Name of the signal to connect to
            target: Observable object to update
            property_name: Name of the property to update
        """
        signal = getattr(widget, widget_signal)
        
        def update_property(value):
            """Create and execute a property change command."""
            cmd = CommandFactory.create_property_change(target, property_name, value)
            CommandManager.instance().execute_command(cmd)
            
        signal.connect(update_property)
    
    @staticmethod
    def create_value_changed_handler(target: Observable, property_name: str) -> Callable:
        """
        Create a handler for value changed signals.
        
        Args:
            target: Observable object to update
            property_name: Name of the property to update
            
        Returns:
            A function that can be connected to a value changed signal
        """
        def handler(value):
            """Create and execute a property change command."""
            cmd = CommandFactory.create_property_change(target, property_name, value)
            CommandManager.instance().execute_command(cmd)
            
        return handler
    
    @staticmethod
    def setup_widget_binding(widget: QWidget, target: Observable, property_name: str) -> None:
        """
        Set up two-way binding between a widget and an observable property.
        
        Args:
            widget: Widget to bind
            target: Observable object with the property
            property_name: Name of the property to bind
        """
        # Get the property object from the class
        prop = getattr(type(target), property_name, None)
        if not isinstance(prop, ObservableProperty):
            raise ValueError(f"Property {property_name} is not an ObservableProperty")
            
        # Determine widget type and bind appropriately
        if isinstance(widget, QLineEdit):
            prop.bind_to_ui(target, widget, "text")
        elif isinstance(widget, QSpinBox):
            prop.bind_to_ui(target, widget, "value")
        elif isinstance(widget, QDoubleSpinBox):
            prop.bind_to_ui(target, widget, "value")
        elif isinstance(widget, QCheckBox):
            prop.bind_to_ui(target, widget, "checked")
        elif isinstance(widget, QComboBox):
            prop.bind_to_ui(target, widget, "currentIndex")
        elif isinstance(widget, QSlider):
            prop.bind_to_ui(target, widget, "value")
        elif isinstance(widget, QLabel):
            # One-way binding for labels
            prop.bind_to_ui(target, widget, "text", bidirectional=False)
        else:
            raise TypeError(f"Unsupported widget type: {type(widget).__name__}")


class CommandButton(QPushButton):
    """
    Button that executes a command when clicked.
    
    This is a convenience widget that simplifies command integration with UI.
    """
    
    def __init__(self, command_class: Type[Command], text: str = "", 
                 parent: Optional[QWidget] = None, **command_params):
        """
        Initialize the command button.
        
        Args:
            command_class: Command class to create and execute
            text: Button text
            parent: Parent widget
            **command_params: Additional parameters to pass to the command constructor
        """
        super().__init__(text, parent)
        
        self.command_class = command_class
        self.command_params = command_params
        
        # Connect clicked signal to execute the command
        self.clicked.connect(self._execute_command)
    
    def _execute_command(self):
        """Create and execute the command when clicked."""
        cmd = CommandFactory.create(self.command_class, **self.command_params)
        CommandManager.instance().execute_command(cmd)
        
    def set_command_params(self, **params):
        """
        Update command parameters.
        
        Args:
            **params: New parameters to use when creating the command
        """
        self.command_params.update(params)


class CommandAction(QAction):
    """
    Menu action that executes a command when triggered.
    
    This is a convenience widget that simplifies command integration with menus.
    """
    
    def __init__(self, command_class: Type[Command], text: str, 
                 parent: Optional[QObject] = None, **command_params):
        """
        Initialize the command action.
        
        Args:
            command_class: Command class to create and execute
            text: Action text
            parent: Parent object
            **command_params: Additional parameters to pass to the command constructor
        """
        super().__init__(text, parent)
        
        self.command_class = command_class
        self.command_params = command_params
        
        # Connect triggered signal to execute the command
        self.triggered.connect(self._execute_command)
    
    def _execute_command(self):
        """Create and execute the command when triggered."""
        cmd = CommandFactory.create(self.command_class, **self.command_params)
        CommandManager.instance().execute_command(cmd)
        
    def set_command_params(self, **params):
        """
        Update command parameters.
        
        Args:
            **params: New parameters to use when creating the command
        """
        self.command_params.update(params)


class PropertyWidget:
    """
    Mixin for widgets that bind to observable properties.
    
    This mixin adds methods for binding widget properties to observable properties.
    """
    
    def bind_to_property(self, target: Observable, property_name: str):
        """
        Bind this widget to an observable property.
        
        Args:
            target: Observable object with the property
            property_name: Name of the property to bind
        """
        CommandConnector.setup_widget_binding(self, target, property_name)


class PropertyLineEdit(QLineEdit, PropertyWidget):
    """QLineEdit that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property line edit."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertySpinBox(QSpinBox, PropertyWidget):
    """QSpinBox that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property spin box."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertyDoubleSpinBox(QDoubleSpinBox, PropertyWidget):
    """QDoubleSpinBox that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property double spin box."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertyCheckBox(QCheckBox, PropertyWidget):
    """QCheckBox that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property check box."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertyComboBox(QComboBox, PropertyWidget):
    """QComboBox that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property combo box."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertySlider(QSlider, PropertyWidget):
    """QSlider that can bind to an observable property."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property slider."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            self.bind_to_property(target, property_name)


class PropertyLabel(QLabel, PropertyWidget):
    """QLabel that can display an observable property (one-way binding)."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the property label."""
        target = kwargs.pop('target', None)
        property_name = kwargs.pop('property_name', None)
        
        super().__init__(*args, **kwargs)
        
        if target and property_name:
            # Get the property to bind
            prop = getattr(type(target), property_name, None)
            if isinstance(prop, ObservableProperty):
                # Create a one-way binding
                prop.bind_to_ui(target, self, "text", bidirectional=False)