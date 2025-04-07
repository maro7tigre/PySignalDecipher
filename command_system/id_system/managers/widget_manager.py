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
    
    def __init__(self):
        """Initialize the widget manager."""
        # Maps widget IDs to widget objects
        self._widgets = {}
        
        # Maps widget unique IDs to full widget IDs
        self._unique_id_to_widget_id = {}
        
        # Maps widgets to their widget IDs
        self._widget_objects_to_id = weakref.WeakKeyDictionary()
        
        # Maps container unique IDs to sets of widget IDs contained by them
        self._container_to_widgets = {}
        
        # Maps container unique IDs to location generators
        self._container_location_generators = {}
        
        # Maps container unique IDs to location maps (subcontainer location to widget ID)
        self._container_locations_map = {}
        
        # Callback for widget unregistration
        self._on_widget_unregister = None
    
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
        if container_unique_id == DEFAULT_ROOT_CONTAINER_ID:
            # For root container (no container)
            container_location = DEFAULT_ROOT_LOCATION
        else:
            # Get the container's location from its ID
            container_widget_id = self._unique_id_to_widget_id.get(container_unique_id)
            if container_widget_id:
                container_components = parse_widget_id(container_widget_id)
                if container_components:
                    # Use the container's full path
                    container_loc = container_components['container_location']
                    container_widget_loc = container_components['widget_location_id']
                    
                    # Construct the proper path including the parent's location
                    container_location = f"{container_loc}{PATH_SEPARATOR}{container_widget_loc}"
                else:
                    container_location = DEFAULT_ROOT_LOCATION
            else:
                container_location = DEFAULT_ROOT_LOCATION
        
        # Get the location generator for this container path
        location_gen = self._get_location_generator(container_unique_id, container_location)
        
        # Determine widget_location_id
        widget_location_id = location
        if widget_location_id is None:
            # Generate a new widget_location_id
            widget_location_id = location_gen.generate()
        else:
            # Check if the widget_location_id is available
            if location_gen.is_registered(widget_location_id):
                raise IDRegistrationError(f"Widget location ID '{widget_location_id}' already exists in container location '{container_location}'")
            
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
        
        # If this widget is a container, initialize its widgets set and location generator
        if ContainerTypeCodes.is_valid_code(type_code):
            self._container_to_widgets[unique_id] = set()
            self._container_location_generators[unique_id] = {}
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
        
        # Call the unregister callback if set
        if self._on_widget_unregister:
            self._on_widget_unregister(widget_id, widget)
        
        # If it's a container, handle its children
        if unique_id in self._container_to_widgets:
            # Make a copy to avoid modification during iteration
            child_widgets = list(self._container_to_widgets[unique_id])
            for child_id in child_widgets:
                # Unregister all child widgets
                self.unregister_widget(child_id)
            
            # Clean up container data
            if unique_id in self._container_to_widgets:
                del self._container_to_widgets[unique_id]
            if unique_id in self._container_location_generators:
                del self._container_location_generators[unique_id]
            if unique_id in self._container_locations_map:
                del self._container_locations_map[unique_id]
        
        # Remove from container's widgets set
        if container_unique_id in self._container_to_widgets:
            self._container_to_widgets[container_unique_id].discard(widget_id)
        
        # Unregister from location generator
        if container_unique_id in self._container_location_generators and container_location in self._container_location_generators[container_unique_id]:
            location_gen = self._container_location_generators[container_unique_id][container_location]
            location_gen.unregister(widget_location_id)
        
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
        
        # If the container hasn't changed, no update needed
        if old_container_id == new_container_id:
            return widget_id
        
        # Unregister from old location generator
        if old_container_id in self._container_location_generators and old_container_location in self._container_location_generators[old_container_id]:
            old_location_gen = self._container_location_generators[old_container_id][old_container_location]
            old_location_gen.unregister(widget_location_id)
        
        # Determine the new container location based on container
        if new_container_id == DEFAULT_ROOT_CONTAINER_ID:
            # For root container (no container)
            new_container_location = DEFAULT_ROOT_LOCATION
        else:
            # Get the container's location from its ID
            container_widget_id = self._unique_id_to_widget_id.get(new_container_id)
            if container_widget_id:
                container_components = parse_widget_id(container_widget_id)
                if container_components:
                    # Use the container's full path
                    container_loc = container_components['container_location']
                    container_widget_loc = container_components['widget_location_id']
                    
                    # Construct the proper path including the parent's location
                    new_container_location = f"{container_loc}{PATH_SEPARATOR}{container_widget_loc}"
                else:
                    new_container_location = DEFAULT_ROOT_LOCATION
            else:
                new_container_location = DEFAULT_ROOT_LOCATION
        
        # Get the location generator for the new container path
        new_location_gen = self._get_location_generator(new_container_id, new_container_location)
        
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
            components['type_code'],
            components['unique_id'],
            new_container_id,
            new_container_location,
            final_widget_location_id
        )
        
        # Update the mappings
        widget = self._widgets[widget_id]
        self._widgets[new_widget_id] = widget
        self._unique_id_to_widget_id[components['unique_id']] = new_widget_id
        self._widget_objects_to_id[widget] = new_widget_id
        
        # Remove from old container's widget set
        if old_container_id in self._container_to_widgets:
            self._container_to_widgets[old_container_id].discard(widget_id)
        
        # Add to new container's widget set
        if new_container_id not in self._container_to_widgets:
            self._container_to_widgets[new_container_id] = set()
        self._container_to_widgets[new_container_id].add(new_widget_id)
        
        # Clean up old widget ID
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
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
        
        container_unique_id = components['container_unique_id']
        container_location = components['container_location']
        old_widget_location_id = components['widget_location_id']
        
        # If the widget_location_id hasn't changed, return original ID
        if new_location == old_widget_location_id:
            return widget_id
        
        # Get the location generator
        location_gen = self._get_location_generator(container_unique_id, container_location)
        
        # Unregister from old location
        location_gen.unregister(old_widget_location_id)
        
        # Check if the new widget_location_id is available
        if location_gen.is_registered(new_location):
            raise IDRegistrationError(f"Widget location ID '{new_location}' already exists in container location '{container_location}'")
        
        # Register the new widget_location_id
        location_gen.register(new_location)
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            components['type_code'],
            components['unique_id'],
            container_unique_id,
            container_location,
            new_location
        )
        
        # Update the mappings
        widget = self._widgets[widget_id]
        self._widgets[new_widget_id] = widget
        self._unique_id_to_widget_id[components['unique_id']] = new_widget_id
        self._widget_objects_to_id[widget] = new_widget_id
        
        # Update container's widget set
        if container_unique_id in self._container_to_widgets:
            self._container_to_widgets[container_unique_id].discard(widget_id)
            self._container_to_widgets[container_unique_id].add(new_widget_id)
        
        # Clean up old widget ID
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
        return new_widget_id
    
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
    
    def _get_location_generator(self, container_id, container_location):
        """
        Get or create a location generator for a specific container location.
        
        Args:
            container_id: The container's unique ID
            container_location: The container location
            
        Returns:
            LocationIDGenerator: The location generator
        """
        if container_id not in self._container_location_generators:
            self._container_location_generators[container_id] = {}
        
        if container_location not in self._container_location_generators[container_id]:
            self._container_location_generators[container_id][container_location] = LocationIDGenerator()
        
        return self._container_location_generators[container_id][container_location]
    
    def set_on_widget_unregister(self, callback):
        """
        Set the callback for widget unregistration.
        
        Args:
            callback: The callback function that takes widget_id and widget as arguments
        """
        self._on_widget_unregister = callback
    
    def clear(self):
        """Clear all widget registrations."""
        self._widgets.clear()
        self._unique_id_to_widget_id.clear()
        self._widget_objects_to_id.clear()
        self._container_to_widgets.clear()
        self._container_location_generators.clear()
        self._container_locations_map.clear()