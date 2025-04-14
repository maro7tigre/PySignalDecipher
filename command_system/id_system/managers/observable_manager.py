"""
Observable Manager module.

This module contains the ObservableManager class for managing observables, properties,
and their relationships in the ID system.
"""

from command_system.id_system.core.mapping import Mapping
from command_system.id_system.core.parser import (
    parse_observable_id,
    parse_property_id,
    create_observable_id,
    create_property_id,
    get_unique_id_from_id,
)
from command_system.id_system.types import (
    DEFAULT_NO_OBSERVABLE,
    DEFAULT_NO_CONTROLLER,
    DEFAULT_NO_PROPERTY_NAME,
    ID_SEPARATOR,
)

#MARK: - ObservableManager class

class ObservableManager:
    """
    Manages observables, properties, and their relationships in the ID system.
    
    This class handles the registration, unregistration, and updates of
    observables, properties, and their relationships with widgets.
    """
    
    def __init__(self, registry):
        """Initialize the observable manager."""
        self.registry = registry
        
        # Create mappings
        self._observable_to_properties = Mapping(update_keys=True, update_values=True)
        self._controller_to_properties = Mapping(update_keys=True, update_values=True)
        
        # Add mappings to registry for automatic updates
        self.registry.mappings.append(self._observable_to_properties)
        self.registry.mappings.append(self._controller_to_properties)
    
    #MARK: - Observable registration methods
    
    def register_observable(self, observable, type_code, unique_id):
        """
        Register an observable with the manager.
        
        Args:
            observable: The observable object to register
            type_code: The observable type code
            unique_id: The unique ID for the observable
            
        Returns:
            str: The generated observable ID
        """
        # Create the observable ID
        observable_id = create_observable_id(type_code, unique_id)
        
        # Initialize empty property set for this observable
        self._observable_to_properties.add(unique_id, set())
        
        return observable_id
    
    def unregister_observable(self, observable_id):
        """
        Unregister an observable from the manager.
        
        Args:
            observable_id: The ID of the observable to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Extract components
        components = parse_observable_id(observable_id)
        if not components:
            return False
        
        unique_id = components['unique_id']
        
        # Get the observable object
        observable = self.registry.get_observable(observable_id)
        
        # Call the unregister callback if set
        self.registry._on_observable_unregister(observable_id, observable)
        
        # Handle associated properties - get all property IDs for this observable
        property_ids = self.get_property_ids_by_observable_id(unique_id)
        
        # Unregister all associated properties
        for property_id in list(property_ids):
            self.registry.unregister(property_id)
        
        # Remove from observable mapping
        self._observable_to_properties.delete(unique_id)
        
        return True
    
    #MARK: - Property registration methods
    
    def register_property(self, property_obj, type_code, unique_id, 
                         observable_id=DEFAULT_NO_OBSERVABLE,
                         property_name=DEFAULT_NO_PROPERTY_NAME, 
                         controller_id=DEFAULT_NO_CONTROLLER):
        """
        Register a property with the manager.
        
        Args:
            property_obj: The property object to register (can be None for descriptor properties)
            type_code: The property type code
            unique_id: The unique ID for the property
            observable_id: The observable ID or unique ID (default: "0")
            property_name: The name of the property (default: "0")
            controller_id: The controller ID or unique ID (default: "0")
            
        Returns:
            str: The generated property ID
        """
        # Extract observable unique ID if full ID provided
        observable_unique_id = observable_id
        if observable_id and observable_id != DEFAULT_NO_OBSERVABLE and ID_SEPARATOR in observable_id:
            observable_unique_id = get_unique_id_from_id(observable_id)
            
        # Extract controller unique ID if full ID provided
        controller_unique_id = controller_id
        if controller_id and controller_id != DEFAULT_NO_CONTROLLER and ID_SEPARATOR in controller_id:
            controller_unique_id = get_unique_id_from_id(controller_id)
        elif not controller_id:
            controller_unique_id = DEFAULT_NO_CONTROLLER
        
        # Create the property ID
        property_id = create_property_id(
            type_code,
            unique_id,
            observable_unique_id,
            property_name,
            controller_unique_id
        )
        
        # Add to observable's property set if applicable
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            # Get current properties for this observable
            props = self._observable_to_properties.get(observable_unique_id) or set()
            props.add(property_id)
            self._observable_to_properties.add(observable_unique_id, props)
        
        # Add to controller's property set if applicable
        if controller_unique_id != DEFAULT_NO_CONTROLLER:
            # Get current properties for this controller
            props = self._controller_to_properties.get(controller_unique_id) or set()
            props.add(property_id)
            self._controller_to_properties.add(controller_unique_id, props)
        
        return property_id
    
    def unregister_property(self, property_id):
        """
        Unregister a property from the manager.
        
        Args:
            property_id: The ID of the property to unregister
                
        Returns:
            bool: True if successful, False otherwise
        """
        # Extract components
        components = parse_property_id(property_id)
        if not components:
            return False
        
        observable_unique_id = components['observable_unique_id']
        controller_id = components['controller_id']
        
        # Get the property object
        property_obj = self.registry.get_observable_property(property_id)
        
        # Call the unregister callback if set
        self.registry._on_property_unregister(property_id, property_obj)
        
        # Remove from observable's property set if applicable
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            props = self._observable_to_properties.get(observable_unique_id)
            if props:
                props.discard(property_id)
                if not props:
                    # If this was the last property, remove the observable
                    self._observable_to_properties.delete(observable_unique_id)
                    
                    # Find the observable_id and unregister it
                    observable_id = self.registry.get_full_id_from_unique_id(observable_unique_id)
                    if observable_id:
                        self.registry.unregister(observable_id)
                else:
                    # Update the property set
                    self._observable_to_properties.add(observable_unique_id, props)
        
        # Remove from controller's property set if applicable
        if controller_id != DEFAULT_NO_CONTROLLER:
            props = self._controller_to_properties.get(controller_id)
            if props:
                props.discard(property_id)
                if not props:
                    # If this was the last property, remove the entry
                    self._controller_to_properties.delete(controller_id)
                else:
                    # Update the property set
                    self._controller_to_properties.add(controller_id, props)
        
        return True
    
    #MARK: - Update methods
    
    def update_property_observable(self, property_id, new_observable_unique_id):
        """
        Update a property's observable reference.
        
        Args:
            property_id: The ID of the property to update
            new_observable_unique_id: The new observable's unique ID
            
        Returns:
            str: The updated property ID
        """
        property_obj = self.registry.get_observable_property(property_id)
        if property_obj is None:
            return property_id
        
        # Extract components
        components = parse_property_id(property_id)
        if not components:
            return property_id
        
        old_observable_unique_id = components['observable_unique_id']
        
        # If the observable hasn't changed, no update needed
        if old_observable_unique_id == new_observable_unique_id:
            return property_id
        
        # Create the updated property ID
        new_property_id = create_property_id(
            components['type_code'],
            components['unique_id'],
            new_observable_unique_id,
            components['property_name'],
            components['controller_id']
        )
        
        # Remove from old observable's property set
        if old_observable_unique_id != DEFAULT_NO_OBSERVABLE:
            props = self._observable_to_properties.get(old_observable_unique_id)
            if props:
                props.discard(property_id)
                if not props:
                    # If this was the last property, remove the observable
                    self._observable_to_properties.delete(old_observable_unique_id)
                else:
                    # Update the property set
                    self._observable_to_properties.add(old_observable_unique_id, props)
        
        # Add to new observable's property set
        if new_observable_unique_id != DEFAULT_NO_OBSERVABLE:
            props = self._observable_to_properties.get(new_observable_unique_id) or set()
            props.add(new_property_id)
            self._observable_to_properties.add(new_observable_unique_id, props)
        
        return new_property_id
    
    def update_property_name(self, property_id, new_property_name):
        """
        Update a property's name.
        
        Args:
            property_id: The ID of the property to update
            new_property_name: The new property name
            
        Returns:
            str: The updated property ID
        """
        property_obj = self.registry.get_observable_property(property_id)
        if property_obj is None:
            return property_id
        
        # Extract components
        components = parse_property_id(property_id)
        if not components:
            return property_id
        
        old_property_name = components['property_name']
        
        # If the property name hasn't changed, no update needed
        if old_property_name == new_property_name:
            return property_id
        
        # Create the updated property ID
        new_property_id = create_property_id(
            components['type_code'],
            components['unique_id'],
            components['observable_unique_id'],
            new_property_name,
            components['controller_id']
        )
        
        # Update observable's property set
        observable_unique_id = components['observable_unique_id']
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            props = self._observable_to_properties.get(observable_unique_id)
            if props:
                props.discard(property_id)
                props.add(new_property_id)
                self._observable_to_properties.add(observable_unique_id, props)
        
        # Update controller's property set
        controller_id = components['controller_id']
        if controller_id != DEFAULT_NO_CONTROLLER:
            props = self._controller_to_properties.get(controller_id)
            if props:
                props.discard(property_id)
                props.add(new_property_id)
                self._controller_to_properties.add(controller_id, props)
        
        return new_property_id
    
    def update_property_controller(self, property_id, new_controller_id):
        """
        Update a property's controller reference with validation for non-controlling observables.
        
        Args:
            property_id: The ID of the property to update
            new_controller_id: The new controller's unique ID
            
        Returns:
            str: The updated property ID
        """
        property_obj = self.registry.get_observable_property(property_id)
        if property_obj is None:
            return property_id
        
        # Extract components
        components = parse_property_id(property_id)
        if not components:
            return property_id
        
        old_controller_id = components['controller_id']
        
        # If the controller hasn't changed, no update needed
        if old_controller_id == new_controller_id:
            return property_id
        
        # Only check non-controlling relationship if setting a new controller (not removing one)
        if new_controller_id != DEFAULT_NO_CONTROLLER:
            # Get the observable ID from the property
            observable_unique_id = components['observable_unique_id']
            if observable_unique_id != DEFAULT_NO_OBSERVABLE:
                # Find the full observable ID
                observable_id = self.registry.get_full_id_from_unique_id(observable_unique_id)
                
                # If we found the observable, check if control should be prevented
                if observable_id:
                    # Get the controller widget ID
                    controller_widget_id = self.registry.get_full_id_from_unique_id(new_controller_id)
                    if controller_widget_id and self.registry.should_prevent_control(controller_widget_id, observable_id):
                        # Skip setting this controller
                        return property_id
        
        # Create the updated property ID
        new_property_id = create_property_id(
            components['type_code'],
            components['unique_id'],
            components['observable_unique_id'],
            components['property_name'],
            new_controller_id
        )
        
        # Remove from old controller's property set
        if old_controller_id != DEFAULT_NO_CONTROLLER:
            props = self._controller_to_properties.get(old_controller_id)
            if props:
                props.discard(property_id)
                if not props:
                    # If this was the last property, remove the controller
                    self._controller_to_properties.delete(old_controller_id)
                else:
                    # Update the property set
                    self._controller_to_properties.add(old_controller_id, props)
        
        # Add to new controller's property set
        if new_controller_id != DEFAULT_NO_CONTROLLER:
            props = self._controller_to_properties.get(new_controller_id) or set()
            props.add(new_property_id)
            self._controller_to_properties.add(new_controller_id, props)
        
        # Update observable's property set
        observable_unique_id = components['observable_unique_id']
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            props = self._observable_to_properties.get(observable_unique_id)
            if props:
                props.discard(property_id)
                props.add(new_property_id)
                self._observable_to_properties.add(observable_unique_id, props)
        
        return new_property_id
    
    def update_properties_for_controller(self, old_controller_id, new_controller_id):
        """
        Update all properties referring to a controller when its ID changes.
        
        This method should be called when a widget's ID changes, to update
        all properties it controls.
        
        Args:
            old_controller_id: The controller's old unique ID
            new_controller_id: The controller's new unique ID
            
        Returns:
            list: A list of (old_property_id, new_property_id) tuples
        """
        if old_controller_id == new_controller_id:
            return []
        
        updates = []
        
        # Get all properties controlled by old_controller_id
        props = self._controller_to_properties.get(old_controller_id)
        if props:
            # Make a copy to avoid modification during iteration
            property_ids = list(props)
            
            # Update each property
            for property_id in property_ids:
                new_property_id = self.update_property_controller(property_id, new_controller_id)
                updates.append((property_id, new_property_id))
        
        return updates
    
    def update_observable_id(self, old_observable_id, new_observable_id):
        """
        Update an observable's ID directly.
        
        This method updates the observable's ID and all references to it,
        including property relationships.
        
        Args:
            old_observable_id: The current observable ID
            new_observable_id: The new observable ID to use
            
        Returns:
            tuple: (success, actual_new_id, error_message) where:
                - success: Boolean indicating whether the update was successful
                - actual_new_id: The actual new ID after the update
                - error_message: Description of error if unsuccessful
        """
        # 1. Validate inputs
        observable = self.registry.get_observable(old_observable_id)
        if observable is None:
            return False, old_observable_id, "Observable not found"
        
        old_components = parse_observable_id(old_observable_id)
        new_components = parse_observable_id(new_observable_id)
        
        if not old_components or not new_components:
            return False, old_observable_id, "Invalid observable ID format"
        
        if old_components['type_code'] != new_components['type_code']:
            return False, old_observable_id, "Cannot change observable type code"
        
        # 2. Get key information
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        # If no change in unique ID, nothing to do
        if old_unique_id == new_unique_id:
            return True, old_observable_id, None
        
        # 3. Check for ID collision
        if self.registry.get_full_id_from_unique_id(new_unique_id):
            return False, old_observable_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # 4. Find all properties referencing this observable
        property_ids = self.get_property_ids_by_observable_id(old_unique_id)
        
        # 5. Create new observable ID
        final_observable_id = create_observable_id(old_components['type_code'], new_unique_id)
        
        # 6. Update all property references
        property_updates = []
        for prop_id in property_ids:
            new_prop_id = self.update_property_observable(prop_id, new_unique_id)
            property_updates.append((prop_id, new_prop_id))
        
        # 7. Update mappings
        # Move the properties from old observable to new one
        props = self._observable_to_properties.get(old_unique_id)
        if props:
            self._observable_to_properties.add(new_unique_id, props)
            self._observable_to_properties.delete(old_unique_id)
        
        return True, final_observable_id, None
    
    def update_property_id(self, old_property_id, new_property_id):
        """
        Update a property's ID directly.
        
        This method updates the property's ID and all references to it.
        
        Args:
            old_property_id: The current property ID
            new_property_id: The new property ID to use
            
        Returns:
            tuple: (success, actual_new_id, error_message) where:
                - success: Boolean indicating whether the update was successful
                - actual_new_id: The actual new ID after the update
                - error_message: Description of error if unsuccessful
        """
        property_obj = self.registry.get_observable_property(old_property_id)
        if property_obj is None:
            return False, old_property_id, "Property not found"
        
        # Parse both IDs
        old_components = parse_property_id(old_property_id)
        new_components = parse_property_id(new_property_id)
        
        if not old_components or not new_components:
            return False, old_property_id, "Invalid property ID format"
        
        # Make sure type codes match
        if old_components['type_code'] != new_components['type_code']:
            return False, old_property_id, "Cannot change property type code"
        
        # Check if the unique ID is changing
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        if old_unique_id != new_unique_id:
            # Make sure the new unique ID isn't already used
            if self.registry.get_full_id_from_unique_id(new_unique_id):
                return False, old_property_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # Check if observable reference is changing
        old_observable_id = old_components['observable_unique_id']
        new_observable_id = new_components['observable_unique_id']
        
        if old_observable_id != new_observable_id:
            # Verify the new observable exists if it's not "0"
            if new_observable_id != DEFAULT_NO_OBSERVABLE and not self.registry.get_full_id_from_unique_id(new_observable_id):
                return False, old_property_id, f"Observable with ID '{new_observable_id}' does not exist"
        
        # Check if controller reference is changing
        old_controller_id = old_components['controller_id']
        new_controller_id = new_components['controller_id']
        
        # Property name
        old_property_name = old_components['property_name']
        new_property_name = new_components['property_name']
        
        # Create the final property ID
        final_property_id = create_property_id(
            old_components['type_code'],  # Type code remains the same
            new_unique_id,
            new_observable_id,
            new_property_name,
            new_controller_id
        )
        
        # If this is the same as the original ID, nothing to do
        if final_property_id == old_property_id:
            return True, old_property_id, None
        
        # Update observable mappings
        if old_observable_id != new_observable_id:
            # Remove from old observable's property set
            if old_observable_id != DEFAULT_NO_OBSERVABLE:
                props = self._observable_to_properties.get(old_observable_id)
                if props:
                    props.discard(old_property_id)
                    if not props:
                        # If this was the last property, remove the observable
                        self._observable_to_properties.delete(old_observable_id)
                    else:
                        # Update the property set
                        self._observable_to_properties.add(old_observable_id, props)
            
            # Add to new observable's property set
            if new_observable_id != DEFAULT_NO_OBSERVABLE:
                props = self._observable_to_properties.get(new_observable_id) or set()
                props.add(final_property_id)
                self._observable_to_properties.add(new_observable_id, props)
        else:
            # Just update the property ID in the same observable
            if old_observable_id != DEFAULT_NO_OBSERVABLE:
                props = self._observable_to_properties.get(old_observable_id)
                if props:
                    props.discard(old_property_id)
                    props.add(final_property_id)
                    self._observable_to_properties.add(old_observable_id, props)
        
        # Update controller mappings
        if old_controller_id != new_controller_id:
            # Remove from old controller's property set
            if old_controller_id != DEFAULT_NO_CONTROLLER:
                props = self._controller_to_properties.get(old_controller_id)
                if props:
                    props.discard(old_property_id)
                    if not props:
                        # If this was the last property, remove the controller
                        self._controller_to_properties.delete(old_controller_id)
                    else:
                        # Update the property set
                        self._controller_to_properties.add(old_controller_id, props)
            
            # Add to new controller's property set
            if new_controller_id != DEFAULT_NO_CONTROLLER:
                props = self._controller_to_properties.get(new_controller_id) or set()
                props.add(final_property_id)
                self._controller_to_properties.add(new_controller_id, props)
        else:
            # Just update the property ID in the same controller
            if old_controller_id != DEFAULT_NO_CONTROLLER:
                props = self._controller_to_properties.get(old_controller_id)
                if props:
                    props.discard(old_property_id)
                    props.add(final_property_id)
                    self._controller_to_properties.add(old_controller_id, props)
        
        return True, final_property_id, None
    
    #MARK: - Query methods
    
    def get_observable_id_from_property_id(self, property_id):
        """
        Get the observable ID associated with a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The observable ID, or None if not found or invalid property ID
        """
        # Parse the property ID
        components = parse_property_id(property_id)
        if not components:
            return None
            
        # Get the observable unique ID from the components
        observable_unique_id = components['observable_unique_id']
        
        # If it's a default/null value, return None
        if observable_unique_id == DEFAULT_NO_OBSERVABLE:
            return None
            
        # Look up the full observable ID by unique ID
        return self.registry.get_full_id_from_unique_id(observable_unique_id)
    
    def get_property_ids_by_observable_id(self, observable_unique_id):
        """
        Get all property IDs for a specific observable.
        
        Args:
            observable_unique_id: The observable's unique ID
            
        Returns:
            list: A list of property IDs for the observable
        """
        props = self._observable_to_properties.get(observable_unique_id)
        if not props:
            return []
        
        return list(props)
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_unique_id, property_name):
        """
        Get all property IDs for a specific observable and property name.
        
        Args:
            observable_unique_id: The observable's unique ID
            property_name: The property name
            
        Returns:
            list: A list of property IDs matching the criteria
        """
        props = self._observable_to_properties.get(observable_unique_id)
        if not props:
            return []
        
        matching_props = []
        for property_id in props:
            components = parse_property_id(property_id)
            if components and components['property_name'] == property_name:
                matching_props.append(property_id)
        
        return matching_props
    
    def get_property_ids_by_controller_id(self, controller_unique_id):
        """
        Get all property IDs for a specific controller.
        
        Args:
            controller_unique_id: The controller's unique ID
            
        Returns:
            list: A list of property IDs controlled by the controller
        """
        props = self._controller_to_properties.get(controller_unique_id)
        if not props:
            return []
        
        return list(props)
    
    def get_controller_id_from_property_id(self, property_id):
        """
        Get the controller unique ID associated with a property ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            str: The controller unique ID, or None if not found or invalid property ID
        """
        # Parse the property ID
        components = parse_property_id(property_id)
        if not components:
            return None
            
        # Get the controller ID from the components
        controller_id = components['controller_id']
        
        # If it's a default/null value, return None
        if controller_id == DEFAULT_NO_CONTROLLER:
            return None
            
        return controller_id
    
    #MARK: - Helper methods
    
    def clear(self):
        """Clear all observable and property registrations."""
        for mapping in [self._observable_to_properties, self._controller_to_properties]:
            mapping._storage.clear()
            mapping._key_log.clear()
            mapping._value_log.clear()