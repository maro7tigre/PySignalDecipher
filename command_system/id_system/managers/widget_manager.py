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
    get_full_container_path,
    replace_container_path_prefix
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
        
        # Create a bidirectional mapping: container_id -> child_widget_ids and widget_id -> container_id
        self._container_to_widgets = Mapping(update_keys=True, update_values=True)
        self._widget_to_container = Mapping(update_keys=True, update_values=True)  # New mapping for quick lookups
        
        # Mapping for container location information
        self._container_locations_map = Mapping(update_keys=True, update_values=True)
        
        # Create the specialized generator mapping
        self._location_generators = GeneratorMapping()
        
        # Add mappings to registry for automatic updates
        self.registry.mappings.append(self._container_to_widgets)
        self.registry.mappings.append(self._widget_to_container)
        self.registry.mappings.append(self._container_locations_map)
        self.registry.mappings.append(self._location_generators)
    
    def register_widget(self, widget, type_code, unique_id, container_id=DEFAULT_ROOT_CONTAINER_ID, 
                      location=None):
        """
        Register a widget with the manager.
        
        Args:
            widget: The widget object to register
            type_code: The widget type code
            unique_id: The unique ID for the widget
            container_id: The container's full ID or unique ID (default: "0")
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
        
        # Set up container reference for this widget
        full_container_id = container_id
        if container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in container_id:
            full_container_id = self.registry.get_full_id_from_unique_id(container_unique_id)
            if not full_container_id:
                full_container_id = DEFAULT_ROOT_CONTAINER_ID
                
        # Update container_to_widgets mapping
        container_widgets = self._container_to_widgets.get(full_container_id) or set()
        container_widgets.add(widget_id)
        self._container_to_widgets.add(full_container_id, container_widgets)
        
        # Update widget_to_container mapping
        self._widget_to_container.add(widget_id, full_container_id)
        
        # Update the container's locations map
        self._update_container_locations_map(full_container_id)
        
        # If this widget is a container, initialize its widgets set
        if ContainerTypeCodes.is_valid_code(type_code):
            self._container_to_widgets.add(widget_id, set())
            self._container_locations_map.add(widget_id, {})
        
        return widget_id
    
    def unregister_widget(self, widget_id):
        """
        Unregister a widget from the manager.
        
        Args:
            widget_id: The full ID of the widget to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return False
        
        # Get the widget object
        widget = self.registry.get_widget(widget_id)
        
        # Call the registry's widget unregister callback
        self.registry._on_widget_unregister(widget_id, widget)
        
        # Handle container separately
        is_container = ContainerTypeCodes.is_valid_code(components['type_code'])
        if is_container:
            # Get all children before unregistering
            container_widgets = list(self._container_to_widgets.get(widget_id) or [])
            
            # Unregister all child widgets first
            for child_id in container_widgets:
                self.registry.unregister(child_id)
            
            # Clean up container data
            self._container_to_widgets.delete(widget_id)
            self._container_locations_map.delete(widget_id)
            
            # Clean up location generators for this container
            full_container_path = get_full_container_path(
                components['container_location'], 
                components['widget_location_id']
            )
            self._location_generators.cleanup_container_locations(full_container_path)
        
        # Get parent container
        container_id = self._widget_to_container.get(widget_id)
        if container_id:
            # Remove from container's widgets set
            container_widgets = self._container_to_widgets.get(container_id) or set()
            container_widgets.discard(widget_id)
            self._container_to_widgets.add(container_id, container_widgets)
            
            # Update the container's locations map
            self._update_container_locations_map(container_id)
            
            # Remove widget-to-container mapping
            self._widget_to_container.delete(widget_id)
        
        # Unregister from location generator
        self._location_generators.delete_widget_location(widget_id)
        
        # Remove from any locations maps
        self._remove_from_locations_maps(widget_id)
        
        return True
    
    def update_widget_container(self, widget_id, new_container_id):
        """
        Update a widget's container reference.
        
        Args:
            widget_id: The full ID of the widget to update
            new_container_id: The new container's full ID or unique ID
            
        Returns:
            str: The updated widget ID
            
        Raises:
            IDRegistrationError: If the widget_location_id already exists in the new container location
        """
        # Get components from existing widget ID
        components = parse_widget_id(widget_id)
        if not components:
            return widget_id
        
        # Extract new container unique ID
        new_container_unique_id = new_container_id
        if new_container_id and ID_SEPARATOR in new_container_id:
            new_container_unique_id = get_unique_id_from_id(new_container_id)
        
        # If container hasn't changed, no update needed
        old_container_unique_id = components['container_unique_id']
        if old_container_unique_id == new_container_unique_id:
            return widget_id
        
        # Get the full new container ID
        new_full_container_id = new_container_id
        if new_container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in new_container_id:
            new_full_container_id = self.registry.get_full_id_from_unique_id(new_container_unique_id)
            if not new_full_container_id:
                new_full_container_id = DEFAULT_ROOT_CONTAINER_ID
        
        # Get new container location
        new_container_location = self._get_container_location(new_container_unique_id)
        
        # Check if we need a new location ID in the new container
        widget_location_id = components['widget_location_id']
        if self._location_generators.is_location_registered(new_container_location, widget_location_id):
            # Need a new location ID
            widget_location_id = self._location_generators.generate_location_id(new_container_location)
        
        # Create the updated widget ID
        type_code = components['type_code']
        unique_id = components['unique_id']
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            new_container_unique_id,
            new_container_location,
            widget_location_id
        )
        
        # Update location generator registrations
        self._location_generators.delete_widget_location(widget_id)
        self._location_generators.register_widget_location(new_widget_id)
        
        # Update container mappings
        old_container_id = self._widget_to_container.get(widget_id)
        if old_container_id:
            # Remove from old container
            old_container_widgets = self._container_to_widgets.get(old_container_id) or set()
            old_container_widgets.discard(widget_id)
            self._container_to_widgets.add(old_container_id, old_container_widgets)
            self._update_container_locations_map(old_container_id)
        
        # Add to new container
        new_container_widgets = self._container_to_widgets.get(new_full_container_id) or set()
        new_container_widgets.add(new_widget_id)
        self._container_to_widgets.add(new_full_container_id, new_container_widgets)
        self._update_container_locations_map(new_full_container_id)
        
        # Update widget-to-container mapping
        self._widget_to_container.delete(widget_id)
        self._widget_to_container.add(new_widget_id, new_full_container_id)
        
        # If this is a container with children, update all child widgets
        if ContainerTypeCodes.is_valid_code(type_code):
            # Create old and new container paths for child updates
            old_container_path = get_full_container_path(
                components['container_location'], 
                components['widget_location_id']
            )
            new_container_path = get_full_container_path(
                new_container_location, 
                widget_location_id
            )
            
            # Update all children - copy the container data to the new ID first
            if widget_id in self._container_to_widgets:
                # Copy the children set to the new ID
                self._container_to_widgets.add(new_widget_id, self._container_to_widgets.get(widget_id))
                self._container_locations_map.add(new_widget_id, self._container_locations_map.get(widget_id) or {})
                
                # Now update all children's IDs
                self._update_children_recursively(widget_id, new_widget_id, old_container_path, new_container_path)
                
                # Clean up old container entries
                self._container_to_widgets.delete(widget_id)
                self._container_locations_map.delete(widget_id)
        
        return new_widget_id
    
    def update_widget_location(self, widget_id, new_location):
        """
        Update a widget's location ID within its container.
        
        Args:
            widget_id: The full ID of the widget to update
            new_location: The new widget_location_id
            
        Returns:
            str: The updated widget ID
            
        Raises:
            IDRegistrationError: If the new widget_location_id already exists in the container location
        """
        # Get components from existing widget ID
        components = parse_widget_id(widget_id)
        if not components:
            return widget_id
        
        # If location hasn't changed, no update needed
        old_widget_location_id = components['widget_location_id']
        if old_widget_location_id == new_location:
            return widget_id
        
        container_location = components['container_location']
        
        # Check if the new location ID is available
        if self._location_generators.is_location_registered(container_location, new_location):
            raise IDRegistrationError(
                f"Widget location ID '{new_location}' already exists in container location '{container_location}'"
            )
        
        # Create the updated widget ID
        type_code = components['type_code']
        unique_id = components['unique_id']
        container_unique_id = components['container_unique_id']
        new_widget_id = create_widget_id(
            type_code,
            unique_id,
            container_unique_id,
            container_location,
            new_location
        )
        
        # Update location generator registrations
        self._location_generators.delete_widget_location(widget_id)
        self._location_generators.register_widget_location(new_widget_id)
        
        # Update container mappings
        container_id = self._widget_to_container.get(widget_id)
        if container_id:
            container_widgets = self._container_to_widgets.get(container_id) or set()
            container_widgets.discard(widget_id)
            container_widgets.add(new_widget_id)
            self._container_to_widgets.add(container_id, container_widgets)
            self._update_container_locations_map(container_id)
        
        # Update widget-to-container mapping
        self._widget_to_container.delete(widget_id)
        self._widget_to_container.add(new_widget_id, container_id)
        
        # If this is a container with children, update all child widgets
        if ContainerTypeCodes.is_valid_code(type_code):
            # Create old and new container paths for child updates
            old_container_path = get_full_container_path(
                container_location, 
                old_widget_location_id
            )
            new_container_path = get_full_container_path(
                container_location, 
                new_location
            )
            
            # Update all children - copy the container data to the new ID first
            if widget_id in self._container_to_widgets:
                # Copy the children set to the new ID
                self._container_to_widgets.add(new_widget_id, self._container_to_widgets.get(widget_id))
                self._container_locations_map.add(new_widget_id, self._container_locations_map.get(widget_id) or {})
                
                # Now update all children's IDs
                self._update_children_recursively(widget_id, new_widget_id, old_container_path, new_container_path)
                
                # Clean up old container entries
                self._container_to_widgets.delete(widget_id)
                self._container_locations_map.delete(widget_id)
        
        return new_widget_id
    
    def update_widget_id(self, old_widget_id, new_widget_id):
        """
        Update a widget's ID with a completely new ID.
        
        This is a more direct approach than calling update_container or update_location
        and allows changing multiple aspects of the ID at once.
        
        Args:
            old_widget_id: The current full widget ID
            new_widget_id: The new full widget ID
            
        Returns:
            tuple: (success, actual_new_id, error_message) where:
                - success: Boolean indicating whether the update was successful
                - actual_new_id: The actual new ID after the update (may be different from requested)
                - error_message: Description of any error that occurred (None if successful)
        """
        # Make sure the widget exists
        widget = self.registry.get_widget(old_widget_id)
        if widget is None:
            return False, old_widget_id, "Widget not found"
        
        # Parse both IDs
        old_components = parse_widget_id(old_widget_id)
        new_components = parse_widget_id(new_widget_id)
        
        if not old_components or not new_components:
            return False, old_widget_id, "Invalid widget ID format"
        
        # Type codes must match
        if old_components['type_code'] != new_components['type_code']:
            return False, old_widget_id, "Cannot change widget type code"
        
        # Check if the unique ID is changing and not already in use
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        if old_unique_id != new_unique_id:
            # Make sure new unique ID isn't already used by someone else
            existing_id = self.registry.get_full_id_from_unique_id(new_unique_id)
            if existing_id and existing_id != old_widget_id:
                return False, old_widget_id, f"Unique ID '{new_unique_id}' is already in use"
        
        # If container is changing, verify it exists
        old_container_id = old_components['container_unique_id']
        new_container_id = new_components['container_unique_id']
        
        if new_container_id != DEFAULT_ROOT_CONTAINER_ID and new_container_id != old_container_id:
            new_full_container_id = self.registry.get_full_id_from_unique_id(new_container_id)
            if not new_full_container_id:
                return False, old_widget_id, f"Container with ID '{new_container_id}' does not exist"
        
        # Check if location ID needs validation
        new_container_location = new_components['container_location']
        new_widget_location_id = new_components['widget_location_id'] 
        
        # If only the widget location ID is changing within the same container location
        if (old_components['container_location'] == new_container_location and 
            old_components['widget_location_id'] != new_widget_location_id):
            
            # Verify the new location ID is available
            if self._location_generators.is_location_registered(new_container_location, new_widget_location_id):
                return False, old_widget_id, f"Widget location ID '{new_widget_location_id}' already exists in container location '{new_container_location}'"
                
        # If container location is changing, we might need a new widget location ID
        elif old_components['container_location'] != new_container_location:
            if self._location_generators.is_location_registered(new_container_location, new_widget_location_id):
                # Generate a new location ID instead of the requested one
                new_widget_location_id = self._location_generators.generate_location_id(new_container_location)
        
        # Create the final widget ID
        type_code = old_components['type_code']  # Type code remains the same
        final_widget_id = create_widget_id(
            type_code,
            new_unique_id,
            new_container_id,
            new_container_location,
            new_widget_location_id
        )
        
        # If no changes, we're done
        if final_widget_id == old_widget_id:
            return True, old_widget_id, None
            
        # Handle the remaining update steps through our update_container method
        # if container or location has changed
        container_changed = (old_components['container_unique_id'] != new_container_id or
                            old_components['container_location'] != new_container_location)
        
        location_changed = old_components['widget_location_id'] != new_widget_location_id
        
        # Register new location ID
        self._location_generators.delete_widget_location(old_widget_id)
        self._location_generators.register_widget_location(final_widget_id)
        
        # Handle container and children updates
        # Get current parent container from our mapping
        old_full_container_id = self._widget_to_container.get(old_widget_id)
        
        # Get new container ID
        new_full_container_id = None
        if new_container_id != DEFAULT_ROOT_CONTAINER_ID:
            new_full_container_id = self.registry.get_full_id_from_unique_id(new_container_id)
        if not new_full_container_id:
            new_full_container_id = DEFAULT_ROOT_CONTAINER_ID
        
        # Update container references if container changed
        if container_changed and old_full_container_id:
            # Remove from old container
            old_container_widgets = self._container_to_widgets.get(old_full_container_id) or set()
            old_container_widgets.discard(old_widget_id)
            self._container_to_widgets.add(old_full_container_id, old_container_widgets)
            self._update_container_locations_map(old_full_container_id)
            
            # Add to new container
            new_container_widgets = self._container_to_widgets.get(new_full_container_id) or set()
            new_container_widgets.add(final_widget_id)
            self._container_to_widgets.add(new_full_container_id, new_container_widgets)
            self._update_container_locations_map(new_full_container_id)
        elif old_full_container_id:
            # Just update the ID in the same container
            container_widgets = self._container_to_widgets.get(old_full_container_id) or set()
            container_widgets.discard(old_widget_id)
            container_widgets.add(final_widget_id)
            self._container_to_widgets.add(old_full_container_id, container_widgets)
            self._update_container_locations_map(old_full_container_id)
        
        # Update widget-to-container mapping
        self._widget_to_container.delete(old_widget_id)
        self._widget_to_container.add(final_widget_id, new_full_container_id if container_changed else old_full_container_id)
        
        # If this is a container, update all children
        is_container = ContainerTypeCodes.is_valid_code(type_code)
        if is_container and (container_changed or location_changed):
            # Create old and new container paths for child updates
            old_container_path = get_full_container_path(
                old_components['container_location'], 
                old_components['widget_location_id']
            )
            new_container_path = get_full_container_path(
                new_container_location, 
                new_widget_location_id
            )
            
            # Copy container data to new ID
            if old_widget_id in self._container_to_widgets:
                # Copy the children set to the new ID
                self._container_to_widgets.add(final_widget_id, self._container_to_widgets.get(old_widget_id))
                self._container_locations_map.add(final_widget_id, self._container_locations_map.get(old_widget_id) or {})
                
                # Update all children
                self._update_children_recursively(old_widget_id, final_widget_id, old_container_path, new_container_path)
                
                # Clean up old container entries
                self._container_to_widgets.delete(old_widget_id)
                self._container_locations_map.delete(old_widget_id)
        elif is_container:
            # Just unique ID changed - transfer the container data
            if old_widget_id in self._container_to_widgets:
                # Copy the container data
                self._container_to_widgets.add(final_widget_id, self._container_to_widgets.get(old_widget_id))
                self._container_locations_map.add(final_widget_id, self._container_locations_map.get(old_widget_id) or {})
                
                # Update references to container by all children
                self._update_container_references(old_widget_id, final_widget_id)
                
                # Clean up old data
                self._container_to_widgets.delete(old_widget_id)
                self._container_locations_map.delete(old_widget_id)
        
        # Update any locations map entries
        self._update_locations_map_references(old_widget_id, final_widget_id)
        
        return True, final_widget_id, None
    
    def set_locations_map(self, container_id, locations_map):
        """
        Set the container's locations map.
        
        Args:
            container_id: The container's full ID or unique ID
            locations_map: A dictionary mapping subcontainer locations to widget IDs
        """
        full_container_id = container_id
        if container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in container_id:
            full_container_id = self.registry.get_full_id_from_unique_id(container_id)
            
        if full_container_id:
            self._container_locations_map.add(full_container_id, locations_map.copy())
    
    def get_locations_map(self, container_id):
        """
        Get the container's locations map.
        
        Args:
            container_id: The container's full ID or unique ID
            
        Returns:
            dict: A dictionary mapping subcontainer locations to widget IDs
        """
        full_container_id = container_id
        if container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in container_id:
            full_container_id = self.registry.get_full_id_from_unique_id(container_id)
            
        if full_container_id:
            return self._container_locations_map.get(full_container_id) or {}
        return {}
    
    def get_container_id_from_widget_id(self, widget_id):
        """
        Get the container ID from a widget ID.
        
        Args:
            widget_id: The full widget ID
            
        Returns:
            str: The container's unique ID, or None if invalid
        """
        components = parse_widget_id(widget_id)
        if not components:
            return None
        
        return components['container_unique_id']
    
    def get_widget_ids_by_container_id(self, container_id):
        """
        Get all widget IDs for a specific container.
        
        Args:
            container_id: The container's full ID or unique ID
            
        Returns:
            list: A list of widget IDs in the container
        """
        full_container_id = container_id
        if container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in container_id:
            full_container_id = self.registry.get_full_id_from_unique_id(container_id)
            
        if full_container_id:
            return list(self._container_to_widgets.get(full_container_id) or [])
        return []
    
    def get_widget_ids_by_container_id_and_location(self, container_id, container_location):
        """
        Get all widget IDs for a specific container and location.
        
        Args:
            container_id: The container's full ID or unique ID
            container_location: The container location
            
        Returns:
            list: A list of widget IDs in the container at the specified location
        """
        full_container_id = container_id
        if container_id != DEFAULT_ROOT_CONTAINER_ID and ID_SEPARATOR not in container_id:
            full_container_id = self.registry.get_full_id_from_unique_id(container_id)
            
        if not full_container_id:
            return []
                
        container_widgets = self._container_to_widgets.get(full_container_id) or set()
        
        widgets = []
        for widget_id in container_widgets:
            components = parse_widget_id(widget_id)
            if components and components['container_location'] == container_location:
                widgets.append(widget_id)
        
        return widgets
    
    def clear(self):
        """Clear all widget registrations."""
        self._container_to_widgets._storage.clear()
        self._container_to_widgets._key_log.clear()
        self._container_to_widgets._value_log.clear()
        
        self._widget_to_container._storage.clear()
        self._widget_to_container._key_log.clear()
        self._widget_to_container._value_log.clear()
        
        self._container_locations_map._storage.clear()
        self._container_locations_map._key_log.clear()
        self._container_locations_map._value_log.clear()
    
    # Helper methods
    
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
        
        # Get the container's full widget ID
        container_widget_id = self.registry.get_full_id_from_unique_id(container_id)
        if not container_widget_id:
            return DEFAULT_ROOT_LOCATION
        
        # Parse the container's widget ID
        container_components = parse_widget_id(container_widget_id)
        if not container_components:
            return DEFAULT_ROOT_LOCATION
        
        # Return the full path
        return get_full_container_path(
            container_components['container_location'],
            container_components['widget_location_id']
        )
    
    def _update_container_locations_map(self, container_id):
        """
        Update the container's locations map based on current widget relationships.
        
        Args:
            container_id: The container's full ID
        """
        if not container_id:
            return
            
        container_widgets = self._container_to_widgets.get(container_id)
        if not container_widgets:
            # If container has no widgets, ensure it has an empty map
            self._container_locations_map.add(container_id, {})
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
        self._container_locations_map.add(container_id, location_map)
    
    def _update_children_recursively(self, old_container_id, new_container_id, old_path, new_path):
        """
        Update all children of a container when its ID or location changes.
        
        Args:
            old_container_id: The old container ID
            new_container_id: The new container ID
            old_path: The old container path
            new_path: The new container path
        """
        # Get all children from the old container ID
        children = list(self._container_to_widgets.get(old_container_id) or [])
        
        for child_id in children:
            # Parse the child ID
            components = parse_widget_id(child_id)
            if not components:
                continue
                
            child_type_code = components['type_code']
            child_unique_id = components['unique_id']
            old_container_unique_id = components['container_unique_id']
            old_container_location = components['container_location']
            child_widget_location_id = components['widget_location_id']
            
            # Extract new container unique ID
            new_container_unique_id = get_unique_id_from_id(new_container_id)
            
            # Calculate new container location by replacing the old path prefix with new one
            new_container_location = replace_container_path_prefix(old_container_location, old_path, new_path)
            
            # Create new child ID
            new_child_id = create_widget_id(
                child_type_code,
                child_unique_id,
                new_container_unique_id,
                new_container_location,
                child_widget_location_id
            )
            
            # Update location generator registration
            self._location_generators.delete_widget_location(child_id)
            self._location_generators.register_widget_location(new_child_id)
            
            # Update widget-to-container mapping
            self._widget_to_container.delete(child_id)
            self._widget_to_container.add(new_child_id, new_container_id)
            
            # Update parent container's children list
            container_widgets = self._container_to_widgets.get(new_container_id) or set()
            container_widgets.discard(child_id)
            container_widgets.add(new_child_id)
            self._container_to_widgets.add(new_container_id, container_widgets)
            
            # If this child is a container, recursively update its children
            if ContainerTypeCodes.is_valid_code(child_type_code):
                old_child_path = f"{old_container_location}/{child_widget_location_id}"
                new_child_path = f"{new_container_location}/{child_widget_location_id}"
                
                # First copy container data to new ID
                if child_id in self._container_to_widgets:
                    # Copy container children
                    self._container_to_widgets.add(new_child_id, self._container_to_widgets.get(child_id))
                    
                    # Copy container locations map
                    self._container_locations_map.add(new_child_id, self._container_locations_map.get(child_id) or {})
                    
                    # Recursively update children
                    self._update_children_recursively(child_id, new_child_id, old_child_path, new_child_path)
                    
                    # Clean up old container data
                    self._container_to_widgets.delete(child_id)
                    self._container_locations_map.delete(child_id)
            
            # Notify registry of the ID change
            self.registry.update_all_mappings(child_id, new_child_id)
            
    def _update_container_references(self, old_container_id, new_container_id):
        """
        Update children's references when only the container's unique ID changes.
        
        Args:
            old_container_id: The old container ID
            new_container_id: The new container ID
        """
        children = list(self._container_to_widgets.get(old_container_id) or [])
        new_container_unique_id = get_unique_id_from_id(new_container_id)
        
        for child_id in children:
            components = parse_widget_id(child_id)
            if not components:
                continue
                
            # Just update the container unique ID reference
            new_child_id = create_widget_id(
                components['type_code'],
                components['unique_id'],
                new_container_unique_id,
                components['container_location'],
                components['widget_location_id']
            )
            
            # Update widget-to-container mapping
            self._widget_to_container.delete(child_id)
            self._widget_to_container.add(new_child_id, new_container_id)
            
            # Update parent's children list
            container_widgets = self._container_to_widgets.get(new_container_id) or set()
            container_widgets.discard(child_id)
            container_widgets.add(new_child_id)
            self._container_to_widgets.add(new_container_id, container_widgets)
            
            # If this child is also a container, recursively update its children
            if ContainerTypeCodes.is_valid_code(components['type_code']) and child_id in self._container_to_widgets:
                # Copy container data to new ID
                self._container_to_widgets.add(new_child_id, self._container_to_widgets.get(child_id))
                self._container_locations_map.add(new_child_id, self._container_locations_map.get(child_id) or {})
                
                # Recursively update references for this container's children
                self._update_container_references(child_id, new_child_id)
                
                # Clean up old container data
                self._container_to_widgets.delete(child_id)
                self._container_locations_map.delete(child_id)
            
            # Notify registry of the ID change
            self.registry.update_all_mappings(child_id, new_child_id)
    
    def _update_locations_map_references(self, old_widget_id, new_widget_id):
        """
        Update any locations map entries that reference a widget ID.
        
        Args:
            old_widget_id: The old widget ID to replace
            new_widget_id: The new widget ID to use
        """
        for container_id, locations_map in self._container_locations_map._storage.items():
            updated = False
            
            for location, widget_ids in list(locations_map.items()):
                if isinstance(widget_ids, list):
                    # If it's a list of widget IDs
                    if old_widget_id in widget_ids:
                        locations_map[location] = [new_widget_id if id == old_widget_id else id for id in widget_ids]
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