"""
Core Registry module.

This module contains the central IDRegistry class that coordinates all components
of the ID system.
"""

from command_system.id_system.core.generator import UniqueIDGenerator
from command_system.id_system.core.parser import (
    parse_widget_id,
    parse_observable_id,
    parse_property_id,
    get_unique_id_from_id,
)
from command_system.id_system.managers.widget_manager import WidgetManager
from command_system.id_system.managers.observable_manager import ObservableManager
from command_system.id_system.managers.subscription_manager import (
    subscribe_to_id,
    unsubscribe_from_id,
    clear_subscriptions,
    get_subscription_manager,
)
from command_system.id_system.types import (
    DEFAULT_ROOT_CONTAINER_ID,
    DEFAULT_ROOT_LOCATION,
    DEFAULT_NO_OBSERVABLE,
    DEFAULT_NO_CONTROLLER,
    DEFAULT_NO_PROPERTY_NAME,
    CONTAINER_TYPE_CODES,
    WIDGET_TYPE_CODES,
    ALL_WIDGET_TYPE_CODES,
    OBSERVABLE_TYPE_CODES,
    PROPERTY_TYPE_CODES,
)

# Global ID registry instance
_id_registry = None

def get_id_registry():
    """
    Get the global ID registry instance.
    
    Returns:
        IDRegistry: The global ID registry
    """
    global _id_registry
    if _id_registry is None:
        _id_registry = IDRegistry()
    
    return _id_registry

#MARK: - IDRegistry class

