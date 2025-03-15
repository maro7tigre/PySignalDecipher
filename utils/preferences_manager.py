from typing import Any, Dict, Optional
from PySide6.QtCore import QSettings, QObject, Signal


class PreferencesManager(QObject):
    """
    Manages user preferences across the application.
    
    Provides a centralized interface for storing and retrieving user preferences
    using QSettings, with proper typing and default values.
    """
    
    # Signal emitted when preferences change
    preferences_changed = Signal(str, object)
    
    def __init__(self):
        """Initialize the PreferencesManager."""
        super().__init__()
        
        # Create settings object with organization and application name
        self._settings = QSettings("PySignalDecipher", "PySignalDecipher")
        
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference by key.
        
        Args:
            key: Preference key (e.g., "window/size")
            default: Default value if preference doesn't exist
            
        Returns:
            The preference value, or the default if not found
        """
        return self._settings.value(key, default)
        
    def set_preference(self, key: str, value: Any) -> None:
        """
        Set a user preference.
        
        Args:
            key: Preference key (e.g., "window/size")
            value: Value to store
        """
        self._settings.setValue(key, value)
        self.preferences_changed.emit(key, value)
        
    def has_preference(self, key: str) -> bool:
        """
        Check if a preference exists.
        
        Args:
            key: Preference key to check
            
        Returns:
            True if the preference exists, False otherwise
        """
        return self._settings.contains(key)
        
    def remove_preference(self, key: str) -> None:
        """
        Remove a preference.
        
        Args:
            key: Preference key to remove
        """
        self._settings.remove(key)
        self.preferences_changed.emit(key, None)
        
    def clear_preferences(self) -> None:
        """Clear all preferences."""
        self._settings.clear()
        self.preferences_changed.emit("", None)
        
    def get_group(self, group: str) -> Dict[str, Any]:
        """
        Get all preferences in a group.
        
        Args:
            group: Group prefix (e.g., "window/" for all window preferences)
            
        Returns:
            Dictionary of preference key-value pairs in the group
        """
        result = {}
        self._settings.beginGroup(group)
        keys = self._settings.childKeys()
        for key in keys:
            result[key] = self._settings.value(key)
        self._settings.endGroup()
        return result
        
    def save_window_state(self, window) -> None:
        """
        Save the state of a window.
        
        Args:
            window: Qt window object with saveGeometry() and saveState() methods
        """
        self._settings.setValue("window/geometry", window.saveGeometry())
        self._settings.setValue("window/state", window.saveState())
        
    def restore_window_state(self, window) -> bool:
        """
        Restore the state of a window.
        
        Args:
            window: Qt window object with restoreGeometry() and restoreState() methods
            
        Returns:
            True if the window state was restored, False otherwise
        """
        geometry = self._settings.value("window/geometry")
        state = self._settings.value("window/state")
        
        restored = False
        
        if geometry:
            restored = window.restoreGeometry(geometry) or restored
            
        if state:
            restored = window.restoreState(state) or restored
            
        return restored