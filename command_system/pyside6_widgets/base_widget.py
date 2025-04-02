"""
Base widget for integrating PySide6 widgets with the command system.

This module provides a base implementation for all command-enabled widgets,
handling ID registration, property binding, and command generation.
"""
from enum import Enum
from typing import Any, Optional, Callable, Dict, Union, TypeVar, Generic
import time
from PySide6.QtCore import QTimer

from command_system.id_system import get_id_registry, TypeCodes
from command_system.core import Command, WidgetPropertyCommand, PropertyCommand, get_command_manager

# Type for observable targets
T = TypeVar('T')

class CommandTriggerMode(Enum):
    """
    Defines when a command should be triggered for widget value changes.
    """
    IMMEDIATE = 0      # Trigger command immediately on any change
    DELAYED = 1        # Trigger command after a delay (batching rapid changes)
    ON_EDIT_FINISHED = 2  # Trigger command only when editing is finished
    
class BaseCommandWidget:
    """Base class for all command-system enabled widgets."""
    
    def __init__(self):
        """
        Empty initializer to avoid multiple inheritance issues.
        Child classes should call initiate_widget after their own initialization.
        """
        pass
    
    def initiate_widget(self, type_code: str= None, container_id: Optional[str] = None, 
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
    
    def _ensure_qt_widget(self):
        """
        Ensure this class also inherits from a Qt widget.
        Called by child classes to validate inheritance.
        """
        from PySide6.QtWidgets import QWidget
        if not isinstance(self, QWidget):
            raise TypeError(f"{self.__class__.__name__} must also inherit from a PySide6 QWidget class")
    
    def set_command_trigger_mode(self, mode: CommandTriggerMode, delay_ms: int = 300):
        """
        Set when commands should be triggered for widget value changes.
        
        Args:
            mode: When to trigger the command
            delay_ms: Delay in milliseconds for DELAYED mode
        """
        self._command_trigger_mode = mode
        self._change_delay_ms = delay_ms
    
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
    
    def update_location(self, new_location: str):
        """
        Update the location within the container.
        
        Args:
            new_location: New location string
        """
        id_registry = get_id_registry()
        if id_registry.update_location(self.widget_id, new_location):
            # Update our stored widget ID
            self.widget_id = id_registry.get_id(self)
        return self.widget_id
    
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
            # Property already registered, update controller
            property_id = property_ids[0]
            id_registry.update_controller_id(property_id, self.widget_id)
        else:
            # Property not yet registered with this property name
            # This shouldn't happen with ObservableProperty attributes
            raise ValueError(f"Property '{property_name}' not registered with observable")
        
        # Store the controlled property mapping
        self._controlled_properties[widget_property] = property_id
        
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
    
    def unregister_widget(self) -> None:
        """Unregister this widget"""
        id_registry = get_id_registry()
        id_registry.unregister(self.widget_id)
        
        # TODO: consider more cleanup
    
    # -MARK: Serialization
    #TODO: Implement serialization of Observers
    def get_serialization(self):
        """
        Get serialized representation of this widget.
        
        For containers, this will recursively serialize all children.
        
        Returns:
            Dict containing serialized widget state
        """
        # Get basic properties
        result = self.get_serialization_properties()
        
        # For containers, add children
        if hasattr(self, 'get_child_widgets'):
            children = []
            for child in self.get_child_widgets():
                if hasattr(child, 'get_serialization'):
                    children.append(child.get_serialization())
            
            if children:
                result['children'] = children
        
        return result

    def get_serialization_properties(self):
        """
        Get serializable properties for this widget.
        Override in subclasses to add widget-specific properties.
        
        Returns:
            Dict containing basic widget properties
        """
        return {
            'id': self.widget_id,
            'type_code': self.type_code,
            # Add layout info if available
            'layout': self._get_layout_info() if hasattr(self, '_get_layout_info') else {}
        }

    @staticmethod
    def deserialize(data, parent=None):
        """
        Create a widget from serialized data.
        
        Args:
            data: Serialized widget data dictionary
            parent: Optional parent widget
            
        Returns:
            Newly created widget instance
        """
        # TODO: Implement basic deserialization
        # This will need to create the appropriate widget type based on type_code
        pass

    def restore_widget(self, id, type_id, layout, children=None):
        """
        Restore this widget's state from serialized data.
        Override in subclasses to handle widget-specific restoration.
        
        Args:
            id: Widget ID
            type_id: Widget type ID
            layout: Layout information
            children: List of child widget data (for containers)
            
        Returns:
            True if successful
        """
        # TODO: Implement basic widget restoration
        return True

    def _get_layout_info(self):
        """
        Get layout information for serialization.
        
        Returns:
            Dictionary with layout properties
        """
        # Basic implementation for QWidget
        return {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height(),
            'visible': self.isVisible()
        }