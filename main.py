"""
PySignalDecipher - Advanced Signal Analysis & Protocol Reverse Engineering Platform.

Main entry point for the application.
"""

import sys
from PySide6.QtWidgets import QApplication

# Import core components
from ui.theme.color_manager import ColorManager
from ui.theme.style_manager import StyleManager
from ui.theme.theme_manager import ThemeManager
from utils.preferences_manager import PreferencesManager
from core.hardware.device_manager import DeviceManager
from core.service_registry import ServiceRegistry
from ui.layout_manager import LayoutManager
from ui.docking.dock_manager import DockManager

# Import UI components
from ui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("PySignalDecipher")
    app.setOrganizationName("PySignalDecipher")
    
    # Initialize core services
    color_manager = ColorManager()
    style_manager = StyleManager(color_manager)
    preferences_manager = PreferencesManager()
    theme_manager = ThemeManager(color_manager, style_manager, preferences_manager)
    device_manager = DeviceManager()
    layout_manager = LayoutManager(preferences_manager)
    dock_manager = DockManager(preferences_manager, theme_manager)
    
    # Initialize the service registry
    ServiceRegistry.initialize(
        color_manager=color_manager,
        style_manager=style_manager,
        preferences_manager=preferences_manager,
        theme_manager=theme_manager,
        device_manager=device_manager,
        layout_manager=layout_manager,
        dock_manager=dock_manager
    )
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Apply theme
    theme_manager.apply_theme()
    
    # Start the application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())