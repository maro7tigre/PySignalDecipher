"""
Property binding system for UI integration.
"""
from abc import ABC, abstractmethod
from command_system.command import PropertyCommand
from command_system import get_command_manager


class Binding(ABC):
    """
    Abstract base class for property bindings.
    Manages the connection between model properties and UI widgets.
    """
    
    def __init__(self, model, property_name, widget, command_manager=None):
        """
        Initialize binding.
        
        Args:
            model: Model object with observable property
            property_name (str): Name of the property to bind
            widget: UI widget to bind to
            command_manager: Command manager instance (optional)
        """
        self.model = model
        self.property_name = property_name
        self.widget = widget
        self.command_manager = command_manager or get_command_manager()
        self.observer_id = None
        self.updating_model = False
        self.updating_widget = False
        
    def activate(self):
        """
        Activate the binding.
        Connects property observers and widget signals.
        """
        # Observe model property changes
        self.observer_id = self.model.add_property_observer(
            self.property_name, self._on_property_changed
        )
        
        # Connect widget signals
        self._connect_widget_signals()
        
        # Initialize widget with model value
        self._update_widget_from_model()
        
    def deactivate(self):
        """
        Deactivate the binding.
        Disconnects property observers and widget signals.
        """
        # Remove property observer
        if self.observer_id:
            self.model.remove_property_observer(self.property_name, self.observer_id)
            self.observer_id = None
            
        # Disconnect widget signals
        self._disconnect_widget_signals()
        
    def _on_property_changed(self, property_name, old_value, new_value):
        """
        Called when the bound property changes.
        Updates the widget with the new value.
        
        Args:
            property_name (str): Name of the property that changed
            old_value: Previous value
            new_value: New value
        """
        # Prevent infinite recursion
        if self.updating_model:
            return
            
        self.updating_widget = True
        try:
            self._update_widget_from_model()
        finally:
            self.updating_widget = False
            
    def _on_widget_changed(self):
        """
        Called when the widget value changes.
        Updates the model with the new value.
        """
        # Prevent infinite recursion
        if self.updating_widget:
            return
            
        self.updating_model = True
        try:
            value = self._get_widget_value()
            old_value = getattr(self.model, self.property_name)
            
            # Only update if value actually changed
            if value != old_value:
                # Create and execute command
                cmd = PropertyCommand(self.model, self.property_name, value)
                self.command_manager.execute(cmd)
        finally:
            self.updating_model = False
            
    def _update_widget_from_model(self):
        """
        Update the widget with the current model value.
        """
        value = getattr(self.model, self.property_name)
        self._set_widget_value(value)
        
    @abstractmethod
    def _connect_widget_signals(self):
        """
        Connect widget signals for value change notification.
        """
        pass
        
    @abstractmethod
    def _disconnect_widget_signals(self):
        """
        Disconnect widget signals.
        """
        pass
        
    @abstractmethod
    def _get_widget_value(self):
        """
        Get the current value from the widget.
        
        Returns:
            Current widget value
        """
        pass
        
    @abstractmethod
    def _set_widget_value(self, value):
        """
        Set the widget value.
        
        Args:
            value: Value to set
        """
        pass


class PropertyBinder:
    """
    Manages property bindings between models and widgets.
    """
    
    def __init__(self):
        """Initialize property binder."""
        self._bindings = {}
        self._command_manager = get_command_manager()
        
    def bind(self, model, property_name, widget, widget_property):
        """
        Create binding between model property and widget.
        
        Args:
            model: Model object with observable property
            property_name (str): Name of the property to bind
            widget: UI widget to bind to
            widget_property (str): Name of the widget property
            
        Returns:
            str: Binding ID, or None if binding failed
        """
        binding_id = f"{id(model)}:{property_name}:{id(widget)}:{widget_property}"
        
        # Create appropriate binding
        binding = self._create_binding(model, property_name, widget, widget_property)
        
        if binding:
            self._bindings[binding_id] = binding
            binding.activate()
            return binding_id
            
        return None
        
    def unbind(self, binding_id):
        """
        Remove binding.
        
        Args:
            binding_id (str): Binding ID returned by bind()
            
        Returns:
            bool: True if binding was removed
        """
        if binding_id in self._bindings:
            self._bindings[binding_id].deactivate()
            del self._bindings[binding_id]
            return True
        return False
        
    def unbind_all(self):
        """Unbind all bindings."""
        for binding in self._bindings.values():
            binding.deactivate()
        self._bindings.clear()
        
    def _create_binding(self, model, property_name, widget, widget_property):
        """
        Create appropriate binding based on widget type.
        
        Args:
            model: Model object
            property_name (str): Property name
            widget: UI widget
            widget_property (str): Widget property name
            
        Returns:
            Binding: Created binding, or None if binding not supported
        """
        # Import here to avoid circular imports
        from command_system.ui.qt_bindings import (
            LineEditBinding, 
            SpinBoxBinding,
            DoubleSpinBoxBinding,
            ComboBoxBinding,
            CheckBoxBinding,
            SliderBinding,
            LabelBinding,
            TextEditBinding
        )
        
        # Check widget type and property
        try:
            from PySide6.QtWidgets import (
                QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
                QComboBox, QCheckBox, QSlider, QLabel
            )
            
            if isinstance(widget, QLineEdit) and widget_property == "text":
                return LineEditBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QTextEdit) and widget_property == "text":
                return TextEditBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QSpinBox) and widget_property == "value":
                return SpinBoxBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QDoubleSpinBox) and widget_property == "value":
                return DoubleSpinBoxBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QComboBox) and widget_property == "currentIndex":
                return ComboBoxBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QCheckBox) and widget_property == "checked":
                return CheckBoxBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QSlider) and widget_property == "value":
                return SliderBinding(model, property_name, widget, self._command_manager)
            elif isinstance(widget, QLabel) and widget_property == "text":
                return LabelBinding(model, property_name, widget, self._command_manager)
        except ImportError:
            # PySide6 not available
            pass
            
        # No supported binding found
        return None