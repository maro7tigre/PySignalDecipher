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
from command_system.id_system.utils.id_operations import (
    update_widget_container,
    update_widget_location,
    find_available_widget_location_id,
)
from command_system.id_system.types import (
    DEFAULT_ROOT_CONTAINER_ID,
    DEFAULT_ROOT_LOCATION,
    CONTAINER_TYPE_CODES,
)

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
                      location=None, widget_location_id=None):
        """
        Register a widget with the manager.
        
        Args:
            widget: The widget object to register
            type_code: The widget type code
            unique_id: The unique ID for the widget
            container_id: The container's unique ID (default: "0")
            location: The container location (default: None, will use root location)
            widget_location_id: The widget's location ID (default: None, will be generated)
            
        Returns:
            str: The generated widget ID
        """
        # Parse container location
        container_location = DEFAULT_ROOT_LOCATION
        if location is not None:
            container_location = location
        
        # Check if we need to generate a widget location ID
        final_widget_location_id = widget_location_id
        if final_widget_location_id is None:
            # Get or create location generator for this container location
            location_gen = self._get_location_generator(container_id, container_location)
            final_widget_location_id = location_gen.generate()
        else:
            # Check if the widget location ID is available
            location_gen = self._get_location_generator(container_id, container_location)
            if location_gen.is_registered(final_widget_location_id):
                # Find an available ID
                final_widget_location_id = find_available_widget_location_id(
                    final_widget_location_id,
                    lambda wlid: location_gen.is_registered(wlid)
                )
            # Register the widget location ID
            location_gen.register(final_widget_location_id)
        
        # Create the widget ID
        widget_id = create_widget_id(
            type_code,
            unique_id,
            container_id,
            container_location,
            final_widget_location_id
        )
        
        # Save the ID mappings
        self._widgets[widget_id] = widget
        self._unique_id_to_widget_id[unique_id] = widget_id
        self._widget_objects_to_id[widget] = widget_id
        
        # Add to the container's widget set
        if container_id not in self._container_to_widgets:
            self._container_to_widgets[container_id] = set()
        self._container_to_widgets[container_id].add(widget_id)
        
        # If this widget is a container, initialize its widgets set and location generator
        if type_code in CONTAINER_TYPE_CODES:
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
        container_id = components['container_unique_id']
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
        if container_id in self._container_to_widgets:
            self._container_to_widgets[container_id].discard(widget_id)
        
        # Unregister from location generator
        if container_id in self._container_location_generators and container_location in self._container_location_generators[container_id]:
            location_gen = self._container_location_generators[container_id][container_location]
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
    
    def update_widget_container(self, widget_id, new_container_id, new_container_location=None):
        """
        Update a widget's container reference.
        
        Args:
            widget_id: The ID of the widget to update
            new_container_id: The new container's unique ID
            new_container_location: The new container's location (default: None, will use root location)
            
        Returns:
            str: The updated widget ID
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
        if old_container_id == new_container_id and (new_container_location is None or old_container_location == new_container_location):
            return widget_id
        
        # Determine the new container location
        final_container_location = new_container_location if new_container_location is not None else DEFAULT_ROOT_LOCATION
        
        # Unregister from old location generator
        if old_container_id in self._container_location_generators and old_container_location in self._container_location_generators[old_container_id]:
            old_location_gen = self._container_location_generators[old_container_id][old_container_location]
            old_location_gen.unregister(widget_location_id)
        
        # Register with new location generator
        new_location_gen = self._get_location_generator(new_container_id, final_container_location)
        
        # Check if the widget location ID is available in the new container
        final_widget_location_id = widget_location_id
        if new_location_gen.is_registered(widget_location_id):
            # Find an available ID
            final_widget_location_id = find_available_widget_location_id(
                widget_location_id,
                lambda wlid: new_location_gen.is_registered(wlid)
            )
        
        # Register the widget location ID
        new_location_gen.register(final_widget_location_id)
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            components['type_code'],
            components['unique_id'],
            new_container_id,
            final_container_location,
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
    
    def update_widget_location(self, widget_id, new_widget_location_id):
        """
        Update a widget's location ID within its container.
        
        Args:
            widget_id: The ID of the widget to update
            new_widget_location_id: The new widget location ID
            
        Returns:
            str: The updated widget ID
        """
        if widget_id not in self._widgets:
            return widget_id
        
        # Extract components
        components = parse_widget_id(widget_id)
        if not components:
            return widget_id
        
        container_id = components['container_unique_id']
        container_location = components['container_location']
        old_widget_location_id = components['widget_location_id']
        
        # If the location ID hasn't changed, no update needed
        if old_widget_location_id == new_widget_location_id:
            return widget_id
        
        # Get the location generator
        location_gen = self._get_location_generator(container_id, container_location)
        
        # Check if the new widget location ID is available
        final_widget_location_id = new_widget_location_id
        if location_gen.is_registered(new_widget_location_id):
            # Find an available ID
            final_widget_location_id = find_available_widget_location_id(
                new_widget_location_id,
                lambda wlid: location_gen.is_registered(wlid)
            )
        
        # Unregister old location ID and register new one
        location_gen.unregister(old_widget_location_id)
        location_gen.register(final_widget_location_id)
        
        # Create the updated widget ID
        new_widget_id = create_widget_id(
            components['type_code'],
            components['unique_id'],
            container_id,
            container_location,
            final_widget_location_id
        )
        
        # Update the mappings
        widget = self._widgets[widget_id]
        self._widgets[new_widget_id] = widget
        self._unique_id_to_widget_id[components['unique_id']] = new_widget_id
        self._widget_objects_to_id[widget] = new_widget_id
        
        # Update container's widget set
        if container_id in self._container_to_widgets:
            self._container_to_widgets[container_id].discard(widget_id)
            self._container_to_widgets[container_id].add(new_widget_id)
        
        # Clean up old widget ID
        if widget_id in self._widgets:
            del self._widgets[widget_id]
        
        return new_widget_id
    
    def update_widget_id(self, old_id, new_id):
        """
        Update a widget's ID and all references to it.
        
        Args:
            old_id: The current widget ID
            new_id: The new widget ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if old_id not in self._widgets:
            return False
        
        # Parse old and new IDs
        old_components = parse_widget_id(old_id)
        new_components = parse_widget_id(new_id)
        
        if not old_components or not new_components:
            return False
        
        old_unique_id = old_components['unique_id']
        new_unique_id = new_components['unique_id']
        
        # Get the widget object
        widget = self._widgets[old_id]
        
        # If it's a container, update all child widgets' container references
        if old_unique_id in self._container_to_widgets:
            # Make a copy to avoid modification during iteration
            child_widgets = list(self._container_to_widgets[old_unique_id])
            
            # Move children to the new container ID
            self._container_to_widgets[new_unique_id] = set(child_widgets)
            
            # Update each child's container reference
            for child_id in child_widgets:
                child_components = parse_widget_id(child_id)
                if child_components:
                    new_child_id = create_widget_id(
                        child_components['type_code'],
                        child_components['unique_id'],
                        new_unique_id,  # New container unique ID
                        child_components['container_location'],
                        child_components['widget_location_id']
                    )
                    
                    # Update mappings for this child
                    child_widget = self._widgets[child_id]
                    self._widgets[new_child_id] = child_widget
                    self._unique_id_to_widget_id[child_components['unique_id']] = new_child_id
                    self._widget_objects_to_id[child_widget] = new_child_id
                    
                    # Remove old child ID
                    if child_id in self._widgets:
                        del self._widgets[child_id]
            
            # Move location generators and location maps
            if old_unique_id in self._container_location_generators:
                self._container_location_generators[new_unique_id] = self._container_location_generators[old_unique_id]
                del self._container_location_generators[old_unique_id]
            
            if old_unique_id in self._container_locations_map:
                self._container_locations_map[new_unique_id] = self._container_locations_map[old_unique_id]
                del self._container_locations_map[old_unique_id]
            
            # Clean up old container data
            if old_unique_id in self._container_to_widgets:
                del self._container_to_widgets[old_unique_id]
        
        # Update container's widget set
        old_container_id = old_components['container_unique_id']
        new_container_id = new_components['container_unique_id']
        
        if old_container_id in self._container_to_widgets:
            self._container_to_widgets[old_container_id].discard(old_id)
        
        if new_container_id not in self._container_to_widgets:
            self._container_to_widgets[new_container_id] = set()
        self._container_to_widgets[new_container_id].add(new_id)
        
        # Update location generator registration
        old_container_location = old_components['container_location']
        old_widget_location_id = old_components['widget_location_id']
        new_container_location = new_components['container_location']
        new_widget_location_id = new_components['widget_location_id']
        
        # Unregister from old location generator
        if old_container_id in self._container_location_generators and old_container_location in self._container_location_generators[old_container_id]:
            old_location_gen = self._container_location_generators[old_container_id][old_container_location]
            old_location_gen.unregister(old_widget_location_id)
        
        # Register with new location generator
        if new_container_id in self._container_location_generators:
            if new_container_location not in self._container_location_generators[new_container_id]:
                self._container_location_generators[new_container_id][new_container_location] = LocationIDGenerator()
            
            new_location_gen = self._container_location_generators[new_container_id][new_container_location]
            new_location_gen.register(new_widget_location_id)
        
        # Update mappings
        self._widgets[new_id] = widget
        self._unique_id_to_widget_id[new_unique_id] = new_id
        self._widget_objects_to_id[widget] = new_id
        
        # Remove old ID
        if old_id in self._widgets:
            del self._widgets[old_id]
        if old_unique_id in self._unique_id_to_widget_id:
            del self._unique_id_to_widget_id[old_unique_id]
        
        return True
    
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