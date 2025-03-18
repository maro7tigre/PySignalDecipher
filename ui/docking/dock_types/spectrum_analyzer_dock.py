"""
Spectrum Analyzer Dock for PySignalDecipher.

This dock provides spectrum analysis visualization for signal data.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu, QHBoxLayout, QComboBox, QCheckBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize

from command_system.command_manager import CommandManager
from ..dockable_widget import DockableWidget


class SpectrumAnalyzerDock(DockableWidget):
    """
    Dock widget for displaying spectrum analysis of signals.
    
    Provides real-time or static spectrum analysis with various display options.
    """
    
    # Signal emitted when display settings change
    display_settings_changed = Signal(dict)
    
    def __init__(self, title="Spectrum Analyzer", parent=None, widget_id=None):
        """
        Initialize the spectrum analyzer dock.
        
        Args:
            title: Title for the dock widget
            parent: Parent widget
            widget_id: Unique identifier for this widget
        """
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"spectrum_analyzer_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Initialize spectrum-specific properties
        self._settings = {
            "display_mode": "magnitude",  # magnitude, phase, spectrogram
            "window_type": "hanning",     # hanning, hamming, blackman, etc.
            "scale": "log",               # log, linear
            "fft_size": 1024,             # FFT size
            "show_peak_markers": True,    # Show peak markers
            "averaging": 0,               # 0 = off, otherwise number of frames to average
        }
        
        # Current signal data
        self._signal_data = None
        
        # Access application services through CommandManager
        self._command_manager = CommandManager.instance()
        
        # Get required services
        if self._command_manager:
            try:
                from ui.theme.theme_manager import ThemeManager
                self._theme_manager = self._command_manager.get_service(ThemeManager)
            except Exception as e:
                print(f"Error getting ThemeManager: {e}")
                
            try:
                from utils.preferences_manager import PreferencesManager
                self._preferences_manager = self._command_manager.get_service(PreferencesManager)
            except Exception as e:
                print(f"Error getting PreferencesManager: {e}")
        
        # Set up the content widget
        self._setup_content()
    
    def _setup_content(self):
        """Set up the content widget for the spectrum analyzer."""
        # Create a layout for the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # Display mode selector
        self._display_mode_combo = QComboBox()
        self._display_mode_combo.addItems(["Magnitude", "Phase", "Spectrogram"])
        self._display_mode_combo.setCurrentText("Magnitude")
        self._display_mode_combo.currentTextChanged.connect(self._on_display_mode_changed)
        
        # Scale selector
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["Log", "Linear"])
        self._scale_combo.setCurrentText("Log")
        self._scale_combo.currentTextChanged.connect(self._on_scale_changed)
        
        # Peak markers checkbox
        self._peak_markers_checkbox = QCheckBox("Peak Markers")
        self._peak_markers_checkbox.setChecked(self._settings["show_peak_markers"])
        self._peak_markers_checkbox.stateChanged.connect(self._on_peak_markers_changed)
        
        # Add controls to layout
        controls_layout.addWidget(QLabel("Display:"))
        controls_layout.addWidget(self._display_mode_combo)
        controls_layout.addWidget(QLabel("Scale:"))
        controls_layout.addWidget(self._scale_combo)
        controls_layout.addWidget(self._peak_markers_checkbox)
        controls_layout.addStretch()
        
        # Add controls layout to main layout
        layout.addLayout(controls_layout)
        
        # Add placeholder for spectrum view
        # In a real implementation, this would be a custom spectrum visualization widget
        self._spectrum_view = QLabel("Spectrum Visualization")
        self._spectrum_view.setAlignment(Qt.AlignCenter)
        self._spectrum_view.setStyleSheet("background-color: rgba(0, 0, 0, 0.1); border-radius: 4px;")
        self._spectrum_view.setMinimumHeight(150)
        layout.addWidget(self._spectrum_view, 1)  # 1 = stretch factor
    
    def _on_display_mode_changed(self, mode):
        """
        Handle changes to the display mode.
        
        Args:
            mode: New display mode
        """
        self._settings["display_mode"] = mode.lower()
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _on_scale_changed(self, scale):
        """
        Handle changes to the scale.
        
        Args:
            scale: New scale
        """
        self._settings["scale"] = scale.lower()
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _on_peak_markers_changed(self, state):
        """
        Handle changes to the peak markers setting.
        
        Args:
            state: Qt.CheckState value
        """
        self._settings["show_peak_markers"] = (state == Qt.Checked)
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _update_display(self):
        """Update the spectrum display based on current settings and data."""
        # This would update the spectrum visualization with current settings
        if self._signal_data is not None:
            # In a real implementation, this would update the spectrum view
            self._spectrum_view.setText(f"Spectrum View\n"
                                       f"Mode: {self._settings['display_mode']}\n"
                                       f"Scale: {self._settings['scale']}\n"
                                       f"Peaks: {self._settings['show_peak_markers']}")
    
    def sizeHint(self):
        """
        Provide a size hint for the dock widget.
        
        Returns:
            QSize: Suggested size for the dock
        """
        return QSize(400, 300)
    
    def _add_context_menu_items(self, menu):
        """
        Add dock-specific items to the context menu.
        
        Args:
            menu: Menu to add items to
        """
        # Add a separator before dock-specific actions
        menu.addSeparator()
        
        # Window type submenu
        window_menu = QMenu("Window Type", menu)
        
        for window_type in ["Hanning", "Hamming", "Blackman", "Rectangle", "Kaiser"]:
            action = QAction(window_type, window_menu)
            action.setCheckable(True)
            action.setChecked(self._settings["window_type"].lower() == window_type.lower())
            action.triggered.connect(lambda checked, wt=window_type: self._set_window_type(wt.lower()))
            window_menu.addAction(action)
            
        menu.addMenu(window_menu)
        
        # FFT size submenu
        fft_menu = QMenu("FFT Size", menu)
        
        for fft_size in [256, 512, 1024, 2048, 4096, 8192]:
            action = QAction(str(fft_size), fft_menu)
            action.setCheckable(True)
            action.setChecked(self._settings["fft_size"] == fft_size)
            action.triggered.connect(lambda checked, fs=fft_size: self._set_fft_size(fs))
            fft_menu.addAction(action)
            
        menu.addMenu(fft_menu)
        
        # Averaging submenu
        avg_menu = QMenu("Averaging", menu)
        
        for avg in [0, 2, 4, 8, 16, 32]:
            name = "Off" if avg == 0 else str(avg)
            action = QAction(name, avg_menu)
            action.setCheckable(True)
            action.setChecked(self._settings["averaging"] == avg)
            action.triggered.connect(lambda checked, a=avg: self._set_averaging(a))
            avg_menu.addAction(action)
            
        menu.addMenu(avg_menu)
        
        # Reset action
        menu.addSeparator()
        reset_action = QAction("Reset Settings", menu)
        reset_action.triggered.connect(self._reset_settings)
        menu.addAction(reset_action)
    
    def _set_window_type(self, window_type):
        """
        Set the window type.
        
        Args:
            window_type: New window type
        """
        self._settings["window_type"] = window_type
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _set_fft_size(self, fft_size):
        """
        Set the FFT size.
        
        Args:
            fft_size: New FFT size
        """
        self._settings["fft_size"] = fft_size
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _set_averaging(self, averaging):
        """
        Set the averaging value.
        
        Args:
            averaging: New averaging value
        """
        self._settings["averaging"] = averaging
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def _reset_settings(self):
        """Reset all settings to defaults."""
        self._settings = {
            "display_mode": "magnitude",
            "window_type": "hanning",
            "scale": "log",
            "fft_size": 1024,
            "show_peak_markers": True,
            "averaging": 0,
        }
        
        # Update UI controls
        self._display_mode_combo.setCurrentText("Magnitude")
        self._scale_combo.setCurrentText("Log")
        self._peak_markers_checkbox.setChecked(True)
        
        # Update display
        self.display_settings_changed.emit(self._settings)
        self._update_display()
    
    def set_signal_data(self, data):
        """
        Set signal data for spectrum analysis.
        
        Args:
            data: Signal data (time domain)
        """
        self._signal_data = data
        self._update_display()
    
    def clear(self):
        """Clear the spectrum view."""
        self._signal_data = None
        self._spectrum_view.setText("Spectrum Visualization")
    
    def save_state(self):
        """
        Save the dock state for serialization.
        
        Returns:
            dict: State dictionary
        """
        # Get the base state from the parent class
        state = super().save_state()
        
        # Add dock-specific state
        state["settings"] = self._settings.copy()
        state["dock_type"] = "spectrum_analyzer"  # Important for restoring the dock
        
        return state
    
    def restore_state(self, state):
        """
        Restore the dock state from serialization.
        
        Args:
            state: State dictionary
            
        Returns:
            bool: True if the state was restored successfully
        """
        # Restore the base state from the parent class
        result = super().restore_state(state)
        
        # Restore dock-specific state
        if "settings" in state:
            self._settings.update(state["settings"])
            
            # Update UI controls
            self._display_mode_combo.setCurrentText(self._settings["display_mode"].capitalize())
            self._scale_combo.setCurrentText(self._settings["scale"].capitalize())
            self._peak_markers_checkbox.setChecked(self._settings["show_peak_markers"])
            
            # Update display
            self._update_display()
            
        return result