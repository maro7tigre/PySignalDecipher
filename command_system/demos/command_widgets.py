"""
Demo application for command-enabled PySide6 widgets.

This demo showcases all the command widgets with property binding
and automatic undo/redo support through the command system.
"""
import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFormLayout,
    QGroupBox, QFrame, QSplitter, QTextBrowser
)
from PySide6.QtCore import Qt, QDate, Slot

# Add project root to path to ensure imports work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import command system components
from command_system.core import Observable, ObservableProperty, get_command_manager
from command_system.pyside6_widgets import (
    CommandLineEdit, CommandSpinBox, CommandCheckBox, CommandSlider,
    CommandComboBox, CommandTextEdit, CommandDateEdit, CommandDoubleSpinBox,
    CommandTriggerMode
)

class Product(Observable):
    """Product model with observable properties for demonstration."""
    
    # Define properties at the class level
    name = ObservableProperty("Sample Product")
    description = ObservableProperty("This is a sample product description.")
    sku = ObservableProperty("ABC-12345")
    price = ObservableProperty(29.99)
    quantity = ObservableProperty(10)
    rating = ObservableProperty(4)
    in_stock = ObservableProperty(True)
    is_featured = ObservableProperty(False)
    discount_percent = ObservableProperty(0)
    category = ObservableProperty("Electronics")
    categories = ObservableProperty(["Electronics", "Books", "Clothing", "Food", "Toys"])
    release_date = ObservableProperty("")
    discount_price = ObservableProperty(0.0)
    
    def __init__(self):
        """Initialize the product model with default values."""
        super().__init__()
        
        # Set the release date to current date
        today = QDate.currentDate()
        self.release_date = today.toString("yyyy-MM-dd")
        
        # Set up property observers for calculated fields
        self._update_discount_price()
        
        # Set up property observers for calculated fields
        self.add_property_observer("price", lambda name, old, new: self._update_discount_price())
        self.add_property_observer("discount_percent", lambda name, old, new: self._update_discount_price())
    
    def _update_discount_price(self):
        """Update the discounted price based on price and discount."""
        discount = self.discount_percent / 100.0
        # Need to force this to actually update by using a fresh value
        new_price = round(self.price * (1 - discount), 2)
        self.discount_price = new_price

