"""
Base workspace utility for PySignalDecipher.

This module provides a base class for workspace-specific utilities with a dynamic
grid layout system that distributes controls evenly across available space.
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox
from PySide6.QtCore import Qt, QEvent


class BaseWorkspaceUtility(QWidget):
    """
    Base class for workspace-specific utilities.
    
    Provides a dynamic grid layout system that automatically distributes
    controls evenly across the available width.
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
        
        # List to store all controls for dynamic layout
        self._controls = []
        
        # Default item height
        self._item_height = 30
        
        # Set up the base UI
        self._setup_base_ui()
        
    @property
    def item_height(self):
        """Get the height for all items."""
        return self._item_height
        
    @item_height.setter
    def item_height(self, value):
        """Set the height for all items."""
        self._item_height = value
        self._update_control_heights()
        self._update_layout()  # Update layout when height changes
        
    def _update_control_heights(self):
        """Update the height of all controls."""
        for control_type, control in self._controls:
            if control_type in ["label", "button", "combo", "spin", "check"]:
                control.setFixedHeight(self.item_height)
            elif control_type == "pair":
                label, widget = control
                label.setFixedHeight(self.item_height)
                widget.setFixedHeight(self.item_height)
        
    def _setup_base_ui(self):
        """Set up the base user interface for workspace utilities."""
        # Main layout - using grid for dynamic spacing
        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(8, 8, 8, 8)
        self._grid_layout.setHorizontalSpacing(15)
        self._grid_layout.setVerticalSpacing(8)
        
    def _create_label(self, text):
        """
        Create a label without adding it to the layout.
        
        Args:
            text: Text for the label
            
        Returns:
            QLabel: The created label
        """
        label = QLabel(text)
        label.setFixedHeight(self.item_height)
        self._controls.append(("label", label))
        return label
        
    def _create_button(self, text, callback=None):
        """
        Create a button without adding it to the layout.
        
        Args:
            text: Text for the button
            callback: Function to call when button is clicked
            
        Returns:
            QPushButton: The created button
        """
        button = QPushButton(text)
        button.setFixedHeight(self.item_height)
        if callback:
            button.clicked.connect(callback)
        self._controls.append(("button", button))
        return button
        
    def _create_combo_box(self, items=None):
        """
        Create a combo box without adding it to the layout.
        
        Args:
            items: List of items to add to the combo box
            
        Returns:
            QComboBox: The created combo box
        """
        combo = QComboBox()
        combo.setFixedHeight(self.item_height)
        if items:
            for item in items:
                combo.addItem(item)
        self._controls.append(("combo", combo))
        return combo
        
    def _create_spin_box(self, minimum=0, maximum=100, value=0):
        """
        Create a spin box without adding it to the layout.
        
        Args:
            minimum: Minimum value
            maximum: Maximum value
            value: Initial value
            
        Returns:
            QSpinBox: The created spin box
        """
        spin = QSpinBox()
        spin.setFixedHeight(self.item_height)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        self._controls.append(("spin", spin))
        return spin
        
    def _create_check_box(self, text, checked=False):
        """
        Create a check box without adding it to the layout.
        
        Args:
            text: Text for the checkbox
            checked: Initial checked state
            
        Returns:
            QCheckBox: The created check box
        """
        check = QCheckBox(text)
        check.setFixedHeight(self.item_height)
        check.setChecked(checked)
        self._controls.append(("check", check))
        return check
        
    def _create_control_pair(self, label_text, control):
        """
        Create a label-control pair without adding it to the layout.
        
        Args:
            label_text: Text for the label
            control: Control widget
            
        Returns:
            tuple: (QLabel, control widget)
        """
        label = QLabel(label_text)
        label.setFixedHeight(self.item_height)
        # Control's height is already set when it was created
        self._controls.append(("pair", (label, control)))
        return label, control
        
    def _update_layout(self):
        """
        Update the layout to distribute controls evenly.
        This should be called after all controls have been created.
        Fills columns from top to bottom, then left to right.
        """
        # Clear the existing layout
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Number of controls
        num_controls = len(self._controls)
        if num_controls == 0:
            return
            
        # Calculate optimal grid dimensions based on available width
        width = self.width()
        if width < 50:  # Not yet properly sized
            width = 600  # Reasonable default
            
        # Determine number of columns based on available width
        if width < 300:
            cols = 1
        elif width < 550:
            cols = 2
        elif width < 800:
            cols = 3
        else:
            cols = 4
            
        # Count the total number of rows needed based on controls
        # Label-control pairs count as 2 rows
        total_rows = 0
        for control_type, _ in self._controls:
            if control_type == "pair":
                total_rows += 2  # Label and control need separate rows
            else:
                total_rows += 1
        
        # Calculate rows per column - distribute evenly across columns
        rows_per_col = max(1, (total_rows + cols - 1) // cols)  # Ceiling division
        
        # Add all controls to the grid, filling columns from top to bottom
        curr_row, curr_col = 0, 0
        for control_type, control in self._controls:
            if control_type in ["label", "button", "combo", "spin", "check"]:
                # Add a single widget
                self._grid_layout.addWidget(control, curr_row, curr_col)
                curr_row += 1
            elif control_type == "pair":
                # For pairs, add label and control in consecutive rows
                label, widget = control
                self._grid_layout.addWidget(label, curr_row, curr_col)
                curr_row += 1
                self._grid_layout.addWidget(widget, curr_row, curr_col)
                curr_row += 1
                
            # If we've filled this column, move to the next column
            if curr_row >= rows_per_col:
                curr_row = 0
                curr_col += 1
        
        # Add column stretches to distribute space evenly
        for c in range(cols):
            self._grid_layout.setColumnStretch(c, 1)
            
    def eventFilter(self, obj, event):
        """
        Event filter to catch resize events.
        
        Args:
            obj: Object that generated the event
            event: The event that occurred
            
        Returns:
            bool: True if the event was handled, False to pass it on
        """
        if obj == self and event.type() == QEvent.Resize:
            # Update layout when widget is resized
            self._update_layout()
            return True
            
        return super().eventFilter(obj, event)
        
    def resizeEvent(self, event):
        """
        Handle resize events.
        
        Args:
            event: Resize event
        """
        super().resizeEvent(event)
        self._update_layout()
    
    def _setup_ui(self):
        """
        Set up the user interface for this specific workspace utility.
        
        To be overridden by subclasses. After implementing this method,
        subclasses should call _update_layout() to distribute controls.
        """
        pass
        
    def set_workspace(self, workspace):
        """
        Set the workspace associated with this utility panel.
        
        Args:
            workspace: Reference to the workspace widget
        """
        self._workspace = workspace
        self._workspace_updated()
        
        # Install event filter to catch resize events
        self.installEventFilter(self)
        
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