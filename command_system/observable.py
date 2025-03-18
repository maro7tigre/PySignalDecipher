"""
Observable properties for PySignalDecipher.

This module provides property tracking and change notification
for objects whose state changes should be tracked and undoable.
"""

from typing import Any, Dict, Callable, List, Optional, Set, TypeVar, Generic, Union
import uuid
import weakref
from PySide6.QtCore import QObject, Signal
from .command import Command

T = TypeVar('T')  # Generic type for property values


class ObservableProperty(Generic[T]):
    """
    A property descriptor that tracks changes and notifies observers.
    
    This provides a way to track changes to object properties and
    automatically integrate with the command system.
    """
    
    def __init__(self, default_value: T = None, path: str = None):
        """
        Initialize a new observable property.
        
        Args:
            default_value: The default value for the property
            path: Optional path identifier for data binding (e.g., "signal.amplitude")
        """
        self.default_value = default_value
        self.path = path
        self.name = None  # Will be set when the property is assigned to a class
    
    def __set_name__(self, owner, name):
        """
        Called when the property is assigned to a class.
        
        Args:
            owner: The class that owns this property
            name: The name of the property
        """
        self.name = name
        self.private_name = f"_{name}"
        
        # If path is not set, use the class and property name
        if self.path is None:
            self.path = f"{owner.__name__.lower()}.{name}"
    
    def __get__(self, instance, owner):
        """
        Get the property value.
        
        Args:
            instance: The object instance
            owner: The class
            
        Returns:
            The property value
        """
        if instance is None:
            return self
        
        # Return the value or default
        return getattr(instance, self.private_name, self.default_value)
    
    def __set__(self, instance, value):
        """
        Set the property value.
        
        Args:
            instance: The object instance
            value: The new value
        """
        if not hasattr(instance, self.private_name):
            # First time setting, just set it
            setattr(instance, self.private_name, value)
            return
        
        # Get the old value
        old_value = getattr(instance, self.private_name)
        
        # If the value is the same, do nothing
        if old_value == value:
            return
        
        # Set the new value
        setattr(instance, self.private_name, value)
        
        # Notify property changed if instance is Observable
        if isinstance(instance, Observable) and hasattr(instance, "_property_changed"):
            instance._property_changed(self.name, old_value, value)
            
    def bind_to_ui(self, instance, widget, widget_property: str = "text", 
                  bidirectional: bool = True):
        """
        Bind this property to a UI widget property.
        
        Args:
            instance: The object instance containing this property
            widget: The UI widget to bind to
            widget_property: The property name on the widget to bind to
            bidirectional: Whether changes should propagate in both directions
        
        Returns:
            A binding object that can be used to unbind later
        """
        if not isinstance(instance, Observable):
            raise TypeError("Instance must be Observable to bind to UI")
            
        binding = PropertyBinding(instance, self.name, widget, widget_property, bidirectional)
        binding.bind()
        return binding


