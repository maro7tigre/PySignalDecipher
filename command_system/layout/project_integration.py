"""
Integration of layout system with the project manager.

Extends the project manager to save and load layout data with projects.
"""
import os
import json
from typing import Dict, Any, Optional, Tuple

from ..project_manager import get_project_manager
from .layout_manager import get_layout_manager


def save_layout_with_project(filename: str) -> bool:
    """
    Save the current layout with the project file.
    
    This is done by appending a special layout section to the end of the 
    project file. The layout data is stored separately from the main project
    data to avoid affecting the command system.
    
    Args:
        filename: Path to the project file
        
    Returns:
        True if layout was saved successfully
    """
    try:
        # Get layout data
        layout_manager = get_layout_manager()
        layout_data = layout_manager.capture_current_layout()
        
        if not layout_data:
            return False
            
        # Convert to JSON string
        layout_json = json.dumps(layout_data)
        
        # Append to file with a special marker
        with open(filename, 'a', encoding='utf-8') as f:
            f.write("\n__LAYOUT_DATA_BEGIN__\n")
            f.write(layout_json)
            f.write("\n__LAYOUT_DATA_END__\n")
            
        return True
    except Exception as e:
        print(f"Error saving layout with project: {e}")
        return False


def load_layout_from_project(filename: str) -> bool:
    """
    Load and apply layout data from a project file.
    
    Extracts layout data that was appended to the project file
    and applies it to the current UI.
    
    Args:
        filename: Path to the project file
        
    Returns:
        True if layout was loaded and applied successfully
    """
    try:
        # Check if file exists
        if not os.path.exists(filename):
            return False
            
        # Read the file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract layout data
        start_marker = "__LAYOUT_DATA_BEGIN__"
        end_marker = "__LAYOUT_DATA_END__"
        
        start_pos = content.find(start_marker)
        if start_pos == -1:
            return False  # No layout data found
            
        start_pos += len(start_marker)
        end_pos = content.find(end_marker, start_pos)
        
        if end_pos == -1:
            return False  # Incomplete layout data
            
        # Extract and parse layout JSON
        layout_json = content[start_pos:end_pos].strip()
        layout_data = json.loads(layout_json)
        
        # Apply layout
        layout_manager = get_layout_manager()
        return layout_manager.apply_layout(layout_data)
            
    except Exception as e:
        print(f"Error loading layout from project: {e}")
        return False


def extend_project_manager():
    """
    Extend the project manager with layout capabilities.
    
    This function monkey-patches the project manager to add layout
    saving and loading to the project save/load operations.
    """
    # Get the original methods
    project_manager = get_project_manager()
    original_save = project_manager.save_project
    original_load = project_manager.load_project
    
    # Replace with extended versions
    def extended_save_project(model, filename, *args, **kwargs):
        """Extended save_project method with layout support."""
        # First, call the original method
        success = original_save(model, filename, *args, **kwargs)
        
        # If successful, add layout data
        if success:
            save_layout_with_project(filename)
            
        return success
    
    def extended_load_project(filename, *args, **kwargs):
        """Extended load_project method with layout support."""
        # First, call the original method
        model = original_load(filename, *args, **kwargs)
        
        # If successful, apply layout
        if model is not None:
            # Wait until the model has been fully loaded before applying layout
            # This ensures all widgets have been created and registered
            load_layout_from_project(filename)
            
        return model
    
    # Apply monkey patching
    project_manager.save_project = extended_save_project
    project_manager.load_project = extended_load_project
    
    # Add an attribute to indicate extension has been applied
    project_manager._layout_extension_applied = True