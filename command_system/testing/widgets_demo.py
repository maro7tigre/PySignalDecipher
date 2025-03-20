"""
command_system/testing/widgets_demo.py
Demonstration of command-aware widgets
"""
import sys
import os
from datetime import date

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt

# Import from the command system
from command_system import Observable, ObservableProperty, get_command_manager
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandDoubleSpinBox,
    CommandComboBox, CommandCheckBox, CommandSlider,
    CommandDateEdit, CommandTextEdit
)


class DemoModel(Observable):
    """Model for the demo with various property types."""
    
    # Text properties
    name = ObservableProperty[str](default="John Doe")
    description = ObservableProperty[str](default="This is a demo model")
    
    # Numeric properties
    count = ObservableProperty[int](default=0)
    price = ObservableProperty[float](default=9.99)
    percentage = ObservableProperty[int](default=50)
    
    # Selection properties
    category_index = ObservableProperty[int](default=0)
    is_active = ObservableProperty[bool](default=True)
    
    # Date property
    creation_date = ObservableProperty[date](default=date.today())


class MainWindow(QMainWindow):
    """Main window for the widgets demo."""
    
    def __init__(self):
        """Initialize the window."""
        super().__init__()
        
        # Set up the window
        self.setWindowTitle("Command-Aware Widgets Demo")
        self.setMinimumSize(700, 600)
        
        # Get command manager
        self.cmd_manager = get_command_manager()
        
        # Create model
        self.model = DemoModel()
        
        # Create UI
        self._create_ui()
        
        # Initial update of button states
        self._update_undo_redo_buttons()
        
    def _create_ui(self):
        """Create the UI elements."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Status and buttons at top
        status_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Spacer
        status_layout.addStretch()
        
        # Undo/Redo buttons
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._on_undo)
        self.undo_button.setEnabled(False)
        status_layout.addWidget(self.undo_button)
        
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._on_redo)
        self.redo_button.setEnabled(False)
        status_layout.addWidget(self.redo_button)
        
        main_layout.addLayout(status_layout)
        
        # Create grid layout for all widgets
        grid_layout = QGridLayout()
        
        # Text widgets
        text_group = QGroupBox("Text Widgets")
        text_layout = QGridLayout(text_group)
        
        # Line edit
        text_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = CommandLineEdit()
        self.name_edit.bind_to_model(self.model, "name")
        text_layout.addWidget(self.name_edit, 0, 1)
        
        # Text edit
        text_layout.addWidget(QLabel("Description:"), 1, 0)
        self.desc_edit = CommandTextEdit()
        self.desc_edit.bind_to_model(self.model, "description")
        text_layout.addWidget(self.desc_edit, 1, 1)
        
        grid_layout.addWidget(text_group, 0, 0)
        
        # Number widgets
        number_group = QGroupBox("Number Widgets")
        number_layout = QGridLayout(number_group)
        
        # Spin box
        number_layout.addWidget(QLabel("Count:"), 0, 0)
        self.count_spin = CommandSpinBox()
        self.count_spin.setRange(0, 100)
        self.count_spin.bind_to_model(self.model, "count")
        number_layout.addWidget(self.count_spin, 0, 1)
        
        # Double spin box
        number_layout.addWidget(QLabel("Price:"), 1, 0)
        self.price_spin = CommandDoubleSpinBox()
        self.price_spin.setRange(0.0, 1000.0)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$")
        self.price_spin.bind_to_model(self.model, "price")
        number_layout.addWidget(self.price_spin, 1, 1)
        
        # Slider
        number_layout.addWidget(QLabel("Percentage:"), 2, 0)
        self.percent_slider = CommandSlider(Qt.Orientation.Horizontal)
        self.percent_slider.setRange(0, 100)
        self.percent_slider.bind_to_model(self.model, "percentage")
        number_layout.addWidget(self.percent_slider, 2, 1)
        
        grid_layout.addWidget(number_group, 0, 1)
        
        # Selection widgets
        selection_group = QGroupBox("Selection Widgets")
        selection_layout = QGridLayout(selection_group)
        
        # Combo box
        selection_layout.addWidget(QLabel("Category:"), 0, 0)
        self.category_combo = CommandComboBox()
        self.category_combo.addItems(["Category A", "Category B", "Category C"])
        self.category_combo.bind_to_model(self.model, "category_index")
        selection_layout.addWidget(self.category_combo, 0, 1)
        
        # Check box
        selection_layout.addWidget(QLabel("Active:"), 1, 0)
        self.active_check = CommandCheckBox()
        self.active_check.bind_to_model(self.model, "is_active")
        selection_layout.addWidget(self.active_check, 1, 1)
        
        # Date edit
        selection_layout.addWidget(QLabel("Creation Date:"), 2, 0)
        self.date_edit = CommandDateEdit()
        self.date_edit.bind_to_model(self.model, "creation_date")
        selection_layout.addWidget(self.date_edit, 2, 1)
        
        grid_layout.addWidget(selection_group, 1, 0)
        
        # Model Value Display
        values_group = QGroupBox("Current Model Values")
        values_layout = QVBoxLayout(values_group)
        
        self.model_values_label = QLabel()
        self.model_values_label.setTextFormat(Qt.TextFormat.RichText)
        values_layout.addWidget(self.model_values_label)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Values")
        refresh_button.clicked.connect(self._update_model_display)
        values_layout.addWidget(refresh_button)
        
        grid_layout.addWidget(values_group, 1, 1)
        
        main_layout.addLayout(grid_layout)
        
        # Set main widget
        self.setCentralWidget(main_widget)
        
        # Connect property observers
        for prop_name in ["name", "description", "count", "price", 
                         "percentage", "category_index", "is_active", 
                         "creation_date"]:
            self.model.add_property_observer(prop_name, self._on_model_changed)
            
        # Initial update
        self._update_model_display()
        
    def _on_model_changed(self, property_name, old_value, new_value):
        """Handle model property changes."""
        self.status_label.setText(f"Property '{property_name}' changed: {old_value} → {new_value}")
        self._update_undo_redo_buttons()
        self._update_model_display()
        
    def _update_model_display(self):
        """Update the model values display."""
        html = "<table>"
        html += f"<tr><td><b>Name:</b></td><td>{self.model.name}</td></tr>"
        html += f"<tr><td><b>Description:</b></td><td>{self.model.description}</td></tr>"
        html += f"<tr><td><b>Count:</b></td><td>{self.model.count}</td></tr>"
        html += f"<tr><td><b>Price:</b></td><td>${self.model.price:.2f}</td></tr>"
        html += f"<tr><td><b>Percentage:</b></td><td>{self.model.percentage}%</td></tr>"
        
        category = ["Category A", "Category B", "Category C"][self.model.category_index]
        html += f"<tr><td><b>Category:</b></td><td>{category}</td></tr>"
        
        html += f"<tr><td><b>Active:</b></td><td>{'Yes' if self.model.is_active else 'No'}</td></tr>"
        html += f"<tr><td><b>Creation Date:</b></td><td>{self.model.creation_date.isoformat()}</td></tr>"
        html += "</table>"
        
        self.model_values_label.setText(html)
        
    def _update_undo_redo_buttons(self):
        """Update undo/redo button states."""
        self.undo_button.setEnabled(self.cmd_manager.can_undo())
        self.redo_button.setEnabled(self.cmd_manager.can_redo())
        
    def _on_undo(self):
        """Handle undo button click."""
        if self.cmd_manager.undo():
            self.status_label.setText("Undo: Success")
        else:
            self.status_label.setText("Undo: Nothing to undo")
        self._update_undo_redo_buttons()
        
    def _on_redo(self):
        """Handle redo button click."""
        if self.cmd_manager.redo():
            self.status_label.setText("Redo: Success")
        else:
            self.status_label.setText("Redo: Nothing to redo")
        self._update_undo_redo_buttons()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()