"""
Auto-initialization for the command system.

This module is imported when the package is loaded and automatically
sets up various components like layout integration.
"""
import importlib.util


def _initialize_system():
    """
    Automatically initialize the command system components.
    """
    # Check if layout module is available
    if importlib.util.find_spec("command_system.layout") is not None:
        try:
            # Import the layout module first
            from command_system.layout import initialize_layout_integration
            
            # Initialize layout integration
            initialize_layout_integration()
        except Exception as e:
            print(f"Warning: Failed to initialize layout integration: {e}")


# Run initialization
_initialize_system()