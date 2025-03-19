# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QFormLayout, QPushButton, QSlider, QGroupBox, QFileDialog, QMessageBox,
    QStatusBar, QToolBar, QColorDialog
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QAction, QColor

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from command_system import (
    get_command_manager,
    Command, CompoundCommand,
    Observable, ObservableProperty,
    PropertyBinder, DockManager,
    SignalData, SignalDataManager
)

# ========== Model Classes ==========

class UtilitySettings(Observable):
    """Settings for the utility panel"""
    title = ObservableProperty(default="Utility Panel")
    alpha = ObservableProperty(default=1.0)
    beta = ObservableProperty(default=5)
    enabled = ObservableProperty(default=True)
    view_mode = ObservableProperty(default=0)  # 0: Simple, 1: Advanced, 2: Expert


class DockSettings(Observable):
    """Base settings for dock widgets"""
    name = ObservableProperty(default="Dock")
    enabled = ObservableProperty(default=True)
    color = ObservableProperty(default="#3498db")  # Default blue


class PlotSettings(DockSettings):
    """Settings for the plot dock"""
    amplitude = ObservableProperty(default=1.0)
    frequency = ObservableProperty(default=1.0)
    phase = ObservableProperty(default=0.0)
    plot_type = ObservableProperty(default=0)  # 0: Line, 1: Scatter, 2: Bar


class FilterSettings(DockSettings):
    """Settings for the filter dock"""
    cutoff = ObservableProperty(default=1000)
    order = ObservableProperty(default=4)
    filter_type = ObservableProperty(default=0)  # 0: Lowpass, 1: Highpass, 2: Bandpass
    ripple = ObservableProperty(default=0.5)


class AnalysisSettings(DockSettings):
    """Settings for the analysis dock"""
    window_size = ObservableProperty(default=1024)
    overlap = ObservableProperty(default=50)
    method = ObservableProperty(default=0)  # 0: FFT, 1: Welch, 2: Wavelet
    scaling = ObservableProperty(default=0)  # 0: Linear, 1: Log


# ========== Command Classes ==========

