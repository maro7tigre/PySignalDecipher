"""
Integration of layout system with the project manager.

Extends the project manager to save and load layout data with projects.
"""
import os
import json
from typing import Dict, Any, Optional, Tuple

from ..project.project_manager import get_project_manager
from .layout_manager import get_layout_manager


def save_layout_with_project(filename: str) -> bool:
    """
    Save the current layout with a project file.
    
    Args:
        filename: Project filename
        
    Returns:
        True if saved successfully
    """
    layout_manager = get_layout_manager()
    
    try:
        # Get current layout
        layout_data = layout_manager.capture_current_layout()
        
        # Convert to JSON
        layout_json = json.dumps(layout_data)
        
        # Check if file exists
        if not os.path.exists(filename):
            return False
            
        # Read existing file content
        with open(filename, 'r') as f:
            content = f.read()
            
        # Check if file already has layout section
        start_marker = "__LAYOUT_DATA_BEGIN__"
        end_marker = "__LAYOUT_DATA_END__"
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos >= 0 and end_pos >= 0:
            # Replace existing layout section
            before = content[:start_pos]
            after = content[end_pos + len(end_marker):]
            new_content = before + start_marker + "\n" + layout_json + "\n" + end_marker + after
        else:
            # Append layout section
            new_content = content + "\n\n" + start_marker + "\n" + layout_json + "\n" + end_marker + "\n"
            
        # Write updated content
        with open(filename, 'w') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"Error saving layout with project: {e}")
        return False


def load_layout_from_project(filename: str) -> bool:
    """
    Load layout from a project file.
    
    Args:
        filename: Project filename
        
    Returns:
        True if loaded successfully
    """
    layout_manager = get_layout_manager()
    
    try:
        # Check if file exists
        if not os.path.exists(filename):
            return False
            
        # Read file content
        with open(filename, 'r') as f:
            content = f.read()
            
        # Extract layout section
        start_marker = "__LAYOUT_DATA_BEGIN__"
        end_marker = "__LAYOUT_DATA_END__"
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos < 0 or end_pos < 0 or start_pos >= end_pos:
            # No valid layout section found
            return False
            
        # Extract layout JSON
        layout_json = content[start_pos + len(start_marker):end_pos].strip()
        
        # Parse layout data
        layout_data = json.loads(layout_json)
        
        # Apply layout
        return layout_manager.apply_layout(layout_data)
    except Exception as e:
        print(f"Error loading layout from project: {e}")
        return False


def initialize_layout_integration():
    """
    Initialize integration between layout system and project manager.
    
    Registers layout save/load handlers with the project manager.
    """
    project_manager = get_project_manager()
    
    # Register layout handlers
    project_manager.register_layout_handlers(
        save_layout_with_project,
        load_layout_from_project
    )
    
    # Enable layout saving by default
    project_manager.set_save_layouts(True)
    
    print("Layout integration initialized")


# For backward compatibility
def extend_project_manager():
    """
    Extend the project manager with layout capabilities.
    
    This is now just a wrapper around initialize_layout_integration 
    for backward compatibility.
    """
    initialize_layout_integration()