# Command Widgets Implementation and Usage Guide

## Overview

We've implemented a comprehensive set of PySide6 widgets that integrate with the command system, providing automatic undo/redo functionality, property binding, and serialization support. These widgets are built around the `BaseCommandWidget` class which handles the core functionality.

## Implemented Widgets

1. **CommandLineEdit** - For single-line text input
2. **CommandSpinBox** - For integer input
3. **CommandDoubleSpinBox** - For floating-point input
4. **CommandCheckBox** - For boolean values
5. **CommandSlider** - For range-based values
6. **CommandComboBox** - For selection from a list
7. **CommandTextEdit** - For multi-line text
8. **CommandDateEdit** - For date selection

## Architecture

The command widget system is built on several key components:

- **BaseCommandWidget** - Base class for all command widgets that handles property binding, command generation, and serialization
- **CommandTriggerMode** - Enum to control when commands are generated (IMMEDIATE, DELAYED, ON_EDIT_FINISHED)
- **Observable** and **ObservableProperty** - Model classes that support observation of property changes
- **PropertyCommand** - Command class that handles property changes for undo/redo support
- **CommandManager** - Central manager for executing, undoing, and redoing commands

## Basic Usage

To use a command widget:

1. Create an `Observable` model with `ObservableProperty` attributes
2. Instantiate the appropriate command widget
3. Bind widget properties to observable properties
4. Configure the command trigger mode as needed

### Example

```python
# 1. Create an observable model
class Person(Observable):
    def __init__(self):
        super().__init__("Person")
        self.name = ObservableProperty("John Doe", self)
        self.age = ObservableProperty(30, self)

# 2. Instantiate the model and widgets
person = Person()
name_edit = CommandLineEdit()
age_spinbox = CommandSpinBox()

# 3. Bind widget properties to observable properties
name_edit.bind_to_text_property(person.get_id(), "name")
age_spinbox.bind_to_value_property(person.get_id(), "age")

# 4. Configure command trigger modes
name_edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
age_spinbox.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
```

## Command Trigger Modes

Each widget supports three trigger modes that control when commands are generated:

1. **IMMEDIATE** - Commands are generated immediately on any change (e.g., every keystroke)
2. **DELAYED** - Commands are generated after a specified delay of inactivity (good for rapid changes)
3. **ON_EDIT_FINISHED** - Commands are generated only when editing is complete (e.g., focus changes)

Choose the appropriate mode based on the widget type and user experience:

| Widget Type | Recommended Mode | Rationale |
|-------------|------------------|-----------|
| Spin boxes  | IMMEDIATE        | Users expect immediate feedback for value changes |
| Text fields | ON_EDIT_FINISHED | Avoids creating commands for every keystroke |
| Checkboxes  | IMMEDIATE        | Binary changes are discrete events |
| Sliders     | DELAYED          | Prevents excessive commands during dragging |
| Combo boxes | IMMEDIATE        | Selection changes are discrete events |

## Extending the System

To create a new command widget:

1. Inherit from both the PySide6 widget and `BaseCommandWidget`
2. Call `initiate_widget()` in the constructor
3. Implement `_update_widget_property()` to handle property updates
4. Connect appropriate widget signals to handle value changes
5. Add convenience methods for binding and unbinding properties
6. Implement serialization support as needed

### Example Template

```python
class CommandMyWidget(QMyWidget, BaseCommandWidget):
    def __init__(self, container_id=None, location=None, parent=None):
        # Initialize widget first
        QMyWidget.__init__(self, parent)
        
        # Initialize command functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.MY_WIDGET, container_id, location)
        
        # Connect signals
        self.valueChanged.connect(self._handle_value_changed)
        
        # Set default trigger mode
        self.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
    
    def _update_widget_property(self, property_name, value):
        self.blockSignals(True)
        if property_name == "value":
            self.setValue(value)
        self.blockSignals(False)
    
    def _handle_value_changed(self, value):
        self._on_widget_value_changed("value", value)
```

## Best Practices

1. **Always block signals** when updating widget properties to prevent recursion
2. **Set appropriate trigger modes** for different widget types
3. **Provide convenience methods** for binding and unbinding properties
4. **Clean up resources** by calling `unregister_widget()` when widgets are destroyed
5. **Handle serialization** for all relevant widget properties
6. **Use type checking** to handle different value formats in `_update_widget_property()`

## Serialization

Each widget implements `get_serialization()` and `deserialize()` to support saving and restoring widget state:

```python
def get_serialization(self):
    result = super().get_serialization()
    # Add widget-specific properties
    result['widget_props'] = {
        'specific_property': self.specificProperty()
    }
    return result

def deserialize(self, data):
    if not super().deserialize(data):
        return False
    # Handle widget-specific properties
    if 'widget_props' in data:
        props = data['widget_props']
        if 'specific_property' in props:
            self.setSpecificProperty(props['specific_property'])
    return True
```

## Conclusion

These command widgets provide a powerful foundation for building applications with comprehensive undo/redo support. By integrating directly with the command system, they require minimal additional code to implement robust history tracking and property binding.

The demo application (`command_widgets_test.py`) showcases all these widgets working together in a practical product management interface.