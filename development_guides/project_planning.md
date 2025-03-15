# PySignalDecipher: Project Planning Document

## 1. Project Development Approach

PySignalDecipher will be developed as a modular, extensible platform that follows modern software engineering principles. This document defines our development approach, including UI/UX guidelines, code organization, and project structure.

### 1.1 Development Philosophy

- **User-Centric Design**: All features should prioritize the engineer's workflow and mental model
- **Progressive Disclosure**: Show simple interfaces by default, reveal complexity as needed
- **Modularity**: Maintain strong separation between system components
- **Testability**: Design components that can be tested in isolation
- **Extensibility**: Enable future additions through plugins and extension points

### 1.2 Technology Stack Confirmation

- **Core Language**: Python 3.9+
- **GUI Framework**: PySide6 (Qt for Python)
- **Hardware Interface**: PyVISA with appropriate backends
- **Signal Processing**: NumPy, SciPy, PyWavelets
- **Data Visualization**: PyQtGraph for performance-critical displays
- **Data Storage**: HDF5 for signal data, JSON for configurations

## 2. UI/UX Design Specifications

### 2.1 Theme System (IMPLEMENTED)

PySignalDecipher implements a comprehensive theming system that allows full customization while providing sensible defaults.

#### 2.1.1 Default Theme

The application uses a dark theme by default, optimized for signal analysis work:

