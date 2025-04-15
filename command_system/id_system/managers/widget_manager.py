"""
Widget Manager module.

This module contains the WidgetManager class for managing widgets and their
relationships with containers in the ID system.
"""

from command_system.id_system.core.mapping import Mapping
from command_system.id_system.core.mapping import GeneratorMapping
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
        
        # Create mappings for containers and locations
        self._container_to_widgets = Mapping(update_keys=True, update_values=True)
        self._container_locations_map = Mapping(update_keys=True, update_values=True)
        
        # Add mappings to registry for automatic updates
        self.registry.mappings.append(self._container_to_widgets)
        self.registry.mappings.append(self._container_locations_map)
        
        # Create the specialized generator mapping
        self._location_generators = GeneratorMapping()
        self.registry.mappings.append(self._location_generators)
    
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
            
        # Determine container location based on container
        container_location = self._get_container_location(container_unique_id)
        
        # Determine widget_location_id
        widget_location_id = location
        if widget_location_id is None:
            # Generate a new widget_location_id
            widget_location_id = self._location_generators.generate_location_id(container_location)
        else:
            # Check if the widget_location_id is available
            if self._location_generators.is_location_registered(container_location, widget_location_id):
                raise IDRegistrationError(
                    f"Widget location ID '{widget_location_id}' already exists in container location '{container_location}'"
                )
            
            # Register the widget location ID
            self._location_generators.register_widget_location(
                create_widget_id(type_code, unique_id, container_unique_id, container_location, widget_location_id)
            )
        
        # Create the widget ID
        widget_id = create_widget_id(
            type_code,
            unique_id,
            container_unique_id,
            container_location,
            widget_location_id
        )
        
        # Add to the container's widget set
        container_widgets = self._container_to_widgets.get(container_unique_id) or set()
        container_widgets.add(widget_id)
        self._container_to_widgets.add(container_unique_id, container_widgets)
        
        # Update the container's locations map
        self._update_container_locations_map(container_unique_id)
        
        # If this widget is a container, initialize its widgets set
        if ContainerTypeCodes.is_valid_code(type_code):
            self._container_to_widgets.add(unique_id, set())
            self._container_locations_map.add(unique_id, {})
        
        return widget_id
    
    def unregister_widget(self, widget_id):
        """
        Unregister a widget from the manager.
        
        Args:
            widget_id: The ID of the widget to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return False
        
        unique_id = components['unique_id']
        container_unique_id = components['container_unique_id']
        container_location = components['container_location']
        widget_location_id = components['widget_location_id']
        
        # Get the widget object
        widget = self.registry.get_widget(widget_id)
        
        # Call the registry's widget unregister callback
        self.registry._on_widget_unregister(widget_id, widget)
        
        # If it's a container, handle its children first
        if unique_id in self._container_to_widgets:
            # Make a copy to avoid modification during iteration
            container_widgets = self._container_to_widgets.get(unique_id) or set()
            child_widgets = list(container_widgets)
            for child_id in child_widgets:
                # Unregister all child widgets
                self.registry.unregister(child_id)
            
            # Clean up container data
            self._container_to_widgets.delete(unique_id)
            self._container_locations_map.delete(unique_id)
                
            # Clean up any location generators for this container's locations
            full_container_path = f"{container_location}/{widget_location_id}"
            self._location_generators.cleanup_container_locations(full_container_path)
        
        # Remove from container's widgets set
        container_widgets = self._container_to_widgets.get(container_unique_id) or set()
        if widget_id in container_widgets:
            container_widgets.discard(widget_id)
            self._container_to_widgets.add(container_unique_id, container_widgets)
            # Update the container's locations map after removing widget
            self._update_container_locations_map(container_unique_id)
        
        # Unregister from location generator
        self._location_generators.delete_widget_location(widget_id)
        
        # If this widget is in any container's locations map, remove it
        self._remove_from_locations_maps(widget_id)
        
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
        # Extract container unique ID if full ID provided
        new_container_unique_id = new_container_id
        if new_container_id and ID_SEPARATOR in new_container_id:
            new_container_unique_id = get_unique_id_from_id(new_container_id)
            
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
        if old_container_id == new_container_unique_id:
            return widget_id
        
        # Check if this is a container with children
        is_container = ContainerTypeCodes.is_valid_code(type_code)
        
        # Unregister from old location generator
        self._location_generators.delete_widget_location(widget_id)
        
        # Remove from old container's widget set
        old_container_widgets = self._container_to_widgets.get(old_container_id) or set()
        if widget_id in old_container_widgets:
            old_container_widgets.discard(widget_id)
            self._container_to_widgets.add(old_container_id, old_container_widgets)
            # Update old container's locations map
            self._update_container_locations_map(old_container_id)
        
        # Determine the new container location based on container
        new_container_location = self._get_container_location(new_container_unique_id)
        
        # Check if the widget_location_id is available in the new container
        if self._location_generators.is_location_registered(new_container_location, widget_location_id):
            # Generate a new widget_location_id
            final_widget_location_id = self._location_generators.generate_location_id(new_container_location)
        else:
            final_widget_location_id = widget_location_id
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            new_container_unique_id,
            new_container_location,
            final_widget_location_id
        )
        
        # Register with the new location generator
        self._location_generators.register_widget_location(new_widget_id)
        
        # Add to new container's widget set
        new_container_widgets = self._container_to_widgets.get(new_container_unique_id) or set()
        new_container_widgets.add(new_widget_id)
        self._container_to_widgets.add(new_container_unique_id, new_container_widgets)
        
        # Update new container's locations map
        self._update_container_locations_map(new_container_unique_id)
        
        # If it's a container, update all its children's container locations
        if is_container:
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
        
        # Unregister from old location
        self._location_generators.delete_widget_location(widget_id)
        
        # Check if the new widget_location_id is available
        if self._location_generators.is_location_registered(container_location, new_location):
            raise IDRegistrationError(f"Widget location ID '{new_location}' already exists in container location '{container_location}'")
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            container_unique_id,
            container_location,
            new_location
        )
        
        # Register with the new location
        self._location_generators.register_widget_location(new_widget_id)
        
        # Update container's widget set
        container_widgets = self._container_to_widgets.get(container_unique_id) or set()
        if widget_id in container_widgets:
            container_widgets.discard(widget_id)
            container_widgets.add(new_widget_id)
            self._container_to_widgets.add(container_unique_id, container_widgets)
            # Update container's locations map
            self._update_container_locations_map(container_unique_id)
        
        # If it's a container, update all its children's container locations
        if is_container:
            old_full_path = f"{container_location}/{old_widget_location_id}"
            new_full_path = f"{container_location}/{new_location}"
            self._update_children_container_locations(unique_id, old_full_path, new_full_path)
        
        # Update any locations map entries that reference this widget
        self._update_locations_map_references(widget_id, new_widget_id)
        
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
        widget = self.registry.get_widget(old_widget_id)
        if widget is None:
            return False, old_widget_id, "Widget not found"
        
        # Parse both IDs
        old_components = parse_widget_id(old_widget_id)
        new_components = parse_widget_id(new_widget_id)
        
        if not old_components or not new_components:
            return False, old_widget_id, "Invalid widget ID format"
        
        # Make sure type codes match
        if old_components['type_code'] != new_components['type_code']:
            return False, old_widget_id, "Cannot change widget type code"
        
        # Check if the unique ID is changing
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        if old_unique_id != new_unique_id:
            # Make sure the new unique ID isn't already used
            if old_unique_id != new_unique_id and self.registry.get_full_id_from_unique_id(new_unique_id):
                return False, old_widget_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # Check if container is changing
        old_container_id = old_components['container_unique_id']
        new_container_id = new_components['container_unique_id']
        
        # Handle container change if necessary
        if old_container_id != new_container_id:
            # Verify the new container exists if it's not the root
            if new_container_id != DEFAULT_ROOT_CONTAINER_ID and new_container_id not in self._container_to_widgets:
                return False, old_widget_id, f"Container with ID '{new_container_id}' does not exist"
                
            # Remove from old container's widget set
            old_container_widgets = self._container_to_widgets.get(old_container_id) or set()
            if old_widget_id in old_container_widgets:
                old_container_widgets.discard(old_widget_id)
                self._container_to_widgets.add(old_container_id, old_container_widgets)
                # Update old container's locations map
                self._update_container_locations_map(old_container_id)
        
        # Handle location changes
        old_container_location = old_components['container_location']
        new_container_location = new_components['container_location']
        old_widget_location_id = old_components['widget_location_id']
        new_widget_location_id = new_components['widget_location_id']
        
        # Unregister from old location
        self._location_generators.delete_widget_location(old_widget_id)
        
        # If container location changing or widget location changing, check availability
        final_widget_location_id = new_widget_location_id
        if old_container_location != new_container_location:
            # Check if the widget_location_id is available in the new container
            if self._location_generators.is_location_registered(new_container_location, new_widget_location_id):
                # Generate a new widget_location_id
                final_widget_location_id = self._location_generators.generate_location_id(new_container_location)
        else:
            # Same container location, just updating widget_location_id
            if old_widget_location_id != new_widget_location_id:
                # Check if new location ID is available
                if self._location_generators.is_location_registered(new_container_location, new_widget_location_id):
                    return False, old_widget_id, f"Widget location ID '{new_widget_location_id}' already exists in container location '{old_container_location}'"
        
        # Create the final widget ID
        final_widget_id = create_widget_id(
            old_components['type_code'],  # Type code remains the same
            new_unique_id,
            new_container_id,
            new_container_location,
            final_widget_location_id
        )
        
        # Register with the location generator
        self._location_generators.register_widget_location(final_widget_id)
        
        # If this is the same as the original ID, nothing to do
        if final_widget_id == old_widget_id:
            return True, old_widget_id, None
        
        # Update container's widget set with the new ID
        if old_container_id != new_container_id:
            # Add to new container's widget set
            new_container_widgets = self._container_to_widgets.get(new_container_id) or set()
            new_container_widgets.add(final_widget_id)
            self._container_to_widgets.add(new_container_id, new_container_widgets)
            # Update new container's locations map
            self._update_container_locations_map(new_container_id)
        else:
            # Update the same container's widget set
            container_widgets = self._container_to_widgets.get(old_container_id) or set()
            if old_widget_id in container_widgets:
                container_widgets.discard(old_widget_id)
                container_widgets.add(final_widget_id)
                self._container_to_widgets.add(old_container_id, container_widgets)
                # Update container's locations map
                self._update_container_locations_map(old_container_id)
        
        # If this is a container, update all its children's container locations
        is_container = ContainerTypeCodes.is_valid_code(old_components['type_code'])
        if is_container:
            # Update internal container mappings if unique ID changed
            if old_unique_id != new_unique_id:
                # Transfer container's widget set
                container_widgets = self._container_to_widgets.get(old_unique_id) or set()
                if container_widgets:
                    self._container_to_widgets.add(new_unique_id, container_widgets)
                    self._container_to_widgets.delete(old_unique_id)
                
                # Transfer container's locations map
                container_locations = self._container_locations_map.get(old_unique_id) or {}
                if container_locations:
                    self._container_locations_map.add(new_unique_id, container_locations)
                    self._container_locations_map.delete(old_unique_id)
            
            # Update child container locations if path changed
            if old_container_location != new_container_location or old_widget_location_id != final_widget_location_id:
                old_full_path = f"{old_container_location}/{old_widget_location_id}"
                new_full_path = f"{new_container_location}/{final_widget_location_id}"
                self._update_children_container_locations(new_unique_id, old_full_path, new_full_path)
        
        # Update any locations map entries that reference this widget
        self._update_locations_map_references(old_widget_id, final_widget_id)
        
        return True, final_widget_id, None
    
    #MARK: - Container location methods
    
    def set_locations_map(self, container_id, locations_map):
        """
        Set the container's locations map.
        
        Args:
            container_id: The container's unique ID
            locations_map: A dictionary mapping subcontainer locations to widget IDs
        """
        self._container_locations_map.add(container_id, locations_map.copy())
    
    def get_locations_map(self, container_id):
        """
        Get the container's locations map.
        
        Args:
            container_id: The container's unique ID
            
        Returns:
            dict: A dictionary mapping subcontainer locations to widget IDs
        """
        return self._container_locations_map.get(container_id) or {}
    
    def get_subcontainer_id_at_location(self, container_id, location):
        """
        Get the subcontainer widget ID at a specific location.
        
        Args:
            container_id: The container's unique ID
            location: The subcontainer location within the container
            
        Returns:
            str: The widget ID of the subcontainer, or None if not found
        """
        locations_map = self._container_locations_map.get(container_id) or {}
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
        container_widgets = self._container_to_widgets.get(container_id) or set()
        
        widgets = []
        for widget_id in container_widgets:
            components = parse_widget_id(widget_id)
            if components and components['container_location'] == container_location:
                widgets.append(widget_id)
        
        return widgets
    
    #MARK: - Query methods
    
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
        return list(self._container_to_widgets.get(container_unique_id) or [])
    
    def get_widget_ids_by_container_id_and_location(self, container_unique_id, container_location):
        """
        Get all widget IDs for a specific container and location.
        
        Args:
            container_unique_id: The container's unique ID
            container_location: The container location
            
        Returns:
            list: A list of widget IDs in the container at the specified location
        """
        container_widgets = self._container_to_widgets.get(container_unique_id) or set()
        
        widgets = []
        for widget_id in container_widgets:
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
        container_widgets = self._container_to_widgets.get(container_unique_id)
        if not container_widgets:
            # If container has no widgets, ensure it has an empty map
            self._container_locations_map.add(container_unique_id, {})
            return
        
        # Group widgets by their container location
        location_map = {}
        for widget_id in container_widgets:
            components = parse_widget_id(widget_id)
            if components:
                location = components['container_location']
                if location not in location_map:
                    location_map[location] = []
                location_map[location].append(widget_id)
        
        # Update the container's locations map
        self._container_locations_map.add(container_unique_id, location_map)
    
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
        container_widget_id = self.registry.get_full_id_from_unique_id(container_id)
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
        container_widgets = self._container_to_widgets.get(container_unique_id)
        if not container_widgets:
            return
        
        # Get all children (make a copy because we'll modify during iteration)
        child_widget_ids = list(container_widgets)
        
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
            
            # Update location generator registration
            self._location_generators.delete_widget_location(child_id)
            self._location_generators.register_widget_location(new_child_id)
            
            # Update container's widget set
            container_widgets.discard(child_id)
            container_widgets.add(new_child_id)
            
            # Update any locations map entries
            self._update_locations_map_references(child_id, new_child_id)
            
            # If this child is a container, recursively update its children
            if ContainerTypeCodes.is_valid_code(child_type_code):
                old_child_path = f"{old_path}/{child_widget_location_id}"
                new_child_path = f"{new_path}/{child_widget_location_id}"
                self._update_children_container_locations(child_unique_id, old_child_path, new_child_path)
                
                # Update container's locations map
                self._update_container_locations_map(child_unique_id)
        
        # Update the mapping with the modified set
        self._container_to_widgets.add(container_unique_id, container_widgets)
    
    def _update_locations_map_references(self, old_widget_id, new_widget_id):
        """
        Update any locations map entries that reference a widget ID.
        
        Args:
            old_widget_id: The old widget ID to replace
            new_widget_id: The new widget ID to use
        """
        for container_id, locations_map in self._container_locations_map._storage.items():
            if not locations_map:
                continue
                
            updated = False
            for location, widget_ids in list(locations_map.items()):
                if isinstance(widget_ids, list):
                    # If it's a list of widget IDs
                    if old_widget_id in widget_ids:
                        widget_ids = [new_widget_id if id == old_widget_id else id for id in widget_ids]
                        locations_map[location] = widget_ids
                        updated = True
                elif widget_ids == old_widget_id:
                    # If it's a single widget ID
                    locations_map[location] = new_widget_id
                    updated = True
            
            if updated:
                self._container_locations_map.add(container_id, locations_map)
    
    def _remove_from_locations_maps(self, widget_id):
        """
        Remove a widget ID from all locations maps.
        
        Args:
            widget_id: The widget ID to remove
        """
        for container_id, locations_map in list(self._container_locations_map._storage.items()):
            if not locations_map:
                continue
                
            updated = False
            for location, widget_ids in list(locations_map.items()):
                if isinstance(widget_ids, list):
                    # If it's a list of widget IDs
                    if widget_id in widget_ids:
                        widget_ids.remove(widget_id)
                        if not widget_ids:
                            del locations_map[location]
                        else:
                            locations_map[location] = widget_ids
                        updated = True
                elif widget_ids == widget_id:
                    # If it's a single widget ID
                    del locations_map[location]
                    updated = True
            
            if updated:
                self._container_locations_map.add(container_id, locations_map)
    
    def clear(self):
        """Clear all widget registrations."""
        for mapping in [self._container_to_widgets, self._container_locations_map]:
            mapping._storage.clear()
            mapping._key_log.clear()
            mapping._value_log.clear()