"""
Subscription Manager module.

This module contains the SubscriptionManager class and related functions for
managing subscriptions to ID changes in the ID system.
"""

from command_system.id_system.core.mapping import Mapping

# Global subscription manager instance
_subscription_manager = None

#MARK: - Public subscription API

def subscribe_to_id(component_id, callback):
    """
    Subscribe to changes for a specific component ID.
    
    Args:
        component_id: The component ID to subscribe to
        callback: The callback function that takes old_id and new_id as arguments
        
    Returns:
        bool: True if subscription was successful, False otherwise
    """
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    
    return _subscription_manager.subscribe(component_id, callback)


def unsubscribe_from_id(component_id, callback=None):
    """
    Unsubscribe from changes for a specific component ID.
    
    Args:
        component_id: The component ID to unsubscribe from
        callback: The callback function to unsubscribe, or None to unsubscribe all
        
    Returns:
        bool: True if unsubscription was successful, False otherwise
    """
    global _subscription_manager
    if _subscription_manager is None:
        return False
    
    return _subscription_manager.unsubscribe(component_id, callback)


def clear_subscriptions():
    """
    Clear all ID subscriptions.
    
    Returns:
        bool: True if successful
    """
    global _subscription_manager
    if _subscription_manager is None:
        return True
    
    _subscription_manager.clear()
    return True


def get_subscription_manager():
    """
    Get the global subscription manager instance.
    
    Returns:
        SubscriptionManager: The global subscription manager
    """
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    
    return _subscription_manager


#MARK: - SubscriptionManager class

class SubscriptionManager:
    """
    Manages subscriptions to ID changes in the ID system.
    
    This class handles subscription registration, notification, and cleanup
    for ID changes throughout the system.
    """
    
    def __init__(self):
        """Initialize the subscription manager."""

        
        # Track callbacks to component IDs (for cleanup)
        self._callback_map = {}
        
    def init_mapping(self, registry):
        """
        Initiate the mapping for the subscription manager.

        This method is called when the
        """
        # Use a mapping to track component IDs to sets of callback functions
        self._subscriptions = Mapping(update_keys=True, update_values=False)  
        registry.mappings.append(self._subscriptions)      
        
        
    def subscribe(self, component_id, callback):
        """
        Subscribe to changes for a specific component ID.
        
        Args:
            component_id: The component ID to subscribe to
            callback: The callback function that takes old_id and new_id as arguments
            
        Returns:
            bool: True if subscription was successful, False otherwise
        """
        if not component_id or not callable(callback):
            return False
        
        # Get current subscribers or create new set
        subscribers = self._subscriptions.get(component_id) or set()
        
        # Add the callback to the subscription set
        subscribers.add(callback)
        self._subscriptions.add(component_id, subscribers)
        
        # Track which IDs this callback is subscribed to
        if callback not in self._callback_map:
            self._callback_map[callback] = set()
        
        self._callback_map[callback].add(component_id)
        
        return True
    
    def unsubscribe(self, component_id, callback=None):
        """
        Unsubscribe from changes for a specific component ID.
        
        Args:
            component_id: The component ID to unsubscribe from
            callback: The callback function to unsubscribe, or None to unsubscribe all
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        subscribers = self._subscriptions.get(component_id)
        if not component_id or not subscribers:
            return False
        
        if callback is None:
            # Unsubscribe all callbacks for this ID
            for cb in list(subscribers):
                if cb in self._callback_map:
                    self._callback_map[cb].discard(component_id)
                    
                    # Clean up empty sets
                    if not self._callback_map[cb]:
                        del self._callback_map[cb]
            
            # Remove the subscription set
            self._subscriptions.delete(component_id)
        else:
            # Unsubscribe only the specified callback
            if callback not in subscribers:
                return False
            
            # Remove from subscription set
            subscribers.discard(callback)
            
            # Clean up empty sets
            if not subscribers:
                self._subscriptions.delete(component_id)
            else:
                self._subscriptions.add(component_id, subscribers)
            
            # Remove from callback tracking
            if callback in self._callback_map:
                self._callback_map[callback].discard(component_id)
                
                # Clean up empty sets
                if not self._callback_map[callback]:
                    del self._callback_map[callback]
        
        return True
    
    def notify(self, old_id, new_id):
        """
        Notify subscribers of an ID change.
        
        Args:
            old_id: The old component ID
            new_id: The new component ID
            
        Returns:
            bool: True if notification was successful, False otherwise
        """
        subscribers = self._subscriptions.get(old_id)
        if not old_id or not new_id or not subscribers:
            return False
        
        # Make a copy to avoid modification during iteration
        callbacks = list(subscribers)
        
        # Call all callbacks
        for callback in callbacks:
            try:
                callback(old_id, new_id)
            except Exception as e:
                # Handle or log the error as needed
                print(f"Error in ID change callback: {e}")
        
        # The mapping system will automatically update the key,
        # but we need to ensure the callbacks are properly tracked
        for callback in callbacks:
            if callback in self._callback_map:
                self._callback_map[callback].discard(old_id)
                self._callback_map[callback].add(new_id)
        
        return True
    
    def get_subscribers(self, component_id):
        """
        Get all subscribers for a specific component ID.
        
        Args:
            component_id: The component ID
            
        Returns:
            list: A list of callback functions subscribed to the ID
        """
        subscribers = self._subscriptions.get(component_id)
        if not component_id or not subscribers:
            return []
        
        return list(subscribers)
    
    def clear(self):
        """Clear all subscriptions."""
        self._subscriptions._storage.clear()
        self._subscriptions._key_log.clear()
        self._subscriptions._value_log.clear()
        self._callback_map.clear()
    
    def cleanup_callback(self, callback):
        """
        Clean up all subscriptions for a specific callback.
        
        This is useful when a callback object is being destroyed.
        
        Args:
            callback: The callback function to clean up
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        if not callback or callback not in self._callback_map:
            return False
        
        # Make a copy to avoid modification during iteration
        subscribed_ids = list(self._callback_map[callback])
        
        # Remove from all subscription sets
        for component_id in subscribed_ids:
            subscribers = self._subscriptions.get(component_id)
            if subscribers:
                subscribers.discard(callback)
                
                # Clean up empty sets
                if not subscribers:
                    self._subscriptions.delete(component_id)
                else:
                    self._subscriptions.add(component_id, subscribers)
        
        # Remove from callback tracking
        del self._callback_map[callback]
        
        return True