- **Background Colors**: Dark grays (#1E1E1E, #252526, #2D2D30)
- **Text**: Off-white (#E8E8E8) with high contrast for readability
- **Accent Colors**: 
  - Primary: Blue (#007ACC) for selection, focus and primary actions
  - Secondary: Green (#3F9142) for confirmation and success indicators
  - Warning: Amber (#FF8C00) for cautions
  - Error: Red (#E51400) for errors and critical warnings
- **Signal Display**: High-contrast colors for waveforms against dark backgrounds
- **Grid Lines**: Subtle, non-distracting grid lines (#3F3F3F)

#### 2.1.2 Theme System Architecture (IMPLEMENTED)

The theme system has been implemented as a modular, three-tier architecture:

1. **ColorManager**:
   - Loads color schemes from JSON files in `assets/themes/colors/`
   - Provides colors via a path-based API (e.g., `get_color("background.primary")`)
   - Manages active color scheme switching
   - Notifies observers when color schemes change
   - Supports custom color schemes

2. **StyleManager**:
   - Compiles Qt stylesheets using colors from ColorManager
   - Applies styles to the application or specific widgets
   - Manages style preferences and overrides
   - Provides style snippets for different UI components
   - Reacts to color scheme changes

3. **ThemeManager**:
   - Coordinates ColorManager and StyleManager
   - Provides a simplified API for theme operations
   - Acts as a facade for the theme system
   - Handles theme preferences with PreferencesManager

4. **Theme Files**:
   - Color schemes: `assets/themes/colors/dark_colors.json` and `light_colors.json`
   - Style definitions: `assets/themes/styles/control_styles.json` and `graph_styles.json`

5. **Themed Widgets**:
   - Custom widget classes in `ui/themed_widgets/`
   - Automatically adapt to theme changes

#### 2.1.3 Theme System Implementation Notes

- **Signal/Slot Pattern**: Uses Qt's signal/slot mechanism for theme change notifications
- **Observer Pattern**: Components can register as observers for theme changes
- **Path-Based Access**: Colors are accessed using dot notation (e.g., "background.primary")
- **Qt Stylesheets**: Styles are applied using Qt's stylesheet mechanism
- **Preference Persistence**: Theme choices are saved using the PreferencesManager

#### 2.1.4 Theme Customization (PLANNED)

Users will be able to:
- Select from built-in themes (Dark, Light)
- Customize individual theme elements
- Create and save custom themes
- Export themes for sharing and import themes from files

### 2.2 Window Management System (PLANNED)

The application will use a flexible docking system that allows users to arrange tools according to their workflow needs.

#### 2.2.1 Docking Architecture

- Based on Qt's QDockWidget system with enhanced functionality
- Windows can be:
  - Docked (attached to main window or other docks)
  - Floated (as separate windows)
  - Tabbed (stacked within a dock area)
  - Minimized (as tabs in a dock bar)

#### 2.2.2 Layout Management

- **Default Layouts**: Each module (tab) will have sensible default layouts
- **Custom Layouts**: Users can create and save custom layouts
- **Layout Persistence**: Window arrangements are saved between sessions
- **Layout Sharing**: Layouts can be exported and imported

#### 2.2.3 Context-Sensitive Tool Availability

- Tools relevant to the current task are prominently displayed
- Less-used tools can be hidden but easily accessible
- Tool visibility can be toggled through View menu

#### 2.2.4 Implementation Strategy

- Create a LayoutManager class to handle saving/loading layouts
- Use Qt's state saving/restoration mechanism
- Implement custom serialization for complex dock arrangements

## 3. Save/Export/Load/Import System

PySignalDecipher will implement a comprehensive system for saving, loading, and exporting various components.

### 3.1 Project Files

Projects (.psd files) will serve as containers for complete work sessions:

- **Content**: Signals, configurations, analysis results, window layouts
- **Format**: HDF5-based container with JSON metadata
- **Versioning**: Schema versioning for backward compatibility

### 3.2 Component-Specific Files

Individual components can be saved separately for reuse across projects:

| Component | Extension | Description | Format |
|-----------|-----------|-------------|--------|
| Signals | .sigsav | Captured or generated signals with metadata | HDF5 |
| Protocols | .proto | Protocol definitions with parameters | JSON |
| Patterns | .pattern | Signal patterns for recognition | HDF5 + JSON metadata |
| Configs | .sigconf | Device/analysis configurations | JSON |
| Layouts | .layout | Window arrangements | JSON |
| Filters | .filter | Custom signal filters | JSON + Python code |
| Theme | .sigtheme | Custom UI theme | JSON |

### 3.3 Export Formats

For sharing and external use, data can be exported to standard formats.

### 3.4 Import Capabilities

The system will support importing from various sources.

## 4. Project Structure

The project is organized into the following directory structure. Note the modifications (marked with [MODIFIED]) to reflect the implemented theme system and preferences manager:

```
pysignaldecipher/
├── __init__.py
├── main.py                    # Application entry point
├── quick_test.py              # Standalone script for rapid device testing
├── assets/                    # Static resources
│   ├── icons/
│   ├── themes/                # [MODIFIED] Theme files
│   │   ├── colors/            # Color definitions
│   │   │   ├── dark_colors.json
│   │   │   └── light_colors.json
│   │   └── styles/            # Style definitions
│   │       ├── control_styles.json
│   │       └── graph_styles.json
│   └── defaults/
├── core/                      # Core application logic
│   ├── __init__.py
│   ├── hardware/              # Hardware interface (PyVISA)
│   │   ├── __init__.py
│   │   ├── oscilloscope.py
│   │   ├── device_factory.py
│   │   └── drivers/           # Device-specific drivers
│   ├── signal/                # Signal management
│   │   ├── __init__.py
│   │   ├── signal_registry.py
│   │   ├── signal_source.py
│   │   └── signal_data.py
│   ├── processing/            # Signal processing algorithms
│   │   ├── __init__.py
│   │   ├── filters.py
│   │   ├── transforms.py
│   │   ├── measurements.py
│   │   └── mathematics.py
│   ├── protocol/              # Protocol analysis
│   │   ├── __init__.py
│   │   ├── decoder_factory.py
│   │   ├── protocol_base.py
│   │   └── decoders/          # Protocol-specific decoders
│   ├── pattern/               # Pattern recognition
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── matcher.py
│   │   └── pattern_library.py
│   └── workspace/             # Project management
│       ├── __init__.py
│       ├── project.py
│       ├── persistence.py
│       └── history.py
├── ui/                        # User interface
│   ├── __init__.py
│   ├── main_window.py
│   ├── theme/                 # Theme management system
│   │   ├── __init__.py
│   │   ├── color_manager.py   # Color scheme management
│   │   ├── style_manager.py   # Style generation and application
│   │   ├── theme_manager.py   # Coordinates theming system
│   │   └── theme_editor.py    # Theme customization dialog
│   ├── layout_manager.py
│   ├── themed_widgets/        # Theme-aware widgets
│   │   ├── __init__.py
│   │   ├── base_themed_widget.py
│   │   ├── themed_button.py
│   │   ├── themed_label.py
│   │   └── themed_slider.py
│   ├── widgets/               # Custom widgets
│   │   ├── __init__.py
│   │   ├── signal_view.py
│   │   ├── spectrum_view.py
│   │   └── ...
│   ├── dialogs/               # Application dialogs
│   │   ├── __init__.py
│   │   ├── settings_dialog.py
│   │   ├── export_dialog.py
│   │   └── ...
│   └── workspaces/            # Tab-specific UIs
│       ├── __init__.py
│       ├── basic_workspace.py
│       ├── protocol_workspace.py
│       └── ...
├── utils/                     # Utility functions and helpers
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   ├── preferences_manager.py # User preference management
│   └── math_utils.py
└── plugins/                   # Plugin system
    ├── __init__.py
    ├── plugin_manager.py
    ├── extension_points.py
    └── standard/              # Built-in plugins
├── tests/                     # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py            # pytest configuration
│   ├── core/                  # Tests mirroring the core package structure
│   │   ├── hardware/
│   │   ├── signal/
│   │   ├── processing/
│   │   ├── protocol/
│   │   └── pattern/
│   ├── ui/                    # UI tests
│   │   ├── test_theme.py
│   │   └── test_widgets.py
│   ├── integration/           # Cross-module integration tests
│   │   ├── test_workflows.py
│   │   └── test_end_to_end.py
│   └── test_helpers/          # Test utilities and mock objects
│       ├── mock_oscilloscope.py
│       └── sample_signals.py
├── development/           # Developer guides
│   ├── coding_standards.md
│   ├── project_planning.md
│   ├── project_proposal.md
│   └── pyvisa_usage_notes.md
└── docs/                      # Project documentation
    ├── architecture/          # System design docs
    │   ├── system_overview.md
    │   ├── protocol_system.md
    │   └── diagrams/
    ├── user/                  # User documentation
    │   ├── installation.md
    │   ├── quick_start.md
    │   └── tutorials/
    ├── api/                   # API documentation (auto-generated)
    └── assets/                # Documentation assets
```

## 5. Implementation Details

### 5.1 Theme System Implementation Details (IMPLEMENTED)

The theme system is fully implemented and consists of three primary components:

#### 5.1.1 ColorManager

The `ColorManager` (`ui/theme/color_manager.py`) handles color scheme management:

```python
# Example usage
color_manager = ColorManager()
primary_bg = color_manager.get_color("background.primary")  # Returns "#1E1E1E" in dark theme
color_manager.set_active_scheme("light")  # Switch to light theme
```

**Key features**:
- Loads color schemes from JSON files (`dark_colors.json`, `light_colors.json`)
- Provides dot-notation access to nested color values
- Emits signals when color scheme changes
- Supports custom color scheme creation and persistence
- Observer pattern for theme change notifications

#### 5.1.2 StyleManager

The `StyleManager` (`ui/theme/style_manager.py`) generates and applies Qt stylesheets:

```python
# Example usage
style_manager = StyleManager(color_manager)
button_style = style_manager.get_style_sheet("control")  # Get button-specific styles
style_manager.apply_application_style()  # Apply styles to entire application
```

**Key features**:
- Compiles Qt stylesheets using colors from ColorManager
- Provides style snippets for specific UI components
- Applies styles to the application or individual widgets
- Manages style preferences and overrides
- Updates styles in response to color scheme changes

#### 5.1.3 ThemeManager

The `ThemeManager` (`ui/theme/theme_manager.py`) coordinates the theme system:

```python
# Example usage
theme_manager = ThemeManager(color_manager, style_manager, preferences_manager)
theme_manager.set_theme("dark")  # Switch to dark theme
theme_manager.apply_theme()  # Apply the current theme
```

**Key features**:
- Acts as a facade for ColorManager and StyleManager
- Provides a simplified API for theme operations
- Handles theme preferences persistence
- Coordinates theme changes across the application

### 5.2 PreferencesManager Implementation Details (IMPLEMENTED)

The `PreferencesManager` (`utils/preferences_manager.py`) manages user preferences:

```python
# Example usage
preferences_manager = PreferencesManager()
preferences_manager.set_preference("theme/active_theme", "dark")
current_theme = preferences_manager.get_preference("theme/active_theme", "dark")  # Default if not set
preferences_manager.save_window_state(window)  # Save window geometry and state
restored = preferences_manager.restore_window_state(window)  # Restore window geometry and state
```

**Key features**:
- Provides a centralized interface for storing and retrieving preferences
- Uses Qt's QSettings for cross-platform persistence
- Emits signals when preferences change
- Supports preference groups for organization
- Handles window state persistence (geometry, docking arrangement)

## 6. Implementation Phases

The development of PySignalDecipher is organized into clear phases:

### Phase 1: Core Infrastructure (IN PROGRESS)
- ✅ Theme system implementation (COMPLETED)
  - Color management system
  - Style management system
  - Theme coordination and application
- ✅ Preferences management system (COMPLETED)
  - User preference storage and retrieval
  - Window state persistence
- 🔄 Window management framework (IN PROGRESS)
  - Docking system
  - Layout persistence
- ⏳ Signal data model (PLANNED)
- ⏳ Core project structure (PLANNED)

### Phase 2: Basic Functionality (PLANNED)
- Hardware interface base classes
- Signal acquisition from hardware
- Basic signal visualization
- Simple processing operations
- Project save/load functionality

### Phase 3: Advanced Analysis (PLANNED)
- Signal processing algorithms
- Protocol decoding framework
- Pattern recognition basics
- Multiple signal views

### Phase 4: Specialized Features (PLANNED)
- Complex trigger configurations
- Advanced protocol analysis
- Signal separation algorithms
- Pattern library management

### Phase 5: Refinement and Optimization (PLANNED)
- Performance optimizations
- User experience improvements
- Extended file format support
- Advanced reporting

## 7. Developer Reference: Implementing Theme-Aware Components

When developing new UI components for PySignalDecipher, follow these guidelines to ensure proper theme integration:

### 7.1 Using ThemeManager in Components

```python
class MyCustomWidget(QWidget):
    def __init__(self, theme_manager):
        super().__init__()
        self._theme_manager = theme_manager
        
        # Get colors from the theme
        bg_color = self._theme_manager.get_color("background.primary")
        text_color = self._theme_manager.get_color("text.primary")
        
        # Apply initial styling
        self.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
        
        # Connect to theme changes
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_name):
        # Update colors when theme changes
        bg_color = self._theme_manager.get_color("background.primary")
        text_color = self._theme_manager.get_color("text.primary")
        self.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
```

### 7.2 Creating Theme-Aware Widgets

For reusable widgets that need theme awareness, extend from the base themed widget classes:

```python
# Import the base themed widget
from ui.themed_widgets.base_themed_widget import BaseThemedWidget

class MyThemedWidget(BaseThemedWidget):
    def __init__(self, theme_manager):
        super().__init__(theme_manager)
        # Widget-specific initialization
```

### 7.3 Using StyleManager for Custom Styles

For complex components that need specialized styling:

```python
class ComplexWidget(QWidget):
    def __init__(self, style_manager):
        super().__init__()
        self._style_manager = style_manager
        
        # Apply widget-specific styles
        self._style_manager.apply_widget_style(self, "custom_style")
        
        # Register for style updates
        self._style_manager.register_observer("my_widget", self._on_style_updated)
    
    def _on_style_updated(self):
        # Reapply styles when they change
        self._style_manager.apply_widget_style(self, "custom_style")
    
    def __del__(self):
        # Clean up observer registration
        self._style_manager.unregister_observer("my_widget")
```

### 7.4 Using PreferencesManager

For components that need to save/restore state:

```python
class StatefulWidget(QWidget):
    def __init__(self, preferences_manager):
        super().__init__()
        self._preferences_manager = preferences_manager
        
        # Restore widget state
        saved_state = self._preferences_manager.get_preference("widgets/my_widget/state")
        if saved_state:
            self._restore_state(saved_state)
    
    def closeEvent(self, event):
        # Save widget state
        current_state = self._get_current_state()
        self._preferences_manager.set_preference("widgets/my_widget/state", current_state)
        event.accept()
```

## 8. Conclusion

This updated planning document reflects the current state of PySignalDecipher development. The theme system and preferences manager have been successfully implemented, providing a solid foundation for the remaining components. The modular architecture and clear separation of concerns continue to guide development, ensuring maintainability and extensibility as the project grows.

Developers should refer to this document for guidance on the project structure, implementation details of existing components, and guidelines for implementing new features that integrate properly with the established architecture.