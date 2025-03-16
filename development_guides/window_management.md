# Window Management Framework for PySignalDecipher

## Overview

The Window Management Framework provides a flexible docking system that allows users to arrange tools according to their workflow needs. This implementation follows Qt's docking paradigm while adding specialized functionality for signal analysis workspaces.

## Key Components

### 1. LayoutManager (`ui/layout_manager.py`)
- Manages workspace layouts
- Handles saving and loading layout configurations
- Maintains default layouts for each workspace type
- Provides layout serialization/deserialization

### 2. DockableWidget Base Class (`ui/docking/dockable_widget.py`)
- Extends Qt's QDockWidget with theme support
- Implements state persistence
- Provides context menu integration
- Handles serialization for state saving

### 3. DockManager (`ui/docking/dock_manager.py`)
- Central management of dock widgets
- Coordinates dock creation and registration
- Handles workspace-specific dock arrangements
- Manages dock persistence

### 4. SignalViewDock Example (`ui/docking/signal_view_dock.py`)
- Example implementation of a dockable signal view
- Shows context menu customization
- Demonstrates state persistence

### 5. Workspace Integration
- Each workspace contains an internal QMainWindow for docking
- Provides context menu for adding dock widgets
- Supports loading/saving layouts

## Usage Example

```python
# Creating a dock widget in a workspace
signal_view = self._dock_manager.create_dock(
    self.get_workspace_id(),
    "signal_view",  # Registered dock type
    title="Time Domain",
    area=Qt.TopDockWidgetArea
)

# Saving the current layout
self._layout_manager.create_layout(
    self.get_workspace_id(),
    "My Custom Layout",
    self._main_window
)

# Applying a saved layout
self._layout_manager.apply_layout(
    self.get_workspace_id(),
    layout_id,
    self._main_window
)
```

## Implementation Details

### Dock Behavior

1. **Docking Areas**: Docks can be placed in top, bottom, left, or right areas
2. **Tabbing**: Multiple docks in the same area can be tabbed together
3. **Floating**: Docks can be detached into floating windows
4. **Persistence**: Dock states (position, size, visibility) are saved with layouts

### Layout Serialization

Layouts are serialized to JSON files with:
- Window state (encoded in Base64)
- Individual dock configurations
- Metadata (workspace type, name, default status)

### Workspace Integration

Each workspace tab contains its own QMainWindow with:
- Central widget for primary content
- Dock widget areas around the central widget
- Context menu for dock and layout management

## Getting Started

1. **Initialize Components**: 
   - Create LayoutManager and DockManager
   - Register them with ServiceRegistry

2. **Register Dock Types**:
   - Register custom dock widget types with DockManager

3. **Create Default Layouts**:
   - Define default layouts for each workspace type

4. **Workspace Setup**:
   - Integrate LayoutManager and DockManager with workspaces
   - Handle context menus for dock creation