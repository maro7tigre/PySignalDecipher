pysignaldecipher/
├── __init__.py
├── main.py                    # Application entry point with Service Registry initialization
├── quick_test.py              # Standalone script for rapid device testing
├── assets/                    # Static resources
│   ├── icons/
│   ├── themes/                #  Theme files
│   │   ├── colors/            # Color definitions
│   │   │   ├── dark_colors.json
│   │   │   ├── light_colors.json
│   │   │   └── purple_colors.json
│   │   ├── styles/            # Style definitions
│   │   │   ├── control_styles.json
│   │   │   └── graph_styles.json
│   │   └── qss/               # QSS stylesheets
│   │       └── purple_theme.qss
│   └── defaults/
├── core/                      # Core application logic
│   ├── __init__.py
│   ├── service_registry.py    # Central registry for application services
│   ├── hardware/              # Hardware interface (PyVISA)
│   │   ├── __init__.py
│   │   ├── device_manager.py  # Centralized device management
│   │   ├── oscilloscope.py
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
│   ├── main_window.py         # Main window using Service Registry
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
│   │   ├── themed_slider.py
│   │   └── themed_tab.py      # Themed tab widget
│   ├── utility_panel/         # Utility panel using Service Registry
│   │   ├── __init__.py
│   │   ├── utility_panel.py               # Main container class using Service Registry
│   │   ├── hardware_utility.py            # Uses DeviceManager instead of direct PyVISA
│   │   ├── workspace_utility_manager.py   # Uses Service Registry
│   │   ├── widget_utility_manager.py      # Uses Service Registry
│   │   └── workspace_utilities/           # Folder for workspace-specific utilities
│   │       ├── __init__.py
│   │       ├── base_workspace_utility.py  # Base class using Service Registry
│   │       ├── basic_workspace_utility.py # Basic Signal Analysis workspace utilities
│   │       ├── protocol_workspace_utility.py
│   │       ├── pattern_workspace_utility.py
│   │       └── ...                        # Other workspace utilities
│   ├── widget_utilities/                  # Folder for widget-specific utilities
│   │   ├── __init__.py
│   │   ├── base_widget_utility.py         # Base class for all widget utilities
│   │   ├── signal_view_utility.py         # Utilities for signal view widgets
│   │   ├── spectrum_view_utility.py       # Utilities for spectrum view widgets
│   │   └── ...                            # Other widget utilities
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
│   ├── menus/                 # Menu system
│   │   ├── __init__.py
│   │   ├── menu_manager.py
│   │   ├── menu_actions.py
│   │   ├── file_menu.py
│   │   ├── edit_menu.py
│   │   ├── view_menu.py
│   │   ├── workspace_menu.py
│   │   ├── window_menu.py
│   │   ├── tools_menu.py
│   │   └── help_menu.py
│   └── workspaces/            # Tab-specific UIs
│       ├── __init__.py
│       ├── base_workspace.py  # Base class for all workspaces
│       ├── basic_workspace.py
│       ├── protocol_workspace.py
│       ├── pattern_workspace.py
│       ├── separation_workspace.py
│       ├── origin_workspace.py
│       └── advanced_workspace.py
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
├── development/               # Developer guides
│   ├── coding_standards.md
│   ├── project_planning.md    # Updated to include Service Registry and utilities
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