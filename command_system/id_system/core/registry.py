"""
Core Registry module.

This module contains the central IDRegistry class that coordinates all components
of the ID system.
"""

from command_system.id_system.core.generator import UniqueIDGenerator
from command_system.id_system.core.mapping import Mapping, UniqueIdMapping
from command_system.id_system.core.parser import (
    parse_widget_id,
    parse_observable_id,
    parse_property_id,
    get_unique_id_from_id,
    create_widget_id,
    create_observable_id,
    create_property_id,
    get_type_code_from_id
)
from command_system.id_system.managers.widget_manager import WidgetManager, IDRegistrationError
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
    ObservableTypeCodes,
    TypeCodes,
    PropertyTypeCodes,
    ID_SEPARATOR
)
from command_system.id_system.utils.validation import validate_id_type_consistency
from command_system.id_system.utils.id_operations import update_id as util_update_id

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
        
        # List of mapping objects to update when IDs change
        self.mappings = []
        
        # Callback lists for different events
        self._widget_unregister_callbacks = []
        self._observable_unregister_callbacks = []
        self._property_unregister_callbacks = []
        self._id_changed_callbacks = []
        
        # Create the core mappings that the system relies on
        self._widgets_mapping = Mapping(update_keys=True, update_values=False)
        self._unique_to_full_id_mapping = UniqueIdMapping()
        self._objects_to_id_mapping = Mapping(update_keys=False, update_values=True)
        
        # Add the mappings to the registry
        self.mappings.append(self._widgets_mapping)
        self.mappings.append(self._unique_to_full_id_mapping)
        self.mappings.append(self._objects_to_id_mapping)
        
        # Managers for different component types
        self._widget_manager = WidgetManager(self)
        self._observable_manager = ObservableManager(self)
        
        # Get the subscription manager
        self._subscription_manager = get_subscription_manager()
        self._subscription_manager.init_mapping(self)
        
        # Create mapping for non-controlling observables
        self._non_controlling_observables = Mapping(update_keys=True, update_values=True)
        self.mappings.append(self._non_controlling_observables)
    
    #MARK: - Mapping update methods
    
    def update_all_mappings(self, old_id, new_id):
        """
        Update all mappings when an ID changes.
        
        Args:
            old_id: The current ID string
            new_id: The new ID string
        """
        for mapping in self.mappings:
            mapping.update(old_id, new_id)
    
    def remove_from_all_mappings(self, id_to_remove):
        """
        Remove an ID from all mappings when it's unregistered.
        
        Args:
            id_to_remove: The ID to remove from all mappings
        """
        for mapping in self.mappings:
            # Only delete if this ID is a key in the mapping
            if id_to_remove in mapping:
                mapping.delete(id_to_remove)
    
    #MARK: - Registration methods
    
    def register(self, widget, type_code, widget_id=None, container_id=None, location=None):
        """
        Register a widget with the registry.
        
        Args:
            widget: The widget object to register
            type_code: The widget type code
            widget_id: Optional full widget ID or unique ID (default: None, will be generated)
            container_id: The container's full ID (default: None, will use root container)
            location: The widget_location_id (default: None, will be generated)
            
        Returns:
            str: The generated widget ID
            
        Raises:
            IDRegistrationError: If the widget_location_id already exists in the container location
        """
        # Extract unique ID if full widget ID is provided
        unique_id = None
        if widget_id:
            if ID_SEPARATOR in widget_id:
                unique_id = get_unique_id_from_id(widget_id)
            else:
                unique_id = widget_id
                
        # Generate or use the provided unique ID
        if unique_id is None:
            unique_id = self._id_generator.generate()
        else:
            # Ensure the ID is registered with the generator to prevent collisions
            self._id_generator.register(unique_id)
        
        # Determine container ID
        final_container_id = container_id if container_id else DEFAULT_ROOT_CONTAINER_ID
        
        # Register with the widget manager
        try:
            widget_id = self._widget_manager.register_widget(
                widget,
                type_code,
                unique_id,
                final_container_id,
                location
            )
            
            # Use mappings to store the relationships
            self._widgets_mapping.add(widget_id, widget)
            self._unique_to_full_id_mapping.add_id_mapping(widget_id)
            if widget is not None:
                self._objects_to_id_mapping.add(widget, widget_id)
                
            return widget_id
        except IDRegistrationError as e:
            # Unregister the unique ID since registration failed
            self._id_generator.unregister(unique_id)
            raise e
    
    def register_observable(self, observable, type_code, observable_id=None):
        """
        Register an observable with the registry.
        
        Args:
            observable: The observable object to register
            type_code: The observable type code
            observable_id: Optional full observable ID or unique ID (default: None, will be generated)
            
        Returns:
            str: The generated observable ID
        """
        # Extract unique ID if full observable ID is provided
        unique_id = None
        if observable_id:
            if ID_SEPARATOR in observable_id:
                unique_id = get_unique_id_from_id(observable_id)
            else:
                unique_id = observable_id
                
        # Generate or use the provided unique ID
        if unique_id is None:
            unique_id = self._id_generator.generate()
        else:
            # Ensure the ID is registered with the generator to prevent collisions
            self._id_generator.register(unique_id)
        
        # Register with the observable manager
        observable_id = self._observable_manager.register_observable(
            observable,
            type_code,
            unique_id
        )
        
        # Use mappings to store the relationships
        self._widgets_mapping.add(observable_id, observable)
        self._unique_to_full_id_mapping.add_id_mapping(observable_id)
        if observable is not None:
            self._objects_to_id_mapping.add(observable, observable_id)
        
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
            property_id: Optional full property ID or unique ID (default: None, will be generated)
            property_name: The name of the property (default: "0")
            observable_id: The full observable ID or unique ID (default: "0")
            controller_id: The full controller widget ID or unique ID (default: "0")
            
        Returns:
            str: The generated property ID
        """
        # Extract unique ID if full property ID is provided
        unique_id = None
        if property_id:
            if ID_SEPARATOR in property_id:
                unique_id = get_unique_id_from_id(property_id)
            else:
                unique_id = property_id
                
        # Generate or use the provided unique ID
        if unique_id is None:
            unique_id = self._id_generator.generate()
        else:
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
        
        # Use mappings to store the relationships
        self._widgets_mapping.add(property_id, property_obj)
        self._unique_to_full_id_mapping.add_id_mapping(property_id)
        if property_obj is not None:
            self._objects_to_id_mapping.add(property_obj, property_id)
        
        return property_id
    
    def unregister(self, component_id):
        """
        Unregister a component from the registry.
        
        When a widget that controls properties is unregistered, all properties it controls
        will also be unregistered.
        
        When an observable's last property is unregistered, the observable itself will also
        be unregistered.
        
        When a container is unregistered, all widgets within it will be unregistered.
        
        Args:
            component_id: The ID of the component to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the component object before unregistering
        component = self._widgets_mapping.get(component_id)
        
        # Determine component type from ID prefix
        if component_id.startswith(tuple(TypeCodes.get_all_widget_codes())):
            # Check if this widget is controlling any properties
            controlled_properties = self.get_controller_properties(component_id)
            
            # Widget/Container
            success = self._widget_manager.unregister_widget(component_id)
            if success:
                # Remove from mappings
                unique_id = get_unique_id_from_id(component_id)
                self.remove_from_all_mappings(component_id)
                self._unique_to_full_id_mapping.delete(unique_id)
                if component is not None:
                    self._objects_to_id_mapping.delete(component)
                self._id_generator.unregister(unique_id)
                
                # Unregister all properties this widget was controlling
                for property_id in controlled_properties:
                    self.unregister(property_id)
                    
                return True
            return False
        
        elif component_id.startswith(tuple(ObservableTypeCodes.get_all_codes())):
            # Observable
            success = self._observable_manager.unregister_observable(component_id)
            if success:
                # Remove from mappings
                unique_id = get_unique_id_from_id(component_id)
                self.remove_from_all_mappings(component_id)
                self._unique_to_full_id_mapping.delete(unique_id)
                if component is not None:
                    self._objects_to_id_mapping.delete(component)
                self._id_generator.unregister(unique_id)
                return True
            return False
        
        elif component_id.startswith(tuple(PropertyTypeCodes.get_all_codes())):
            # Get observable ID before unregistering the property
            observable_id = self.get_observable_id_from_property_id(component_id)
            
            # Property
            success = self._observable_manager.unregister_property(component_id)
            if success:
                # Remove from mappings
                unique_id = get_unique_id_from_id(component_id)
                self.remove_from_all_mappings(component_id)
                self._unique_to_full_id_mapping.delete(unique_id)
                if component is not None:
                    self._objects_to_id_mapping.delete(component)
                self._id_generator.unregister(unique_id)
                
                # Check if this was the last property of the observable
                if observable_id and not self.get_observable_properties(observable_id):
                    # If no properties left, unregister the observable
                    self.unregister(observable_id)
                    
                return True
            return False
        
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
        return self._widgets_mapping.get(widget_id)
    
    def get_observable(self, observable_id):
        """
        Get an observable by its ID.
        
        Args:
            observable_id: The observable ID
            
        Returns:
            object: The observable object, or None if not found
        """
        return self._widgets_mapping.get(observable_id)
    
    def get_observable_property(self, property_id):
        """
        Get a property by its ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            object: The property object, or None if not found
        """
        return self._widgets_mapping.get(property_id)
    
    def get_id(self, component):
        """
        Get the ID for a component.
        
        Args:
            component: The component object
            
        Returns:
            str: The component ID, or None if not found
        """
        if component is None:
            return None
        return self._objects_to_id_mapping.get(component)
    
    def get_unique_id_from_id(self, id_string):
        """
        Extract the unique ID portion from any type of ID string.
        
        Args:
            id_string: The ID string to extract from
            
        Returns:
            str: The unique ID or None if invalid format
        """
        return get_unique_id_from_id(id_string)
    
    def get_full_id_from_unique_id(self, unique_id, type_code=None):
        """
        Find the full ID for a component with the given unique ID.
        
        Args:
            unique_id: The unique ID to look up
            type_code: Optional type code to limit the search (default: None)
            
        Returns:
            str: The full ID or None if not found
        """
        # If no unique ID provided, return None
        if not unique_id:
            return None
        
        # Get the full ID from the mapping
        full_id = self._unique_to_full_id_mapping.get(unique_id)
        
        # If type_code is provided, check if the ID is of the right type
        if full_id and type_code:
            actual_type_code = get_type_code_from_id(full_id)
            if actual_type_code != type_code:
                return None
                
        return full_id
    
    #MARK: - Container relationship methods
    
    def get_container_widgets(self, container_id):
        """
        Get all widgets in a container.
        
        Args:
            container_id: The container's ID
            
        Returns:
            list: A list of widget IDs in the container
        """
        return self._widget_manager.get_widget_ids_by_container_id(container_id)
    
    #MARK: - Observable relationship methods
    
    def get_observable_properties(self, observable_id):
        """
        Get all properties of an observable.
        
        Args:
            observable_id: The observable's ID
            
        Returns:
            list: A list of property IDs for the observable
        """
        return self._observable_manager.get_property_ids_by_observable_id(observable_id)
    
    def get_controller_properties(self, controller_id):
        """
        Get all properties controlled by a controller.
        
        Args:
            controller_id: The controller's ID
            
        Returns:
            list: A list of property IDs controlled by the controller
        """
        return self._observable_manager.get_property_ids_by_controller_id(controller_id)
    
    def get_observable_id_from_property_id(self, property_id):
        """
        Get the observable ID associated with a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The full observable ID, or None if not found or invalid property ID
        """
        return self._observable_manager.get_observable_id_from_property_id(property_id)
    
    def get_controller_id_from_property_id(self, property_id):
        """
        Get the controller ID associated with a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The full controller ID, or None if not found or invalid property ID
        """
        controller_unique_id = self._observable_manager.get_controller_id_from_property_id(property_id)
        
        if not controller_unique_id or controller_unique_id == DEFAULT_NO_CONTROLLER:
            return None
        
        # Return the full controller ID
        return self.get_full_id_from_unique_id(controller_unique_id)
    
    def get_container_id_from_widget_id(self, widget_id):
        """
        Get the container ID from a widget ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            str: The full container ID, or None if not found or the widget has no container
        """
        # Get the unique container ID
        container_unique_id = self._widget_manager.get_container_id_from_widget_id(widget_id)
        
        if not container_unique_id or container_unique_id == DEFAULT_ROOT_CONTAINER_ID:
            return DEFAULT_ROOT_CONTAINER_ID
        
        # Return the full container ID
        return self.get_full_id_from_unique_id(container_unique_id)
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_id, property_name):
        """
        Get all property IDs for a given observable and property name.

        Args:
            observable_id: The observable's ID
            property_name: The property name

        Returns:
            list: A list of property IDs for the observable and property name
        """
        return self._observable_manager.get_property_ids_by_observable_id_and_property_name(observable_id, property_name)

    def register_non_controlling_observables(self, container_id, observable_ids):
        """
        Register observables that should not be controlled by widgets in a container location.
        
        Args:
            container_id: The container's ID
            observable_ids: List of observable IDs that should not be controlled
        """
        if not container_id or not observable_ids:
            return
            
        # Extract container components to get the location
        components = parse_widget_id(container_id)
        if not components:
            return
            
        # Use container_location/widget_location_id as the key for the mapping
        container_location = components['container_location']
        widget_location_id = components['widget_location_id']
        full_location = f"{container_location}/{widget_location_id}"
        
        # Get or create a set for this location
        current_observables = self._non_controlling_observables.get(full_location) or set()
        
        # Add the new observable IDs
        current_observables.update(observable_ids)
        
        # Update the mapping
        self._non_controlling_observables.add(full_location, current_observables)

    def should_prevent_control(self, widget_id, observable_id):
        """
        Check if a widget should not control a specific observable.
        
        Args:
            widget_id: The widget's ID
            observable_id: The observable's ID
            
        Returns:
            bool: True if control should be prevented, False otherwise
        """
        # Get the container hierarchy for this widget
        components = parse_widget_id(widget_id)
        if not components:
            return False
            
        # Extract widget's container location
        container_location = components['container_location']
        
        # Check all stored non-controlling locations
        for location, observables in self._non_controlling_observables._storage.items():
            # Check if widget's location starts with a non-controlling location
            if container_location.startswith(location):
                # Check if this observable is in the non-controlling set
                if observable_id in observables:
                    return True
        
        return False
    
    #MARK: - ID update methods
    
    def update_id(self, old_id, new_id):
        """
        Update any component's ID with a new ID.
        
        This method determines the component type and delegates to the appropriate
        manager to handle the update. It ensures type consistency and validates
        the updated ID.
        
        Args:
            old_id: The current ID string
            new_id: The new ID string to use
            
        Returns:
            tuple: (success, updated_id, error_message) where:
                - success is a boolean indicating if the update was successful
                - updated_id is the resulting ID after applying the update
                - error_message is None if successful or a string describing the issue
        """
        # First check for basic type consistency
        is_consistent, error_message = validate_id_type_consistency(old_id, new_id)
        if not is_consistent:
            return False, old_id, error_message
        
        # Determine component type from ID prefix
        type_code = get_type_code_from_id(old_id)
        
        # Delegate to the appropriate manager based on component type
        if type_code in TypeCodes.get_all_widget_codes():
            # Widget/Container ID update
            success, updated_id, error = self._widget_manager.update_widget_id(old_id, new_id)
            
            # If successful, update mappings and notify subscribers
            if success and updated_id != old_id:
                self.update_all_mappings(old_id, updated_id)
                self._subscription_manager.notify(old_id, updated_id)
                self._notify_id_changed_callbacks(old_id, updated_id)
                
            return success, updated_id, error
            
        elif type_code in ObservableTypeCodes.get_all_codes():
            # Observable ID update
            success, updated_id, error = self._observable_manager.update_observable_id(old_id, new_id)
            
            # If successful, update mappings and notify subscribers
            if success and updated_id != old_id:
                self.update_all_mappings(old_id, updated_id)
                self._subscription_manager.notify(old_id, updated_id)
                self._notify_id_changed_callbacks(old_id, updated_id)
                
            return success, updated_id, error
            
        elif type_code in PropertyTypeCodes.get_all_codes():
            # Property ID update
            success, updated_id, error = self._observable_manager.update_property_id(old_id, new_id)
            
            # If successful, update mappings and notify subscribers
            if success and updated_id != old_id:
                self.update_all_mappings(old_id, updated_id)
                self._subscription_manager.notify(old_id, updated_id)
                self._notify_id_changed_callbacks(old_id, updated_id)
                
            return success, updated_id, error
        
        # Unknown component type
        return False, old_id, f"Unknown component type: {type_code}"
    
    def update_container(self, widget_id, new_container_id):
        """
        Update a widget's container.
        
        Args:
            widget_id: The ID of the widget to update
            new_container_id: The new container's ID
            
        Returns:
            str: The updated widget ID
            
        Raises:
            IDRegistrationError: If the widget_location_id already exists in the new container location
        """
        old_id = widget_id
        
        try:
            new_id = self._widget_manager.update_widget_container(widget_id, new_container_id)
            
            # If the widget ID changed, update mappings and notify subscribers
            if old_id != new_id:
                self.update_all_mappings(old_id, new_id)
                self._subscription_manager.notify(old_id, new_id)
                self._notify_id_changed_callbacks(old_id, new_id)
            
            return new_id
        except IDRegistrationError as e:
            # Re-raise the error
            raise e
    
    def update_location(self, widget_id, new_location):
        """
        Update a widget's location ID within its container.
        
        Args:
            widget_id: The ID of the widget to update
            new_location: The new widget_location_id
            
        Returns:
            str: The updated widget ID
            
        Raises:
            IDRegistrationError: If the new widget_location_id already exists in the container location
        """
        old_id = widget_id
        
        try:
            new_id = self._widget_manager.update_widget_location(widget_id, new_location)
            
            # If the widget ID changed, update mappings and notify subscribers
            if old_id != new_id:
                self.update_all_mappings(old_id, new_id)
                self._subscription_manager.notify(old_id, new_id)
                self._notify_id_changed_callbacks(old_id, new_id)
            
            return new_id
        except IDRegistrationError as e:
            # Re-raise the error
            raise e
    
    def update_observable_reference(self, property_id, new_observable_id):
        """
        Update a property's observable reference.
        
        Args:
            property_id: The ID of the property to update
            new_observable_id: The new observable's ID
            
        Returns:
            str: The updated property ID
        """
        old_id = property_id
        new_id = self._observable_manager.update_property_observable(property_id, new_observable_id)
        
        # If the property ID changed, update mappings and notify subscribers
        if old_id != new_id:
            self.update_all_mappings(old_id, new_id)
            self._subscription_manager.notify(old_id, new_id)
            self._notify_id_changed_callbacks(old_id, new_id)
        
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
        
        # If the property ID changed, update mappings and notify subscribers
        if old_id != new_id:
            self.update_all_mappings(old_id, new_id)
            self._subscription_manager.notify(old_id, new_id)
            self._notify_id_changed_callbacks(old_id, new_id)
        
        return new_id
    
    def update_controller_reference(self, property_id, new_controller_id):
        """
        Update a property's controller reference.
        
        Args:
            property_id: The ID of the property to update
            new_controller_id: The new controller's ID
            
        Returns:
            str: The updated property ID
        """
        old_id = property_id
        new_id = self._observable_manager.update_property_controller(property_id, new_controller_id)
        
        # If the property ID changed, update mappings and notify subscribers
        if old_id != new_id:
            self.update_all_mappings(old_id, new_id)
            self._subscription_manager.notify(old_id, new_id)
            self._notify_id_changed_callbacks(old_id, new_id)
        
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
        return self.update_container(widget_id, DEFAULT_ROOT_CONTAINER_ID)
    
    def remove_observable_reference(self, property_id):
        """
        Remove a property's observable reference.
        
        Args:
            property_id: The ID of the property
            
        Returns:
            str: The updated property ID
        """
        return self.update_observable_reference(property_id, DEFAULT_NO_OBSERVABLE)
    
    def remove_controller_reference(self, property_id):
        """
        Remove a property's controller reference.
        
        Args:
            property_id: The ID of the property
            
        Returns:
            str: The updated property ID
        """
        return self.update_controller_reference(property_id, DEFAULT_NO_CONTROLLER)
    
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
    
    def add_widget_unregister_callback(self, callback):
        """
        Add a callback for widget unregistration.
        
        Args:
            callback: The callback function that takes widget_id and widget as arguments
            
        Returns:
            bool: True if addition was successful, False if callback already exists
        """
        if callback not in self._widget_unregister_callbacks:
            self._widget_unregister_callbacks.append(callback)
            return True
        return False
    
    def remove_widget_unregister_callback(self, callback):
        """
        Remove a callback for widget unregistration.
        
        Args:
            callback: The callback function to remove
            
        Returns:
            bool: True if removal was successful, False if callback not found
        """
        if callback in self._widget_unregister_callbacks:
            self._widget_unregister_callbacks.remove(callback)
            return True
        return False
    
    def add_observable_unregister_callback(self, callback):
        """
        Add a callback for observable unregistration.
        
        Args:
            callback: The callback function that takes observable_id and observable as arguments
            
        Returns:
            bool: True if addition was successful, False if callback already exists
        """
        if callback not in self._observable_unregister_callbacks:
            self._observable_unregister_callbacks.append(callback)
            return True
        return False
    
    def remove_observable_unregister_callback(self, callback):
        """
        Remove a callback for observable unregistration.
        
        Args:
            callback: The callback function to remove
            
        Returns:
            bool: True if removal was successful, False if callback not found
        """
        if callback in self._observable_unregister_callbacks:
            self._observable_unregister_callbacks.remove(callback)
            return True
        return False
    
    def add_property_unregister_callback(self, callback):
        """
        Add a callback for property unregistration.
        
        Args:
            callback: The callback function that takes property_id and property as arguments
            
        Returns:
            bool: True if addition was successful, False if callback already exists
        """
        if callback not in self._property_unregister_callbacks:
            self._property_unregister_callbacks.append(callback)
            return True
        return False
    
    def remove_property_unregister_callback(self, callback):
        """
        Remove a callback for property unregistration.
        
        Args:
            callback: The callback function to remove
            
        Returns:
            bool: True if removal was successful, False if callback not found
        """
        if callback in self._property_unregister_callbacks:
            self._property_unregister_callbacks.remove(callback)
            return True
        return False
    
    def add_id_changed_callback(self, callback):
        """
        Add a callback for ID changes.
        
        Args:
            callback: The callback function that takes old_id and new_id as arguments
            
        Returns:
            bool: True if addition was successful, False if callback already exists
        """
        if callback not in self._id_changed_callbacks:
            self._id_changed_callbacks.append(callback)
            return True
        return False
    
    def remove_id_changed_callback(self, callback):
        """
        Remove a callback for ID changes.
        
        Args:
            callback: The callback function to remove
            
        Returns:
            bool: True if removal was successful, False if callback not found
        """
        if callback in self._id_changed_callbacks:
            self._id_changed_callbacks.remove(callback)
            return True
        return False

    def clear_widget_unregister_callbacks(self):
        """
        Clear all widget unregister callbacks.
        """
        self._widget_unregister_callbacks.clear()

    def clear_observable_unregister_callbacks(self):
        """
        Clear all observable unregister callbacks.
        """
        self._observable_unregister_callbacks.clear()

    def clear_property_unregister_callbacks(self):
        """
        Clear all property unregister callbacks.
        """
        self._property_unregister_callbacks.clear()

    def clear_id_changed_callbacks(self):
        """
        Clear all ID changed callbacks.
        """
        self._id_changed_callbacks.clear()

    def clear_all_callbacks(self):
        """
        Clear all callbacks.
        """
        self.clear_widget_unregister_callbacks()
        self.clear_observable_unregister_callbacks()
        self.clear_property_unregister_callbacks()
        self.clear_id_changed_callbacks()

    #MARK: - Internal callback notification methods

    def _notify_widget_unregister_callbacks(self, widget_id, widget):
        """
        Notify all registered widget unregister callbacks.
        
        Args:
            widget_id: The ID of the unregistered widget
            widget: The unregistered widget object
        """
        for callback in self._widget_unregister_callbacks:
            try:
                callback(widget_id, widget)
            except Exception as e:
                print(f"Error in widget unregister callback: {e}")

    def _notify_observable_unregister_callbacks(self, observable_id, observable):
        """
        Notify all registered observable unregister callbacks.
        
        Args:
            observable_id: The ID of the unregistered observable
            observable: The unregistered observable object
        """
        for callback in self._observable_unregister_callbacks:
            try:
                callback(observable_id, observable)
            except Exception as e:
                print(f"Error in observable unregister callback: {e}")

    def _notify_property_unregister_callbacks(self, property_id, property_obj):
        """
        Notify all registered property unregister callbacks.
        
        Args:
            property_id: The ID of the unregistered property
            property_obj: The unregistered property object
        """
        for callback in self._property_unregister_callbacks:
            try:
                callback(property_id, property_obj)
            except Exception as e:
                print(f"Error in property unregister callback: {e}")

    def _notify_id_changed_callbacks(self, old_id, new_id):
        """
        Notify all registered ID changed callbacks.
        
        Args:
            old_id: The old component ID
            new_id: The new component ID
        """
        for callback in self._id_changed_callbacks:
            try:
                callback(old_id, new_id)
            except Exception as e:
                print(f"Error in ID changed callback: {e}")

    #MARK: - Internal methods

    def _on_widget_unregister(self, widget_id, widget):
        """
        Internal callback for widget unregistration.
        
        Args:
            widget_id: The ID of the unregistered widget
            widget: The unregistered widget object
        """
        # Notify all widget unregister callbacks
        self._notify_widget_unregister_callbacks(widget_id, widget)

    def _on_observable_unregister(self, observable_id, observable):
        """
        Internal callback for observable unregistration.
        
        Args:
            observable_id: The ID of the unregistered observable
            observable: The unregistered observable object
        """
        # Notify all observable unregister callbacks
        self._notify_observable_unregister_callbacks(observable_id, observable)

    def _on_property_unregister(self, property_id, property_obj):
        """
        Internal callback for property unregistration.
        
        Args:
            property_id: The ID of the unregistered property
            property_obj: The unregistered property object
        """
        # Notify all property unregister callbacks
        self._notify_property_unregister_callbacks(property_id, property_obj)

    #MARK: - Cleanup method

    def clear(self):
        """Clear the entire registry and all managers."""
        self._widget_manager.clear()
        self._observable_manager.clear()
        self._subscription_manager.clear()
        
        # Clear all mappings
        for mapping in self.mappings:
            mapping._storage.clear()
            mapping._key_log.clear()
            mapping._value_log.clear()
        
        # Clear all callbacks
        self.clear_all_callbacks()
        
        # Reset ID generator
        self._id_generator = UniqueIDGenerator()

    def get_container_widgets_at_location(self, container_id, location):
        """
        Get all widgets at a specific location in a container.
        
        Args:
            container_id: The container's ID
            location: The container location
            
        Returns:
            list: A list of widget IDs at the specified location
        """
        return self._widget_manager.get_widget_ids_by_container_id_and_location(container_id, location)
        
    def get_widgets_by_container_id(self, container_id):
        """
        Get all widgets in a container.

        Args:
            container_id: The container's ID

        Returns:
            list: A list of widget IDs in the container
        """
        return self._widget_manager.get_widget_ids_by_container_id(container_id)
        
    def get_container_id_from_widget_id(self, widget_id):
        """
        Get the container ID from a widget ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            str: The container's full ID, or DEFAULT_ROOT_CONTAINER_ID if not found or the widget has no container
        """
        # Get the container unique ID
        container_unique_id = self._widget_manager.get_container_id_from_widget_id(widget_id)
        
        if not container_unique_id or container_unique_id == DEFAULT_ROOT_CONTAINER_ID:
            return DEFAULT_ROOT_CONTAINER_ID
        
        # Return the full container ID
        return self.get_full_id_from_unique_id(container_unique_id)

    def set_locations_map(self, container_id, locations_map):
        """
        Set the container's locations map.
        
        Args:
            container_id: The container's ID
            locations_map: A dictionary mapping subcontainer locations to widget IDs
        """
        self._widget_manager.set_locations_map(container_id, locations_map)

    def get_locations_map(self, container_id):
        """
        Get the container's locations map.
        
        Args:
            container_id: The container's ID
            
        Returns:
            dict: A dictionary mapping subcontainer locations to widget IDs
        """
        return self._widget_manager.get_locations_map(container_id)
    
    def is_id_registered(self, component_id):
        """
        Check if an ID is registered in the registry.
        
        Args:
            component_id: The ID to check
            
        Returns:
            bool: True if the ID is registered, False otherwise
        """
        return component_id in self._widgets_mapping