class CreateDockCommand(Command):
    """Command to create a dock widget"""
    
    def __init__(self, main_window, dock_id, dock_title, settings):
        super().__init__()
        self.main_window = main_window
        self.dock_id = dock_id
        self.dock_title = dock_title
        self.settings = settings
        self.dock_widget = None
        self.dock_area = Qt.RightDockWidgetArea
        
    def execute(self):
        if self.dock_widget is None:
            # Create the dock widget
            self.dock_widget = QDockWidget(self.dock_title, self.main_window)
            self.dock_widget.setObjectName(self.dock_id)
            self.dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
            
            # Create content based on settings type
            content_widget = QWidget()
            layout = QVBoxLayout(content_widget)
            
            form_layout = QFormLayout()
            layout.addLayout(form_layout)
            
            # Add common settings
            name_edit = QLineEdit(self.settings.name)
            enabled_check = QCheckBox()
            enabled_check.setChecked(self.settings.enabled)
            
            form_layout.addRow("Name:", name_edit)
            form_layout.addRow("Enabled:", enabled_check)
            
            # Add color button
            color_button = QPushButton()
            color_button.setMinimumSize(24, 24)
            color_button.setStyleSheet(f"background-color: {self.settings.color};")
            
            def update_color_button():
                color_button.setStyleSheet(f"background-color: {self.settings.color};")
                
            def pick_color():
                color = QColorDialog.getColor(QColor(self.settings.color))
                if color.isValid():
                    cmd = PropertyCommand(self.settings, "color", color.name())
                    get_command_manager().execute(cmd)
                    
            color_button.clicked.connect(pick_color)
            self.settings.add_property_observer("color", lambda _, __, ___: update_color_button())
            
            form_layout.addRow("Color:", color_button)
            
            # Add specific settings based on settings type
            if isinstance(self.settings, PlotSettings):
                amplitude_spin = QDoubleSpinBox()
                amplitude_spin.setRange(0.1, 10.0)
                amplitude_spin.setSingleStep(0.1)
                amplitude_spin.setValue(self.settings.amplitude)
                
                frequency_spin = QDoubleSpinBox()
                frequency_spin.setRange(0.1, 20.0)
                frequency_spin.setSingleStep(0.1)
                frequency_spin.setValue(self.settings.frequency)
                
                phase_spin = QDoubleSpinBox()
                phase_spin.setRange(0.0, 360.0)
                phase_spin.setSingleStep(15.0)
                phase_spin.setValue(self.settings.phase)
                
                plot_type_combo = QComboBox()
                plot_type_combo.addItems(["Line", "Scatter", "Bar"])
                plot_type_combo.setCurrentIndex(self.settings.plot_type)
                
                form_layout.addRow("Amplitude:", amplitude_spin)
                form_layout.addRow("Frequency:", frequency_spin)
                form_layout.addRow("Phase:", phase_spin)
                form_layout.addRow("Plot Type:", plot_type_combo)
                
                # Create bindings
                binder = PropertyBinder()
                binder.bind(self.settings, "name", name_edit, "text")
                binder.bind(self.settings, "enabled", enabled_check, "checked")
                binder.bind(self.settings, "amplitude", amplitude_spin, "value")
                binder.bind(self.settings, "frequency", frequency_spin, "value")
                binder.bind(self.settings, "phase", phase_spin, "value")
                binder.bind(self.settings, "plot_type", plot_type_combo, "currentIndex")
                
            elif isinstance(self.settings, FilterSettings):
                cutoff_spin = QSpinBox()
                cutoff_spin.setRange(20, 20000)
                cutoff_spin.setSingleStep(100)
                cutoff_spin.setValue(self.settings.cutoff)
                
                order_spin = QSpinBox()
                order_spin.setRange(1, 12)
                order_spin.setValue(self.settings.order)
                
                filter_type_combo = QComboBox()
                filter_type_combo.addItems(["Lowpass", "Highpass", "Bandpass"])
                filter_type_combo.setCurrentIndex(self.settings.filter_type)
                
                ripple_spin = QDoubleSpinBox()
                ripple_spin.setRange(0.1, 3.0)
                ripple_spin.setSingleStep(0.1)
                ripple_spin.setValue(self.settings.ripple)
                
                form_layout.addRow("Cutoff:", cutoff_spin)
                form_layout.addRow("Order:", order_spin)
                form_layout.addRow("Type:", filter_type_combo)
                form_layout.addRow("Ripple:", ripple_spin)
                
                # Create bindings
                binder = PropertyBinder()
                binder.bind(self.settings, "name", name_edit, "text")
                binder.bind(self.settings, "enabled", enabled_check, "checked")
                binder.bind(self.settings, "cutoff", cutoff_spin, "value")
                binder.bind(self.settings, "order", order_spin, "value")
                binder.bind(self.settings, "filter_type", filter_type_combo, "currentIndex")
                binder.bind(self.settings, "ripple", ripple_spin, "value")
                
            elif isinstance(self.settings, AnalysisSettings):
                window_size_combo = QComboBox()
                window_size_combo.addItems(["256", "512", "1024", "2048", "4096"])
                window_index = {256: 0, 512: 1, 1024: 2, 2048: 3, 4096: 4}.get(self.settings.window_size, 2)
                window_size_combo.setCurrentIndex(window_index)
                
                overlap_spin = QSpinBox()
                overlap_spin.setRange(0, 90)
                overlap_spin.setSingleStep(10)
                overlap_spin.setValue(self.settings.overlap)
                
                method_combo = QComboBox()
                method_combo.addItems(["FFT", "Welch", "Wavelet"])
                method_combo.setCurrentIndex(self.settings.method)
                
                scaling_combo = QComboBox()
                scaling_combo.addItems(["Linear", "Log"])
                scaling_combo.setCurrentIndex(self.settings.scaling)
                
                form_layout.addRow("Window Size:", window_size_combo)
                form_layout.addRow("Overlap %:", overlap_spin)
                form_layout.addRow("Method:", method_combo)
                form_layout.addRow("Scaling:", scaling_combo)
                
                # Handle window size specially since it's not a direct mapping
                def on_window_size_changed(index):
                    sizes = [256, 512, 1024, 2048, 4096]
                    new_size = sizes[index]
                    cmd = PropertyCommand(self.settings, "window_size", new_size)
                    get_command_manager().execute(cmd)
                    
                window_size_combo.currentIndexChanged.connect(on_window_size_changed)
                
                # Create bindings
                binder = PropertyBinder()
                binder.bind(self.settings, "name", name_edit, "text")
                binder.bind(self.settings, "enabled", enabled_check, "checked")
                binder.bind(self.settings, "overlap", overlap_spin, "value")
                binder.bind(self.settings, "method", method_combo, "currentIndex")
                binder.bind(self.settings, "scaling", scaling_combo, "currentIndex")
            
            # Create a visualization area (just a placeholder)
            viz_widget = QWidget()
            viz_widget.setMinimumHeight(150)
            viz_widget.setStyleSheet(f"background-color: {self.settings.color}; border-radius: 5px;")
            
            # Update visualization when color changes
            self.settings.add_property_observer("color", lambda _, __, new_color: 
                viz_widget.setStyleSheet(f"background-color: {new_color}; border-radius: 5px;"))
            
            # Add visualization to layout
            layout.addWidget(viz_widget)
            
            # Set content widget
            self.dock_widget.setWidget(content_widget)
            
            # Add to main window
            self.main_window.addDockWidget(self.dock_area, self.dock_widget)
            
            # Register with dock manager
            dock_manager = DockManager.get_instance()
            dock_manager.register_dock(self.dock_id, self.dock_widget)
            
        elif self.dock_widget.isHidden():
            # Show the dock widget if it exists but is hidden
            self.dock_widget.show()
            
    def undo(self):
        if self.dock_widget:
            self.dock_widget.hide()
            
    def serialize(self):
        return {
            "type": "CreateDockCommand",
            "dock_id": self.dock_id,
            "dock_title": self.dock_title,
            "settings_id": self.settings.get_id()
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        from command_system.internal.registry import Registry
        
        main_window = registry.get_object("main_window")
        settings = registry.get_object(state["settings_id"])
        
        cmd = cls(main_window, state["dock_id"], state["dock_title"], settings)
        return cmd


class DeleteDockCommand(Command):
    """Command to delete a dock widget"""
    
    def __init__(self, dock_id):
        super().__init__()
        self.dock_id = dock_id
        self.dock_widget = None
        self.dock_area = None
        self.was_visible = True
        self.geometry = None
        
    def execute(self):
        dock_manager = DockManager.get_instance()
        self.dock_widget = dock_manager.get_dock(self.dock_id)
        
        if self.dock_widget:
            # Save state before hiding
            self.was_visible = self.dock_widget.isVisible()
            self.geometry = self.dock_widget.geometry()
            
            # Hide the dock widget (not deleting it to support undo)
            self.dock_widget.hide()
            
    def undo(self):
        if self.dock_widget and self.was_visible:
            self.dock_widget.show()
            if self.geometry:
                self.dock_widget.setGeometry(self.geometry)
                
    def serialize(self):
        return {
            "type": "DeleteDockCommand",
            "dock_id": self.dock_id,
            "was_visible": self.was_visible,
            "geometry": {
                "x": self.geometry.x(),
                "y": self.geometry.y(),
                "width": self.geometry.width(),
                "height": self.geometry.height()
            } if self.geometry else None
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        cmd = cls(state["dock_id"])
        cmd.was_visible = state["was_visible"]
        
        if state["geometry"]:
            from PySide6.QtCore import QRect
            cmd.geometry = QRect(
                state["geometry"]["x"],
                state["geometry"]["y"],
                state["geometry"]["width"],
                state["geometry"]["height"]
            )
            
        return cmd


class PropertyCommand(Command):
    """Command for changing a property on an observable object"""
    
    def __init__(self, target, property_name, new_value):
        super().__init__()
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(target, property_name)
        
    def execute(self):
        setattr(self.target, self.property_name, self.new_value)
        
    def undo(self):
        setattr(self.target, self.property_name, self.old_value)
        
    def serialize(self):
        return {
            "type": "PropertyCommand",
            "target_id": self.target.get_id(),
            "property_name": self.property_name,
            "new_value": self.new_value,
            "old_value": self.old_value
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        target = registry.get_object(state["target_id"])
        cmd = cls(target, state["property_name"], state["new_value"])
        cmd.old_value = state["old_value"]
        return cmd


# ========== Main Application ==========

class Project:
    """Simple project container"""
    
    def __init__(self, name="Untitled"):
        self.name = name
        self.id = id(self)
        self.utility_settings = None
        self.dock_settings = {}
        
    def get_id(self):
        """Get unique identifier"""
        return str(self.id)
        
    def set_id(self, id_value):
        """Set unique identifier (for deserialization)"""
        self.id = int(id_value)


# Register command deserializers
from command_system.internal.serialization import deserialize_command

# Add deserializer for our custom commands
def deserialize_custom_command(state, registry):
    """Deserialize custom commands"""
    cmd_type = state.get("type")
    
    if cmd_type == "CreateDockCommand":
        return CreateDockCommand.deserialize(state, registry)
    elif cmd_type == "DeleteDockCommand":
        return DeleteDockCommand.deserialize(state, registry)
    elif cmd_type == "PropertyCommand":
        return PropertyCommand.deserialize(state, registry)
    
    return None


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Set up core objects
        self.project = Project("Untitled Project")
        self.cmd_manager = get_command_manager()
        self.dock_manager = DockManager.get_instance()
        
        # Register main window with registry
        from command_system.internal.registry import Registry
        Registry.get_instance().register_object(self, "main_window")
        
        # Set up window properties
        self.setWindowTitle(f"{self.project.name} - Command System Demo")
        self.setMinimumSize(800, 600)
        
        # Create settings
        self.utility_settings = UtilitySettings()
        self.project.utility_settings = self.utility_settings
        
        # Create dock settings
        self.plot_settings = PlotSettings()
        self.plot_settings.name = "Plot Dock"
        self.plot_settings.color = "#3498db"  # Blue
        self.project.dock_settings["plot_dock"] = self.plot_settings
        
        self.filter_settings = FilterSettings()
        self.filter_settings.name = "Filter Dock"
        self.filter_settings.color = "#e74c3c"  # Red
        self.project.dock_settings["filter_dock"] = self.filter_settings
        
        self.analysis_settings = AnalysisSettings()
        self.analysis_settings.name = "Analysis Dock"
        self.analysis_settings.color = "#2ecc71"  # Green
        self.project.dock_settings["analysis_dock"] = self.analysis_settings
        
        # Register with command manager
        self.cmd_manager.register_observable(self.utility_settings)
        self.cmd_manager.register_observable(self.plot_settings)
        self.cmd_manager.register_observable(self.filter_settings)
        self.cmd_manager.register_observable(self.analysis_settings)
        
        # Create UI
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_central_widget()
        
        # Update window title when project changes
        self.project_file_path = None
        
        # Initialize dock manager
        self.dock_manager = DockManager.get_instance()
        
        # Set up command manager
        self.cmd_manager.set_project(self.project)
        self.cmd_manager.enable_auto_commands()
        
        # Update UI state
        self._update_ui_state()
        
    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        self.undo_action = undo_action
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Shift+Z")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        self.redo_action = redo_action
        
        # Layout menu
        layout_menu = menubar.addMenu("&Layout")
        
        save_layout_action = QAction("&Save Layout...", self)
        save_layout_action.triggered.connect(self.save_layout)
        layout_menu.addAction(save_layout_action)
        
        load_layout_action = QAction("&Load Layout...", self)
        load_layout_action.triggered.connect(self.load_layout)
        layout_menu.addAction(load_layout_action)
        
        layout_menu.addSeparator()
        
        reset_layout_action = QAction("&Reset Layout", self)
        reset_layout_action.triggered.connect(self.reset_layout)
        layout_menu.addAction(reset_layout_action)
        
        # Dock menu
        dock_menu = menubar.addMenu("&Docks")
        
        show_plot_action = QAction("Show &Plot Dock", self)
        show_plot_action.triggered.connect(lambda: self.show_dock("plot_dock", "Plot", self.plot_settings))
        dock_menu.addAction(show_plot_action)
        
        show_filter_action = QAction("Show &Filter Dock", self)
        show_filter_action.triggered.connect(lambda: self.show_dock("filter_dock", "Filter", self.filter_settings))
        dock_menu.addAction(show_filter_action)
        
        show_analysis_action = QAction("Show &Analysis Dock", self)
        show_analysis_action.triggered.connect(lambda: self.show_dock("analysis_dock", "Analysis", self.analysis_settings))
        dock_menu.addAction(show_analysis_action)
        
        dock_menu.addSeparator()
        
        remove_plot_action = QAction("Remove P&lot Dock", self)
        remove_plot_action.triggered.connect(lambda: self.remove_dock("plot_dock"))
        dock_menu.addAction(remove_plot_action)
        
        remove_filter_action = QAction("Remove F&ilter Dock", self)
        remove_filter_action.triggered.connect(lambda: self.remove_dock("filter_dock"))
        dock_menu.addAction(remove_filter_action)
        
        remove_analysis_action = QAction("Remove A&nalysis Dock", self)
        remove_analysis_action.triggered.connect(lambda: self.remove_dock("analysis_dock"))
        dock_menu.addAction(remove_analysis_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def _create_tool_bar(self):
        """Create the toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        
        # Add toolbar buttons (with text for simplicity)
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo)
        toolbar.addAction(undo_action)
        self.toolbar_undo_action = undo_action
        
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.redo)
        toolbar.addAction(redo_action)
        self.toolbar_redo_action = redo_action
        
        toolbar.addSeparator()
        
        # Add dock toolbar buttons
        plot_action = QAction("Plot Dock", self)
        plot_action.triggered.connect(lambda: self.show_dock("plot_dock", "Plot", self.plot_settings))
        toolbar.addAction(plot_action)
        
        filter_action = QAction("Filter Dock", self)
        filter_action.triggered.connect(lambda: self.show_dock("filter_dock", "Filter", self.filter_settings))
        toolbar.addAction(filter_action)
        
        analysis_action = QAction("Analysis Dock", self)
        analysis_action.triggered.connect(lambda: self.show_dock("analysis_dock", "Analysis", self.analysis_settings))
        toolbar.addAction(analysis_action)
        
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets to the status bar
        self.mode_label = QLabel("Mode: Normal")
        self.status_bar.addPermanentWidget(self.mode_label)
        
    def _create_central_widget(self):
        """Create the central widget (utility panel)"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create utility panel group
        utility_group = QGroupBox("Utility Panel")
        utility_layout = QFormLayout()
        utility_group.setLayout(utility_layout)
        
        # Create utility controls
        title_edit = QLineEdit(self.utility_settings.title)
        
        alpha_spin = QDoubleSpinBox()
        alpha_spin.setRange(0.1, 10.0)
        alpha_spin.setSingleStep(0.1)
        alpha_spin.setValue(self.utility_settings.alpha)
        
        beta_spin = QSpinBox()
        beta_spin.setRange(1, 100)
        beta_spin.setValue(self.utility_settings.beta)
        
        enabled_check = QCheckBox()
        enabled_check.setChecked(self.utility_settings.enabled)
        
        view_mode_combo = QComboBox()
        view_mode_combo.addItems(["Simple", "Advanced", "Expert"])
        view_mode_combo.setCurrentIndex(self.utility_settings.view_mode)
        
        # Add controls to layout
        utility_layout.addRow("Title:", title_edit)
        utility_layout.addRow("Alpha:", alpha_spin)
        utility_layout.addRow("Beta:", beta_spin)
        utility_layout.addRow("Enabled:", enabled_check)
        utility_layout.addRow("View Mode:", view_mode_combo)
        
        # Create bindings
        binder = PropertyBinder()
        binder.bind(self.utility_settings, "title", title_edit, "text")
        binder.bind(self.utility_settings, "alpha", alpha_spin, "value")
        binder.bind(self.utility_settings, "beta", beta_spin, "value")
        binder.bind(self.utility_settings, "enabled", enabled_check, "checked")
        binder.bind(self.utility_settings, "view_mode", view_mode_combo, "currentIndex")
        
        # Add dock control buttons
        dock_buttons_layout = QHBoxLayout()
        
        show_plot_btn = QPushButton("Show Plot Dock")
        show_plot_btn.clicked.connect(lambda: self.show_dock("plot_dock", "Plot", self.plot_settings))
        
        show_filter_btn = QPushButton("Show Filter Dock")
        show_filter_btn.clicked.connect(lambda: self.show_dock("filter_dock", "Filter", self.filter_settings))
        
        show_analysis_btn = QPushButton("Show Analysis Dock")
        show_analysis_btn.clicked.connect(lambda: self.show_dock("analysis_dock", "Analysis", self.analysis_settings))
        
        dock_buttons_layout.addWidget(show_plot_btn)
        dock_buttons_layout.addWidget(show_filter_btn)
        dock_buttons_layout.addWidget(show_analysis_btn)
        
        # Add widgets to main layout
        main_layout.addWidget(utility_group)
        main_layout.addLayout(dock_buttons_layout)
        
        # Add spacer to push everything to the top
        main_layout.addStretch()
        
    def _update_ui_state(self):
        """Update UI state based on command manager state"""
        # Update undo/redo actions
        self.undo_action.setEnabled(self.cmd_manager.can_undo())
        self.redo_action.setEnabled(self.cmd_manager.can_redo())
        self.toolbar_undo_action.setEnabled(self.cmd_manager.can_undo())
        self.toolbar_redo_action.setEnabled(self.cmd_manager.can_redo())
        
        # Update window title
        title = f"{self.project.name}"
        if self.project_file_path:
            title += f" - {os.path.basename(self.project_file_path)}"
        title += " - Command System Demo"
        self.setWindowTitle(title)
        
    def show_dock(self, dock_id, dock_title, settings):
        """Show a dock widget"""
        cmd = CreateDockCommand(self, dock_id, dock_title, settings)
        self.cmd_manager.execute(cmd)
        self._update_ui_state()
        self.status_bar.showMessage(f"Dock '{dock_title}' shown")
        
    def remove_dock(self, dock_id):
        """Remove a dock widget"""
        if self.dock_manager.has_dock(dock_id):
            cmd = DeleteDockCommand(dock_id)
            self.cmd_manager.execute(cmd)
            self._update_ui_state()
            self.status_bar.showMessage(f"Dock '{dock_id}' removed")
            
    def undo(self):
        """Undo the last command"""
        if self.cmd_manager.can_undo():
            self.cmd_manager.undo()
            self._update_ui_state()
            self.status_bar.showMessage("Undo")
            
    def redo(self):
        """Redo the last undone command"""
        if self.cmd_manager.can_redo():
            self.cmd_manager.redo()
            self._update_ui_state()
            self.status_bar.showMessage("Redo")
            
    def new_project(self):
        """Create a new project"""
        # Confirm with user if there are unsaved changes
        if self.cmd_manager.can_undo():
            reply = QMessageBox.question(
                self, 
                "New Project", 
                "Create a new project? Any unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Create new project
        self.project = Project("Untitled Project")
        
        # Create new settings
        self.utility_settings = UtilitySettings()
        self.project.utility_settings = self.utility_settings
        
        # Create dock settings
        self.plot_settings = PlotSettings()
        self.plot_settings.name = "Plot Dock"
        self.plot_settings.color = "#3498db"  # Blue
        self.project.dock_settings["plot_dock"] = self.plot_settings
        
        self.filter_settings = FilterSettings()
        self.filter_settings.name = "Filter Dock"
        self.filter_settings.color = "#e74c3c"  # Red
        self.project.dock_settings["filter_dock"] = self.filter_settings
        
        self.analysis_settings = AnalysisSettings()
        self.analysis_settings.name = "Analysis Dock"
        self.analysis_settings.color = "#2ecc71"  # Green
        self.project.dock_settings["analysis_dock"] = self.analysis_settings
        
        # Reset command manager
        self.cmd_manager.clear()
        self.cmd_manager.set_project(self.project)
        
        # Register with command manager
        self.cmd_manager.register_observable(self.utility_settings)
        self.cmd_manager.register_observable(self.plot_settings)
        self.cmd_manager.register_observable(self.filter_settings)
        self.cmd_manager.register_observable(self.analysis_settings)
        
        # Reset file path
        self.project_file_path = None
        
        # Reset dock widgets
        self.reset_layout()
        
        # Update UI
        self._update_ui_state()
        self.status_bar.showMessage("New project created")
        
    def open_project(self):
        """Open a project from a file"""
        # Confirm with user if there are unsaved changes
        if self.cmd_manager.can_undo():
            reply = QMessageBox.question(
                self, 
                "Open Project", 
                "Open a project? Any unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Project Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Load project
            loaded_project = self.cmd_manager.load_project(file_path)
            
            if loaded_project:
                self.project = loaded_project
                self.project_file_path = file_path
                
                # Get settings from loaded project
                self.utility_settings = self.project.utility_settings
                
                # Get dock settings
                self.plot_settings = self.project.dock_settings.get("plot_dock")
                self.filter_settings = self.project.dock_settings.get("filter_dock")
                self.analysis_settings = self.project.dock_settings.get("analysis_dock")
                
                # Reset dock widgets
                self.reset_layout()
                
                # Update UI
                self._update_ui_state()
                self.status_bar.showMessage(f"Project loaded from {file_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not load project from {file_path}"
                )
                
    def save_project(self):
        """Save the current project"""
        if self.project_file_path:
            success = self.cmd_manager.save_project(self.project_file_path)
            
            if success:
                self.status_bar.showMessage(f"Project saved to {self.project_file_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not save project to {self.project_file_path}"
                )
        else:
            self.save_project_as()
            
    def save_project_as(self):
        """Save the current project to a new file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            "Project Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Ensure file has .json extension
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
                
            # Save project
            success = self.cmd_manager.save_project(file_path)
            
            if success:
                self.project_file_path = file_path
                self._update_ui_state()
                self.status_bar.showMessage(f"Project saved to {file_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not save project to {file_path}"
                )
                
    def save_layout(self):
        """Save the current layout to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Layout",
            "",
            "Layout Files (*.layout);;All Files (*)"
        )
        
        if file_path:
            # Ensure file has .layout extension
            if not file_path.lower().endswith('.layout'):
                file_path += '.layout'
                
            try:
                # Serialize layout
                layout_data = self.dock_manager.serialize_layout()
                
                # Save to file
                import json
                with open(file_path, 'w') as f:
                    json.dump(layout_data, f, indent=2)
                    
                self.status_bar.showMessage(f"Layout saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not save layout to {file_path}: {str(e)}"
                )
                
    def load_layout(self):
        """Load a layout from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Layout",
            "",
            "Layout Files (*.layout);;All Files (*)"
        )
        
        if file_path:
            try:
                # Load layout data
                import json
                with open(file_path, 'r') as f:
                    layout_data = json.load(f)
                    
                # Restore layout
                success = self.dock_manager.deserialize_layout(layout_data)
                
                if success:
                    self.status_bar.showMessage(f"Layout loaded from {file_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        f"Could not fully restore layout from {file_path}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not load layout from {file_path}: {str(e)}"
                )
                
    def reset_layout(self):
        """Reset dock layout to default"""
        # First clear all dock widgets
        dock_ids = list(self.dock_manager._dock_states.keys())
        for dock_id in dock_ids:
            self.dock_manager.unregister_dock(dock_id)
            
        # Then recreate default docks
        if self.plot_settings:
            self.show_dock("plot_dock", "Plot", self.plot_settings)
            
        if self.filter_settings:
            self.show_dock("filter_dock", "Filter", self.filter_settings)
            
        if self.analysis_settings:
            self.show_dock("analysis_dock", "Analysis", self.analysis_settings)
            
        self.status_bar.showMessage("Layout reset to default")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Command System Demo",
            "Command System Demo\n\n"
            "A demonstration of the PySignalDecipher Command System.\n\n"
            "Features:\n"
            "- Undo/Redo functionality\n"
            "- Observable properties\n"
            "- UI binding\n"
            "- Dock management\n"
            "- Project serialization"
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Confirm with user if there are unsaved changes
        if self.cmd_manager.can_undo():
            reply = QMessageBox.question(
                self, 
                "Exit", 
                "Exit application? Any unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        # Accept the event and close the window
        event.accept()


# ========== Main Function ==========

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Create default docks
    window.show_dock("plot_dock", "Plot", window.plot_settings)
    window.show_dock("filter_dock", "Filter", window.filter_settings)
    window.show_dock("analysis_dock", "Analysis", window.analysis_settings)
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()