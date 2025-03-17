# PySignalDecipher Dock Types Package
"""
This package contains all dock widget types for the application.

To create a new dock type:
1. Create a new Python file in this directory
2. Define a class that extends DockableWidget from ..dockable_widget
3. Implement the required methods (see dock_template.py for a template)

The dock will be automatically discovered and registered with the DockManager
at application startup.
"""

# This package is intentionally empty to allow dynamic discovery of dock types