from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence


class EditMenu:
    """
    Edit menu implementation for the application.
    
    Contains actions for editing operations like undo, redo, cut, copy, paste, etc.
    """
    
    def __init__(self, menu_manager):
        """
        Initialize the edit menu.
        
        Args:
            menu_manager: Reference to the MenuManager
        """
        self._menu_manager = menu_manager
        
        # Create the menu
        self._menu = QMenu("&Edit")
        
        # Initialize actions
        self._initialize_actions()
        
    def _initialize_actions(self):
        """Set up all actions for this menu."""
        # Undo
        undo_action = self._menu_manager.create_action(
            self._menu, "edit.undo", "&Undo",
            shortcut=QKeySequence.Undo,
            status_tip="Undo the last action"
        )
        self._menu.addAction(undo_action)
        
        # Redo
        redo_action = self._menu_manager.create_action(
            self._menu, "edit.redo", "&Redo",
            shortcut=QKeySequence.Redo,
            status_tip="Redo the previously undone action"
        )
        self._menu.addAction(redo_action)
        
        self._menu.addSeparator()
        
        # Cut
        cut_action = self._menu_manager.create_action(
            self._menu, "edit.cut", "Cu&t",
            shortcut=QKeySequence.Cut,
            status_tip="Cut the selected content to the clipboard"
        )
        self._menu.addAction(cut_action)
        
        # Copy
        copy_action = self._menu_manager.create_action(
            self._menu, "edit.copy", "&Copy",
            shortcut=QKeySequence.Copy,
            status_tip="Copy the selected content to the clipboard"
        )
        self._menu.addAction(copy_action)
        
        # Paste
        paste_action = self._menu_manager.create_action(
            self._menu, "edit.paste", "&Paste",
            shortcut=QKeySequence.Paste,
            status_tip="Paste content from the clipboard"
        )
        self._menu.addAction(paste_action)
        
        # Delete
        delete_action = self._menu_manager.create_action(
            self._menu, "edit.delete", "&Delete",
            shortcut=QKeySequence.Delete,
            status_tip="Delete the selected content"
        )
        self._menu.addAction(delete_action)
        
        self._menu.addSeparator()
        
        # Select All
        select_all_action = self._menu_manager.create_action(
            self._menu, "edit.select_all", "Select &All",
            shortcut=QKeySequence.SelectAll,
            status_tip="Select all content"
        )
        self._menu.addAction(select_all_action)
        
        self._menu.addSeparator()
        
        # Preferences
        preferences_action = self._menu_manager.create_action(
            self._menu, "edit.preferences", "&Preferences...",
            status_tip="Edit application preferences"
        )
        self._menu.addAction(preferences_action)
        
    @property
    def menu(self):
        """Get the menu instance."""
        return self._menu