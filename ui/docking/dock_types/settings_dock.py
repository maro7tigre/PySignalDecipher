"""
Settings Dock for PySignalDecipher.

This dock provides a centralized place for configuring settings for the current workspace.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMenu, QHBoxLayout, 
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QGroupBox, QFormLayout, QPushButton, QGridLayout
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QSize

from ..dockable_widget import DockableWidget
from core.service_registry import ServiceRegistry


class SettingsDock(DockableWidget):
    """
    Dock widget for managing workspace settings.
    
    Provides a central place for configuring workspace-specific settings
    that affect multiple components.
    """
    
    # Signal emitted when settings change
    settings_changed = Signal(str, object)  # setting_name, new_value
    
    def __init__(self, title="Settings", parent=None, widget_id=None):
        """
        Initialize the settings dock.
        
        Args:
            title: Title for the dock widget
            parent: Parent widget
            widget_id: Unique identifier for this widget
        """
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"settings_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Settings categories and values
        self._settings = {
            "display": {
                "grid_visible": True,
                "cursor_snap": True,
                "axis_labels": True,
                "legend_visible": True,
                "theme": "auto"
            },
            "acquisition": {
                "sample_rate": 44100,
                "buffer_size": 1024,
                "trigger_level": 0.5,
                "trigger_mode": "auto",
                "pre_trigger": 0.2
            },
            "analysis": {
                "window_type": "hanning",
                "fft_size": 1024,
                "averaging": 2,
                "scaling": "log"
            }
        }
        
        # Track setting controls to easily update them
        self._setting_controls = {}
        
        # Access application services through ServiceRegistry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._preferences_manager = ServiceRegistry.get_preferences_manager()
        
        # Set up the content widget
        self._setup_content()
    
    def _setup_content(self):
        """Set up the content widget for the settings dock."""
        # Create a layout for the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        
        # Display settings group
        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        
        # Grid visibility
        grid_checkbox = QCheckBox("Show Grid")
        grid_checkbox.setChecked(self._settings["display"]["grid_visible"])
        grid_checkbox.stateChanged.connect(
            lambda state: self._update_setting("display.grid_visible", state == Qt.Checked)
        )
        self._setting_controls["display.grid_visible"] = grid_checkbox
        display_layout.addRow("", grid_checkbox)
        
        # Cursor snap
        snap_checkbox = QCheckBox("Snap Cursor to Data")
        snap_checkbox.setChecked(self._settings["display"]["cursor_snap"])
        snap_checkbox.stateChanged.connect(
            lambda state: self._update_setting("display.cursor_snap", state == Qt.Checked)
        )
        self._setting_controls["display.cursor_snap"] = snap_checkbox
        display_layout.addRow("", snap_checkbox)
        
        # Axis labels
        axis_checkbox = QCheckBox("Show Axis Labels")
        axis_checkbox.setChecked(self._settings["display"]["axis_labels"])
        axis_checkbox.stateChanged.connect(
            lambda state: self._update_setting("display.axis_labels", state == Qt.Checked)
        )
        self._setting_controls["display.axis_labels"] = axis_checkbox
        display_layout.addRow("", axis_checkbox)
        
        # Legend visibility
        legend_checkbox = QCheckBox("Show Legend")
        legend_checkbox.setChecked(self._settings["display"]["legend_visible"])
        legend_checkbox.stateChanged.connect(
            lambda state: self._update_setting("display.legend_visible", state == Qt.Checked)
        )
        self._setting_controls["display.legend_visible"] = legend_checkbox
        display_layout.addRow("", legend_checkbox)
        
        # Theme selection
        theme_combo = QComboBox()
        theme_combo.addItems(["Auto", "Light", "Dark", "Custom"])
        theme_combo.setCurrentText(self._settings["display"]["theme"].capitalize())
        theme_combo.currentTextChanged.connect(
            lambda text: self._update_setting("display.theme", text.lower())
        )
        self._setting_controls["display.theme"] = theme_combo
        display_layout.addRow("Theme:", theme_combo)
        
        # Add display settings to layout
        layout.addWidget(display_group)
        
        # Acquisition settings group
        acq_group = QGroupBox("Acquisition")
        acq_layout = QFormLayout(acq_group)
        
        # Sample rate
        sample_rate_spin = QSpinBox()
        sample_rate_spin.setRange(8000, 192000)
        sample_rate_spin.setSingleStep(1000)
        sample_rate_spin.setSuffix(" Hz")
        sample_rate_spin.setValue(self._settings["acquisition"]["sample_rate"])
        sample_rate_spin.valueChanged.connect(
            lambda value: self._update_setting("acquisition.sample_rate", value)
        )
        self._setting_controls["acquisition.sample_rate"] = sample_rate_spin
        acq_layout.addRow("Sample Rate:", sample_rate_spin)
        
        # Buffer size
        buffer_size_combo = QComboBox()
        buffer_size_combo.addItems(["256", "512", "1024", "2048", "4096", "8192"])
        buffer_size_combo.setCurrentText(str(self._settings["acquisition"]["buffer_size"]))
        buffer_size_combo.currentTextChanged.connect(
            lambda text: self._update_setting("acquisition.buffer_size", int(text))
        )
        self._setting_controls["acquisition.buffer_size"] = buffer_size_combo
        acq_layout.addRow("Buffer Size:", buffer_size_combo)
        
        # Trigger level
        trigger_level_spin = QDoubleSpinBox()
        trigger_level_spin.setRange(0.0, 1.0)
        trigger_level_spin.setSingleStep(0.05)
        trigger_level_spin.setValue(self._settings["acquisition"]["trigger_level"])
        trigger_level_spin.valueChanged.connect(
            lambda value: self._update_setting("acquisition.trigger_level", value)
        )
        self._setting_controls["acquisition.trigger_level"] = trigger_level_spin
        acq_layout.addRow("Trigger Level:", trigger_level_spin)
        
        # Add acquisition settings to layout
        layout.addWidget(acq_group)
        
        # Analysis settings group
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QFormLayout(analysis_group)
        
        # Window type
        window_combo = QComboBox()
        window_combo.addItems(["Hanning", "Hamming", "Blackman", "Rectangle", "Kaiser"])
        window_combo.setCurrentText(self._settings["analysis"]["window_type"].capitalize())
        window_combo.currentTextChanged.connect(
            lambda text: self._update_setting("analysis.window_type", text.lower())
        )
        self._setting_controls["analysis.window_type"] = window_combo
        analysis_layout.addRow("Window Type:", window_combo)
        
        # FFT size
        fft_combo = QComboBox()
        fft_combo.addItems(["256", "512", "1024", "2048", "4096", "8192"])
        fft_combo.setCurrentText(str(self._settings["analysis"]["fft_size"]))
        fft_combo.currentTextChanged.connect(
            lambda text: self._update_setting("analysis.fft_size", int(text))
        )
        self._setting_controls["analysis.fft_size"] = fft_combo
        analysis_layout.addRow("FFT Size:", fft_combo)
        
        # Averaging
        averaging_spin = QSpinBox()
        averaging_spin.setRange(0, 32)
        averaging_spin.setValue(self._settings["analysis"]["averaging"])
        averaging_spin.valueChanged.connect(
            lambda value: self._update_setting("analysis.averaging", value)
        )
        self._setting_controls["analysis.averaging"] = averaging_spin
        analysis_layout.addRow("Averaging:", averaging_spin)
        
        # Scaling
        scaling_combo = QComboBox()
        scaling_combo.addItems(["Log", "Linear"])
        scaling_combo.setCurrentText(self._settings["analysis"]["scaling"].capitalize())
        scaling_combo.currentTextChanged.connect(
            lambda text: self._update_setting("analysis.scaling", text.lower())
        )
        self._setting_controls["analysis.scaling"] = scaling_combo
        analysis_layout.addRow("Scaling:", scaling_combo)
        
        # Add analysis settings to layout
        layout.addWidget(analysis_group)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_button)
        
        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self._apply_settings)
        buttons_layout.addWidget(apply_button)
        
        # Add buttons to layout
        layout.addLayout(buttons_layout)
        
        # Add stretch to push everything to the top
        layout.addStretch(1)
    
    def _update_setting(self, path, value):
        """
        Update a setting value.
        
        Args:
            path: Dot-separated path to the setting (e.g., "display.grid_visible")
            value: New value for the setting
        """
        # Split the path into category and name
        parts = path.split(".")
        if len(parts) == 2:
            category, name = parts
            if category in self._settings and name in self._settings[category]:
                # Update the setting
                self._settings[category][name] = value
                
                # Emit the settings_changed signal
                self.settings_changed.emit(path, value)
    
    def _reset_settings(self):
        """Reset all settings to defaults."""
        # Default settings
        default_settings = {
            "display": {
                "grid_visible": True,
                "cursor_snap": True,
                "axis_labels": True,
                "legend_visible": True,
                "theme": "auto"
            },
            "acquisition": {
                "sample_rate": 44100,
                "buffer_size": 1024,
                "trigger_level": 0.5,
                "trigger_mode": "auto",
                "pre_trigger": 0.2
            },
            "analysis": {
                "window_type": "hanning",
                "fft_size": 1024,
                "averaging": 2,
                "scaling": "log"
            }
        }
        
        # Update settings
        self._settings = default_settings
        
        # Update UI controls
        self._update_controls_from_settings()
        
        # Emit signals for all settings
        for category, settings in self._settings.items():
            for name, value in settings.items():
                self.settings_changed.emit(f"{category}.{name}", value)
    
    def _apply_settings(self):
        """Apply all current settings."""
        # This would apply all settings at once, which might be more efficient
        # than applying them individually as they change
        for category, settings in self._settings.items():
            for name, value in settings.items():
                self.settings_changed.emit(f"{category}.{name}", value)
    
    def _update_controls_from_settings(self):
        """Update all UI controls from the current settings."""
        # Update each control based on the current settings
        for path, control in self._setting_controls.items():
            parts = path.split(".")
            if len(parts) == 2:
                category, name = parts
                if category in self._settings and name in self._settings[category]:
                    value = self._settings[category][name]
                    
                    # Update the control based on its type
                    if isinstance(control, QCheckBox):
                        control.setChecked(value)
                    elif isinstance(control, QComboBox):
                        if isinstance(value, int):
                            control.setCurrentText(str(value))
                        else:
                            control.setCurrentText(str(value).capitalize())
                    elif isinstance(control, QSpinBox) or isinstance(control, QDoubleSpinBox):
                        control.setValue(value)
    
    def get_setting(self, path, default=None):
        """
        Get a setting value.
        
        Args:
            path: Dot-separated path to the setting (e.g., "display.grid_visible")
            default: Default value if the setting doesn't exist
            
        Returns:
            The setting value or the default
        """
        parts = path.split(".")
        if len(parts) == 2:
            category, name = parts
            if category in self._settings and name in self._settings[category]:
                return self._settings[category][name]
        return default
    
    def set_setting(self, path, value):
        """
        Set a setting value.
        
        This updates both the internal setting and the UI control.
        
        Args:
            path: Dot-separated path to the setting (e.g., "display.grid_visible")
            value: New value for the setting
        """
        self._update_setting(path, value)
        
        # Update the control if it exists
        if path in self._setting_controls:
            control = self._setting_controls[path]
            
            # Update the control based on its type
            if isinstance(control, QCheckBox):
                control.setChecked(value)
            elif isinstance(control, QComboBox):
                if isinstance(value, int):
                    control.setCurrentText(str(value))
                else:
                    control.setCurrentText(str(value).capitalize())
            elif isinstance(control, QSpinBox) or isinstance(control, QDoubleSpinBox):
                control.setValue(value)
    
    def sizeHint(self):
        """
        Provide a size hint for the dock widget.
        
        Returns:
            QSize: Suggested size for the dock
        """
        return QSize(300, 500)
    
    def save_state(self):
        """
        Save the dock state for serialization.
        
        Returns:
            dict: State dictionary
        """
        # Get the base state from the parent class
        state = super().save_state()
        
        # Add dock-specific state
        state["settings"] = self._settings
        state["dock_type"] = "settings"  # Important for restoring the dock
        
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
            # Update settings
            for category, settings in state["settings"].items():
                if category in self._settings:
                    self._settings[category].update(settings)
            
            # Update UI controls
            self._update_controls_from_settings()
            
        return result