class PropertyBinding:
    """
    Manages binding between an Observable property and a UI widget property.
    
    Handles synchronization and event connections in both directions.
    """
    
    def __init__(self, observable_obj, property_name, widget, widget_property, bidirectional=True):
        """
        Initialize binding between an observable property and widget property.
        
        Args:
            observable_obj: Observable object containing the property
            property_name: Name of the property on the observable object
            widget: UI widget to bind to
            widget_property: Name of the property on the widget
            bidirectional: Whether to sync changes in both directions
        """
        self.observable = observable_obj
        self.property_name = property_name
        self.widget = widget
        self.widget_property = widget_property
        self.bidirectional = bidirectional
        
        # Connections
        self._observable_connection = None
        self._widget_connections = []
        
    def bind(self):
        """Establish the binding between the observable and widget."""
        # Add property observer for observable -> widget
        self._observable_connection = self.observable.add_property_observer(
            self.property_name, self._update_widget_from_observable
        )
        
        # Connect widget signals for widget -> observable (if bidirectional)
        if self.bidirectional:
            self._connect_widget_signals()
            
        # Initial update to sync widget with current value
        self._update_widget_from_observable(
            self.property_name, None, getattr(self.observable, self.property_name)
        )
    
    def unbind(self):
        """Remove the binding between observable and widget."""
        # Remove property observer
        if self._observable_connection:
            self.observable.remove_property_observer(
                self.property_name, self._observable_connection
            )
            self._observable_connection = None
            
        # Disconnect widget signals
        for connection in self._widget_connections:
            try:
                if hasattr(connection[0], connection[1]):
                    signal = getattr(connection[0], connection[1])
                    if hasattr(signal, "disconnect"):
                        signal.disconnect(connection[2])
            except:
                pass
        self._widget_connections = []
            
    def _update_widget_from_observable(self, property_name, old_value, new_value):
        """
        Update widget when observable property changes.
        
        Args:
            property_name: Name of the changed property
            old_value: Previous property value
            new_value: New property value
        """
        # Temporarily prevent widget from updating observable
        old_bidirectional = self.bidirectional
        self.bidirectional = False
        
        try:
            # Handle different widget types and properties
            if hasattr(self.widget, f"set{self.widget_property.capitalize()}"):
                # Use setter method if it exists (e.g., setText for "text")
                getattr(self.widget, f"set{self.widget_property.capitalize()}")(new_value)
            else:
                # Otherwise set property directly
                setattr(self.widget, self.widget_property, new_value)
        finally:
            # Restore bidirectional binding
            self.bidirectional = old_bidirectional
            
    def _update_observable_from_widget(self, *args):
        """
        Update observable when widget property changes.
        
        This method is connected to the appropriate widget signals.
        """
        if not self.bidirectional:
            return
            
        # Get current widget value
        if hasattr(self.widget, f"{self.widget_property}"):
            # Use getter method if it exists
            value = getattr(self.widget, f"{self.widget_property}")()
        else:
            # Otherwise get property directly
            value = getattr(self.widget, self.widget_property)
            
        # Create a command to update the property
        from .command import CommandFactory
        from .command_manager import CommandManager
        
        cmd = CommandFactory.create_property_change(
            self.observable, self.property_name, value
        )
        CommandManager.instance().execute_command(cmd)
            
    def _connect_widget_signals(self):
        """
        Connect to appropriate widget signals based on widget type.
        
        This method handles different widget classes and their
        corresponding signals for property changes.
        """
        from PySide6.QtWidgets import (
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, 
            QComboBox, QCheckBox, QSlider, QPushButton
        )
        
        # Determine which signals to connect to based on widget type
        if isinstance(self.widget, QLineEdit):
            if self.widget_property == "text":
                self.widget.textChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "textChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QTextEdit):
            if self.widget_property == "text":
                self.widget.textChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "textChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QSpinBox):
            if self.widget_property == "value":
                self.widget.valueChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "valueChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QDoubleSpinBox):
            if self.widget_property == "value":
                self.widget.valueChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "valueChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QComboBox):
            if self.widget_property == "currentText":
                self.widget.currentTextChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "currentTextChanged", self._update_observable_from_widget))
            elif self.widget_property == "currentIndex":
                self.widget.currentIndexChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "currentIndexChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QCheckBox):
            if self.widget_property == "checked":
                self.widget.stateChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "stateChanged", self._update_observable_from_widget))
                
        elif isinstance(self.widget, QSlider):
            if self.widget_property == "value":
                self.widget.valueChanged.connect(self._update_observable_from_widget)
                self._widget_connections.append((self.widget, "valueChanged", self._update_observable_from_widget))


