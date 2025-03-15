from PySide6.QtWidgets import QTabWidget, QTabBar
from PySide6.QtCore import Qt, Signal

from .base_themed_widget import BaseThemedWidget


class ThemedTab(QTabWidget):
    """
    Custom QTabWidget that adapts to the current application theme.
    
    Provides enhanced features such as theme integration, drag-and-drop
    tab reordering, and customizable appearance.
    """
    
    # Signal emitted when a tab is moved
    tab_moved = Signal(int, int)
    
    def __init__(self, parent=None):
        """
        Initialize the themed tab widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Setup tab appearance and behavior
        self.setTabsClosable(False)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.West)  # Set tabs to appear on the left side
        
        # Connect signals
        self.tabBarDoubleClicked.connect(self._handle_tab_double_clicked)
        
        # Connect to the QTabWidget's tabMoved signal
        if hasattr(self, 'tabMoved'):
            self.tabMoved.connect(self._handle_tab_moved)
        
    def _handle_tab_double_clicked(self, index):
        """
        Handle double click on a tab.
        
        Could be used to implement custom behavior like renaming.
        
        Args:
            index: Index of the tab that was double-clicked
        """
        # Placeholder for custom behavior
        pass
        
    def _handle_tab_moved(self, from_index, to_index):
        """
        Handle a tab being moved.
        
        Args:
            from_index: Original index of the tab
            to_index: New index of the tab
        """
        # Emit the tab_moved signal
        self.tab_moved.emit(from_index, to_index)
        
    def set_theme(self, theme_manager):
        """
        Apply theme to the tab widget.
        
        Args:
            theme_manager: Reference to the ThemeManager
        """
        # Store the theme manager reference
        self._theme_manager = theme_manager
        
        # Apply theme to child widgets
        for i in range(self.count()):
            widget = self.widget(i)
            if hasattr(widget, 'apply_theme') and callable(widget.apply_theme):
                widget.apply_theme(theme_manager)
        
    def add_tab_with_icon(self, widget, icon, title):
        """
        Add a tab with an icon.
        
        Args:
            widget: Widget to add as a tab
            icon: Icon to display on the tab
            title: Title of the tab
            
        Returns:
            int: Index of the new tab
        """
        return self.addTab(widget, icon, title)