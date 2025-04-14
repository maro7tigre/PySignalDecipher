"""
Observable Manager module.

This module contains the ObservableManager class for managing observables, properties,
and their relationships in the ID system.
"""

import weakref
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
        
        # Maps observable IDs to observable objects
        self._observables = {}
        
        # Maps observable unique IDs to full observable IDs
        self._unique_id_to_observable_id = {}
        
        # Maps observable objects to their observable IDs
        self._observable_objects_to_id = weakref.WeakKeyDictionary()
        
        # Maps property IDs to property objects
        self._properties = {}
        
        # Maps property unique IDs to full property IDs
        self._unique_id_to_property_id = {}
        
        # Maps property objects to their property IDs
        self._property_objects_to_id = weakref.WeakKeyDictionary()
        
        # Maps observable unique IDs to sets of property IDs associated with them
        self._observable_to_properties = {}
        
        # Maps controller unique IDs to sets of property IDs controlled by them
        self._controller_to_properties = {}
        
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
        
        # Save the ID mappings
        self._observables[observable_id] = observable
        self._unique_id_to_observable_id[unique_id] = observable_id
        
        # Only add to weak dictionary if observable is not None
        if observable is not None:
            self._observable_objects_to_id[observable] = observable_id
        
        # Initialize property set for this observable
        self._observable_to_properties[unique_id] = set()
        
        return observable_id
    
    def unregister_observable(self, observable_id):
        """
        Unregister an observable from the manager.
        
        Args:
            observable_id: The ID of the observable to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        if observable_id not in self._observables:
            return False
        
        # Extract components
        components = parse_observable_id(observable_id)
        if not components:
            return False
        
        unique_id = components['unique_id']
        
        # Get the observable object
        observable = self._observables[observable_id]
        
        # Call the unregister callback if set
        self.registry._on_observable_unregister(observable_id, observable)
        
        # Handle associated properties
        if unique_id in self._observable_to_properties:
            # Make a copy to avoid modification during iteration
            property_ids = list(self._observable_to_properties[unique_id])
            for property_id in property_ids:
                # Unregister all associated properties
                self.unregister_property(property_id)
            
            # Clean up
            if unique_id in self._observable_to_properties:  # Check if key exists before deleting
                del self._observable_to_properties[unique_id]
        
        # Remove from all mappings
        if observable is not None and observable in self._observable_objects_to_id:
            del self._observable_objects_to_id[observable]
        if unique_id in self._unique_id_to_observable_id:
            del self._unique_id_to_observable_id[unique_id]
        if observable_id in self._observables:
            del self._observables[observable_id]
        
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
        # Fix issue 1: Ensure controller_id is set to DEFAULT_NO_CONTROLLER when none provided
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
        
        # Save the ID mappings
        self._properties[property_id] = property_obj
        self._unique_id_to_property_id[unique_id] = property_id
        
        # Only add to _property_objects_to_id if property_obj is not None
        # This allows descriptor properties (which don't have concrete objects)
        # to be registered without causing weak reference errors
        if property_obj is not None:
            self._property_objects_to_id[property_obj] = property_id
        
        # Add to observable's property set if applicable
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            if observable_unique_id not in self._observable_to_properties:
                self._observable_to_properties[observable_unique_id] = set()
            self._observable_to_properties[observable_unique_id].add(property_id)
        
        # Add to controller's property set if applicable
        if controller_unique_id != DEFAULT_NO_CONTROLLER:
            if controller_unique_id not in self._controller_to_properties:
                self._controller_to_properties[controller_unique_id] = set()
            self._controller_to_properties[controller_unique_id].add(property_id)
        
        return property_id
    
    def unregister_property(self, property_id):
        """
        Unregister a property from the manager.
        
        Args:
            property_id: The ID of the property to unregister
                
        Returns:
            bool: True if successful, False otherwise
        """
        if property_id not in self._properties:
            return False
        
        # Extract components
        components = parse_property_id(property_id)
        if not components:
            return False
        
        unique_id = components['unique_id']
        observable_unique_id = components['observable_unique_id']
        controller_id = components['controller_id']
        
        # Get the property object
        property_obj = self._properties[property_id]
        
        # Call the unregister callback if set
        self.registry._on_property_unregister(property_id, property_obj)
        
        # Remove from observable's property set if applicable
        if observable_unique_id != DEFAULT_NO_OBSERVABLE:
            if observable_unique_id in self._observable_to_properties:
                self._observable_to_properties[observable_unique_id].discard(property_id)
                
                # Check if this was the last property for this observable
                if not self._observable_to_properties[observable_unique_id]:
                    # Clean up empty set
                    del self._observable_to_properties[observable_unique_id]
                    
                    # Find the observable_id from the unique_id
                    for obs_id in list(self._observables.keys()):
                        if get_unique_id_from_id(obs_id) == observable_unique_id:
                            # Unregister the observable
                            self.unregister_observable(obs_id)
                            break
        
        # Remove from controller's property set if applicable
        if controller_id != DEFAULT_NO_CONTROLLER:
            if controller_id in self._controller_to_properties:
                self._controller_to_properties[controller_id].discard(property_id)
                
                # Clean up empty sets
                if controller_id in self._controller_to_properties and not self._controller_to_properties[controller_id]:
                    del self._controller_to_properties[controller_id]
        
        # Remove from all mappings
        if property_obj is not None and property_obj in self._property_objects_to_id:
            del self._property_objects_to_id[property_obj]
        if unique_id in self._unique_id_to_property_id:
            del self._unique_id_to_property_id[unique_id]
        if property_id in self._properties:
            del self._properties[property_id]
        
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
        if property_id not in self._properties:
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
        
        # Update the mappings
        property_obj = self._properties[property_id]
        self._properties[new_property_id] = property_obj
        self._unique_id_to_property_id[components['unique_id']] = new_property_id
        
        # Update _property_objects_to_id only if property_obj is not None
        if property_obj is not None:
            self._property_objects_to_id[property_obj] = new_property_id
        
        # Update observable's property sets
        if old_observable_unique_id != DEFAULT_NO_OBSERVABLE and old_observable_unique_id in self._observable_to_properties:
            self._observable_to_properties[old_observable_unique_id].discard(property_id)
            
            # Clean up empty sets
            if not self._observable_to_properties[old_observable_unique_id]:
                del self._observable_to_properties[old_observable_unique_id]
        
        if new_observable_unique_id != DEFAULT_NO_OBSERVABLE:
            if new_observable_unique_id not in self._observable_to_properties:
                self._observable_to_properties[new_observable_unique_id] = set()
            self._observable_to_properties[new_observable_unique_id].add(new_property_id)
        
        # Clean up old property ID
        if property_id in self._properties:
            del self._properties[property_id]
        
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
        if property_id not in self._properties:
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
        
        # Update the mappings
        property_obj = self._properties[property_id]
        self._properties[new_property_id] = property_obj
        self._unique_id_to_property_id[components['unique_id']] = new_property_id
        
        # Update _property_objects_to_id only if property_obj is not None
        if property_obj is not None:
            self._property_objects_to_id[property_obj] = new_property_id
        
        # Update observable's property set
        observable_unique_id = components['observable_unique_id']
        if observable_unique_id != DEFAULT_NO_OBSERVABLE and observable_unique_id in self._observable_to_properties:
            self._observable_to_properties[observable_unique_id].discard(property_id)
            self._observable_to_properties[observable_unique_id].add(new_property_id)
        
        # Update controller's property set
        controller_id = components['controller_id']
        if controller_id != DEFAULT_NO_CONTROLLER and controller_id in self._controller_to_properties:
            self._controller_to_properties[controller_id].discard(property_id)
            self._controller_to_properties[controller_id].add(new_property_id)
        
        # Clean up old property ID
        if property_id in self._properties:
            del self._properties[property_id]
        
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
        if property_id not in self._properties:
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
                observable_id = None
                for obs_id in self._observables:
                    if get_unique_id_from_id(obs_id) == observable_unique_id:
                        observable_id = obs_id
                        break
                
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
        
        # Update the mappings
        property_obj = self._properties[property_id]
        self._properties[new_property_id] = property_obj
        self._unique_id_to_property_id[components['unique_id']] = new_property_id
        
        # Update _property_objects_to_id only if property_obj is not None
        if property_obj is not None:
            self._property_objects_to_id[property_obj] = new_property_id
        
        # Update observable's property set
        observable_unique_id = components['observable_unique_id']
        if observable_unique_id != DEFAULT_NO_OBSERVABLE and observable_unique_id in self._observable_to_properties:
            self._observable_to_properties[observable_unique_id].discard(property_id)
            self._observable_to_properties[observable_unique_id].add(new_property_id)
        
        # Update controller's property sets
        if old_controller_id != DEFAULT_NO_CONTROLLER and old_controller_id in self._controller_to_properties:
            self._controller_to_properties[old_controller_id].discard(property_id)
            
            # Clean up empty sets
            if old_controller_id in self._controller_to_properties and not self._controller_to_properties[old_controller_id]:
                del self._controller_to_properties[old_controller_id]
        
        if new_controller_id != DEFAULT_NO_CONTROLLER:
            if new_controller_id not in self._controller_to_properties:
                self._controller_to_properties[new_controller_id] = set()
            self._controller_to_properties[new_controller_id].add(new_property_id)
        
        # Clean up old property ID
        if property_id in self._properties:
            del self._properties[property_id]
        
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
        if old_controller_id in self._controller_to_properties:
            # Make a copy to avoid modification during iteration
            property_ids = list(self._controller_to_properties[old_controller_id])
            
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
        if old_observable_id not in self._observables:
            return False, old_observable_id, "Observable not found"
        
        old_components = parse_observable_id(old_observable_id)
        new_components = parse_observable_id(new_observable_id)
        
        if not old_components or not new_components:
            return False, old_observable_id, "Invalid observable ID format"
        
        if old_components['type_code'] != new_components['type_code']:
            return False, old_observable_id, "Cannot change observable type code"
        
        # 2. Get key information
        observable = self._observables[old_observable_id]
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        # If no change in unique ID, nothing to do
        if old_unique_id == new_unique_id:
            return True, old_observable_id, None
        
        # Check for ID collision
        if new_unique_id in self._unique_id_to_observable_id and self._unique_id_to_observable_id[new_unique_id] != old_observable_id:
            return False, old_observable_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # 3. Directly find all properties referencing this observable
        properties_to_update = []
        for prop_id in list(self._properties.keys()):
            components = parse_property_id(prop_id)
            if components and components['observable_unique_id'] == old_unique_id:
                properties_to_update.append(prop_id)
        
        # 4. Create new observable ID
        final_observable_id = create_observable_id(old_components['type_code'], new_unique_id)
        
        # 5. Update all property references in one go
        property_updates = []
        for prop_id in properties_to_update:
            # This is a direct call to update the property's observable reference
            new_prop_id = self.update_property_observable(prop_id, new_unique_id)
            property_updates.append((prop_id, new_prop_id))
        
        # 6. Update observable mappings
        self._observables[final_observable_id] = observable
        self._unique_id_to_observable_id[new_unique_id] = final_observable_id
        if observable is not None:
            self._observable_objects_to_id[observable] = final_observable_id
        
        # 7. Clean up old mappings
        del self._observables[old_observable_id]
        del self._unique_id_to_observable_id[old_unique_id]
        
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
        if old_property_id not in self._properties:
            return False, old_property_id, "Property not found"
        
        # Parse both IDs
        old_components = parse_property_id(old_property_id)
        new_components = parse_property_id(new_property_id)
        
        if not old_components or not new_components:
            return False, old_property_id, "Invalid property ID format"
        
        # Make sure type codes match
        if old_components['type_code'] != new_components['type_code']:
            return False, old_property_id, "Cannot change property type code"
        
        # Get the property object
        property_obj = self._properties[old_property_id]
        
        # Check if the unique ID is changing
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        if old_unique_id != new_unique_id:
            # Make sure the new unique ID isn't already used
            if new_unique_id in self._unique_id_to_property_id and self._unique_id_to_property_id[new_unique_id] != old_property_id:
                return False, old_property_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # Check if observable reference is changing
        old_observable_id = old_components['observable_unique_id']
        new_observable_id = new_components['observable_unique_id']
        
        if old_observable_id != new_observable_id:
            # Verify the new observable exists if it's not "0"
            if new_observable_id != DEFAULT_NO_OBSERVABLE and not any(get_unique_id_from_id(obs_id) == new_observable_id for obs_id in self._observables):
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
        
        # Update mappings
        self._properties[final_property_id] = property_obj
        self._unique_id_to_property_id[new_unique_id] = final_property_id
        
        # Update _property_objects_to_id only if property_obj is not None
        if property_obj is not None:
            self._property_objects_to_id[property_obj] = final_property_id
        
        # Update observable references
        if old_observable_id != DEFAULT_NO_OBSERVABLE and old_observable_id in self._observable_to_properties:
            self._observable_to_properties[old_observable_id].discard(old_property_id)
            
            # Clean up empty sets
            if not self._observable_to_properties[old_observable_id]:
                del self._observable_to_properties[old_observable_id]
        
        if new_observable_id != DEFAULT_NO_OBSERVABLE:
            if new_observable_id not in self._observable_to_properties:
                self._observable_to_properties[new_observable_id] = set()
            self._observable_to_properties[new_observable_id].add(final_property_id)
        
        # Update controller references
        if old_controller_id != DEFAULT_NO_CONTROLLER and old_controller_id in self._controller_to_properties:
            self._controller_to_properties[old_controller_id].discard(old_property_id)
            
            # Clean up empty sets
            if not self._controller_to_properties[old_controller_id]:
                del self._controller_to_properties[old_controller_id]
        
        if new_controller_id != DEFAULT_NO_CONTROLLER:
            if new_controller_id not in self._controller_to_properties:
                self._controller_to_properties[new_controller_id] = set()
            self._controller_to_properties[new_controller_id].add(final_property_id)
        
        # Clean up old property ID
        if old_property_id in self._properties:
            del self._properties[old_property_id]
        
        # Remove old unique ID from mappings if changed
        if old_unique_id != new_unique_id and old_unique_id in self._unique_id_to_property_id:
            del self._unique_id_to_property_id[old_unique_id]
        
        return True, final_property_id, None
    
    #MARK: - Query methods
    
    def get_observable(self, observable_id):
        """
        Get an observable by its ID.
        
        Args:
            observable_id: The observable ID
            
        Returns:
            object: The observable object, or None if not found
        """
        return self._observables.get(observable_id)
    
    def get_observable_id(self, observable):
        """
        Get an observable's ID.
        
        Args:
            observable: The observable object
            
        Returns:
            str: The observable ID, or None if not found
        """
        return self._observable_objects_to_id.get(observable)
    
    def get_property(self, property_id):
        """
        Get a property by its ID.
        
        Args:
            property_id: The property ID
            
        Returns:
            object: The property object, or None if not found
        """
        return self._properties.get(property_id)
    
    def get_property_id(self, property_obj):
        """
        Get a property's ID.
        
        Args:
            property_obj: The property object
            
        Returns:
            str: The property ID, or None if not found
        """
        # Only look up in _property_objects_to_id if property_obj is not None
        if property_obj is not None:
            return self._property_objects_to_id.get(property_obj)
        return None
    
    def get_property_ids_by_observable_id(self, observable_unique_id):
        """
        Get all property IDs for a specific observable.
        
        Args:
            observable_unique_id: The observable's unique ID
            
        Returns:
            list: A list of property IDs for the observable
        """
        if observable_unique_id not in self._observable_to_properties:
            return []
        
        return list(self._observable_to_properties[observable_unique_id])
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_unique_id, property_name):
        """
        Get all property IDs for a specific observable and property name.
        
        Args:
            observable_unique_id: The observable's unique ID
            property_name: The property name
            
        Returns:
            list: A list of property IDs matching the criteria
        """
        if observable_unique_id not in self._observable_to_properties:
            return []
        
        properties = []
        for property_id in self._observable_to_properties[observable_unique_id]:
            components = parse_property_id(property_id)
            if components and components['property_name'] == property_name:
                properties.append(property_id)
        
        return properties
    
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
        for observable_id, observable in self._observables.items():
            if get_unique_id_from_id(observable_id) == observable_unique_id:
                return observable_id
                
        # If not found, create an observable ID from the unique ID
        return None
    
    def get_property_ids_by_controller_id(self, controller_unique_id):
        """
        Get all property IDs for a specific controller.
        
        Args:
            controller_unique_id: The controller's unique ID
            
        Returns:
            list: A list of property IDs controlled by the controller
        """
        if controller_unique_id not in self._controller_to_properties:
            return []
        
        return list(self._controller_to_properties[controller_unique_id])
    
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
    
    def set_on_observable_unregister(self, callback):
        """
        Set the callback for observable unregistration.
        
        Args:
            callback: The callback function that takes observable_id and observable as arguments
        """
        self._on_observable_unregister = callback
    
    def set_on_property_unregister(self, callback):
        """
        Set the callback for property unregistration.
        
        Args:
            callback: The callback function that takes property_id and property as arguments
        """
        self._on_property_unregister = callback
    
    def clear(self):
        """Clear all observable and property registrations."""
        self._observables.clear()
        self._unique_id_to_observable_id.clear()
        self._observable_objects_to_id.clear()
        self._properties.clear()
        self._unique_id_to_property_id.clear()
        self._property_objects_to_id.clear()
        self._observable_to_properties.clear()
        self._controller_to_properties.clear()