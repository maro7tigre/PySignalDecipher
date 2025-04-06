"""
Subscription Manager module.

This module contains the SubscriptionManager class and related functions for
managing subscriptions to ID changes in the ID system.
"""

from weakref import WeakKeyDictionary

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
        # Maps component IDs to sets of callback functions
        self._subscriptions = {}
        
        # Maps callback functions to sets of component IDs (for cleanup)
        self._callback_to_ids = WeakKeyDictionary()
    
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
        
        # Initialize the subscription set if needed
        if component_id not in self._subscriptions:
            self._subscriptions[component_id] = set()
        
        # Add the callback to the subscription set
        self._subscriptions[component_id].add(callback)
        
        # Track which IDs this callback is subscribed to
        if callback not in self._callback_to_ids:
            self._callback_to_ids[callback] = set()
        
        self._callback_to_ids[callback].add(component_id)
        
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
        if not component_id or component_id not in self._subscriptions:
            return False
        
        if callback is None:
            # Unsubscribe all callbacks for this ID
            for cb in list(self._subscriptions[component_id]):
                if cb in self._callback_to_ids:
                    self._callback_to_ids[cb].discard(component_id)
                    
                    # Clean up empty sets
                    if not self._callback_to_ids[cb]:
                        del self._callback_to_ids[cb]
            
            # Remove the subscription set
            del self._subscriptions[component_id]
        else:
            # Unsubscribe only the specified callback
            if callback not in self._subscriptions[component_id]:
                return False
            
            # Remove from subscription set
            self._subscriptions[component_id].discard(callback)
            
            # Clean up empty sets
            if not self._subscriptions[component_id]:
                del self._subscriptions[component_id]
            
            # Remove from callback tracking
            if callback in self._callback_to_ids:
                self._callback_to_ids[callback].discard(component_id)
                
                # Clean up empty sets
                if not self._callback_to_ids[callback]:
                    del self._callback_to_ids[callback]
        
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
        if not old_id or not new_id or old_id not in self._subscriptions:
            return False
        
        # Make a copy to avoid modification during iteration
        callbacks = list(self._subscriptions[old_id])
        
        # Call all callbacks
        for callback in callbacks:
            try:
                callback(old_id, new_id)
            except Exception as e:
                # Handle or log the error as needed
                print(f"Error in ID change callback: {e}")
        
        # Move subscriptions to the new ID
        self._subscriptions[new_id] = self._subscriptions[old_id]
        del self._subscriptions[old_id]
        
        # Update callback tracking
        for callback in callbacks:
            if callback in self._callback_to_ids:
                self._callback_to_ids[callback].discard(old_id)
                self._callback_to_ids[callback].add(new_id)
        
        return True
    
    def get_subscribers(self, component_id):
        """
        Get all subscribers for a specific component ID.
        
        Args:
            component_id: The component ID
            
        Returns:
            list: A list of callback functions subscribed to the ID
        """
        if not component_id or component_id not in self._subscriptions:
            return []
        
        return list(self._subscriptions[component_id])
    
    def clear(self):
        """Clear all subscriptions."""
        self._subscriptions.clear()
        self._callback_to_ids.clear()
    
    def cleanup_callback(self, callback):
        """
        Clean up all subscriptions for a specific callback.
        
        This is useful when a callback object is being destroyed.
        
        Args:
            callback: The callback function to clean up
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        if not callback or callback not in self._callback_to_ids:
            return False
        
        # Make a copy to avoid modification during iteration
        subscribed_ids = list(self._callback_to_ids[callback])
        
        # Remove from all subscription sets
        for component_id in subscribed_ids:
            if component_id in self._subscriptions:
                self._subscriptions[component_id].discard(callback)
                
                # Clean up empty sets
                if not self._subscriptions[component_id]:
                    del self._subscriptions[component_id]
        
        # Remove from callback tracking
        del self._callback_to_ids[callback]
        
        return True