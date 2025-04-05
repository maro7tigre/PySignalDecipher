"""
Base widget for integrating PySide6 widgets with the command system.

This module provides a base implementation for all command-enabled widgets,
handling ID registration, property binding, and command generation.
"""
from enum import Enum
from typing import Any, Optional, Callable, Dict, Union, TypeVar, Generic
from PySide6.QtCore import QTimer

from command_system.id_system import get_id_registry, TypeCodes, extract_property_name, extract_location, subscribe_to_id, unsubscribe_from_id
from command_system.core import Command, WidgetPropertyCommand, PropertyCommand, get_command_manager

# Type for observable targets
T = TypeVar('T')

# MARK: - Command Trigger Mode
class CommandTriggerMode(Enum):
    """
    Defines when a command should be triggered for widget value changes.
    """
    IMMEDIATE = 0      # Trigger command immediately on any change
    DELAYED = 1        # Trigger command after a delay (batching rapid changes)
    ON_EDIT_FINISHED = 2  # Trigger command only when editing is finished
    
# MARK: - Base Command Widget
class BaseCommandWidget:
    """Base class for all command-system enabled widgets."""
    
    def __init__(self):
        """
        Empty initializer to avoid multiple inheritance issues.
        Child classes should call initiate_widget after their own initialization.
        """
        pass
    
    def initiate_widget(self, type_code: str, container_id: Optional[str] = None, 
                 location: Optional[str] = None):
        """
        Initialize the base command widget.
        
        Args:
            type_code: Type code for ID system
            container_id: Optional ID of the parent container
            location: Optional location within the container
        """
        # Save the widget type code
        self.type_code = type_code
        
        # Register with ID system
        id_registry = get_id_registry()
        self.widget_id = id_registry.register(self, type_code, None, container_id, location)
        
        # Controlled properties tracking
        self._controlled_properties: Dict[str, str] = {}  # Widget property -> Observable property ID
        
        # Value change handling
        self._command_trigger_mode = CommandTriggerMode.IMMEDIATE
        self._change_delay_ms = 300  # Default delay for DELAYED mode
        self._change_timer = QTimer()
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._on_change_timer_timeout)
        self._pending_changes: Dict[str, Any] = {}  # Property name -> New value
        self._last_values: Dict[str, Any] = {}  # Property name -> Last committed value
        
        # We're tracking whether we're already processing a command to prevent recursion
        self._processing_command = False
    
    # MARK: - Command Trigger Configuration
    def set_command_trigger_mode(self, mode: CommandTriggerMode, delay_ms: int = 300):
        """
        Set when commands should be triggered for widget value changes.
        
        Args:
            mode: When to trigger the command
            delay_ms: Delay in milliseconds for DELAYED mode
        """
        self._command_trigger_mode = mode
        self._change_delay_ms = delay_ms
    
    # MARK: - Container Management
    def update_container(self, new_container_id: Optional[str] = None):
        """
        Update the container for this widget.
        
        Args:
            new_container_id: New container ID or None
        """
        id_registry = get_id_registry()
        if id_registry.update_container_id(self.widget_id, new_container_id):
            # Update our stored widget ID
            self.widget_id = id_registry.get_id(self)
        return self.widget_id
    
    # MARK: - Property Binding
    def bind_property(self, widget_property: str, observable_id: str, 
                     property_name: str):
        """
        Bind a widget property to an observable property.
        
        Args:
            widget_property: Name of the widget property to bind
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        # Get registry and observable
        id_registry = get_id_registry()
        observable = id_registry.get_observable(observable_id)
        
        if not observable:
            raise ValueError(f"Observable with ID {observable_id} not found")
        
        # Ensure the observable property exists
        if not hasattr(observable, property_name):
            raise ValueError(f"Observable does not have property '{property_name}'")
        
        # Register observable property with this widget as controller
        property_ids = id_registry.get_property_ids_by_observable_id_and_property_name(
            observable_id, property_name)
        
        if property_ids:
            # Check if we're already bound to this property
            for prop_id in property_ids:
                controller_id = id_registry.get_controller_id_from_property_id(prop_id)
                if controller_id == self.widget_id:
                    raise ValueError(f"Property '{property_name}' already bound to this widget")
            
            # Property already registered, update controller
            property_id = property_ids[0]
            id_registry.update_controller_id(property_id, self.widget_id)
        else:
            # Property not yet registered with this property name
            # This shouldn't happen with ObservableProperty attributes
            raise ValueError(f"Property '{property_name}' not registered with observable")
        
        # Store the controlled property mapping
        self._controlled_properties[widget_property] = property_id
        subscribe_to_id(property_id, self.refresh_controlled_properties)
        print("subscribed to:", property_id)
        # Set up observer for property changes
        observer_id = observable.add_property_observer(
            property_name, 
            lambda prop_name, old_val, new_val: self._on_observed_property_changed(
                widget_property, old_val, new_val
            ),
            self
        )
        
        # Initialize widget with current observable value
        current_value = getattr(observable, property_name)
        self._on_observed_property_changed(widget_property, None, current_value)
        
        # Child classes should connect their value changed signals
        # to _on_widget_value_changed method for updating the observable

    def unbind_property(self, widget_property: str):
        """
        Unbind a widget property from its observable property.
        
        Args:
            widget_property: Name of the widget property to unbind
        """
        if widget_property not in self._controlled_properties:
            return
            
        # Get the property ID
        property_id = self._controlled_properties[widget_property]
        
        # Remove the controller reference
        id_registry = get_id_registry()
        id_registry.remove_controller_reference(property_id)
        
        # Remove from our tracking
        del self._controlled_properties[widget_property]

    def refresh_controlled_properties(self, old_id, new_id):
        """
        Refresh the controlled properties when the widget ID changes.

        Args:
            old_id: Old widget ID
            new_id: New widget ID
        """
        print("refresh_controlled_properties", old_id, new_id)
        for widget, id in self._controlled_properties.items():
            if id == old_id:
                if new_id is None:
                    del self._controlled_properties[widget]
                else:
                    self._controlled_properties[widget] = new_id
    
    # MARK: - Property Change Handling
    def _on_observed_property_changed(self, widget_property: str, old_value: Any, new_value: Any):
        """
        Handle changes from the observable property.
        
        Args:
            widget_property: Widget property to update
            old_value: Previous value
            new_value: New value
        """
        if self._processing_command:
            return  # Avoid recursion
            
        self._processing_command = True
        try:
            # Update the widget property - must be implemented by subclasses
            self._update_widget_property(widget_property, new_value)
            # Update last known value
            self._last_values[widget_property] = new_value
        finally:
            self._processing_command = False
    
    def _update_widget_property(self, property_name: str, value: Any):
        """
        Update a widget property value.
        Must be implemented by subclasses for each supported property.
        
        Args:
            property_name: Name of the property to update
            value: New value for the property
        """
        raise NotImplementedError(
            f"_update_widget_property not implemented in {self.__class__.__name__}"
        )
    
    def _on_widget_value_changed(self, widget_property: str, new_value: Any):
        """
        Handle value changes from the widget.
        
        Args:
            widget_property: Name of the widget property that changed
            new_value: New property value
        """
        if self._processing_command:
            return  # Avoid recursion
            
        # Skip if no change from last value
        last_value = self._last_values.get(widget_property)
        if last_value == new_value:
            return
            
        # Handle based on trigger mode
        if self._command_trigger_mode == CommandTriggerMode.IMMEDIATE:
            self._create_and_execute_property_command(widget_property, new_value)
        elif self._command_trigger_mode == CommandTriggerMode.DELAYED:
            # Store pending change and restart timer
            self._pending_changes[widget_property] = new_value
            self._change_timer.start(self._change_delay_ms)
        # ON_EDIT_FINISHED mode is handled by _on_widget_editing_finished
    
    def _on_widget_editing_finished(self):
        """
        Handle the completion of editing.
        Should be called by subclasses when editing is finished.
        """
        # Stop any pending delayed updates
        if self._change_timer.isActive():
            self._change_timer.stop()
            
        if self._command_trigger_mode == CommandTriggerMode.ON_EDIT_FINISHED:
            # Process all pending changes
            for widget_property, new_value in self._pending_changes.items():
                self._create_and_execute_property_command(widget_property, new_value)
            self._pending_changes.clear()
    
    def _on_change_timer_timeout(self):
        """Handle the timeout of the change delay timer."""
        # Process all pending changes
        for widget_property, new_value in self._pending_changes.items():
            self._create_and_execute_property_command(widget_property, new_value)
        self._pending_changes.clear()
    
    def _create_and_execute_property_command(self, widget_property: str, new_value: Any):
        """
        Create and execute a command to update the controlled property.
        
        Args:
            widget_property: Name of the widget property
            new_value: New value for the property
        """
        if widget_property not in self._controlled_properties:
            return
        
        # Skip if no change from last value
        last_value = self._last_values.get(widget_property)
        if last_value == new_value:
            return
            
        # Get the property ID
        property_id = self._controlled_properties[widget_property]
        
        # Create and execute the command directly with property ID
        command = PropertyCommand(property_id, new_value)
        command.set_trigger_widget(self.widget_id)
        
        # Execute the command
        get_command_manager().execute(command)
        
        # Update last known value
        self._last_values[widget_property] = new_value
    
    def update_controlled_property(self, widget_property: str, new_value: Any):
        """
        Programmatically update a controlled property.
        
        Args:
            widget_property: Name of the widget property
            new_value: New value for the property
        """
        # First update the widget itself
        self._update_widget_property(widget_property, new_value)
        
        # Then create and execute a command if property is bound
        if widget_property in self._controlled_properties:
            self._create_and_execute_property_command(widget_property, new_value)
    
    # MARK: - Resource Management
    def unregister_widget(self) -> None:
        """Unregister this widget from the ID system"""
        id_registry = get_id_registry()
        id_registry.unregister(self.widget_id)
        # TODO: Unregister any links in the command system as well
    
    # MARK: - Serialization
    def get_serialization(self):
        """
        Get serialized representation of this widget.
        
        Returns:
            Dict containing serialized widget state
        """
        result = {
            'id': self.widget_id,
            'location': extract_location(self.widget_id),
            'properties': {}
        }
        
        # Serialize controlled properties
        for widget_property, property_id in self._controlled_properties.items():
            id_registry = get_id_registry()
            observable_id = id_registry.get_observable_id_from_property_id(property_id)
            
            if observable_id:
                observable = id_registry.get_observable(observable_id)
                if observable and hasattr(observable, 'serialize_property'):
                    serialized_property = observable.serialize_property(property_id)
                    result['properties'][property_id] = serialized_property
        
        return result
        # TODO: Add serialize_property method to Observable class
    
    def deserialize(self, data):
        """
        Restore this widget's state from serialized data.

        Args:
            data: Dictionary containing widget state

        Returns:
            True if successful
        """
        # Update widget ID if needed
        self.restore_widget(data)
        
    def restore_widget(self, data):
        """
        Restore this widget's state from serialized data.
        
        Args:
            data: Dictionary containing widget state
            
        Returns:
            True if successful
        """
        # Update widget ID if needed
        if data['id'] != self.widget_id:
            id_registry = get_id_registry()
            # Register with the specified ID
            id_registry.update_id(self.widget_id, data['id'])
            self.widget_id = id_registry.get_id(self)
        
        
        
        # Restore controlled properties
        for _, property_id in self._controlled_properties.items():
            #TODO: a better tracking of controlled properties observables
            observable_id = id_registry.get_observable_id_from_property_id(property_id)
            print(observable_id)
            observable = id_registry.get_observable(observable_id)
            
            current_property_name = extract_property_name(property_id)
            for _, serialized_property in data['properties'].items():
                if serialized_property['property_name'] == current_property_name:
                    observable.deserialize_property(property_id, serialized_property)
                    break
            
        
        return True