class IDRegistry:
    """
    Central registry for all ID system components.
    
    This class coordinates all aspects of the ID system, delegating operations
    to the appropriate manager classes and maintaining the overall state.
    """
    
    def __init__(self):
        """Initialize the ID registry."""
        # The unique ID generator
        self._id_generator = UniqueIDGenerator()
        
        # Managers for different component types
        self._widget_manager = WidgetManager()
        self._observable_manager = ObservableManager()
        
        # Get the subscription manager
        self._subscription_manager = get_subscription_manager()
        
        # Set up unregister callbacks
        self._widget_manager.set_on_widget_unregister(self._on_widget_unregister)
        self._observable_manager.set_on_observable_unregister(self._on_observable_unregister)
        self._observable_manager.set_on_property_unregister(self._on_property_unregister)
        
        # Callback for ID changes
        self._on_id_changed = None
    
    #MARK: - Registration methods
    
    def register(self, widget, type_code, widget_id=None, container_id=None, location=None):
        """
        Register a widget with the registry.
        
        Args:
            widget: The widget object to register
            type_code: The widget type code
            widget_id: The unique ID for the widget (default: None, will be generated)
            container_id: The container's unique ID (default: None, will use root container)
            location: The location within the container (default: None, will use root location)
            
        Returns:
            str: The generated widget ID
        """
        # Generate or use the provided unique ID
        unique_id = widget_id if widget_id else self._id_generator.generate()
        
        # Ensure the ID is registered with the generator to prevent collisions
        self._id_generator.register(unique_id)
        
        #check if the container ID is the full or unique ID
        if container_id and ":" in container_id:
            container_id = get_unique_id_from_id(container_id)
        
        
        # Determine container ID
        final_container_id = container_id if container_id else DEFAULT_ROOT_CONTAINER_ID
        
        # Register with the widget manager
        widget_id = self._widget_manager.register_widget(
            widget,
            type_code,
            unique_id,
            final_container_id,
            location
        )
        
        return widget_id
    
    def register_observable(self, observable, type_code, observable_id=None):
        """
        Register an observable with the registry.
        
        Args:
            observable: The observable object to register
            type_code: The observable type code
            observable_id: The unique ID for the observable (default: None, will be generated)
            
        Returns:
            str: The generated observable ID
        """
        # Generate or use the provided unique ID
        unique_id = observable_id if observable_id else self._id_generator.generate()
        
        # Ensure the ID is registered with the generator to prevent collisions
        self._id_generator.register(unique_id)
        
        # Register with the observable manager
        observable_id = self._observable_manager.register_observable(
            observable,
            type_code,
            unique_id
        )
        
        return observable_id
    
    def register_observable_property(self, property_obj, type_code, property_id=None,
                                   property_name=DEFAULT_NO_PROPERTY_NAME,
                                   observable_id=DEFAULT_NO_OBSERVABLE,
                                   controller_id=DEFAULT_NO_CONTROLLER):
        """
        Register an observable property with the registry.
        
        Args:
            property_obj: The property object to register
            type_code: The property type code
            property_id: The unique ID for the property (default: None, will be generated)
            property_name: The name of the property (default: "0")
            observable_id: The unique ID of the associated observable (default: "0")
            controller_id: The unique ID of the controller widget (default: "0")
            
        Returns:
            str: The generated property ID
        """
        # Generate or use the provided unique ID
        unique_id = property_id if property_id else self._id_generator.generate()
        
        # Ensure the ID is registered with the generator to prevent collisions
        self._id_generator.register(unique_id)
        
        # Register with the observable manager
        property_id = self._observable_manager.register_property(
            property_obj,
            type_code,
            unique_id,
            observable_id,
            property_name,
            controller_id
        )
        
        return property_id
    
    def unregister(self, component_id, replacement_id=None):
        """
        Unregister a component from the registry.
        
        Args:
            component_id: The ID of the component to unregister
            replacement_id: An optional ID to notify subscribers with (default: None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine component type from ID
        if component_id.startswith(tuple(ALL_WIDGET_TYPE_CODES)):
            # Widget/Container
            result = self._widget_manager.unregister_widget(component_id)
            
            # Notify subscribers if needed
            if result and replacement_id:
                self._subscription_manager.notify(component_id, replacement_id)
            
            return result
        elif component_id.startswith(tuple(OBSERVABLE_TYPE_CODES)):
            # Observable
            result = self._observable_manager.unregister_observable(component_id)
            
            # Notify subscribers if needed
            if result and replacement_id:
                self._subscription_manager.notify(component_id, replacement_id)
            
            return result
        elif component_id.startswith(tuple(PROPERTY_TYPE_CODES)):
            # Property
            result = self._observable_manager.unregister_property(component_id)
            
            # Notify subscribers if needed
            if result and replacement_id:
                self._subscription_manager.notify(component_id, replacement_id)
            
            return result
        
        return False
    
    #MARK: - ID retrieval methods
    
    def get_widget(self, widget_id):
        """
        Get a widget by its ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            object: The widget object, or None if not found
        """
        return self._widget_manager.get_widget(widget_id)
    
    def get_observable(self, observable_id):
        """
        Get an observable by its ID.
        
        Args:
            observable_id: The observable ID
            
        Returns:
            object: The observable object, or None if not found
        """
        return self._observable_manager.get_observable(observable_id)
    
    def get_observable_property(self, property_id):
        """
        Get a property by its ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            object: The property object, or None if not found
        """
        return self._observable_manager.get_property(property_id)
    
    def get_id(self, component):
        """
        Get the ID for a component.
        
        Args:
            component: The component object
            
        Returns:
            str: The component ID, or None if not found
        """
        # Try to find in widget manager
        widget_id = self._widget_manager.get_widget_id(component)
        if widget_id:
            return widget_id
        
        # Try to find in observable manager
        observable_id = self._observable_manager.get_observable_id(component)
        if observable_id:
            return observable_id
        
        # Try to find in property manager
        property_id = self._observable_manager.get_property_id(component)
        if property_id:
            return property_id
        
        return None
    
    def get_unique_id_from_id(self, id_string):
        """
        Extract the unique ID portion from an ID string.
        
        Args:
            id_string: The ID string
            
        Returns:
            str: The unique ID, or None if invalid
        """
        return get_unique_id_from_id(id_string)
    
    def get_full_id_from_unique_id(self, unique_id):
        """
        Get the full ID for a unique ID.
        
        Args:
            unique_id: The unique ID
            
        Returns:
            str: The full ID, or None if not found
        """
        # Try to find in widget manager
        widget_id = self._widget_manager.get_widget_id_by_unique_id(unique_id)
        if widget_id:
            return widget_id
        
        # Try to find in observable manager
        observable_id = self._observable_manager.get_observable_id_by_unique_id(unique_id)
        if observable_id:
            return observable_id
        
        # Try to find in property manager
        property_id = self._observable_manager.get_property_id_by_unique_id(unique_id)
        if property_id:
            return property_id
        
        return None
    
    #MARK: - Container relationship methods
    
    def get_locations_map(self, container_id):
        """
        Get the container's locations map.
        
        Args:
            container_id: The container's unique ID
            
        Returns:
            dict: A dictionary mapping subcontainer locations to widget IDs
        """
        return self._widget_manager.get_locations_map(container_id)
    
    def set_locations_map(self, container_id, locations_map):
        """
        Set the container's locations map.
        
        Args:
            container_id: The container's unique ID
            locations_map: A dictionary mapping subcontainer locations to widget IDs
        """
        self._widget_manager.set_locations_map(container_id, locations_map)
    
    def get_widgets_at_subcontainer_location(self, container_id, subcontainer_location):
        """
        Get all widgets at a specific subcontainer location.
        
        Args:
            container_id: The container's unique ID
            subcontainer_location: The subcontainer location
            
        Returns:
            list: A list of widget IDs at the specified location
        """
        return self._widget_manager.get_widgets_at_location(container_id, subcontainer_location)
    
    def get_subcontainer_id_at_location(self, container_id, location):
        """
        Get the subcontainer widget ID at a specific location.
        
        Args:
            container_id: The container's unique ID
            location: The subcontainer location within the container
            
        Returns:
            str: The widget ID of the subcontainer, or None if not found
        """
        return self._widget_manager.get_subcontainer_id_at_location(container_id, location)
    
    #MARK: - Widget relationship methods
    
    def get_container_id_from_widget_id(self, widget_id):
        """
        Get the container ID from a widget ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            str: The container's unique ID, or None if invalid
        """
        return self._widget_manager.get_container_id_from_widget_id(widget_id)
    
    def get_widget_ids_by_container_id(self, container_unique_id):
        """
        Get all widget IDs for a specific container.
        
        Args:
            container_unique_id: The container's unique ID
            
        Returns:
            list: A list of widget IDs in the container
        """
        return self._widget_manager.get_widget_ids_by_container_id(container_unique_id)
    
    def get_widget_ids_by_container_id_and_location(self, container_unique_id, location):
        """
        Get all widget IDs for a specific container and location.
        
        Args:
            container_unique_id: The container's unique ID
            location: The container location
            
        Returns:
            list: A list of widget IDs in the container at the specified location
        """
        return self._widget_manager.get_widget_ids_by_container_id_and_location(container_unique_id, location)
    
    #MARK: - Observable relationship methods
    
    def get_observable_id_from_property_id(self, property_id):
        """
        Get the observable ID from a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The observable's unique ID, or None if invalid or no observable
        """
        return self._observable_manager.get_observable_id_from_property_id(property_id)
    
    def get_property_ids_by_observable_id(self, observable_unique_id):
        """
        Get all property IDs for a specific observable.
        
        Args:
            observable_unique_id: The observable's unique ID
            
        Returns:
            list: A list of property IDs for the observable
        """
        return self._observable_manager.get_property_ids_by_observable_id(observable_unique_id)
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_unique_id, property_name):
        """
        Get all property IDs for a specific observable and property name.
        
        Args:
            observable_unique_id: The observable's unique ID
            property_name: The property name
            
        Returns:
            list: A list of property IDs matching the criteria
        """
        return self._observable_manager.get_property_ids_by_observable_id_and_property_name(
            observable_unique_id, property_name
        )
    
    def get_controller_id_from_property_id(self, property_id):
        """
        Get the controller ID from a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The controller's unique ID, or None if invalid or no controller
        """
        return self._observable_manager.get_controller_id_from_property_id(property_id)
    
    def get_property_ids_by_controller_id(self, controller_unique_id):
        """
        Get all property IDs for a specific controller.
        
        Args:
            controller_unique_id: The controller's unique ID
            
        Returns:
            list: A list of property IDs controlled by the controller
        """
        return self._observable_manager.get_property_ids_by_controller_id(controller_unique_id)
    
    #MARK: - ID update methods
    
    def update_id(self, old_id, new_id):
        """
        Update a component's ID and all references to it.
        
        Args:
            old_id: The current component ID
            new_id: The new component ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine component type from ID
        if old_id.startswith(tuple(ALL_WIDGET_TYPE_CODES)) and new_id.startswith(tuple(ALL_WIDGET_TYPE_CODES)):
            # Widget/Container
            result = self._widget_manager.update_widget_id(old_id, new_id)
            
            # Notify subscribers
            if result:
                self._subscription_manager.notify(old_id, new_id)
                
                # Call the ID changed callback if set
                if self._on_id_changed:
                    self._on_id_changed(old_id, new_id)
            
            return result
        elif old_id.startswith(tuple(OBSERVABLE_TYPE_CODES)) and new_id.startswith(tuple(OBSERVABLE_TYPE_CODES)):
            # Observable
            result = self._observable_manager.update_observable_id(old_id, new_id)
            
            # Notify subscribers
            if result:
                self._subscription_manager.notify(old_id, new_id)
                
                # Call the ID changed callback if set
                if self._on_id_changed:
                    self._on_id_changed(old_id, new_id)
            
            return result
        elif old_id.startswith(tuple(PROPERTY_TYPE_CODES)) and new_id.startswith(tuple(PROPERTY_TYPE_CODES)):
            # Property
            result = self._observable_manager.update_property_id(old_id, new_id)
            
            # Notify subscribers
            if result:
                self._subscription_manager.notify(old_id, new_id)
                
                # Call the ID changed callback if set
                if self._on_id_changed:
                    self._on_id_changed(old_id, new_id)
            
            return result
        
        return False
    
    def update_container_id(self, widget_id, new_container_id):
        """
        Update a widget's container reference.
        
        Args:
            widget_id: The ID of the widget to update
            new_container_id: The new container's unique ID
            
        Returns:
            str: The updated widget ID
        """
        old_id = widget_id
        new_id = self._widget_manager.update_widget_container(widget_id, new_container_id)
        
        # Notify subscribers if ID changed
        if old_id != new_id:
            self._subscription_manager.notify(old_id, new_id)
            
            # Call the ID changed callback if set
            if self._on_id_changed:
                self._on_id_changed(old_id, new_id)
        
        return new_id
    
    def update_location(self, widget_id, new_location):
        """
        Update a widget's location.
        
        Args:
            widget_id: The ID of the widget to update
            new_location: The new widget location ID
            
        Returns:
            str: The updated widget ID
        """
        old_id = widget_id
        new_id = self._widget_manager.update_widget_location(widget_id, new_location)
        
        # Notify subscribers if ID changed
        if old_id != new_id:
            self._subscription_manager.notify(old_id, new_id)
            
            # Call the ID changed callback if set
            if self._on_id_changed:
                self._on_id_changed(old_id, new_id)
        
        return new_id
    
    def update_observable_id(self, property_id, new_observable_id):
        """
        Update a property's observable reference.
        
        Args:
            property_id: The ID of the property to update
            new_observable_id: The new observable's unique ID
            
        Returns:
            str: The updated property ID
        """
        old_id = property_id
        new_id = self._observable_manager.update_property_observable(property_id, new_observable_id)
        
        # Notify subscribers if ID changed
        if old_id != new_id:
            self._subscription_manager.notify(old_id, new_id)
            
            # Call the ID changed callback if set
            if self._on_id_changed:
                self._on_id_changed(old_id, new_id)
        
        return new_id
    
    def update_property_name(self, property_id, new_property_name):
        """
        Update a property's name.
        
        Args:
            property_id: The ID of the property to update
            new_property_name: The new property name
            
        Returns:
            str: The updated property ID
        """
        old_id = property_id
        new_id = self._observable_manager.update_property_name(property_id, new_property_name)
        
        # Notify subscribers if ID changed
        if old_id != new_id:
            self._subscription_manager.notify(old_id, new_id)
            
            # Call the ID changed callback if set
            if self._on_id_changed:
                self._on_id_changed(old_id, new_id)
        
        return new_id
    
    def update_controller_id(self, property_id, new_controller_id):
        """
        Update a property's controller reference.
        
        Args:
            property_id: The ID of the property to update
            new_controller_id: The new controller's unique ID
            
        Returns:
            str: The updated property ID
        """
        old_id = property_id
        new_id = self._observable_manager.update_property_controller(property_id, new_controller_id)
        
        # Notify subscribers if ID changed
        if old_id != new_id:
            self._subscription_manager.notify(old_id, new_id)
            
            # Call the ID changed callback if set
            if self._on_id_changed:
                self._on_id_changed(old_id, new_id)
        
        return new_id
    
    #MARK: - Reference removal methods
    
    def remove_container_reference(self, widget_id):
        """
        Remove a widget's container reference.
        
        Args:
            widget_id: The ID of the widget
            
        Returns:
            str: The updated widget ID
        """
        return self.update_container_id(widget_id, DEFAULT_ROOT_CONTAINER_ID)
    
    def remove_observable_reference(self, property_id):
        """
        Remove a property's observable reference.
        
        Args:
            property_id: The ID of the property
            
        Returns:
            str: The updated property ID
        """
        return self.update_observable_id(property_id, DEFAULT_NO_OBSERVABLE)
    
    def remove_controller_reference(self, property_id):
        """
        Remove a property's controller reference.
        
        Args:
            property_id: The ID of the property
            
        Returns:
            str: The updated property ID
        """
        return self.update_controller_id(property_id, DEFAULT_NO_CONTROLLER)
    
    #MARK: - Subscription methods
    
    def subscribe_to_id(self, component_id, callback):
        """
        Subscribe to changes for a specific component ID.
        
        Args:
            component_id: The component ID to subscribe to
            callback: The callback function that takes old_id and new_id as arguments
            
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        return self._subscription_manager.subscribe(component_id, callback)
    
    def unsubscribe_from_id(self, component_id, callback=None):
        """
        Unsubscribe from changes for a specific component ID.
        
        Args:
            component_id: The component ID to unsubscribe from
            callback: The callback function to unsubscribe, or None to unsubscribe all
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        return self._subscription_manager.unsubscribe(component_id, callback)
    
    def clear_subscriptions(self):
        """
        Clear all ID subscriptions.
        
        Returns:
            bool: True if successful
        """
        self._subscription_manager.clear()
        return True
    
    #MARK: - Callback methods
    
    def set_on_widget_unregister(self, callback):
        """
        Set the callback for widget unregistration.
        
        Args:
            callback: The callback function that takes widget_id and widget as arguments
        """
        self._widget_manager.set_on_widget_unregister(callback)
    
    def set_on_observable_unregister(self, callback):
        """
        Set the callback for observable unregistration.
        
        Args:
            callback: The callback function that takes observable_id and observable as arguments
        """
        self._observable_manager.set_on_observable_unregister(callback)
    
    def set_on_property_unregister(self, callback):
        """
        Set the callback for property unregistration.
        
        Args:
            callback: The callback function that takes property_id and property as arguments
        """
        self._observable_manager.set_on_property_unregister(callback)
    
    def set_on_id_changed(self, callback):
        """
        Set the callback for ID changes.
        
        Args:
            callback: The callback function that takes old_id and new_id as arguments
        """
        self._on_id_changed = callback
    
    #MARK: - Internal methods
    
    def _on_widget_unregister(self, widget_id, widget):
        """
        Internal callback for widget unregistration.
        
        Args:
            widget_id: The ID of the unregistered widget
            widget: The unregistered widget object
        """
        # Get the unique ID
        unique_id = get_unique_id_from_id(widget_id)
        if unique_id:
            # Unregister from ID generator
            self._id_generator.unregister(unique_id)
    
    def _on_observable_unregister(self, observable_id, observable):
        """
        Internal callback for observable unregistration.
        
        Args:
            observable_id: The ID of the unregistered observable
            observable: The unregistered observable object
        """
        # Get the unique ID
        unique_id = get_unique_id_from_id(observable_id)
        if unique_id:
            # Unregister from ID generator
            self._id_generator.unregister(unique_id)
    
    def _on_property_unregister(self, property_id, property_obj):
        """
        Internal callback for property unregistration.
        
        Args:
            property_id: The ID of the unregistered property
            property_obj: The unregistered property object
        """
        # Get the unique ID
        unique_id = get_unique_id_from_id(property_id)
        if unique_id:
            # Unregister from ID generator
            self._id_generator.unregister(unique_id)
    
    #MARK: - Cleanup method
    
    def clear(self):
        """Clear the entire registry and all managers."""
        self._widget_manager.clear()
        self._observable_manager.clear()
        self._subscription_manager.clear()
        
        # Reset ID generator
        self._id_generator = UniqueIDGenerator()
        
        # Clear callback references
        self._on_id_changed = None