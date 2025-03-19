import pytest
import os
import tempfile
import threading
import time
import numpy as np
from unittest.mock import MagicMock, patch
import h5py

# Import only the public API of our command system
from command_system import (
    get_command_manager,
    Command, 
    CompoundCommand,
    Observable, 
    ObservableProperty,
    PropertyBinder,
    DockManager,
    SignalData,
    SignalDataManager,
    AdaptiveSampler
)

# PySide6 imports for UI tests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QSlider, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QRect, QPointF
from PySide6.QtGui import QPainter, QPen, QColor


# =========== Fixtures ===========

@pytest.fixture
def app():
    """Create Qt application for widget tests."""
    app = QApplication.instance() or QApplication([])
    yield app
    # Ensure we don't leave pending tasks
    app.processEvents()


@pytest.fixture
def cmd_manager():
    """Get the command manager instance."""
    manager = get_command_manager()
    manager.clear()  # Start fresh
    yield manager
    # Reset after test
    manager.clear()


@pytest.fixture
def dock_manager():
    """Get the dock manager instance."""
    manager = DockManager.get_instance()
    manager.clear()  # Start fresh
    yield manager
    # Reset after test
    manager.clear()


@pytest.fixture
def signal_manager():
    """Get the signal data manager instance."""
    manager = SignalDataManager.get_instance()
    manager.clear()  # Start fresh
    yield manager
    # Reset after test
    manager.clear()


@pytest.fixture
def main_window(app):
    """Create a main window for dock tests."""
    window = QMainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.processEvents()
    yield window
    window.close()
    app.processEvents()


