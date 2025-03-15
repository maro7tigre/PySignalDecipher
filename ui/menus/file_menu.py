from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence


class FileMenu:
    """
    File menu implementation for the application.
    
    Contains actions for file operations like open, save, import, export, etc.
    """
    
    def __init__(self, menu_manager):
        """
        Initialize the file menu.
        
        Args:
            menu_manager: Reference to the MenuManager
        """
        self._menu_manager = menu_manager
        
        # Create the menu
        self._menu = QMenu("&File")
        
        # Initialize actions
        self._initialize_actions()
        
    def _initialize_actions(self):
        """Set up all actions for this menu."""
        # New Project
        new_action = self._menu_manager.create_action(
            self._menu, "file.new_project", "&New Project...",
            shortcut=QKeySequence.New,
            status_tip="Create a new project"
        )
        self._menu.addAction(new_action)
        
        # Open Project
        open_action = self._menu_manager.create_action(
            self._menu, "file.open_project", "&Open Project...",
            shortcut=QKeySequence.Open,
            status_tip="Open an existing project"
        )
        self._menu.addAction(open_action)
        
        # Close Project
        close_action = self._menu_manager.create_action(
            self._menu, "file.close_project", "&Close Project",
            shortcut=QKeySequence.Close,
            status_tip="Close the current project"
        )
        self._menu.addAction(close_action)
        
        self._menu.addSeparator()
        
        # Save Project
        save_action = self._menu_manager.create_action(
            self._menu, "file.save_project", "&Save Project",
            shortcut=QKeySequence.Save,
            status_tip="Save the current project"
        )
        self._menu.addAction(save_action)
        
        # Save Project As
        save_as_action = self._menu_manager.create_action(
            self._menu, "file.save_project_as", "Save Project &As...",
            shortcut=QKeySequence.SaveAs,
            status_tip="Save the current project with a new name"
        )
        self._menu.addAction(save_as_action)
        
        self._menu.addSeparator()
        
        # Recent Projects submenu
        self._recent_menu = QMenu("&Recent Projects", self._menu)
        self._menu.addMenu(self._recent_menu)
        
        # Placeholder for recent projects - would be populated dynamically
        self._recent_menu.addAction("No recent projects")
        self._recent_menu.actions()[0].setEnabled(False)
        
        self._menu.addSeparator()
        
        # Import Signal
        import_signal_action = self._menu_manager.create_action(
            self._menu, "file.import_signal", "&Import Signal...",
            status_tip="Import signal data from a file"
        )
        self._menu.addAction(import_signal_action)
        
        # Export Signal
        export_signal_action = self._menu_manager.create_action(
            self._menu, "file.export_signal", "&Export Signal...",
            status_tip="Export signal data to a file"
        )
        self._menu.addAction(export_signal_action)
        
        # Export Results
        export_results_action = self._menu_manager.create_action(
            self._menu, "file.export_results", "Export &Results...",
            status_tip="Export analysis results to a file"
        )
        self._menu.addAction(export_results_action)
        
        self._menu.addSeparator()
        
        # Exit
        exit_action = self._menu_manager.create_action(
            self._menu, "file.exit", "E&xit",
            shortcut=QKeySequence.Quit,
            status_tip="Exit the application"
        )
        self._menu.addAction(exit_action)
        
    @property
    def menu(self):
        """Get the menu instance."""
        return self._menu
        
    def update_recent_projects(self, projects):
        """
        Update the list of recent projects in the menu.
        
        Args:
            projects: List of recent project paths
        """
        # Clear existing items
        self._recent_menu.clear()
        
        if not projects:
            # Add a disabled placeholder action
            self._recent_menu.addAction("No recent projects")
            self._recent_menu.actions()[0].setEnabled(False)
            return
            
        # Add each project to the menu
        for i, project in enumerate(projects):
            action = QAction(f"{i + 1}. {project}", self._recent_menu)
            action.triggered.connect(lambda checked=False, p=project: self._open_recent_project(p))
            self._recent_menu.addAction(action)
            
        self._recent_menu.addSeparator()
        
        # Add a "Clear Recent" action
        clear_action = QAction("Clear Recent Projects", self._recent_menu)
        clear_action.triggered.connect(self._clear_recent_projects)
        self._recent_menu.addAction(clear_action)
        
    def _open_recent_project(self, project_path):
        """
        Open a project from the recent projects list.
        
        Args:
            project_path: Path to the project file
        """
        # This would be implemented to open the specified project
        pass
        
    def _clear_recent_projects(self):
        """Clear the list of recent projects."""
        # This would be implemented to clear the recent projects list
        self.update_recent_projects([])