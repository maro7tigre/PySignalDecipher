"""
PySignalDecipher - Advanced Signal Analysis & Protocol Reverse Engineering Platform.

Main entry point for the application.
"""

import sys
from PySide6.QtWidgets import QApplication

# Import command system
from command_system.command_manager import CommandManager
from command_system.project import Project
from command_system.command import CommandFactory

# Import UI components
from ui.main_window import MainWindow

# Import commands
from command_system.commands import (
    AddSignalCommand, RemoveSignalCommand, RenameSignalCommand,
    ChangeLayoutCommand, SetDockStateCommand, SetWorkspaceSettingCommand,
    RenameProjectCommand, BatchCommand
)
from command_system.commands.workspace_commands import CreateDockCommand, RemoveDockCommand

# Import services that need to be registered
from ui.theme.color_manager import ColorManager
from ui.theme.style_manager import StyleManager
from ui.theme.theme_manager import ThemeManager
from utils.preferences_manager import PreferencesManager
from core.hardware.device_manager import DeviceManager
from ui.layout_manager import LayoutManager
from ui.docking.dock_manager import DockManager


def register_commands(command_manager):
    """
    Register all command types with the command factory.
    
    Args:
        command_manager: CommandManager instance
    """
    # Register command classes
    command_manager.register_command(AddSignalCommand)
    command_manager.register_command(RemoveSignalCommand)
    command_manager.register_command(RenameSignalCommand)
    command_manager.register_command(ChangeLayoutCommand)
    command_manager.register_command(SetDockStateCommand)
    command_manager.register_command(SetWorkspaceSettingCommand)
    command_manager.register_command(RenameProjectCommand)
    command_manager.register_command(BatchCommand)
    command_manager.register_command(CreateDockCommand)
    command_manager.register_command(RemoveDockCommand)


def register_services(command_manager):
    """
    Register all services with the command manager.
    
    Args:
        command_manager: CommandManager instance
    """
    # Initialize core services
    color_manager = ColorManager()
    preferences_manager = PreferencesManager()
    style_manager = StyleManager(color_manager)
    theme_manager = ThemeManager(color_manager, style_manager, preferences_manager)
    device_manager = DeviceManager()
    layout_manager = LayoutManager(preferences_manager)
    dock_manager = DockManager(preferences_manager, theme_manager)
    
    # Register services with command manager
    command_manager.register_service(ColorManager, color_manager)
    command_manager.register_service(StyleManager, style_manager)
    command_manager.register_service(PreferencesManager, preferences_manager)
    command_manager.register_service(ThemeManager, theme_manager)
    command_manager.register_service(DeviceManager, device_manager)
    command_manager.register_service(LayoutManager, layout_manager)
    command_manager.register_service(DockManager, dock_manager)


def main():
    """Main entry point for the application."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("PySignalDecipher")
    app.setOrganizationName("PySignalDecipher")
    
    # Initialize command manager (singleton)
    command_manager = CommandManager.instance()
    
    # Register commands
    register_commands(command_manager)
    
    # Register services
    register_services(command_manager)
    
    # Create initial project
    project = Project("Untitled Project")
    project.set_command_manager(command_manager)
    command_manager.set_active_project(project)
    
    # Create and show main window
    main_window = MainWindow()
    
    # Get theme manager and apply theme
    theme_manager = command_manager.get_service(ThemeManager)
    theme_manager.apply_theme()
    
    # Show the window
    main_window.show()
    
    # Start the application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())