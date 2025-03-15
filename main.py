import sys
from PySide6.QtWidgets import QApplication

from ui.theme.color_manager import ColorManager
from ui.theme.style_manager import StyleManager
from ui.theme.theme_manager import ThemeManager
from utils.preferences_manager import PreferencesManager
from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("PySignalDecipher")
    app.setOrganizationName("PySignalDecipher")
    
    # Create managers
    preferences_manager = PreferencesManager()
    color_manager = ColorManager()
    style_manager = StyleManager(color_manager)
    theme_manager = ThemeManager(color_manager, style_manager, preferences_manager)
    
    # Apply theme preferences
    theme_manager.load_theme_preferences()
    
    # Create and show the main window
    main_window = MainWindow(theme_manager, preferences_manager)
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()