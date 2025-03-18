from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import QObject
from command_system.command_manager import CommandManager


class MenuActionHandler(QObject):
    """
    Handles menu action execution.
    
    Implements handler methods for all menu actions in the application.
    """
    
    def __init__(self, main_window, theme_manager=None, preferences_manager=None):
        """
        Initialize the menu action handler.
        
        Args:
            main_window: Reference to the main application window
            theme_manager: Reference to the ThemeManager
            preferences_manager: Reference to the PreferencesManager
        """
        super().__init__()
        
        # Get command manager
        self._command_manager = CommandManager.instance()
        
        # Get services from command manager if not provided
        if theme_manager is None and self._command_manager:
            from ui.theme.theme_manager import ThemeManager
            theme_manager = self._command_manager.get_service(ThemeManager)
            
        if preferences_manager is None and self._command_manager:
            from utils.preferences_manager import PreferencesManager
            preferences_manager = self._command_manager.get_service(PreferencesManager)
        
        # Store references
        self._main_window = main_window
        self._theme_manager = theme_manager
        self._preferences_manager = preferences_manager
        
        # Dictionary mapping action IDs to handler methods
        self._handlers = {
            # File menu
            "file.new_project": self._new_project,
            "file.open_project": self._open_project,
            "file.close_project": self._close_project,
            "file.save_project": self._save_project,
            "file.save_project_as": self._save_project_as,
            "file.import_signal": self._import_signal,
            "file.export_signal": self._export_signal,
            "file.export_results": self._export_results,
            "file.exit": self._exit_application,
            
            # Edit menu
            "edit.undo": self._undo,
            "edit.redo": self._redo,
            "edit.cut": self._cut,
            "edit.copy": self._copy,
            "edit.paste": self._paste,
            "edit.delete": self._delete,
            "edit.select_all": self._select_all,
            "edit.preferences": self._edit_preferences,
            
            # View menu
            "view.toolbar.main": self._toggle_main_toolbar,
            "view.status_bar": self._toggle_status_bar,
            "view.full_screen": self._toggle_full_screen,
            "view.zoom_in": self._zoom_in,
            "view.zoom_out": self._zoom_out,
            "view.reset_zoom": self._reset_zoom,
            
            # Workspace menu
            "workspace.basic": lambda: self._switch_workspace("basic"),
            "workspace.protocol": lambda: self._switch_workspace("protocol"),
            "workspace.pattern": lambda: self._switch_workspace("pattern"),
            "workspace.separation": lambda: self._switch_workspace("separation"),
            "workspace.origin": lambda: self._switch_workspace("origin"),
            "workspace.advanced": lambda: self._switch_workspace("advanced"),
            "workspace.new_custom": self._new_custom_workspace,
            "workspace.save_layout": self._save_layout,
            "workspace.load_layout": self._load_layout,
            "workspace.manage_layouts": self._manage_layouts,
            
            # Window menu
            "window.new_window": self._new_window,
            "window.cascade": self._cascade_windows,
            "window.tile": self._tile_windows,
            "window.arrange_icons": self._arrange_icons,
            "window.close_all": self._close_all_windows,
            "window.reset_layout": self._reset_layout,
            
            # Tools menu
            "tools.signal_library": self._open_signal_library,
            "tools.protocol_library": self._open_protocol_library,
            "tools.pattern_library": self._open_pattern_library,
            "tools.plugin_manager": self._open_plugin_manager,
            "tools.script_editor": self._open_script_editor,
            "tools.settings": self._open_settings,
            
            # Help menu
            "help.documentation": self._open_documentation,
            "help.quick_start": self._open_quick_start,
            "help.shortcuts": self._open_shortcuts,
            "help.examples": self._open_examples,
            "help.updates": self._check_updates,
            "help.about": self._show_about,
        }
        
        # Add theme handlers dynamically
        if self._theme_manager:
            for theme in self._theme_manager.get_available_themes():
                # Use a factory function to create the correct handler for each theme
                def create_theme_handler(theme_name):
                    return lambda: self._set_theme(theme_name)
                    
                self._handlers[f"view.theme.{theme}"] = create_theme_handler(theme)
        
    def handle_action(self, action_id):
        """
        Handle a menu action being triggered.
        
        Args:
            action_id: Identifier of the triggered action
            
        Returns:
            bool: True if the action was handled, False otherwise
        """
        handler = self._handlers.get(action_id)
        if handler:
            handler()
            return True
        return False
        
    # File menu handlers
    
    def _new_project(self):
        """Create a new project."""
        if self._command_manager:
            from command_system.project import Project
            
            # Check for unsaved changes
            current_project = self._command_manager.get_active_project()
            if current_project and current_project.modified:
                # Ask user to save changes
                result = QMessageBox.question(
                    self._main_window,
                    "Unsaved Changes",
                    "The current project has unsaved changes. Do you want to save them?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                
                if result == QMessageBox.Save:
                    # Save the project
                    self._save_project()
                elif result == QMessageBox.Cancel:
                    # Cancel new project creation
                    return
            
            # Create a new project
            project = Project("Untitled Project")
            project.set_command_manager(self._command_manager)
        
    def _open_project(self):
        """Open an existing project."""
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Open Project",
            "",
            "PySignalDecipher Projects (*.psd);;All Files (*)"
        )
        
        if file_path and self._command_manager:
            from command_system.project import Project
            
            # Load the project
            project = Project.load(file_path, self._command_manager)
            if project:
                # Successful load
                project.set_command_manager(self._command_manager)
            else:
                # Show error
                QMessageBox.critical(
                    self._main_window,
                    "Error Opening Project",
                    "Could not open the project file."
                )
        
    def _close_project(self):
        """Close the current project."""
        if self._command_manager:
            current_project = self._command_manager.get_active_project()
            if current_project and current_project.modified:
                # Ask user to save changes
                result = QMessageBox.question(
                    self._main_window,
                    "Unsaved Changes",
                    "The current project has unsaved changes. Do you want to save them?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                
                if result == QMessageBox.Save:
                    # Save the project
                    self._save_project()
                elif result == QMessageBox.Cancel:
                    # Cancel closing
                    return
                    
            # Create a new empty project
            from command_system.project import Project
            project = Project("Untitled Project")
            project.set_command_manager(self._command_manager)
        
    def _save_project(self):
        """Save the current project."""
        if self._command_manager:
            current_project = self._command_manager.get_active_project()
            if current_project:
                # Check if project has a file path
                # If not, show save as dialog
                if not hasattr(current_project, 'file_path') or not current_project.file_path:
                    self._save_project_as()
                else:
                    # Save to existing path
                    current_project.save(current_project.file_path)
        
    def _save_project_as(self):
        """Save the current project with a new name."""
        if self._command_manager:
            current_project = self._command_manager.get_active_project()
            if current_project:
                # Show save dialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self._main_window,
                    "Save Project As",
                    "",
                    "PySignalDecipher Projects (*.psd);;All Files (*)"
                )
                
                if file_path:
                    # Save project
                    if current_project.save(file_path):
                        # Update window title
                        self._main_window.setWindowTitle(f"PySignalDecipher - {current_project.name}")
                    else:
                        # Show error
                        QMessageBox.critical(
                            self._main_window,
                            "Error Saving Project",
                            "Could not save the project."
                        )
        
    def _import_signal(self):
        """Import signal data from a file."""
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Import Signal",
            "",
            "Signal Files (*.csv *.wav *.dat);;All Files (*)"
        )
        
        if file_path and self._command_manager:
            # Use command to import signal
            from command_system.commands.signal_commands import ImportSignalCommand
            command = ImportSignalCommand(self._command_manager.get_active_project(), file_path)
            self._command_manager.execute_command(command)
        
    def _export_signal(self):
        """Export signal data to a file."""
        # TODO: Implement export signal functionality
        pass
        
    def _export_results(self):
        """Export analysis results to a file."""
        # TODO: Implement export results functionality
        pass
        
    def _exit_application(self):
        """Exit the application."""
        # Check for unsaved changes
        if self._command_manager:
            current_project = self._command_manager.get_active_project()
            if current_project and current_project.modified:
                # Ask user to save changes
                result = QMessageBox.question(
                    self._main_window,
                    "Unsaved Changes",
                    "The current project has unsaved changes. Do you want to save them?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                
                if result == QMessageBox.Save:
                    # Save the project
                    self._save_project()
                elif result == QMessageBox.Cancel:
                    # Cancel exit
                    return
        
        # Quit the application
        QApplication.quit()
        
    # Edit menu handlers
    
    def _undo(self):
        """Undo the last action."""
        if self._command_manager:
            self._command_manager.undo()
        
    def _redo(self):
        """Redo the previously undone action."""
        if self._command_manager:
            self._command_manager.redo()
        
    def _cut(self):
        """Cut the selected content to the clipboard."""
        # Focus widget handles this standard action
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, "cut"):
            focused_widget.cut()
        
    def _copy(self):
        """Copy the selected content to the clipboard."""
        # Focus widget handles this standard action
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, "copy"):
            focused_widget.copy()
        
    def _paste(self):
        """Paste content from the clipboard."""
        # Focus widget handles this standard action
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, "paste"):
            focused_widget.paste()
        
    def _delete(self):
        """Delete the selected content."""
        # Focus widget handles this standard action
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, "clear"):
            focused_widget.clear()
        
    def _select_all(self):
        """Select all content."""
        # Focus widget handles this standard action
        focused_widget = QApplication.focusWidget()
        if focused_widget and hasattr(focused_widget, "selectAll"):
            focused_widget.selectAll()
        
    def _edit_preferences(self):
        """Edit application preferences."""
        # TODO: Implement preference editing
        pass
        
    # View menu handlers
    
    def _toggle_main_toolbar(self):
        """Toggle visibility of the main toolbar."""
        # TODO: Implement toolbar toggle
        pass
        
    def _toggle_status_bar(self):
        """Toggle visibility of the status bar."""
        # Get status bar from main window
        status_bar = self._main_window.statusBar()
        if status_bar:
            status_bar.setVisible(not status_bar.isVisible())
        
    def _set_theme(self, theme):
        """
        Set the application theme.
        
        Args:
            theme: Name of the theme to set
        """
        if self._theme_manager:
            self._theme_manager.set_theme(theme)
        
    def _toggle_full_screen(self):
        """Toggle full screen mode."""
        if self._main_window.isFullScreen():
            self._main_window.showNormal()
        else:
            self._main_window.showFullScreen()
        
    def _zoom_in(self):
        """Zoom in."""
        # TODO: Implement zoom functionality
        pass
        
    def _zoom_out(self):
        """Zoom out."""
        # TODO: Implement zoom functionality
        pass
        
    def _reset_zoom(self):
        """Reset zoom to default level."""
        # TODO: Implement zoom functionality
        pass
        
    # Workspace menu handlers
    
    def _switch_workspace(self, workspace_id):
        """
        Switch to a different workspace.
        
        Args:
            workspace_id: ID of the workspace to switch to
        """
        # Find the tab with the matching workspace ID
        for i in range(self._main_window._tab_widget.count()):
            workspace = self._main_window._tab_widget.widget(i)
            if hasattr(workspace, 'get_workspace_id') and workspace.get_workspace_id() == workspace_id:
                self._main_window._tab_widget.setCurrentIndex(i)
                break
        
    def _new_custom_workspace(self):
        """Create a new custom workspace."""
        # TODO: Implement custom workspace creation
        pass
        
    def _save_layout(self):
        """Save the current workspace layout."""
        # Get current workspace
        current_tab = self._main_window._tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'get_workspace_id') and self._command_manager:
            workspace_id = current_tab.get_workspace_id()
            
            # Use command to save layout
            from command_system.commands.workspace_commands import SaveLayoutCommand
            command = SaveLayoutCommand(
                None,  # Context will be provided by command manager
                workspace_id=workspace_id,
                main_window=current_tab.get_main_window()
            )
            self._command_manager.execute_command(command)
        
    def _load_layout(self):
        """Load a saved workspace layout."""
        # Get current workspace
        current_tab = self._main_window._tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'get_workspace_id') and self._layout_manager:
            workspace_id = current_tab.get_workspace_id()
            
            # Get available layouts
            layouts = self._layout_manager.get_layouts_for_workspace(workspace_id)
            if not layouts:
                QMessageBox.information(
                    self._main_window,
                    "No Layouts",
                    "No saved layouts found for this workspace."
                )
                return
                
            # TODO: Show layout selection dialog
            # For now, just apply the first layout
            layout_id = next(iter(layouts.keys()))
            
            # Apply the layout
            main_window = current_tab.get_main_window()
            if main_window:
                from command_system.commands.workspace_commands import ApplyLayoutCommand
                command = ApplyLayoutCommand(
                    None,  # Context will be provided by command manager
                    workspace_id=workspace_id,
                    layout_id=layout_id,
                    main_window=main_window
                )
                self._command_manager.execute_command(command)

    def _manage_layouts(self):
        """Manage saved workspace layouts."""
        # Get current workspace
        current_tab = self._main_window._tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'get_workspace_id') and self._layout_manager:
            workspace_id = current_tab.get_workspace_id()
            
            # Show layout manager dialog
            from ui.layout_manager import LayoutManagerDialog
            dialog = LayoutManagerDialog(self._main_window, self._layout_manager, workspace_id)
            dialog.exec_()
    
    # Window menu handlers
    
    def _new_window(self):
        """Open a new application window."""
        # TODO: Implement multi-window functionality
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Multi-window functionality is not yet implemented."
        )
    
    def _cascade_windows(self):
        """Arrange windows in a cascading pattern."""
        # This only applies if we have MDI or multi-window
        pass
    
    def _tile_windows(self):
        """Arrange windows in a tiled pattern."""
        # This only applies if we have MDI or multi-window
        pass
    
    def _arrange_icons(self):
        """Arrange minimized window icons."""
        # This only applies if we have MDI or multi-window
        pass
    
    def _close_all_windows(self):
        """Close all windows."""
        # This only applies if we have MDI or multi-window
        pass
    
    def _reset_layout(self):
        """Reset window layout to default."""
        # Get current workspace
        current_tab = self._main_window._tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'get_workspace_id') and self._layout_manager:
            workspace_id = current_tab.get_workspace_id()
            
            # Get default layout
            default_layout = self._layout_manager.get_default_layout(workspace_id)
            if default_layout:
                main_window = current_tab.get_main_window()
                if main_window:
                    # Apply the default layout
                    from command_system.commands.workspace_commands import ApplyLayoutCommand
                    command = ApplyLayoutCommand(
                        None,  # Context will be provided by command manager
                        workspace_id=workspace_id,
                        layout_id=default_layout.id,
                        main_window=main_window
                    )
                    self._command_manager.execute_command(command)
    
    # Tools menu handlers
    
    def _open_signal_library(self):
        """Open the signal library."""
        # TODO: Implement signal library
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Signal library is not yet implemented."
        )
    
    def _open_protocol_library(self):
        """Open the protocol library."""
        # TODO: Implement protocol library
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Protocol library is not yet implemented."
        )
    
    def _open_pattern_library(self):
        """Open the pattern library."""
        # TODO: Implement pattern library
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Pattern library is not yet implemented."
        )
    
    def _open_plugin_manager(self):
        """Open the plugin manager."""
        # TODO: Implement plugin manager
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Plugin manager is not yet implemented."
        )
    
    def _open_script_editor(self):
        """Open the script editor."""
        # TODO: Implement script editor
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Script editor is not yet implemented."
        )
    
    def _open_settings(self):
        """Open the settings dialog."""
        # TODO: Implement settings dialog
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Settings dialog is not yet implemented."
        )
    
    # Help menu handlers
    
    def _open_documentation(self):
        """Open the application documentation."""
        # TODO: Implement documentation viewer
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Documentation viewer is not yet implemented."
        )
    
    def _open_quick_start(self):
        """Open the quick start guide."""
        # TODO: Implement quick start guide
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Quick start guide is not yet implemented."
        )
    
    def _open_shortcuts(self):
        """Open the keyboard shortcuts documentation."""
        # TODO: Implement shortcuts documentation
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Keyboard shortcuts documentation is not yet implemented."
        )
    
    def _open_examples(self):
        """Open the example projects."""
        # TODO: Implement example projects
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Example projects browser is not yet implemented."
        )
    
    def _check_updates(self):
        """Check for application updates."""
        # TODO: Implement update checker
        QMessageBox.information(
            self._main_window,
            "Not Implemented",
            "Update checker is not yet implemented."
        )
    
    def _show_about(self):
        """Show information about the application."""
        QMessageBox.about(
            self._main_window,
            "About PySignalDecipher",
            "<h3>PySignalDecipher</h3>"
            "<p>Version 0.1.0</p>"
            "<p>Advanced Signal Analysis & Protocol Reverse Engineering Platform</p>"
            "<p>© 2023 PySignalDecipher Team</p>"
        )