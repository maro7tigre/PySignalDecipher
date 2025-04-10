"""
Widget Manager module.

This module contains the WidgetManager class for managing widgets and their
relationships with containers in the ID system.
"""

import weakref
from command_system.id_system.core.generator import LocationIDGenerator
from command_system.id_system.core.parser import (
    parse_widget_id,
    create_widget_id,
    get_unique_id_from_id,
    parse_location,
)
from command_system.id_system.types import (
    DEFAULT_ROOT_CONTAINER_ID,
    DEFAULT_ROOT_LOCATION,
    ContainerTypeCodes,
    ID_SEPARATOR,
    PATH_SEPARATOR,
    LOCATION_SEPARATOR,
)

class IDRegistrationError(Exception):
    """Exception raised for ID registration errors."""
    pass

#MARK: - WidgetManager class

class WidgetManager:
    """
    Manages widget-container relationships and locations in the ID system.
    
    This class handles the registration, unregistration, and updates of
    widgets and their relationships with containers.
    """
    
    def __init__(self, registry):
        """
        Initialize the widget manager.
        
        Args:
            registry: The parent IDRegistry
        """
        self.registry = registry
        
        # Maps widget IDs to widget objects
        self._widgets = {}
        
        # Maps widget unique IDs to full widget IDs
        self._unique_id_to_widget_id = {}
        
        # Maps widgets to their widget IDs
        self._widget_objects_to_id = weakref.WeakKeyDictionary()
        
        # Maps container unique IDs to sets of widget IDs contained by them
        self._container_to_widgets = {}
        
        # Maps container locations to location generators
        # Using container_location as the key simplifies the structure
        # and makes cleanup easier
        self._container_location_generators = {}
        
        # Maps container unique IDs to location maps (subcontainer location to widget ID)
        self._container_locations_map = {}
    
    #MARK: - Registration methods
    
    def register_widget(self, widget, type_code, unique_id, container_id=DEFAULT_ROOT_CONTAINER_ID, 
                      location=None):
        """
        Register a widget with the manager.
        
        Args:
            widget: The widget object to register
            type_code: The widget type code
            unique_id: The unique ID for the widget
            container_id: The container's ID or unique ID (default: "0")
            location: The widget_location_id (default: None, will be generated)
            
        Returns:
            str: The generated widget ID
            
        Raises:
            IDRegistrationError: If the widget_location_id already exists in the container location
        """
        # Extract container's unique ID if full ID provided
        container_unique_id = container_id
        if container_id and ID_SEPARATOR in container_id:
            container_unique_id = get_unique_id_from_id(container_id)
            
        # Determine container location and widget location ID based on container
        container_location = self._get_container_location(container_unique_id)
        
        # Get the location generator for this container path
        location_gen = self._get_location_generator(container_location)
        
        # Determine widget_location_id
        widget_location_id = location
        if widget_location_id is None:
            # Generate a new widget_location_id
            widget_location_id = location_gen.generate()
        else:
            # Check if the widget_location_id is available
            if location_gen.is_registered(widget_location_id):
                print(f"Widget location ID '{widget_location_id}' already exists in container location '{container_location}'")
                widget_location_id = location_gen.generate()
            
            # Register the widget location ID
            location_gen.register(widget_location_id)
        
        # Create the widget ID
        widget_id = create_widget_id(
            type_code,
            unique_id,
            container_unique_id,
            container_location,
            widget_location_id
        )
        
        # Save the ID mappings
        self._widgets[widget_id] = widget
        self._unique_id_to_widget_id[unique_id] = widget_id
        self._widget_objects_to_id[widget] = widget_id
        
        # Add to the container's widget set
        if container_unique_id not in self._container_to_widgets:
            self._container_to_widgets[container_unique_id] = set()
        self._container_to_widgets[container_unique_id].add(widget_id)
        
        # Update the container's locations map
        self._update_container_locations_map(container_unique_id)
        
        # If this widget is a container, initialize its widgets set and location generator
        if ContainerTypeCodes.is_valid_code(type_code):
            self._container_to_widgets[unique_id] = set()
            self._container_locations_map[unique_id] = {}
        
        return widget_id
    
    def unregister_widget(self, widget_id):
        """
        Unregister a widget from the manager.
        
        Args:
            widget_id: The ID of the widget to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        if widget_id not in self._widgets:
            return False
        
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return False
        
        unique_id = components['unique_id']
        container_unique_id = components['container_unique_id']
        container_location = components['container_location']
        widget_location_id = components['widget_location_id']
        
        # Get the widget object
        widget = self._widgets[widget_id]
        
        # Call the registry's widget unregister callback
        self.registry._on_widget_unregister(widget_id, widget)
        
        # If it's a container, handle its children first
        if unique_id in self._container_to_widgets:
            # Make a copy to avoid modification during iteration
            child_widgets = list(self._container_to_widgets[unique_id])
            for child_id in child_widgets:
                # Unregister all child widgets
                self.unregister_widget(child_id)
            
            # Clean up container data
            if unique_id in self._container_to_widgets:
                del self._container_to_widgets[unique_id]
            if unique_id in self._container_locations_map:
                del self._container_locations_map[unique_id]
                
            # Clean up any location generators for this container's locations
            full_container_path = f"{container_location}/{widget_location_id}"
            self._cleanup_container_location_generators(full_container_path)
        
        # Remove from container's widgets set
        if container_unique_id in self._container_to_widgets:
            self._container_to_widgets[container_unique_id].discard(widget_id)
            # Update the container's locations map after removing widget
            self._update_container_locations_map(container_unique_id)
        
        # Unregister from location generator
        if container_location in self._container_location_generators:
            location_gen = self._container_location_generators[container_location]
            location_gen.unregister(widget_location_id)
        
        # If this widget is in any container's locations map, remove it
        self._remove_from_locations_maps(widget_id)
        
        # Remove from all mappings
        if widget in self._widget_objects_to_id:
            del self._widget_objects_to_id[widget]
        if unique_id in self._unique_id_to_widget_id:
            del self._unique_id_to_widget_id[unique_id]
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
        return True
    
    #MARK: - Update methods
    
    def update_widget_container(self, widget_id, new_container_id):
        """
        Update a widget's container reference.
        
        Args:
            widget_id: The ID of the widget to update
            new_container_id: The new container's unique ID
            
        Returns:
            str: The updated widget ID
            
        Raises:
            IDRegistrationError: If the widget_location_id already exists in the new container location
        """
        if widget_id not in self._widgets:
            return widget_id
        
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return widget_id
        
        old_container_id = components['container_unique_id']
        old_container_location = components['container_location']
        widget_location_id = components['widget_location_id']
        unique_id = components['unique_id']
        type_code = components['type_code']
        
        # If the container hasn't changed, no update needed
        if old_container_id == new_container_id:
            return widget_id
        
        # Check if this is a container with children
        is_container = ContainerTypeCodes.is_valid_code(type_code)
        
        # Unregister from old location generator
        if old_container_location in self._container_location_generators:
            old_location_gen = self._container_location_generators[old_container_location]
            old_location_gen.unregister(widget_location_id)
        
        # Remove from old container's widget set
        if old_container_id in self._container_to_widgets:
            self._container_to_widgets[old_container_id].discard(widget_id)
            # Update old container's locations map
            self._update_container_locations_map(old_container_id)
        
        # Determine the new container location based on container
        new_container_location = self._get_container_location(new_container_id)
        
        # Get the location generator for the new container path
        new_location_gen = self._get_location_generator(new_container_location)
        
        # Check if the widget_location_id is available in the new container
        if new_location_gen.is_registered(widget_location_id):
            # Generate a new widget_location_id
            final_widget_location_id = new_location_gen.generate()
        else:
            final_widget_location_id = widget_location_id
            # Register the widget location ID
            new_location_gen.register(final_widget_location_id)
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            new_container_id,
            new_container_location,
            final_widget_location_id
        )
        
        # Update the mappings
        widget = self._widgets[widget_id]
        self._widgets[new_widget_id] = widget
        self._unique_id_to_widget_id[unique_id] = new_widget_id
        self._widget_objects_to_id[widget] = new_widget_id
        
        # Add to new container's widget set
        if new_container_id not in self._container_to_widgets:
            self._container_to_widgets[new_container_id] = set()
        self._container_to_widgets[new_container_id].add(new_widget_id)
        
        # Update new container's locations map
        self._update_container_locations_map(new_container_id)
        
        # Clean up old widget ID
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
        # If it's a container, update all its children's container locations
        if is_container and unique_id in self._container_to_widgets:
            old_full_path = f"{old_container_location}/{widget_location_id}"
            new_full_path = f"{new_container_location}/{final_widget_location_id}"
            self._update_children_container_locations(unique_id, old_full_path, new_full_path)
            
        # Update any locations map entries that reference this widget
        self._update_locations_map_references(widget_id, new_widget_id)
        
        return new_widget_id
    
    def update_widget_location(self, widget_id, new_location):
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
        if widget_id not in self._widgets:
            return widget_id
        
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return widget_id
        
        type_code = components['type_code']
        unique_id = components['unique_id']
        container_unique_id = components['container_unique_id']
        container_location = components['container_location']
        old_widget_location_id = components['widget_location_id']
        
        # If the widget_location_id hasn't changed, return original ID
        if new_location == old_widget_location_id:
            return widget_id
        
        # Check if this is a container with children
        is_container = ContainerTypeCodes.is_valid_code(type_code)
        
        # Get the location generator
        location_gen = self._get_location_generator(container_location)
        
        # Unregister from old location
        location_gen.unregister(old_widget_location_id)
        
        # Check if the new widget_location_id is available
        if location_gen.is_registered(new_location):
            raise IDRegistrationError(f"Widget location ID '{new_location}' already exists in container location '{container_location}'")
        
        # Register the new widget_location_id
        location_gen.register(new_location)
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            container_unique_id,
            container_location,
            new_location
        )
        
        # Update the mappings
        widget = self._widgets[widget_id]
        self._widgets[new_widget_id] = widget
        self._unique_id_to_widget_id[unique_id] = new_widget_id
        self._widget_objects_to_id[widget] = new_widget_id
        
        # Update container's widget set
        if container_unique_id in self._container_to_widgets:
            self._container_to_widgets[container_unique_id].discard(widget_id)
            self._container_to_widgets[container_unique_id].add(new_widget_id)
            # Update container's locations map
            self._update_container_locations_map(container_unique_id)
        
        # If it's a container, update all its children's container locations
        if is_container and unique_id in self._container_to_widgets:
            old_full_path = f"{container_location}/{old_widget_location_id}"
            new_full_path = f"{container_location}/{new_location}"
            self._update_children_container_locations(unique_id, old_full_path, new_full_path)
        
        # Update any locations map entries that reference this widget
        self._update_locations_map_references(widget_id, new_widget_id)
        
        # Clean up old widget ID
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
        return new_widget_id

    def update_widget_id(self, old_widget_id, new_widget_id):
        """
        Update a widget's ID with a completely new ID.
        
        This is a more direct approach than calling update_container or update_location
        and allows changing multiple aspects of the ID at once.
        
        Args:
            old_widget_id: The current widget ID
            new_widget_id: The new widget ID
            
        Returns:
            tuple: (success, actual_new_id, error_message) where:
                - success: Boolean indicating whether the update was successful
                - actual_new_id: The actual new ID after the update (may be different from requested)
                - error_message: Description of any error that occurred (None if successful)
        """
        if old_widget_id not in self._widgets:
            return False, old_widget_id, "Widget not found"
        
        # Parse both IDs
        old_components = parse_widget_id(old_widget_id)
        new_components = parse_widget_id(new_widget_id)
        
        if not old_components or not new_components:
            return False, old_widget_id, "Invalid widget ID format"
        
        # Make sure type codes match
        if old_components['type_code'] != new_components['type_code']:
            return False, old_widget_id, "Cannot change widget type code"
        
        # Get the widget object
        widget = self._widgets[old_widget_id]
        
        # Check if the unique ID is changing
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        if old_unique_id != new_unique_id:
            # Make sure the new unique ID isn't already used
            if new_unique_id in self._unique_id_to_widget_id and self._unique_id_to_widget_id[new_unique_id] != old_widget_id:
                return False, old_widget_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # Check if container is changing
        old_container_id = old_components['container_unique_id']
        new_container_id = new_components['container_unique_id']
        
        # Handle container change if necessary
        if old_container_id != new_container_id:
            # Verify the new container exists
            if new_container_id != DEFAULT_ROOT_CONTAINER_ID and new_container_id not in self._container_to_widgets:
                return False, old_widget_id, f"Container with ID '{new_container_id}' does not exist"
            
            # If we're changing container and there's already a widget with same unique ID, fail
            if old_unique_id != new_unique_id and new_unique_id in self._unique_id_to_widget_id:
                return False, old_widget_id, f"Cannot update unique ID to '{new_unique_id}': already in use"
                
            # Update container references
            if old_container_id in self._container_to_widgets:
                self._container_to_widgets[old_container_id].discard(old_widget_id)
                # Update old container's locations map
                self._update_container_locations_map(old_container_id)
            
            if new_container_id not in self._container_to_widgets:
                self._container_to_widgets[new_container_id] = set()
        
        # Handle location changes
        old_container_location = old_components['container_location']
        new_container_location = new_components['container_location']
        old_widget_location_id = old_components['widget_location_id']
        new_widget_location_id = new_components['widget_location_id']
        
        # If container location changing, unregister from old location generator
        if old_container_location != new_container_location:
            if old_container_location in self._container_location_generators:
                old_location_gen = self._container_location_generators[old_container_location]
                old_location_gen.unregister(old_widget_location_id)
            
            # Get or create the new location generator
            new_location_gen = self._get_location_generator(new_container_location)
            
            # Check if the widget_location_id is available in the new container
            if new_location_gen.is_registered(new_widget_location_id):
                # Generate a new widget_location_id
                final_widget_location_id = new_location_gen.generate()
            else:
                final_widget_location_id = new_widget_location_id
                # Register the widget location ID
                new_location_gen.register(final_widget_location_id)
        else:
            # Same container location, just updating widget_location_id
            if old_widget_location_id != new_widget_location_id:
                location_gen = self._get_location_generator(old_container_location)
                
                # Unregister old location ID
                location_gen.unregister(old_widget_location_id)
                
                # Check if new location ID is available
                if location_gen.is_registered(new_widget_location_id):
                    return False, old_widget_id, f"Widget location ID '{new_widget_location_id}' already exists in container location '{old_container_location}'"
                
                # Register new location ID
                location_gen.register(new_widget_location_id)
                final_widget_location_id = new_widget_location_id
            else:
                final_widget_location_id = old_widget_location_id
        
        # Create the final widget ID
        final_widget_id = create_widget_id(
            old_components['type_code'],  # Type code remains the same
            new_unique_id,
            new_container_id,
            new_container_location,
            final_widget_location_id
        )
        
        # If this is the same as the original ID, nothing to do
        if final_widget_id == old_widget_id:
            return True, old_widget_id, None
        
        # Update mappings
        self._widgets[final_widget_id] = widget
        self._unique_id_to_widget_id[new_unique_id] = final_widget_id
        self._widget_objects_to_id[widget] = final_widget_id
        
        # Update container's widget set
        if new_container_id in self._container_to_widgets:
            self._container_to_widgets[new_container_id].add(final_widget_id)
            # Update new container's locations map
            self._update_container_locations_map(new_container_id)
        
        # If this is a container, update all its children's container locations
        is_container = ContainerTypeCodes.is_valid_code(old_components['type_code'])
        if is_container and old_unique_id in self._container_to_widgets:
            # Update internal container mappings if unique ID changed
            if old_unique_id != new_unique_id:
                # Transfer container's widget set
                self._container_to_widgets[new_unique_id] = self._container_to_widgets[old_unique_id]
                del self._container_to_widgets[old_unique_id]
                
                # Transfer container's locations map
                if old_unique_id in self._container_locations_map:
                    self._container_locations_map[new_unique_id] = self._container_locations_map[old_unique_id]
                    del self._container_locations_map[old_unique_id]
            
            # Update child container locations if path changed
            if old_container_location != new_container_location or old_widget_location_id != final_widget_location_id:
                old_full_path = f"{old_container_location}/{old_widget_location_id}"
                new_full_path = f"{new_container_location}/{final_widget_location_id}"
                self._update_children_container_locations(new_unique_id, old_full_path, new_full_path)
        
        # Update any locations map entries that reference this widget
        self._update_locations_map_references(old_widget_id, final_widget_id)
        
        # Clean up old widget ID
        if old_widget_id in self._widgets:
            del self._widgets[old_widget_id]
        
        # Remove old unique ID from mappings if changed
        if old_unique_id != new_unique_id and old_unique_id in self._unique_id_to_widget_id:
            del self._unique_id_to_widget_id[old_unique_id]
        
        return True, final_widget_id, None
    
    #MARK: - Container location methods
    
    def set_locations_map(self, container_id, locations_map):
        """
        Set the container's locations map.
        
        Args:
            container_id: The container's unique ID
            locations_map: A dictionary mapping subcontainer locations to widget IDs
        """
        if container_id not in self._container_locations_map:
            self._container_locations_map[container_id] = {}
        
        self._container_locations_map[container_id] = locations_map.copy()
    
    def get_locations_map(self, container_id):
        """
        Get the container's locations map.
        
        Args:
            container_id: The container's unique ID
            
        Returns:
            dict: A dictionary mapping subcontainer locations to widget IDs
        """
        if container_id not in self._container_locations_map:
            return {}
        
        return self._container_locations_map[container_id].copy()
    
    def get_subcontainer_id_at_location(self, container_id, location):
        """
        Get the subcontainer widget ID at a specific location.
        
        Args:
            container_id: The container's unique ID
            location: The subcontainer location within the container
            
        Returns:
            str: The widget ID of the subcontainer, or None if not found
        """
        if container_id not in self._container_locations_map:
            return None
        
        locations_map = self._container_locations_map[container_id]
        return locations_map.get(location)
    
    def get_widgets_at_location(self, container_id, container_location):
        """
        Get all widgets at a specific container location.
        
        Args:
            container_id: The container's unique ID
            container_location: The container location
            
        Returns:
            list: A list of widget IDs at the specified location
        """
        if container_id not in self._container_to_widgets:
            return []
        
        widgets = []
        for widget_id in self._container_to_widgets[container_id]:
            components = parse_widget_id(widget_id)
            if components and components['container_location'] == container_location:
                widgets.append(widget_id)
        
        return widgets
    
    #MARK: - Query methods
    
    def get_widget(self, widget_id):
        """
        Get a widget by its ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            object: The widget object, or None if not found
        """
        return self._widgets.get(widget_id)
    
    def get_widget_id(self, widget):
        """
        Get a widget's ID.
        
        Args:
            widget: The widget object
            
        Returns:
            str: The widget ID, or None if not found
        """
        return self._widget_objects_to_id.get(widget)
    
    def get_widget_id_by_unique_id(self, unique_id):
        """
        Get a widget's ID by its unique ID.
        
        Args:
            unique_id: The widget's unique ID
            
        Returns:
            str: The widget ID, or None if not found
        """
        return self._unique_id_to_widget_id.get(unique_id)
    
    def get_container_id_from_widget_id(self, widget_id):
        """
        Get the container ID from a widget ID.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            str: The container's unique ID, or None if invalid
        """
        components = parse_widget_id(widget_id)
        if not components:
            return None
        
        return components['container_unique_id']
    
    def get_widget_ids_by_container_id(self, container_unique_id):
        """
        Get all widget IDs for a specific container.
        
        Args:
            container_unique_id: The container's unique ID
            
        Returns:
            list: A list of widget IDs in the container
        """
        if container_unique_id not in self._container_to_widgets:
            return []
        
        return list(self._container_to_widgets[container_unique_id])
    
    def get_widget_ids_by_container_id_and_location(self, container_unique_id, container_location):
        """
        Get all widget IDs for a specific container and location.
        
        Args:
            container_unique_id: The container's unique ID
            container_location: The container location
            
        Returns:
            list: A list of widget IDs in the container at the specified location
        """
        if container_unique_id not in self._container_to_widgets:
            return []
        
        widgets = []
        for widget_id in self._container_to_widgets[container_unique_id]:
            components = parse_widget_id(widget_id)
            if components and components['container_location'] == container_location:
                widgets.append(widget_id)
        
        return widgets
    
    #MARK: - Helper methods
    
    def _update_container_locations_map(self, container_unique_id):
        """
        Update the container's locations map based on current widget relationships.
        
        This synchronizes _container_locations_map with the current state of 
        _container_to_widgets for a specific container.
        
        Args:
            container_unique_id: The container's unique ID
        """
        if container_unique_id not in self._container_to_widgets:
            # If container has no widgets, ensure it has an empty map
            if container_unique_id in self._container_locations_map:
                self._container_locations_map[container_unique_id] = {}
            return
        
        # Initialize/clear the locations map for this container
        if container_unique_id not in self._container_locations_map:
            self._container_locations_map[container_unique_id] = {}
        else:
            self._container_locations_map[container_unique_id].clear()
        
        # Group widgets by their container location
        location_map = {}
        for widget_id in self._container_to_widgets[container_unique_id]:
            components = parse_widget_id(widget_id)
            if components:
                location = components['container_location']
                if location not in location_map:
                    location_map[location] = []
                location_map[location].append(widget_id)
        
        # Update the container's locations map
        self._container_locations_map[container_unique_id] = location_map
    
    def _get_location_generator(self, container_location):
        """
        Get or create a location generator for a specific container location.
        
        Args:
            container_location: The container location
            
        Returns:
            LocationIDGenerator: The location generator
        """
        if container_location not in self._container_location_generators:
            self._container_location_generators[container_location] = LocationIDGenerator()
        
        return self._container_location_generators[container_location]
    
    def _get_container_location(self, container_id):
        """
        Get the container's location path.
        
        Args:
            container_id: The container's unique ID
            
        Returns:
            str: The container's location path, or "0" if root or container not found
        """
        if container_id == DEFAULT_ROOT_CONTAINER_ID:
            return DEFAULT_ROOT_LOCATION
        
        # Get the container's widget ID
        container_widget_id = self._unique_id_to_widget_id.get(container_id)
        if not container_widget_id:
            return DEFAULT_ROOT_LOCATION
        
        # Parse the container's widget ID
        container_components = parse_widget_id(container_widget_id)
        if not container_components:
            return DEFAULT_ROOT_LOCATION
        
        # Construct path from container's location and location ID
        container_loc = container_components['container_location']
        container_widget_loc = container_components['widget_location_id']
        
        # Return the full path
        return f"{container_loc}/{container_widget_loc}"
    
    def _update_children_container_locations(self, container_unique_id, old_path, new_path):
        """
        Update the container_location of all widgets in a container.
        
        This is called when a container's location changes, to update all
        child widget IDs accordingly.
        
        Args:
            container_unique_id: The container's unique ID
            old_path: The container's old location path
            new_path: The container's new location path
        """
        if container_unique_id not in self._container_to_widgets:
            return
        
        # Get all children (make a copy because we'll modify during iteration)
        child_widget_ids = list(self._container_to_widgets[container_unique_id])
        
        for child_id in child_widget_ids:
            components = parse_widget_id(child_id)
            if not components:
                continue
            
            child_type_code = components['type_code']
            child_unique_id = components['unique_id']
            child_widget_location_id = components['widget_location_id']
            
            # Update child's ID with new container location
            new_child_id = create_widget_id(
                child_type_code,
                child_unique_id,
                container_unique_id,
                new_path,
                child_widget_location_id
            )
            
            # Update mappings
            child_widget = self._widgets[child_id]
            self._widgets[new_child_id] = child_widget
            self._unique_id_to_widget_id[child_unique_id] = new_child_id
            self._widget_objects_to_id[child_widget] = new_child_id
            
            # Update container's widget set
            self._container_to_widgets[container_unique_id].discard(child_id)
            self._container_to_widgets[container_unique_id].add(new_child_id)
            
            # Update any locations map entries
            self._update_locations_map_references(child_id, new_child_id)
            
            # Clean up old ID
            del self._widgets[child_id]
            
            # If this child is a container, recursively update its children
            if ContainerTypeCodes.is_valid_code(child_type_code) and child_unique_id in self._container_to_widgets:
                old_child_path = f"{old_path}/{child_widget_location_id}"
                new_child_path = f"{new_path}/{child_widget_location_id}"
                self._update_children_container_locations(child_unique_id, old_child_path, new_child_path)
                
                # Update container's locations map
                self._update_container_locations_map(child_unique_id)
    
    def _update_locations_map_references(self, old_widget_id, new_widget_id):
        """
        Update any locations map entries that reference a widget ID.
        
        Args:
            old_widget_id: The old widget ID to replace
            new_widget_id: The new widget ID to use
        """
        for container_id, locations_map in self._container_locations_map.items():
            for location, widget_ids in locations_map.items():
                if isinstance(widget_ids, list):
                    # If it's a list of widget IDs
                    if old_widget_id in widget_ids:
                        idx = widget_ids.index(old_widget_id)
                        widget_ids[idx] = new_widget_id
                elif widget_ids == old_widget_id:
                    # If it's a single widget ID
                    locations_map[location] = new_widget_id
    
    def _remove_from_locations_maps(self, widget_id):
        """
        Remove a widget ID from all locations maps.
        
        Args:
            widget_id: The widget ID to remove
        """
        for container_id, locations_map in list(self._container_locations_map.items()):
            for location, widget_ids in list(locations_map.items()):
                if isinstance(widget_ids, list):
                    # If it's a list of widget IDs
                    if widget_id in widget_ids:
                        widget_ids.remove(widget_id)
                        if not widget_ids:
                            del locations_map[location]
                elif widget_ids == widget_id:
                    # If it's a single widget ID
                    del locations_map[location]
    
    def _cleanup_container_location_generators(self, container_path):
        """
        Clean up all location generators for a container and its children.
        
        This is called when a container is unregistered to ensure all
        its location generators are removed.
        
        Args:
            container_path: The container's full path
        """
        # Remove the exact container path generator
        if container_path in self._container_location_generators:
            del self._container_location_generators[container_path]
        
        # Also remove any child paths (starting with container_path/)
        prefix = container_path + "/"
        for path in list(self._container_location_generators.keys()):
            if path.startswith(prefix):
                del self._container_location_generators[path]
    
    def clear(self):
        """Clear all widget registrations."""
        self._widgets.clear()
        self._unique_id_to_widget_id.clear()
        self._widget_objects_to_id.clear()
        self._container_to_widgets.clear()
        self._container_location_generators.clear()
        self._container_locations_map.clear()