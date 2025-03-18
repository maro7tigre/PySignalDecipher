"""
Service access utilities for PySignalDecipher.

This module provides utility functions for accessing application services
through the CommandManager rather than a dedicated ServiceRegistry.
"""

from command_system.command_manager import CommandManager

def get_service(service_type):
    """
    Get a service from the command manager.
    
    Args:
        service_type: Type of service to retrieve
        
    Returns:
        The service instance
        
    Raises:
        KeyError: If the service is not registered
        RuntimeError: If the command manager is not initialized
    """
    command_manager = CommandManager.instance()
    if not command_manager:
        raise RuntimeError("CommandManager not initialized")
    
    return command_manager.get_service(service_type)

def get_service_safe(service_type, default=None):
    """
    Get a service from the command manager, returning a default value if not found.
    
    Args:
        service_type: Type of service to retrieve
        default: Default value to return if service not found
        
    Returns:
        The service instance or default value
    """
    try:
        return get_service(service_type)
    except (KeyError, RuntimeError):
        return default