class Observable(QObject):
    """
    Base class for objects with observable properties.
    
    Objects that need to track property changes for undo/redo
    should inherit from this class.
    """
    
    # Signal emitted when a property changes
    property_changed = Signal(str, object, object)  # property_name, old_value, new_value
    
    def __init__(self):
        """Initialize the observable object."""
        super().__init__()
        self._property_observers: Dict[str, List[Callable[[str, Any, Any], None]]] = {}
        self._ignore_changes = False
        self._id = str(uuid.uuid4())  # Unique identifier for this object
    
    def _property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        Handle property changes.
        
        Args:
            property_name: Name of the changed property
            old_value: Previous value
            new_value: New value
        """
        if self._ignore_changes:
            return
        
        # Emit signal
        self.property_changed.emit(property_name, old_value, new_value)
        
        # Notify observers
        if property_name in self._property_observers:
            for observer in list(self._property_observers[property_name].values()):
                observer(property_name, old_value, new_value)
    
    def add_property_observer(self, 
                             property_name: str, 
                             observer: Callable[[str, Any, Any], None]) -> str:
        """
        Add an observer for a specific property.
        
        Args:
            property_name: The property to observe
            observer: Callback to invoke when the property changes
            
        Returns:
            str: A unique identifier for the observer that can be used to remove it
        """
        if property_name not in self._property_observers:
            self._property_observers[property_name] = {}
        
        # Generate a unique ID for this observer
        observer_id = str(uuid.uuid4())
        self._property_observers[property_name][observer_id] = observer
        
        return observer_id
    
    def remove_property_observer(self, 
                                property_name: str, 
                                observer_id: str) -> bool:
        """
        Remove a property observer by ID.
        
        Args:
            property_name: The property being observed
            observer_id: The identifier of the observer to remove
            
        Returns:
            bool: True if the observer was removed, False otherwise
        """
        if (property_name in self._property_observers and 
            observer_id in self._property_observers[property_name]):
            del self._property_observers[property_name][observer_id]
            return True
        return False
    
    def clear_property_observers(self, property_name: Optional[str] = None) -> None:
        """
        Clear all observers for a property or all properties.
        
        Args:
            property_name: Property to clear observers for, or None for all properties
        """
        if property_name is not None:
            if property_name in self._property_observers:
                self._property_observers[property_name] = {}
        else:
            self._property_observers = {}
    
    def get_all_properties(self) -> Dict[str, Any]:
        """
        Get all observable properties.
        
        Returns:
            Dictionary of property names and values
        """
        result = {}
        
        for attr_name in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr_name, None), ObservableProperty):
                result[attr_name] = getattr(self, attr_name)
        
        return result
    
    def set_properties(self, properties: Dict[str, Any], track_changes: bool = True) -> None:
        """
        Set multiple properties at once.
        
        Args:
            properties: Dictionary of property names and values
            track_changes: Whether to track the changes or not
        """
        old_ignore = self._ignore_changes
        if not track_changes:
            self._ignore_changes = True
        
        try:
            for name, value in properties.items():
                if hasattr(self.__class__, name) and isinstance(getattr(self.__class__, name), ObservableProperty):
                    setattr(self, name, value)
        finally:
            self._ignore_changes = old_ignore
    
    def get_id(self) -> str:
        """
        Get the unique identifier for this object.
        
        Returns:
            str: Unique ID
        """
        return self._id
    
    def set_id(self, id_value: str) -> None:
        """
        Set the unique identifier for this object.
        
        This is typically only used when deserializing an object
        to restore its original ID.
        
        Args:
            id_value: New unique ID value
        """
        self._id = id_value


class PropertyChangeCommand(Command):
    """
    Command for changing observable properties.
    
    This command encapsulates property changes so they can be undone/redone.
    """
    
    def __init__(self, context=None, target=None, property_name=None, new_value=None):
        """
        Initialize the property change command.
        
        Args:
            context: Command execution context
            target: The object whose property will change
            property_name: The name of the property
            new_value: The new value for the property
        """
        from .command import Command, CommandContext
        super().__init__(context)
        
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(target, property_name) if target and property_name else None
        
        # Store target ID for serialization
        if isinstance(target, Observable):
            self.target_id = target.get_id()
        else:
            self.target_id = None
    
    def execute(self) -> None:
        """Execute the property change."""
        if self.target and self.property_name:
            # Temporarily disable tracking to avoid recursive commands
            if isinstance(self.target, Observable):
                old_ignore = self.target._ignore_changes
                self.target._ignore_changes = True
                try:
                    setattr(self.target, self.property_name, self.new_value)
                finally:
                    self.target._ignore_changes = old_ignore
            else:
                setattr(self.target, self.property_name, self.new_value)
    
    def undo(self) -> None:
        """Undo the property change."""
        if self.target and self.property_name:
            # Temporarily disable tracking to avoid recursive commands
            if isinstance(self.target, Observable):
                old_ignore = self.target._ignore_changes
                self.target._ignore_changes = True
                try:
                    setattr(self.target, self.property_name, self.old_value)
                finally:
                    self.target._ignore_changes = old_ignore
            else:
                setattr(self.target, self.property_name, self.old_value)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the serialized state.
        
        Returns:
            Dictionary with the command state
        """
        return {
            "target_id": self.target_id,
            "property_name": self.property_name,
            "old_value": self._serialize_value(self.old_value),
            "new_value": self._serialize_value(self.new_value),
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'PropertyChangeCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.target_id = state.get("target_id")
        cmd.property_name = state.get("property_name")
        cmd.old_value = cls._deserialize_value(state.get("old_value"))
        cmd.new_value = cls._deserialize_value(state.get("new_value"))
        
        # Target needs to be found by ID when the command is executed
        # This is typically done by the command manager
        return cmd
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a property value.
        
        Handles special cases like Observable objects.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serializable version of the value
        """
        if isinstance(value, Observable):
            return {"_type": "Observable", "id": value.get_id()}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return value
    
    @classmethod
    def _deserialize_value(cls, value: Any) -> Any:
        """
        Deserialize a property value.
        
        Handles special cases like Observable objects.
        
        Args:
            value: Serialized value
            
        Returns:
            Deserialized value
        """
        if isinstance(value, dict) and "_type" in value:
            if value["_type"] == "Observable":
                # The actual object will need to be looked up when executing
                return {"_type": "Observable", "id": value["id"]}
        elif isinstance(value, list):
            return [cls._deserialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: cls._deserialize_value(v) for k, v in value.items()}
        return value
    
    def resolve_references(self, object_registry: Dict[str, Observable]) -> None:
        """
        Resolve references to Observable objects.
        
        This is called after deserialization to set the actual target.
        
        Args:
            object_registry: Dictionary mapping object IDs to instances
        """
        if self.target_id and self.target_id in object_registry:
            self.target = object_registry[self.target_id]
            
        # Resolve any references in old_value and new_value
        self.old_value = self._resolve_value_references(self.old_value, object_registry)
        self.new_value = self._resolve_value_references(self.new_value, object_registry)
    
    def _resolve_value_references(self, value: Any, 
                                 object_registry: Dict[str, Observable]) -> Any:
        """
        Resolve references in a value.
        
        Args:
            value: Value potentially containing references
            object_registry: Dictionary mapping object IDs to instances
            
        Returns:
            Value with resolved references
        """
        if isinstance(value, dict) and "_type" in value:
            if value["_type"] == "Observable" and value["id"] in object_registry:
                return object_registry[value["id"]]
        elif isinstance(value, list):
            return [self._resolve_value_references(item, object_registry) for item in value]
        elif isinstance(value, dict):
            return {k: self._resolve_value_references(v, object_registry) for k, v in value.items()}
        return value