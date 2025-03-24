"""
Project management components.

This module provides functionality for saving and loading projects,
working with different file formats, and managing project lifecycle.
"""

from .project_manager import ProjectManager, get_project_manager

__all__ = [
    'ProjectManager',
    'get_project_manager'
]