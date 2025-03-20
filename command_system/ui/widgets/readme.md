# Command-Aware Widgets

This extension to the PySignalDecipher command system provides ready-to-use Qt widgets that automatically integrate with the undo/redo system.

## Benefits

- **Simplicity**: Use these widgets just like normal Qt widgets, but get undo/redo for free
- **Seamless integration**: All widget changes automatically create undoable commands
- **Reduced boilerplate**: No need to manually create commands for every widget change
- **Model binding**: Easy binding to Observable model properties
- **Familiar API**: Same API as standard Qt widgets with minimal additions

## Available Widgets

The library provides command-aware versions of common Qt widgets:

- `CommandLineEdit`: For single-line text input
- `CommandSpinBox`: For integer values
- `CommandDoubleSpinBox`: For floating-point values
- `CommandComboBox`: For selecting from a list of options
- `CommandCheckBox`: For boolean values
- `CommandSlider`: For adjustable numeric values
- `CommandDateEdit`: For date selection
- `CommandTextEdit`: For multi-line text input

## Usage

Here's a simple example of using command-aware widgets with an Observable model:

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from command_system import Observable, ObservableProperty, get_command_manager
from command_system.ui.widgets import CommandLineEdit, CommandSpinBox, CommandCheckBox

# Define a model with observable properties
class PersonModel(Observable):
    name = ObservableProperty[str](default="")
    age = ObservableProperty[int](default=0)
    active = ObservableProperty[bool](default=True)

# Create the application
app = QApplication([])
window = QMainWindow()
central = QWidget()
layout = QVBoxLayout(central)

# Create the model
model = PersonModel()
model.name = "John Doe"
model.age = 30

# Create command-aware widgets
name_edit = CommandLineEdit()
age_spin = CommandSpinBox()
active_check = CommandCheckBox("Active")

# Bind widgets to model properties
name_edit.bind_to_model(model, "name")
age_spin.bind_to_model(model, "age")
active_check.bind_to_model(model, "active")

# Add widgets to layout
layout.addWidget(name_edit)
layout.addWidget(age_spin)
layout.addWidget(active_check)

# Add undo/redo buttons
cmd_manager = get_command_manager()
undo_button = QPushButton("Undo")
undo_button.clicked.connect(cmd_manager.undo)
redo_button = QPushButton("Redo")
redo_button.clicked.connect(cmd_manager.redo)
layout.addWidget(undo_button)
layout.addWidget(redo_button)

# Show the window
window.setCentralWidget(central)
window.show()
app.exec()
```

## Advanced Features

### Custom Command Factory

You can customize how commands are created by setting a custom command factory:

```python
def custom_command_factory(model, property_name, new_value, old_value):
    # Create and return a custom command
    return MyCustomCommand(model, property_name, new_value, old_value)

# Set the custom factory
name_edit.set_command_factory(custom_command_factory)
```

### ComboBox Modes

The `CommandComboBox` supports different value modes:

```python
# Index mode (default)
combo = CommandComboBox(value_mode="index")
combo.bind_to_model(model, "category_index")

# Text mode
combo = CommandComboBox(value_mode="text")
combo.bind_to_model(model, "category_name")

# Data mode
combo = CommandComboBox(value_mode="data")
combo.addItem("Option 1", userData=100)
combo.bind_to_model(model, "category_id")
```

### Disabling Commands

You can temporarily disable command creation:

```python
# Disable commands for bulk operations
widget.enable_commands(False)
# ... make multiple changes ...
widget.enable_commands(True)
```

## See Also

For a complete demonstration, check out the `widgets_demo.py` file in the testing directory.