class CommandWidgetsDemo(QMainWindow):
    """
    Demo application for command widgets.
    
    This demo shows how to use all the command widgets together with 
    property binding and automatic undo/redo support.
    """
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        self.setWindowTitle("Command Widgets Demo")
        self.resize(800, 600)
        
        # Create model and get command manager
        self.product = Product()
        self.product_id = self.product.get_id()
        self.cmd_manager = get_command_manager()
        
        # Command history tracking
        self.command_count = 0
        
        # Setup UI
        self._setup_ui()
        
        # Update command count display
        self.update_count()
        
    def _setup_ui(self):
        """Set up the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Create splitter for form and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(form_container)
        
        # Create form sections
        self._create_basic_info_group(form_layout)
        self._create_pricing_group(form_layout)
        self._create_attributes_group(form_layout)
        
        # Add stretcher at bottom of form
        form_layout.addStretch()
        
        # Preview container
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        splitter.addWidget(preview_container)
        
        # Create preview panel
        self._create_preview_panel(preview_layout)
        
        # Set initial splitter sizes (left: 60%, right: 40%)
        splitter.setSizes([480, 320])
        
        # Bottom panel with undo/redo controls
        self._create_command_controls(main_layout)
        
        # Connect command manager callbacks
        self.cmd_manager.add_after_execute_callback("demo", self.update_count)
        self.cmd_manager.add_after_undo_callback("demo", self.update_count)
        # Note: There's no add_after_redo_callback, but redo typically calls execute
        # So the after_execute_callback will handle redo operations too
    
    def _create_basic_info_group(self, parent_layout):
        """Create the basic information form group."""
        group = QGroupBox("Basic Information")
        layout = QFormLayout(group)
        
        # Name field - Immediate mode
        self.name_edit = CommandLineEdit()
        self.name_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        self.name_edit.bind_to_text_property(self.product_id, "name")
        layout.addRow("Name:", self.name_edit)
        
        # SKU field - On edit finished mode
        self.sku_edit = CommandLineEdit()
        self.sku_edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        self.sku_edit.bind_to_text_property(self.product_id, "sku")
        layout.addRow("SKU:", self.sku_edit)
        
        # Category selection - Combo box
        self.category_combo = CommandComboBox()
        self.category_combo.bind_to_items_property(self.product_id, "categories")
        self.category_combo.bind_to_current_text_property(self.product_id, "category")
        layout.addRow("Category:", self.category_combo)
        
        # Description - Text edit with delayed mode
        self.description_edit = CommandTextEdit()
        self.description_edit.set_command_trigger_mode(CommandTriggerMode.DELAYED, 500)
        self.description_edit.bind_to_plain_text_property(self.product_id, "description")
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.description_edit)
        
        # Release date - Date edit
        self.release_date_edit = CommandDateEdit()
        self.release_date_edit.bind_to_date_property(self.product_id, "release_date")
        layout.addRow("Release Date:", self.release_date_edit)
        
        parent_layout.addWidget(group)
    
    def _create_pricing_group(self, parent_layout):
        """Create the pricing form group."""
        group = QGroupBox("Pricing & Inventory")
        layout = QFormLayout(group)
        
        # Price - Double spin box
        self.price_spin = CommandDoubleSpinBox()
        self.price_spin.setRange(0, 9999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("$")
        self.price_spin.bind_to_value_property(self.product_id, "price")
        layout.addRow("Price:", self.price_spin)
        
        # Discount - Slider
        slider_layout = QHBoxLayout()
        self.discount_slider = CommandSlider(Qt.Horizontal)
        self.discount_slider.setRange(0, 100)
        self.discount_slider.bind_to_value_property(self.product_id, "discount_percent")
        slider_layout.addWidget(self.discount_slider)
        
        # Add label to show discount percentage
        self.discount_label = QLabel("0%")
        self.product.add_property_observer(
            "discount_percent", 
            lambda name, old, new: self.discount_label.setText(f"{new}%")
        )
        slider_layout.addWidget(self.discount_label)
        layout.addRow("Discount:", slider_layout)
        
        # Discounted price display
        self.discount_price_label = QLabel("$29.99")
        
        # Update for any price, discount or discount_price change
        def update_discount_label(name, old, new):
            current_price = self.product.discount_price
            self.discount_price_label.setText(f"${current_price:.2f}")
            
        self.product.add_property_observer("price", update_discount_label)
        self.product.add_property_observer("discount_percent", update_discount_label)
        self.product.add_property_observer("discount_price", update_discount_label)
        layout.addRow("Final Price:", self.discount_price_label)
        
        # Quantity - Spin box
        self.quantity_spin = CommandSpinBox()
        self.quantity_spin.setRange(0, 9999)
        self.quantity_spin.bind_to_value_property(self.product_id, "quantity")
        layout.addRow("Quantity:", self.quantity_spin)
        
        parent_layout.addWidget(group)
    
    def _create_attributes_group(self, parent_layout):
        """Create the attributes form group."""
        group = QGroupBox("Attributes")
        layout = QFormLayout(group)
        
        # In stock - Checkbox
        self.in_stock_check = CommandCheckBox("Product is currently available")
        self.in_stock_check.bind_to_checked_property(self.product_id, "in_stock")
        layout.addRow("", self.in_stock_check)
        
        # Featured - Checkbox
        self.featured_check = CommandCheckBox("Display as featured product")
        self.featured_check.bind_to_checked_property(self.product_id, "is_featured")
        # Check command trigger mode is appropriate
        self.featured_check.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        layout.addRow("", self.featured_check)
        
        # Rating - Slider with special display
        rating_layout = QHBoxLayout()
        self.rating_slider = CommandSlider(Qt.Horizontal)
        self.rating_slider.setRange(1, 5)
        self.rating_slider.setTickPosition(CommandSlider.TicksBelow)
        self.rating_slider.setTickInterval(1)
        self.rating_slider.bind_to_value_property(self.product_id, "rating")
        rating_layout.addWidget(self.rating_slider)
        
        # Add label to show star rating
        self.rating_label = QLabel("★★★★☆")
        self.product.add_property_observer(
            "rating", 
            lambda name, old, new: self.rating_label.setText("★" * new + "☆" * (5 - new))
        )
        rating_layout.addWidget(self.rating_label)
        layout.addRow("Rating:", rating_layout)
        
        parent_layout.addWidget(group)
    
    def _create_preview_panel(self, parent_layout):
        """Create the preview panel showing the current product data."""
        # Title
        title_label = QLabel("Product Preview")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        parent_layout.addWidget(title_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        parent_layout.addWidget(separator)
        
        # Preview content
        self.preview_browser = QTextBrowser()
        parent_layout.addWidget(self.preview_browser)
        
        # Update preview when any property changes
        for prop_name in ["name", "sku", "description", "price", "quantity", 
                         "in_stock", "is_featured", "category", "rating",
                         "discount_percent", "discount_price", "release_date"]:
            self.product.add_property_observer(
                prop_name, 
                lambda name, old, new: self.update_preview()
            )
        
        # Initial preview update
        self.update_preview()
    
    def _create_command_controls(self, parent_layout):
        """Create the bottom panel with command history and undo/redo controls."""
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        parent_layout.addWidget(separator)
        
        # Control panel layout
        panel = QWidget()
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(0, 5, 0, 5)
        parent_layout.addWidget(panel)
        
        # Command history display
        self.history_label = QLabel()
        panel_layout.addWidget(self.history_label)
        
        # Spacer
        panel_layout.addStretch()
        
        # Undo/Redo buttons
        undo_btn = QPushButton("Undo")
        undo_btn.setMinimumWidth(100)
        undo_btn.clicked.connect(self.cmd_manager.undo)
        
        redo_btn = QPushButton("Redo")
        redo_btn.setMinimumWidth(100)
        redo_btn.clicked.connect(self.cmd_manager.redo)
        
        panel_layout.addWidget(undo_btn)
        panel_layout.addWidget(redo_btn)
    
    @Slot()
    def update_count(self, command=None, success=None):
        """Update the command count display.
        
        Args:
            command: Command that was executed/undone (passed by command manager)
            success: Whether the command succeeded (passed by command manager)
        """
        executed_count = len(self.cmd_manager._history.get_executed_commands())
        undone_count = len(self.cmd_manager._history._undone_commands)
        
        self.history_label.setText(
            f"Command History: {executed_count} commands executed, {undone_count} undone"
        )
    
    def update_preview(self):
        """Update the product preview panel with current data."""
        # Format the release date
        try:
            release_date = QDate.fromString(self.product.release_date, "yyyy-MM-dd")
            formatted_date = release_date.toString("MMMM d, yyyy")
        except:
            formatted_date = "Invalid date"
        
        # Determine stock status display
        if self.product.in_stock:
            stock_status = '<span style="color: green;">In Stock</span>'
        else:
            stock_status = '<span style="color: red;">Out of Stock</span>'
        
        # Format the rating as stars
        rating_stars = "★" * self.product.rating + "☆" * (5 - self.product.rating)
        
        # Featured flag
        featured_tag = ' <span style="color: #c00; font-weight: bold;">[FEATURED]</span>' if self.product.is_featured else ''
        
        # Build the HTML content
        content = f"""
        <h1>{self.product.name}{featured_tag}</h1>
        <p><strong>SKU:</strong> {self.product.sku}</p>
        <p><strong>Category:</strong> {self.product.category}</p>
        
        <h3>Pricing</h3>
        <p>
            <strong>Regular Price:</strong> ${self.product.price:.2f}<br>
            <strong>Discount:</strong> {self.product.discount_percent}%<br>
            <strong>Final Price:</strong> <span style="color: #c00; font-size: 14px;">
                <strong>${self.product.discount_price:.2f}</strong>
            </span>
        </p>
        
        <h3>Availability</h3>
        <p>
            <strong>Status:</strong> {stock_status}<br>
            <strong>Quantity:</strong> {self.product.quantity} units<br>
            <strong>Release Date:</strong> {formatted_date}
        </p>
        
        <h3>Rating: {rating_stars}</h3>
        
        <h3>Description</h3>
        <p>{self.product.description}</p>
        """
        
        self.preview_browser.setHtml(content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = CommandWidgetsDemo()
    demo.show()
    sys.exit(app.exec())