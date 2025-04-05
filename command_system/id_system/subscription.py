"""
Fixed ID Subscription System for tracking ID changes.

This module provides a subscription system to track changes to specific IDs,
sending notifications when IDs are updated through any method.
"""
from typing import Dict, Callable, List, Tuple, Optional, Set

class IDSubscriptionManager:
    """
    Manages subscriptions to ID changes in the ID registry.
    """
    
    def __init__(self):
        """Initialize the subscription manager."""
        # Map of ID -> list of callbacks
        self._subscriptions: Dict[str, List[Callable[[str, str], None]]] = {}
        
        # Map of object references -> set of subscribed IDs
        # This helps clean up subscriptions when objects are unregistered
        self._object_subscriptions: Dict[str, Set[str]] = {}
        
        # Track current objects that might have ID subscriptions
        self._id_to_object_map: Dict[str, str] = {}
    
    def subscribe(self, component_id: str, callback: Callable[[str, str], None]) -> bool:
        """
        Subscribe to changes for a specific component ID.
        
        Args:
            component_id: ID to monitor for changes
            callback: Function to call when ID changes, receives (old_id, new_id)
            
        Returns:
            True if subscription added, False if component_id doesn't exist
        """
        # Add to subscriptions map
        if component_id not in self._subscriptions:
            self._subscriptions[component_id] = []
        
        self._subscriptions[component_id].append(callback)
        
        # Track this subscription for the object if possible
        object_id = self._id_to_object_map.get(component_id)
        if object_id:
            if object_id not in self._object_subscriptions:
                self._object_subscriptions[object_id] = set()
            self._object_subscriptions[object_id].add(component_id)
        
        return True
    
    def unsubscribe(self, component_id: str, callback: Optional[Callable] = None) -> bool:
        """
        Unsubscribe from changes for a specific component ID.
        
        Args:
            component_id: ID to stop monitoring
            callback: Specific callback to remove, or None to remove all
            
        Returns:
            True if unsubscribed successfully, False if not found
        """
        if component_id not in self._subscriptions:
            return False
            
        if callback is None:
            # Remove all subscriptions for this ID
            del self._subscriptions[component_id]
            
            # Remove from object subscriptions
            object_id = self._id_to_object_map.get(component_id)
            if object_id and object_id in self._object_subscriptions:
                self._object_subscriptions[object_id].discard(component_id)
                if not self._object_subscriptions[object_id]:
                    del self._object_subscriptions[object_id]
            
            return True
        else:
            # Remove specific callback
            if callback in self._subscriptions[component_id]:
                self._subscriptions[component_id].remove(callback)
                
                # If no more callbacks, clean up
                if not self._subscriptions[component_id]:
                    del self._subscriptions[component_id]
                    
                    # Remove from object subscriptions
                    object_id = self._id_to_object_map.get(component_id)
                    if object_id and object_id in self._object_subscriptions:
                        self._object_subscriptions[object_id].discard(component_id)
                        if not self._object_subscriptions[object_id]:
                            del self._object_subscriptions[object_id]
                
                return True
            
            return False
    
    def notify_id_changed(self, old_id: str, new_id: str) -> None:
        """
        Notify subscribers that an ID has changed.
        
        Args:
            old_id: Previous ID
            new_id: New ID
        """
        if old_id in self._subscriptions:
            # Copy the callbacks list to avoid modification during iteration
            callbacks = self._subscriptions[old_id].copy()
            
            # Notify each subscriber
            for callback in callbacks:
                try:
                    callback(old_id, new_id)
                except Exception as e:
                    print(f"Error in ID change callback: {e}")
            
            # Update our tracking
            if new_id != old_id:
                # Get the object ID before we move the subscription
                object_id = self._id_to_object_map.get(old_id)
                
                # Move subscriptions to new ID
                self._subscriptions[new_id] = self._subscriptions[old_id]
                del self._subscriptions[old_id]
                
                # Update object tracking if needed
                if object_id:
                    # Update ID mapping
                    self._id_to_object_map[new_id] = object_id
                    del self._id_to_object_map[old_id]
                    
                    # Update object subscriptions
                    if object_id in self._object_subscriptions:
                        self._object_subscriptions[object_id].discard(old_id)
                        self._object_subscriptions[object_id].add(new_id)
    
    def track_object_id(self, component_id: str, object_id: str) -> None:
        """
        Track an object's ID to help with subscription cleanup.
        
        Args:
            component_id: Component ID
            object_id: Unique identifier for the object
        """
        self._id_to_object_map[component_id] = object_id
        
        # Also make sure the object ID is in the object subscriptions map
        if object_id not in self._object_subscriptions:
            self._object_subscriptions[object_id] = set()
        
        # Ensure this component is tracked for this object
        if component_id in self._subscriptions:
            self._object_subscriptions[object_id].add(component_id)
    
    def object_unregistered(self, object_id: str) -> None:
        """
        Remove all subscriptions for an object when it's unregistered.
        
        Args:
            object_id: Object being unregistered
        """
        # Check if this object ID is tracked before trying to access it
        if object_id in self._object_subscriptions:
            # Get all IDs subscribed by this object
            subscribed_ids = self._object_subscriptions[object_id].copy()
            
            # Remove each subscription
            for component_id in subscribed_ids:
                if component_id in self._subscriptions:
                    del self._subscriptions[component_id]
                if component_id in self._id_to_object_map:
                    del self._id_to_object_map[component_id]
            
            # Clean up object subscriptions
            del self._object_subscriptions[object_id]
    
    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscriptions.clear()
        self._object_subscriptions.clear()
        self._id_to_object_map.clear()