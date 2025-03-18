from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .base_workspace import BaseWorkspace


class BasicSignalWorkspace(BaseWorkspace):
    """
    Workspace for basic signal analysis.
    
    Provides tools for visualizing and analyzing signal data with fundamental
    signal processing operations.
    """
    
    def __init__(self, command_manager=None, parent=None):
        """
        Initialize the basic signal workspace.
        
        Args:
            command_manager: CommandManager instance
            parent: Parent widget
        """
        super().__init__(command_manager, parent)
        
    def _initialize_workspace(self):
        """
        Initialize the workspace components.
        
        Implementation of the method from BaseWorkspace.
        """
        # Set up the central widget layout with a placeholder
        label = QLabel("Basic Signal Analysis Workspace")
        label.setAlignment(Qt.AlignCenter)
        self._central_layout.addWidget(label)
        
        # Create a splitter for the main view
        splitter = QSplitter(Qt.Horizontal)
        self._central_layout.addWidget(splitter)
        
        # Add placeholder widgets for the splitter sections
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_label = QLabel("Signal List")
        left_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(left_label)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_label = QLabel("Main Workspace Area\n\nRight-click to add dock widgets")
        right_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(right_label)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
    def get_workspace_id(self):
        """
        Get the unique identifier for this workspace.
        
        Implementation of the method from BaseWorkspace.
        
        Returns:
            str: Unique ID for this workspace
        """
        return "basic"
        
    def populate_default_docks(self):
        """
        Populate the workspace with default dock widgets.
        
        This is called when a new workspace is created or when the user
        resets the workspace to defaults.
        """
        if not self._dock_manager:
            return
            
        # Create a time domain signal view
        time_view = self._dock_manager.create_dock(
            self.get_workspace_id(),
            "signal_view",
            title="Time Domain",
            area=Qt.TopDockWidgetArea
        )
        
        # Create a frequency domain signal view
        freq_view = self._dock_manager.create_dock(
            self.get_workspace_id(),
            "signal_view", 
            title="Frequency Domain",
            area=Qt.BottomDockWidgetArea
        )
        
        if freq_view and hasattr(freq_view, '_set_display_mode'):
            # Configure as frequency domain view
            freq_view._set_display_mode("frequency")