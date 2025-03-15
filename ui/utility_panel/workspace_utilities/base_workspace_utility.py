"""
Base workspace utility for PySignalDecipher.

This module provides a base class for workspace-specific utilities with a
standardized approach to control creation and automatic distribution.
"""

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QEvent


class BaseWorkspaceUtility(QWidget):
    """
    Base class for workspace-specific utilities.
    
    Provides a standardized approach for creating and distributing controls
    in a grid layout. Subclasses only need to define their controls in
    register_controls() without worrying about layout management.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the base workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self._theme_manager = theme_manager
        
        # Reference to the workspace widget
        self._workspace = None
        
        # Minimum control height
        self._min_control_height = 28
        
        # Fixed label width for alignment
        self._label_width = 80
        
        # Dictionary to store all created controls by their IDs
        self._control_widgets = {}
        
        # Control definition list
        self._control_definitions = []
        
        # Layout properties
        self._max_columns = 4
        
        # Set up the base UI
        self._setup_base_ui()
        
        # Register controls (to be implemented by subclasses)
        self.register_controls()
        
        # Build the layout
        self._build_layout()
        
    def _setup_base_ui(self):
        """Set up the base user interface for workspace utilities."""
        # Main layout - using grid for precise positioning
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(8, 8, 8, 8)
        self._grid_layout.setHorizontalSpacing(12)
        self._grid_layout.setVerticalSpacing(8)
        
    def _create_label(self, text):
        """
        Create a label with consistent styling.
        
        Args:
            text: Text for the label
            
        Returns:
            QLabel: The created label
        """
        label = QLabel(text)
        label.setMinimumHeight(self._min_control_height)
        label.setFixedWidth(self._label_width)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label
    
    def add_combo_box(self, id, label, items=None, enabled=True, callback=None):
        """
        Add a combo box control definition.
        
        Args:
            id: Unique identifier for this control
            label: Label text for the control
            items: List of items to add to the combo box
            enabled: Whether the control is initially enabled
            callback: Function to call when selection changes
        """
        self._control_definitions.append({
            "type": "combo",
            "id": id,
            "label": label,
            "items": items or [],
            "enabled": enabled,
            "callback": callback
        })
        
    def add_spin_box(self, id, label, minimum=0, maximum=100, value=0, enabled=True, callback=None):
        """
        Add a spin box control definition.
        
        Args:
            id: Unique identifier for this control
            label: Label text for the control
            minimum: Minimum value
            maximum: Maximum value
            value: Initial value
            enabled: Whether the control is initially enabled
            callback: Function to call when value changes
        """
        self._control_definitions.append({
            "type": "spin",
            "id": id,
            "label": label,
            "minimum": minimum,
            "maximum": maximum,
            "value": value,
            "enabled": enabled,
            "callback": callback
        })
        
    def add_double_spin_box(self, id, label, minimum=0.0, maximum=100.0, value=0.0, 
                           decimals=2, suffix=None, enabled=True, callback=None):
        """
        Add a double spin box control definition.
        
        Args:
            id: Unique identifier for this control
            label: Label text for the control
            minimum: Minimum value
            maximum: Maximum value
            value: Initial value
            decimals: Number of decimal places to display
            suffix: Optional suffix text (e.g., " MHz")
            enabled: Whether the control is initially enabled
            callback: Function to call when value changes
        """
        self._control_definitions.append({
            "type": "double_spin",
            "id": id,
            "label": label,
            "minimum": minimum,
            "maximum": maximum,
            "value": value,
            "decimals": decimals,
            "suffix": suffix,
            "enabled": enabled,
            "callback": callback
        })
        
    def add_check_box(self, id, text, checked=False, enabled=True, callback=None):
        """
        Add a check box control definition.
        
        Args:
            id: Unique identifier for this control
            text: Text for the check box
            checked: Whether the check box is initially checked
            enabled: Whether the control is initially enabled
            callback: Function to call when checked state changes
        """
        self._control_definitions.append({
            "type": "check",
            "id": id,
            "text": text,
            "checked": checked,
            "enabled": enabled,
            "callback": callback
        })
        
    def add_button(self, id, text, enabled=True, callback=None):
        """
        Add a button control definition.
        
        Args:
            id: Unique identifier for this control
            text: Text for the button
            enabled: Whether the button is initially enabled
            callback: Function to call when button is clicked
        """
        self._control_definitions.append({
            "type": "button",
            "id": id,
            "text": text,
            "enabled": enabled,
            "callback": callback
        })
        
    def register_controls(self):
        """
        Register all controls for this workspace utility.
        
        To be overridden by subclasses. Subclasses should call add_*
        methods to define their controls.
        """
        pass
    
    def _build_layout(self):
        """
        Build the layout by creating and positioning all controls.
        """
        # Clear existing layout
        self._clear_layout()
        
        # Clear widget references
        self._control_widgets = {}
        
        # Determine number of columns based on width
        self._calculate_columns()
        
        # Create and position all controls
        self._create_and_position_controls()
        
        # Set up column stretching
        self._setup_column_stretching()
    
    def _clear_layout(self):
        """
        Clear the existing layout.
        """
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
    def _calculate_columns(self):
        """
        Calculate the number of columns based on available width.
        """
        width = self.width()
        
        if width < 300:
            self._max_columns = 1
        elif width < 550:
            self._max_columns = 2
        elif width < 800:
            self._max_columns = 3
        else:
            self._max_columns = 4
    
    def _create_and_position_controls(self):
        """
        Create and position all controls based on their definitions.
        """
        # Calculate positions
        row = 0
        col = 0
        
        # Create each control and add to layout
        for definition in self._control_definitions:
            if definition["type"] == "combo":
                self._create_combo_box(definition, row, col)
            elif definition["type"] == "spin":
                self._create_spin_box(definition, row, col)
            elif definition["type"] == "double_spin":
                self._create_double_spin_box(definition, row, col)
            elif definition["type"] == "check":
                self._create_check_box(definition, row, col)
            elif definition["type"] == "button":
                self._create_button(definition, row, col)
            
            # Move to next position
            col += 1
            if col >= self._max_columns:
                col = 0
                row += 1
    
    def _create_combo_box(self, definition, row, col):
        """
        Create and position a combo box based on its definition.
        
        Args:
            definition: Control definition
            row: Row position
            col: Column position
        """
        label = self._create_label(definition["label"])
        
        combo = QComboBox()
        combo.setMinimumHeight(self._min_control_height)
        
        # Add items
        for item in definition["items"]:
            combo.addItem(item)
        
        # Set enabled state
        combo.setEnabled(definition["enabled"])
        
        # Connect callback if provided
        if definition["callback"]:
            combo.currentTextChanged.connect(definition["callback"])
        
        # Add to layout
        grid_col = col * 2  # Each logical column uses 2 grid columns
        self._grid_layout.addWidget(label, row, grid_col)
        self._grid_layout.addWidget(combo, row, grid_col + 1)
        
        # Store reference
        self._control_widgets[definition["id"]] = combo
    
    def _create_spin_box(self, definition, row, col):
        """
        Create and position a spin box based on its definition.
        
        Args:
            definition: Control definition
            row: Row position
            col: Column position
        """
        label = self._create_label(definition["label"])
        
        spin = QSpinBox()
        spin.setMinimumHeight(self._min_control_height)
        spin.setRange(definition["minimum"], definition["maximum"])
        spin.setValue(definition["value"])
        spin.setEnabled(definition["enabled"])
        
        # Connect callback if provided
        if definition["callback"]:
            spin.valueChanged.connect(definition["callback"])
        
        # Add to layout
        grid_col = col * 2
        self._grid_layout.addWidget(label, row, grid_col)
        self._grid_layout.addWidget(spin, row, grid_col + 1)
        
        # Store reference
        self._control_widgets[definition["id"]] = spin
    
    def _create_double_spin_box(self, definition, row, col):
        """
        Create and position a double spin box based on its definition.
        
        Args:
            definition: Control definition
            row: Row position
            col: Column position
        """
        label = self._create_label(definition["label"])
        
        spin = QDoubleSpinBox()
        spin.setMinimumHeight(self._min_control_height)
        spin.setRange(definition["minimum"], definition["maximum"])
        spin.setValue(definition["value"])
        spin.setDecimals(definition["decimals"])
        
        if definition["suffix"]:
            spin.setSuffix(definition["suffix"])
            
        spin.setEnabled(definition["enabled"])
        
        # Connect callback if provided
        if definition["callback"]:
            spin.valueChanged.connect(definition["callback"])
        
        # Add to layout
        grid_col = col * 2
        self._grid_layout.addWidget(label, row, grid_col)
        self._grid_layout.addWidget(spin, row, grid_col + 1)
        
        # Store reference
        self._control_widgets[definition["id"]] = spin
    
    def _create_check_box(self, definition, row, col):
        """
        Create and position a check box based on its definition.
        
        Args:
            definition: Control definition
            row: Row position
            col: Column position
        """
        check = QCheckBox(definition["text"])
        check.setMinimumHeight(self._min_control_height)
        check.setChecked(definition["checked"])
        check.setEnabled(definition["enabled"])
        
        # Connect callback if provided
        if definition["callback"]:
            check.stateChanged.connect(definition["callback"])
        
        # Add to layout - spans 2 columns
        grid_col = col * 2
        self._grid_layout.addWidget(check, row, grid_col, 1, 2)
        
        # Store reference
        self._control_widgets[definition["id"]] = check
    
    def _create_button(self, definition, row, col):
        """
        Create and position a button based on its definition.
        
        Args:
            definition: Control definition
            row: Row position
            col: Column position
        """
        button = QPushButton(definition["text"])
        button.setMinimumHeight(self._min_control_height)
        button.setEnabled(definition["enabled"])
        
        # Connect callback if provided
        if definition["callback"]:
            button.clicked.connect(definition["callback"])
        
        # Add to layout - spans 2 columns for consistency
        grid_col = col * 2
        self._grid_layout.addWidget(button, row, grid_col, 1, 2)
        
        # Store reference
        self._control_widgets[definition["id"]] = button
    
    def _setup_column_stretching(self):
        """
        Set up column stretching for even distribution of space.
        """
        for col in range(self._max_columns * 2):
            # For odd columns (control columns), give stretch
            if col % 2 == 1:
                self._grid_layout.setColumnStretch(col, 1)
            else:
                self._grid_layout.setColumnStretch(col, 0)  # No stretch for label columns
    
    def get_control(self, id):
        """
        Get a control widget by its ID.
        
        Args:
            id: ID of the control to get
            
        Returns:
            The control widget, or None if not found
        """
        return self._control_widgets.get(id)
    
    def resizeEvent(self, event):
        """
        Handle resize events.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        
        # Check if we need to redistribute controls
        old_max_columns = self._max_columns
        self._calculate_columns()
        
        if old_max_columns != self._max_columns:
            # Only rebuild if the number of columns changed
            self._build_layout()
    
    def set_workspace(self, workspace):
        """
        Set the workspace associated with this utility panel.
        
        Args:
            workspace: Reference to the workspace widget
        """
        self._workspace = workspace
        self._workspace_updated()
        
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        
        To be overridden by subclasses.
        """
        pass
        
    def apply_theme(self, theme_manager):
        """
        Apply the current theme to this utility panel.
        
        Args:
            theme_manager: Reference to the ThemeManager
        """
        self._theme_manager = theme_manager