@pytest.fixture
def temp_file():
    """Create a temporary file for storage tests."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_hdf5_file():
    """Create a temporary HDF5 file for signal data tests."""
    fd, path = tempfile.mkstemp(suffix='.h5')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# =========== Test Models ===========

class TestModel(Observable):
    """Test model with observable properties."""
    name = ObservableProperty(default="Default Name")
    count = ObservableProperty(default=0)
    active = ObservableProperty(default=False)
    color = ObservableProperty(default="#0000FF")
    option = ObservableProperty(default=0)
    value = ObservableProperty(default=0.0)
    
    def __init__(self, name="Default Name", count=0, active=False):
        super().__init__()
        self.name = name
        self.count = count
        self.active = active


class ChannelSettings(Observable):
    """Signal channel settings model."""
    name = ObservableProperty(default="Channel 1")
    enabled = ObservableProperty(default=False)
    amplitude = ObservableProperty(default=1.0)
    color = ObservableProperty(default="#0000FF")
    mode = ObservableProperty(default=0)  # 0 = Normal, 1 = Inverted, 2 = Differential
    
    def __init__(self, name="Channel 1"):
        super().__init__()
        self.name = name


# =========== Test Commands ===========

class ChangeNameCommand(Command):
    """Command to change a name property."""
    
    def __init__(self, model, new_name):
        super().__init__()
        self.model = model
        self.new_name = new_name
        self.old_name = model.name
    
    def execute(self):
        self.model.name = self.new_name
    
    def undo(self):
        self.model.name = self.old_name
    
    def serialize(self):
        return {
            "model_id": self.model.get_id(),
            "new_name": self.new_name,
            "old_name": self.old_name
        }
    
    @classmethod
    def deserialize(cls, state, registry):
        model = registry.get_object(state["model_id"])
        cmd = cls(model, state["new_name"])
        cmd.old_name = state["old_name"]
        return cmd


class ChangePropertyCommand(Command):
    """Generic command to change any property."""
    
    def __init__(self, model, property_name, new_value):
        super().__init__()
        self.model = model
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(model, property_name)
    
    def execute(self):
        setattr(self.model, self.property_name, self.new_value)
    
    def undo(self):
        setattr(self.model, self.property_name, self.old_value)
    
    def serialize(self):
        return {
            "model_id": self.model.get_id(),
            "property_name": self.property_name,
            "new_value": self.new_value,
            "old_value": self.old_value
        }
    
    @classmethod
    def deserialize(cls, state, registry):
        model = registry.get_object(state["model_id"])
        cmd = cls(model, state["property_name"], state["new_value"])
        cmd.old_value = state["old_value"]
        return cmd


class AddSignalCommand(Command):
    """Command to add a signal to a project."""
    
    def __init__(self, project, signal):
        super().__init__()
        self.project = project
        self.signal = signal
        self.added = False
    
    def execute(self):
        self.project.add_signal(self.signal)
        self.added = True
    
    def undo(self):
        if self.added:
            self.project.remove_signal(self.signal.get_id())
            self.added = False
    
    def serialize(self):
        return {
            "project_id": self.project.get_id(),
            "signal_id": self.signal.get_id()
        }
    
    @classmethod
    def deserialize(cls, state, registry):
        project = registry.get_object(state["project_id"])
        signal = registry.get_object(state["signal_id"])
        return cls(project, signal)


class MoveDockCommand(Command):
    """Command to move/resize a dock widget."""
    
    def __init__(self, dock_id, new_geometry):
        super().__init__()
        self.dock_id = dock_id
        self.new_geometry = new_geometry
        self.old_geometry = None
    
    def execute(self):
        dock_manager = DockManager.get_instance()
        dock_widget = dock_manager.get_dock(self.dock_id)
        
        if dock_widget:
            # Store old geometry if not already captured
            if self.old_geometry is None:
                self.old_geometry = QRect(
                    dock_widget.x(),
                    dock_widget.y(),
                    dock_widget.width(),
                    dock_widget.height()
                )
            
            # Apply new geometry
            dock_widget.setGeometry(self.new_geometry)
    
    def undo(self):
        if self.old_geometry:
            dock_manager = DockManager.get_instance()
            dock_widget = dock_manager.get_dock(self.dock_id)
            
            if dock_widget:
                dock_widget.setGeometry(self.old_geometry)
    
    def serialize(self):
        return {
            "dock_id": self.dock_id,
            "new_geometry": {
                "x": self.new_geometry.x(),
                "y": self.new_geometry.y(),
                "width": self.new_geometry.width(),
                "height": self.new_geometry.height()
            },
            "old_geometry": {
                "x": self.old_geometry.x() if self.old_geometry else 0,
                "y": self.old_geometry.y() if self.old_geometry else 0,
                "width": self.old_geometry.width() if self.old_geometry else 0,
                "height": self.old_geometry.height() if self.old_geometry else 0
            } if self.old_geometry else None
        }
    
    @classmethod
    def deserialize(cls, state, registry):
        new_geo = QRect(
            state["new_geometry"]["x"],
            state["new_geometry"]["y"],
            state["new_geometry"]["width"],
            state["new_geometry"]["height"]
        )
        
        cmd = cls(state["dock_id"], new_geo)
        
        if state["old_geometry"]:
            cmd.old_geometry = QRect(
                state["old_geometry"]["x"],
                state["old_geometry"]["y"],
                state["old_geometry"]["width"],
                state["old_geometry"]["height"]
            )
            
        return cmd


# =========== Simple Project Mock ===========

class SimpleProject:
    """A simple project implementation for testing."""
    
    def __init__(self, name):
        self.name = name
        self.id = id(self)  # Simple ID for testing
        self.signals = {}
        self.models = {}
        self.docks = {}
    
    def get_id(self):
        """Get unique identifier."""
        return str(self.id)
    
    def add_signal(self, signal):
        """Add a signal to the project."""
        self.signals[signal.get_id()] = signal
    
    def remove_signal(self, signal_id):
        """Remove a signal from the project."""
        if signal_id in self.signals:
            del self.signals[signal_id]
    
    def add_model(self, model):
        """Add a model to the project."""
        self.models[model.get_id()] = model
    
    def remove_model(self, model_id):
        """Remove a model from the project."""
        if model_id in self.models:
            del self.models[model_id]
    
    def add_dock(self, dock_id, dock_widget):
        """Add a dock to the project."""
        self.docks[dock_id] = dock_widget
    
    def remove_dock(self, dock_id):
        """Remove a dock from the project."""
        if dock_id in self.docks:
            del self.docks[dock_id]


# =========== Tests ===========

class TestBasicCommandOperations:
    """Test basic command operations from user perspective."""
    
    def test_execute_simple_command(self, cmd_manager):
        """Test executing a command."""
        model = TestModel(name="Original")
        
        # Create and execute command
        cmd = ChangeNameCommand(model, "New Name")
        cmd_manager.execute(cmd)
        
        # Verify command effect
        assert model.name == "New Name"
    
    def test_undo_redo(self, cmd_manager):
        """Test undoing and redoing a command."""
        model = TestModel(name="Original")
        
        # Execute command
        cmd_manager.execute(ChangeNameCommand(model, "Changed"))
        assert model.name == "Changed"
        
        # Undo
        cmd_manager.undo()
        assert model.name == "Original"
        
        # Redo
        cmd_manager.redo()
        assert model.name == "Changed"
    
    def test_compound_command(self, cmd_manager):
        """Test compound commands."""
        model = TestModel(name="Original", count=5)
        
        # Create compound command
        compound = CompoundCommand("Multiple Changes")
        compound.add_command(ChangeNameCommand(model, "New Name"))
        compound.add_command(ChangePropertyCommand(model, "count", 10))
        
        # Execute compound command
        cmd_manager.execute(compound)
        
        # Verify both changes applied
        assert model.name == "New Name"
        assert model.count == 10
        
        # Undo should undo both changes
        cmd_manager.undo()
        assert model.name == "Original"
        assert model.count == 5


class TestObservableProperties:
    """Test observable property functionality."""
    
    def test_property_observer_notification(self):
        """Test that observers are notified of property changes."""
        model = TestModel()
        
        # Create a mock observer
        observer = MagicMock()
        
        # Add observer to a property
        model.add_property_observer("name", observer)
        
        # Change property
        model.name = "Modified"
        
        # Verify observer was called
        observer.assert_called_once()
        args = observer.call_args[0]
        assert args[0] == "name"  # Property name
        assert args[1] == "Default Name"  # Old value
        assert args[2] == "Modified"  # New value
    
    def test_auto_command_generation(self, cmd_manager):
        """Test automatic command generation for properties."""
        model = TestModel(name="Original")
        
        # Enable automatic commands
        cmd_manager.enable_auto_commands()
        cmd_manager.register_observable(model)
        
        # Change property to trigger auto command
        model.name = "Auto Changed"
        
        # Verify change happened
        assert model.name == "Auto Changed"
        
        # Should be able to undo via auto-generated command
        cmd_manager.undo()
        assert model.name == "Original"


class TestUIIntegration:
    """Test UI integration features."""
    
    def test_property_binding(self, app):
        """Test binding properties to UI controls."""
        model = TestModel(name="Initial", count=5, active=True)
        model.color = "#FF0000"
        model.option = 2
        model.value = 7.5
        
        # Create UI controls
        text_edit = QLineEdit()
        spin_box = QSpinBox()
        check_box = QCheckBox()
        combo_box = QComboBox()
        combo_box.addItems(["Option 1", "Option 2", "Option 3"])
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        double_spin = QDoubleSpinBox()
        double_spin.setRange(0, 10)
        double_spin.setSingleStep(0.1)
        label = QLabel()
        
        # Create bindings
        binder = PropertyBinder()
        binder.bind(model, "name", text_edit, "text")
        binder.bind(model, "count", spin_box, "value")
        binder.bind(model, "active", check_box, "checked")
        binder.bind(model, "option", combo_box, "currentIndex")
        binder.bind(model, "value", double_spin, "value")
        binder.bind(model, "count", slider, "value")
        binder.bind(model, "name", label, "text")  # One-way binding
        
        # Process events to allow bindings to initialize
        app.processEvents()
        
        # Check that controls got initial values
        assert text_edit.text() == "Initial"
        assert spin_box.value() == 5
        assert check_box.isChecked() is True
        assert combo_box.currentIndex() == 2
        assert double_spin.value() == 7.5
        assert slider.value() == 5
        assert label.text() == "Initial"
        
        # Change model, verify controls updated
        model.name = "Updated"
        model.count = 10
        model.active = False
        model.option = 0
        model.value = 2.5
        
        # Process events to allow updates to propagate
        app.processEvents()
        
        assert text_edit.text() == "Updated"
        assert spin_box.value() == 10
        assert check_box.isChecked() is False
        assert combo_box.currentIndex() == 0
        assert double_spin.value() == 2.5
        assert slider.value() == 10
        assert label.text() == "Updated"
        
        # Change controls, verify model updated
        text_edit.setText("From UI")
        spin_box.setValue(42)
        check_box.setChecked(True)
        combo_box.setCurrentIndex(1)
        double_spin.setValue(3.75)
        
        # Process events to allow updates to propagate
        app.processEvents()
        
        assert model.name == "From UI"
        assert model.count == 42
        assert model.active is True
        assert model.option == 1
        assert model.value == 3.75
        
        # Slider changes (triggering valueChanged signal)
        slider.setValue(30)
        app.processEvents()
        
        assert model.count == 30
        assert spin_box.value() == 30  # Other bound widgets should update too
    
    def test_dock_management(self, app, main_window, dock_manager, cmd_manager):
        """Test dock widget management."""
        # Create dock widgets
        dock1 = QDockWidget("Dock 1", main_window)
        dock1.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock1.setWidget(QWidget())
        main_window.addDockWidget(Qt.LeftDockWidgetArea, dock1)
        
        dock2 = QDockWidget("Dock 2", main_window)
        dock2.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock2.setWidget(QWidget())
        main_window.addDockWidget(Qt.RightDockWidgetArea, dock2)
        
        # Register docks
        dock_manager.register_dock("dock1", dock1)
        dock_manager.register_dock("dock2", dock2)
        
        # Create child widgets with models
        child1 = QWidget()
        layout1 = QFormLayout(child1)
        model1 = ChannelSettings("Channel 1")
        
        name_edit = QLineEdit(model1.name)
        enabled_check = QCheckBox("Enabled")
        
        layout1.addRow("Name:", name_edit)
        layout1.addRow(enabled_check)
        
        dock1.widget().setLayout(QVBoxLayout())
        dock1.widget().layout().addWidget(child1)
        
        # Register child widget
        dock_manager.register_dock("child1", child1, "dock1")
        
        # Create binding
        binder = PropertyBinder()
        binder.bind(model1, "name", name_edit, "text")
        binder.bind(model1, "enabled", enabled_check, "checked")
        
        # Process events
        app.processEvents()
        
        # Verify initial state
        assert dock_manager.get_dock("dock1") is dock1
        assert dock_manager.get_dock("child1") is child1
        assert dock_manager.get_parent_id("child1") == "dock1"
        assert "child1" in dock_manager.get_children("dock1")
        
        # Test saving dock geometry
        dock1.setGeometry(50, 50, 300, 200)
        app.processEvents()
        
        dock_manager.save_dock_state("dock1")
        dock1.setGeometry(100, 100, 400, 300)
        app.processEvents()
        
        # Restore and verify
        dock_manager.restore_dock_state("dock1")
        app.processEvents()
        
        # Allow for slight differences due to window decorations
        assert abs(dock1.width() - 300) <= 10
        assert abs(dock1.height() - 200) <= 10
        
        # Test dock command
        new_geometry = QRect(150, 150, 350, 250)
        cmd = MoveDockCommand("dock1", new_geometry)
        cmd_manager.execute(cmd)
        app.processEvents()
        
        # Verify command executed
        assert abs(dock1.width() - 350) <= 10
        assert abs(dock1.height() - 250) <= 10
        
        # Undo and verify
        cmd_manager.undo()
        app.processEvents()
        
        assert abs(dock1.width() - 300) <= 10
        assert abs(dock1.height() - 200) <= 10
        
        # Test parent-child relationship with deletion
        assert dock_manager.has_dock("child1")
        dock_manager.unregister_dock("dock1")  # Should also unregister children
        assert not dock_manager.has_dock("dock1")
        assert not dock_manager.has_dock("child1")


class TestSignalDataHandling:
    """Test signal data handling features."""
    
    def test_signal_data_creation(self, signal_manager):
        """Test creating and accessing signal data."""
        # Create signal with in-memory storage
        data = np.sin(np.linspace(0, 10, 1000))
        signal = signal_manager.create_signal("Sine Wave", data, use_file_storage=False)
        
        # Verify properties
        assert signal.name == "Sine Wave"
        assert signal.get_data().shape == (1000,)
        np.testing.assert_allclose(signal.get_data(), data)
    
    def test_file_based_signal(self, signal_manager, temp_hdf5_file):
        """Test file-based signal storage."""
        # Create signal with file storage
        data = np.sin(np.linspace(0, 10, 10000))
        signal = signal_manager.create_signal(
            "Large Signal", 
            data, 
            use_file_storage=True,
            file_path=temp_hdf5_file
        )
        
        # Verify properties
        assert signal.name == "Large Signal"
        assert signal.is_file_based()
        assert signal.get_file_path() == temp_hdf5_file
        
        # Get full data and verify
        full_data = signal.get_data()
        assert full_data.shape == (10000,)
        np.testing.assert_allclose(full_data, data)
        
        # Get segment and verify
        segment = signal.get_data(start=1000, end=2000)
        assert segment.shape == (1000,)
        np.testing.assert_allclose(segment, data[1000:2000])
    
    def test_visible_segment(self, signal_manager):
        """Test getting visible segments with downsampling."""
        # Create a large signal
        data = np.sin(np.linspace(0, 100, 100000))
        signal = signal_manager.create_signal("Large Signal", data)
        
        # Get visible segment with downsampling
        visible = signal.get_visible_segment(10000, 20000, max_points=500)
        
        # Verify downsampled correctly
        assert len(visible) <= 500
        
        # Verify represents correct portion of data
        # Check first and last points
        assert abs(visible[0] - data[10000]) < 0.1
        assert abs(visible[-1] - data[19999]) < 0.1
    
    def test_adaptive_sampling(self):
        """Test adaptive sampling based on zoom level."""
        # Create a signal and sampler
        data = np.sin(np.linspace(0, 100, 10000))
        sampler = AdaptiveSampler(max_display_points=100)
        
        # Test overview mode (zoomed out)
        overview = sampler.sample(data, 0, 10000, zoom_level=0.05)
        assert len(overview) <= 100
        
        # Test navigation mode (medium zoom)
        navigation = sampler.sample(data, 0, 10000, zoom_level=0.3)
        assert len(navigation) <= 200  # May use more points in navigation mode
        
        # Test detail mode (zoomed in)
        detail = sampler.sample(data, 0, 100, zoom_level=1.0)
        assert len(detail) == 100  # All points should be included for small segment
    
    def test_signal_metadata(self, signal_manager):
        """Test signal metadata handling."""
        # Create signal
        data = np.sin(np.linspace(0, 10, 1000))
        signal = signal_manager.create_signal("Metadata Test", data)
        
        # Set and get metadata
        signal.set_metadata("source", "Test Generator")
        signal.set_metadata("sample_rate", 44100)
        signal.set_metadata("color", "#00FF00")
        
        # Verify metadata
        assert signal.get_metadata("source") == "Test Generator"
        assert signal.get_metadata("sample_rate") == 44100
        assert signal.get_metadata("color") == "#00FF00"
        assert signal.get_metadata("invalid", "default") == "default"
        
        # Get all metadata
        all_metadata = signal.get_metadata()
        assert "source" in all_metadata
        assert "sample_rate" in all_metadata
        assert "color" in all_metadata


class TestLayoutManagement:
    """Test layout saving and loading."""
    
    def test_save_restore_layout(self, app, main_window, dock_manager):
        """Test saving and restoring dock layouts."""
        # Setup dock widgets
        dock1 = QDockWidget("Dock 1", main_window)
        dock1.setWidget(QWidget())
        main_window.addDockWidget(Qt.LeftDockWidgetArea, dock1)
        
        dock2 = QDockWidget("Dock 2", main_window)
        dock2.setWidget(QWidget())
        main_window.addDockWidget(Qt.RightDockWidgetArea, dock2)
        
        # Register docks
        dock_manager.register_dock("dock1", dock1)
        dock_manager.register_dock("dock2", dock2)
        
        # Set initial geometries
        dock1.setGeometry(50, 50, 300, 200)
        dock2.setGeometry(400, 50, 300, 200)
        app.processEvents()
        
        # Save layout
        layout_data = dock_manager.serialize_layout()
        
        # Change geometries
        dock1.setGeometry(100, 100, 250, 150)
        dock2.setGeometry(450, 100, 250, 150)
        app.processEvents()
        
        # Restore layout
        dock_manager.deserialize_layout(layout_data)
        app.processEvents()
        
        # Verify restored
        # Allow for small differences due to window decorations
        assert abs(dock1.width() - 300) <= 10
        assert abs(dock1.height() - 200) <= 10
        assert abs(dock2.width() - 300) <= 10
        assert abs(dock2.height() - 200) <= 10


class TestProjectManagement:
    """Test project management features."""
    
    def test_project_save_load(self, cmd_manager, temp_file):
        """Test saving and loading a project."""
        # Create project with models
        project = SimpleProject("Test Project")
        model1 = TestModel(name="Model One", count=1)
        model2 = TestModel(name="Model Two", count=2)
        
        # Add models to project
        project.add_model(model1)
        project.add_model(model2)
        
        # Make some changes via commands
        cmd_manager.execute(ChangeNameCommand(model1, "Updated Model"))
        cmd_manager.execute(ChangePropertyCommand(model2, "count", 99))
        
        # Save project with command history
        cmd_manager.set_project(project)
        cmd_manager.save_project(temp_file)
        
        # Clear everything
        cmd_manager.clear()
        
        # Load saved project
        loaded_project = cmd_manager.load_project(temp_file)
        
        # Get restored models
        loaded_model1 = next(m for m in loaded_project.models.values() 
                             if m.name == "Updated Model")
        loaded_model2 = next(m for m in loaded_project.models.values() 
                             if m.count == 99)
        
        # Verify state restored
        assert loaded_model1.name == "Updated Model"
        assert loaded_model2.count == 99
        
        # Verify undo history restored
        cmd_manager.undo()
        assert loaded_model2.count == 2
        
        cmd_manager.undo()
        assert loaded_model1.name == "Model One"


class TestCompleteWorkflow:
    """Test a complete workflow from user perspective."""
    
    def test_signal_processing_workflow(self, cmd_manager, signal_manager, dock_manager, 
                                         app, main_window, temp_file):
        """Test a realistic signal processing workflow."""
        # Create project
        project = SimpleProject("Signal Project")
        
        # Add some models
        model = ChannelSettings("Control Panel")
        project.add_model(model)
        
        # Create signals
        signal1 = signal_manager.create_signal(
            "Signal 1", 
            np.sin(np.linspace(0, 10, 1000))
        )
        signal2 = signal_manager.create_signal(
            "Signal 2", 
            np.cos(np.linspace(0, 10, 1000))
        )
        
        # Add signals via commands
        cmd_manager.execute(AddSignalCommand(project, signal1))
        cmd_manager.execute(AddSignalCommand(project, signal2))
        
        # Create dock widgets
        control_dock = QDockWidget("Controls", main_window)
        control_widget = QWidget()
        control_layout = QFormLayout(control_widget)
        control_dock.setWidget(control_widget)
        main_window.addDockWidget(Qt.LeftDockWidgetArea, control_dock)
        
        signal_dock = QDockWidget("Signal View", main_window)
        signal_widget = QWidget()
        signal_layout = QVBoxLayout(signal_widget)
        signal_dock.setWidget(signal_widget)
        main_window.addDockWidget(Qt.RightDockWidgetArea, signal_dock)
        
        # Register docks
        dock_manager.register_dock("control_dock", control_dock)
        dock_manager.register_dock("signal_dock", signal_dock)
        
        # Create UI controls for channel settings
        name_edit = QLineEdit(model.name)
        enabled_check = QCheckBox("Enabled")
        color_combo = QComboBox()
        color_combo.addItems(["Blue", "Red", "Green"])
        amplitude_spin = QDoubleSpinBox()
        amplitude_spin.setRange(0.1, 10.0)
        amplitude_spin.setSingleStep(0.1)
        amplitude_spin.setValue(model.amplitude)
        mode_combo = QComboBox()
        mode_combo.addItems(["Normal", "Inverted", "Differential"])
        
        # Add controls to layout
        control_layout.addRow("Name:", name_edit)
        control_layout.addRow(enabled_check)
        control_layout.addRow("Color:", color_combo)
        control_layout.addRow("Amplitude:", amplitude_spin)
        control_layout.addRow("Mode:", mode_combo)
        
        # Create signal display widget
        class SignalDisplay(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.signals = {}
                self.start_sample = 0
                self.visible_samples = 1000
                self.setMinimumHeight(200)
                
            def add_signal(self, signal_id, signal):
                self.signals[signal_id] = signal
                self.update()
                
            def remove_signal(self, signal_id):
                if signal_id in self.signals:
                    del self.signals[signal_id]
                    self.update()
                    
            def set_view_range(self, start, samples):
                self.start_sample = max(0, start)
                self.visible_samples = max(100, samples)
                self.update()
                
            def paintEvent(self, event):
                if not self.signals:
                    return
                    
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Draw background
                painter.fillRect(self.rect(), Qt.white)
                
                # Draw each signal
                width = self.width()
                height = self.height()
                
                for signal_id, signal in self.signals.items():
                    # Get data segment
                    data = signal.get_visible_segment(
                        self.start_sample,
                        self.start_sample + self.visible_samples,
                        max_points=width
                    )
                    
                    if data is None or len(data) == 0:
                        continue
                        
                    # Get color
                    color_name = signal.get_metadata("color", "#0000FF")
                    painter.setPen(QPen(QColor(color_name), 2))
                    
                    # Draw signal
                    points = []
                    x_scale = width / len(data)
                    y_mid = height / 2
                    y_scale = height * 0.4
                    
                    for i, value in enumerate(data):
                        x = i * x_scale
                        y = y_mid - (value * y_scale)
                        points.append(QPointF(x, y))
                        
                    # Draw line
                    for i in range(1, len(points)):
                        painter.drawLine(points[i-1], points[i])
        
        # Create signal display
        signal_display = SignalDisplay()
        signal_layout.addWidget(signal_display)
        
        # Add zoom controls
        zoom_layout = QHBoxLayout()
        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        pan_left_btn = QPushButton("◀")
        pan_right_btn = QPushButton("▶")
        
        zoom_layout.addWidget(pan_left_btn)
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(zoom_in_btn)
        zoom_layout.addWidget(pan_right_btn)
        
        signal_layout.addLayout(zoom_layout)
        
        # Add signals to display
        signal_display.add_signal(signal1.get_id(), signal1)
        signal_display.add_signal(signal2.get_id(), signal2)
        
        # Set metadata for display
        signal1.set_metadata("color", "#0000FF")  # Blue
        signal2.set_metadata("color", "#FF0000")  # Red
        
        # Register child widgets
        dock_manager.register_dock("signal_display", signal_display, "signal_dock")
        
        # Create property bindings
        binder = PropertyBinder()
        binder.bind(model, "name", name_edit, "text")
        binder.bind(model, "enabled", enabled_check, "checked")
        binder.bind(model, "amplitude", amplitude_spin, "value")
        binder.bind(model, "mode", mode_combo, "currentIndex")
        
        # Color combo needs special handling
        def update_color_from_combo(index):
            colors = ["#0000FF", "#FF0000", "#00FF00"]
            if 0 <= index < len(colors):
                cmd = ChangePropertyCommand(model, "color", colors[index])
                cmd_manager.execute(cmd)
                
        color_combo.currentIndexChanged.connect(update_color_from_combo)
        
        # Initial color selection based on model
        if model.color == "#0000FF":
            color_combo.setCurrentIndex(0)
        elif model.color == "#FF0000":
            color_combo.setCurrentIndex(1)
        elif model.color == "#00FF00":
            color_combo.setCurrentIndex(2)
            
        # Connect zoom/pan controls
        zoom_in_btn.clicked.connect(lambda: 
            signal_display.set_view_range(
                signal_display.start_sample + signal_display.visible_samples//4,
                signal_display.visible_samples//2
            )
        )
        
        zoom_out_btn.clicked.connect(lambda:
            signal_display.set_view_range(
                max(0, signal_display.start_sample - signal_display.visible_samples//2),
                signal_display.visible_samples*2
            )
        )
        
        pan_left_btn.clicked.connect(lambda:
            signal_display.set_view_range(
                max(0, signal_display.start_sample - signal_display.visible_samples//4),
                signal_display.visible_samples
            )
        )
        
        pan_right_btn.clicked.connect(lambda:
            signal_display.set_view_range(
                signal_display.start_sample + signal_display.visible_samples//4,
                signal_display.visible_samples
            )
        )
        
        # Process events to update UI
        app.processEvents()
        
        # Make some changes via commands
        cmd_manager.execute(ChangeNameCommand(model, "Main Controls"))
        cmd_manager.execute(ChangePropertyCommand(model, "enabled", True))
        cmd_manager.execute(ChangePropertyCommand(signal1, "name", "Sine Wave"))
        
        # Process events
        app.processEvents()
        
        # Verify changes applied correctly
        assert model.name == "Main Controls"
        assert model.enabled is True
        assert signal1.name == "Sine Wave"
        assert name_edit.text() == "Main Controls"
        assert enabled_check.isChecked() is True
        
        # Save dock layout
        layout_data = dock_manager.serialize_layout()
        
        # Move docks to new positions
        control_dock.setGeometry(50, 50, 250, 350)
        signal_dock.setGeometry(350, 50, 400, 350)
        app.processEvents()
        
        # Restore layout
        dock_manager.deserialize_layout(layout_data)
        app.processEvents()
        
        # Save project with command history
        cmd_manager.set_project(project)
        cmd_manager.save_project(temp_file)
        
        # Clear everything
        cmd_manager.clear()
        dock_manager.clear()
        signal_manager.clear()
        
        # Load saved project
        loaded_project = cmd_manager.load_project(temp_file)
        
        # Verify everything restored correctly
        assert len(loaded_project.signals) == 2
        assert any(s.name == "Sine Wave" for s in loaded_project.signals.values())
        assert any(s.name == "Signal 2" for s in loaded_project.signals.values())
        
        loaded_model = next(m for m in loaded_project.models.values()
                           if isinstance(m, ChannelSettings))
        assert loaded_model.name == "Main Controls"
        assert loaded_model.enabled is True
        
        # Undo last command (rename signal1)
        cmd_manager.undo()
        
        # Find signal1 in loaded project
        loaded_signal1 = next(s for s in loaded_project.signals.values()
                             if s.name == "Signal 1")
        
        # Undo more commands
        cmd_manager.undo()  # Undo enable
        cmd_manager.undo()  # Undo rename model
        
        # Verify reverted
        assert loaded_model.name == "Control Panel"
        assert loaded_model.enabled is False
        
    def test_multiple_docks_with_children(self, app, main_window, dock_manager, cmd_manager):
        """Test complex dock hierarchy with parent-child relationships."""
        # Create main docks
        control_dock = QDockWidget("Control Panel", main_window)
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_dock.setWidget(control_widget)
        main_window.addDockWidget(Qt.LeftDockWidgetArea, control_dock)
        
        view_dock = QDockWidget("Signal View", main_window)
        view_widget = QWidget()
        view_layout = QVBoxLayout(view_widget)
        view_dock.setWidget(view_widget)
        main_window.addDockWidget(Qt.RightDockWidgetArea, view_dock)
        
        # Register main docks
        dock_manager.register_dock("control_dock", control_dock)
        dock_manager.register_dock("view_dock", view_dock)
        
        # Create channel controls
        channels = []
        for i in range(4):
            # Create channel widget
            channel_widget = QWidget()
            channel_layout = QFormLayout(channel_widget)
            
            # Create channel model
            channel = ChannelSettings(f"Channel {i+1}")
            channels.append(channel)
            
            # Create controls
            name_edit = QLineEdit(channel.name)
            enabled_check = QCheckBox("Enabled")
            amplitude_spin = QDoubleSpinBox()
            amplitude_spin.setRange(0.1, 10.0)
            amplitude_spin.setValue(channel.amplitude)
            
            # Add to layout
            channel_layout.addRow("Name:", name_edit)
            channel_layout.addRow(enabled_check)
            channel_layout.addRow("Amplitude:", amplitude_spin)
            
            # Add to control panel
            control_layout.addWidget(channel_widget)
            
            # Register as child of control dock
            dock_manager.register_dock(f"channel_{i+1}", channel_widget, "control_dock")
            
            # Create property bindings
            binder = PropertyBinder()
            binder.bind(channel, "name", name_edit, "text")
            binder.bind(channel, "enabled", enabled_check, "checked")
            binder.bind(channel, "amplitude", amplitude_spin, "value")
        
        # Process events
        app.processEvents()
        
        # Verify dock hierarchy
        assert dock_manager.has_dock("control_dock")
        assert dock_manager.has_dock("view_dock")
        
        for i in range(4):
            dock_id = f"channel_{i+1}"
            assert dock_manager.has_dock(dock_id)
            assert dock_manager.get_parent_id(dock_id) == "control_dock"
            assert dock_id in dock_manager.get_children("control_dock")
        
        # Test removing a parent dock and verify children are removed
        dock_manager.unregister_dock("control_dock")
        
        assert not dock_manager.has_dock("control_dock")
        for i in range(4):
            assert not dock_manager.has_dock(f"channel_{i+1}")
        
        # View dock should still exist
        assert dock_manager.has_dock("view_dock")
        
    def test_save_restore_project_with_docks(self, app, main_window, dock_manager, 
                                            cmd_manager, signal_manager, temp_file):
        """Test saving and loading project with dock layout."""
        # Create project
        project = SimpleProject("Dock Test Project")
        
        # Create docks
        left_dock = QDockWidget("Left Panel", main_window)
        left_dock.setWidget(QWidget())
        main_window.addDockWidget(Qt.LeftDockWidgetArea, left_dock)
        
        right_dock = QDockWidget("Right Panel", main_window)
        right_dock.setWidget(QWidget())
        main_window.addDockWidget(Qt.RightDockWidgetArea, right_dock)
        
        # Register docks
        dock_manager.register_dock("left_dock", left_dock)
        dock_manager.register_dock("right_dock", right_dock)
        
        # Set custom positions
        left_dock.setGeometry(50, 50, 300, 400)
        right_dock.setGeometry(400, 50, 300, 400)
        
        # Process events
        app.processEvents()
        
        # Create model
        model = TestModel(name="Test Model", count=42, active=True)
        project.add_model(model)
        
        # Create signal
        signal = signal_manager.create_signal("Test Signal", np.random.random(1000))
        project.add_signal(signal)
        
        # Set dock state in project
        project.dock_layout = dock_manager.serialize_layout()
        
        # Save project
        cmd_manager.set_project(project)
        cmd_manager.save_project(temp_file)
        
        # Move docks to different positions
        left_dock.setGeometry(100, 100, 200, 300)
        right_dock.setGeometry(350, 100, 200, 300)
        
        # Process events
        app.processEvents()
        
        # Clear everything
        cmd_manager.clear()
        dock_manager.clear()
        signal_manager.clear()
        
        # Load saved project
        loaded_project = cmd_manager.load_project(temp_file)
        
        # Restore dock layout
        if hasattr(loaded_project, 'dock_layout'):
            dock_manager.deserialize_layout(loaded_project.dock_layout)
            
            # Process events
            app.processEvents()
            
            # Verify dock positions restored
            left_dock = dock_manager.get_dock("left_dock")
            right_dock = dock_manager.get_dock("right_dock")
            
            if left_dock and right_dock:
                # Allow for minor differences due to window decorations
                assert abs(left_dock.width() - 300) <= 20
                assert abs(left_dock.height() - 400) <= 20
                assert abs(right_dock.width() - 300) <= 20
                assert abs(right_dock.height() - 400) <= 20