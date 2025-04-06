"""
Manager components for the ID system.

This package contains the manager classes that handle different types of
components in the ID system.
"""

from command_system.id_system.managers.widget_manager import WidgetManager
from command_system.id_system.managers.observable_manager import ObservableManager
from command_system.id_system.managers.subscription_manager import (
    SubscriptionManager,
    subscribe_to_id,
    unsubscribe_from_id,
    clear_subscriptions,
)

__all__ = [
    'WidgetManager',
    'ObservableManager',
    'SubscriptionManager',
    'subscribe_to_id',
    'unsubscribe_from_id',
    'clear_subscriptions',
]