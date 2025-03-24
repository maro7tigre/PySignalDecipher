"""
Qt-specific widget bindings for connecting observable properties to Qt widgets.
"""

from typing import Any

from .property_binding import Binding

# MARK: - Widget Bindings

class LineEditBinding(Binding):
    """Binding for QLineEdit widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect textChanged signal."""
        self.widget.textChanged.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect textChanged signal."""
        try:
            self.widget.textChanged.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> str:
        """Get text from widget."""
        return self.widget.text()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set text in widget."""
        self.widget.setText(str(value) if value is not None else "")


class SpinBoxBinding(Binding):
    """Binding for QSpinBox widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect valueChanged signal."""
        self.widget.valueChanged.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect valueChanged signal."""
        try:
            self.widget.valueChanged.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> int:
        """Get value from widget."""
        return self.widget.value()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set value in widget."""
        try:
            self.widget.setValue(int(value))
        except (ValueError, TypeError):
            # Use minimum value if conversion fails
            self.widget.setValue(self.widget.minimum())


class DoubleSpinBoxBinding(Binding):
    """Binding for QDoubleSpinBox widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect valueChanged signal."""
        self.widget.valueChanged.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect valueChanged signal."""
        try:
            self.widget.valueChanged.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> float:
        """Get value from widget."""
        return self.widget.value()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set value in widget."""
        try:
            self.widget.setValue(float(value))
        except (ValueError, TypeError):
            # Use minimum value if conversion fails
            self.widget.setValue(self.widget.minimum())


class ComboBoxBinding(Binding):
    """Binding for QComboBox widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect currentIndexChanged signal."""
        self.widget.currentIndexChanged.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect currentIndexChanged signal."""
        try:
            self.widget.currentIndexChanged.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> int:
        """Get current index from widget."""
        return self.widget.currentIndex()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set current index in widget."""
        try:
            index = int(value)
            if 0 <= index < self.widget.count():
                self.widget.setCurrentIndex(index)
        except (ValueError, TypeError):
            # Use first item if conversion fails
            self.widget.setCurrentIndex(0)


class CheckBoxBinding(Binding):
    """Binding for QCheckBox widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect toggled signal."""
        self.widget.toggled.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect toggled signal."""
        try:
            self.widget.toggled.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> bool:
        """Get checked state from widget."""
        return self.widget.isChecked()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set checked state in widget."""
        self.widget.setChecked(bool(value))


class SliderBinding(Binding):
    """Binding for QSlider widgets."""
    
    def _connect_widget_signals(self) -> None:
        """Connect valueChanged signal."""
        self.widget.valueChanged.connect(self._on_widget_changed)
        
    def _disconnect_widget_signals(self) -> None:
        """Disconnect valueChanged signal."""
        try:
            self.widget.valueChanged.disconnect(self._on_widget_changed)
        except (TypeError, RuntimeError):
            # Already disconnected
            pass
        
    def _get_widget_value(self) -> int:
        """Get value from widget."""
        return self.widget.value()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set value in widget."""
        try:
            self.widget.setValue(int(value))
        except (ValueError, TypeError):
            # Use minimum value if conversion fails
            self.widget.setValue(self.widget.minimum())


class LabelBinding(Binding):
    """
    One-way binding for QLabel widgets.
    Updates label from model, but not model from label.
    """
    
    def _connect_widget_signals(self) -> None:
        """No signals to connect for one-way binding."""
        pass
        
    def _disconnect_widget_signals(self) -> None:
        """No signals to disconnect."""
        pass
        
    def _get_widget_value(self) -> str:
        """Get text from widget."""
        return self.widget.text()
        
    def _set_widget_value(self, value: Any) -> None:
        """Set text in widget."""
        self.widget.setText(str(value) if value is not None else "")
        
    def _on_widget_changed(self) -> None:
        """Override to do nothing, since this is a one-way binding."""
        pass