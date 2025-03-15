import os
import json
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QApplication


class StyleManager(QObject):
    """
    Manages and generates Qt style sheets based on the current color scheme.
    
    Responsible for generating complete Qt style sheets using colors from ColorManager,
    applying styles to the application or specific widgets, and providing style snippets.
    """
    
    # Signal emitted when styles are updated
    styles_updated = Signal()
    
    def __init__(self, color_manager):
        """
        Initialize the StyleManager.
        
        Args:
            color_manager: Reference to the ColorManager
        """
        super().__init__()
        
        # Reference to the ColorManager
        self._color_manager = color_manager
        
        # Path to style definition files
        self._styles_dir = os.path.join("assets", "themes", "styles")
        
        # Dictionary to store loaded style definitions
        self._style_definitions = {}
        
        # Dictionary to store compiled style sheets
        self._compiled_styles = {}
        
        # Settings for user preferences
        self._settings = QSettings("PySignalDecipher", "PySignalDecipher")
        
        # Dictionary to store registered observers
        self._observers = {}
        
        # Load style definitions
        self._load_style_definitions()
        
        # Connect to color scheme changes
        self._color_manager.color_scheme_changed.connect(self._on_color_scheme_changed)
        
        # Load user style preferences
        self._load_style_preferences()
        
    def _load_style_definitions(self) -> None:
        """
        Load style definitions from JSON files in the styles directory.
        """
        if not os.path.exists(self._styles_dir):
            # Log a warning that the styles directory doesn't exist
            print(f"Warning: Styles directory not found: {self._styles_dir}")
            return
            
        for filename in os.listdir(self._styles_dir):
            if filename.endswith("_styles.json"):
                style_name = filename.replace("_styles.json", "")
                self._load_style_definition(style_name)
                
    def _load_style_definition(self, style_name: str) -> bool:
        """
        Load a style definition from its JSON file.
        
        Args:
            style_name: Name of the style to load (without _styles.json)
            
        Returns:
            bool: True if the style was loaded successfully, False otherwise
        """
        file_path = os.path.join(self._styles_dir, f"{style_name}_styles.json")
        
        if not os.path.exists(file_path):
            # Try to load from a user-defined style
            user_file_path = os.path.join(self._styles_dir, f"{style_name}_custom_styles.json")
            if os.path.exists(user_file_path):
                file_path = user_file_path
            else:
                # Log a warning that the style file doesn't exist
                print(f"Warning: Style file not found: {file_path}")
                return False
            
        try:
            with open(file_path, 'r') as f:
                self._style_definitions[style_name] = json.load(f)
            return True
        except json.JSONDecodeError:
            # Log an error that the style file is invalid JSON
            print(f"Error: Invalid JSON in style file: {file_path}")
            return False
    
    def _load_style_preferences(self) -> None:
        """
        Load user style preferences from settings.
        """
        # Check if user has custom style overrides saved
        style_overrides = self._settings.value("theme/style_overrides", {})
        if isinstance(style_overrides, dict) and style_overrides:
            # Apply saved overrides to style definitions
            for style_name, overrides in style_overrides.items():
                if style_name in self._style_definitions:
                    # Deep merge the overrides with the base definitions
                    self._merge_style_definitions(self._style_definitions[style_name], overrides)
    
    def _merge_style_definitions(self, base: Dict, overrides: Dict) -> None:
        """
        Recursively merge style definition overrides into the base definitions.
        
        Args:
            base: Base style definitions to update
            overrides: Override values to apply
        """
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_style_definitions(base[key], value)
            else:
                base[key] = value
            
    def _on_color_scheme_changed(self, scheme_name: str) -> None:
        """
        Handle color scheme changes by updating compiled styles.
        
        Args:
            scheme_name: Name of the new color scheme
        """
        # Clear compiled styles to force regeneration
        self._compiled_styles = {}
        
        # Apply the new styles to the application
        self.apply_application_style()
        
        # Notify observers
        self.styles_updated.emit()
        
    def _compile_style_sheet(self, style_name: str) -> str:
        """
        Compile a style sheet by combining style definitions with colors.
        
        Args:
            style_name: Name of the style to compile
            
        Returns:
            Compiled style sheet as a string
        """
        # Check if the style is already compiled
        if style_name in self._compiled_styles:
            return self._compiled_styles[style_name]
            
        # Check if the style definition exists
        if style_name not in self._style_definitions:
            if not self._load_style_definition(style_name):
                # Return an empty style sheet if the style doesn't exist
                return ""
                
        style_sheet = ""
        
        # Handle different style types
        if style_name == "control":
            style_sheet = self._compile_control_styles()
        elif style_name == "graph":
            style_sheet = self._compile_graph_styles()
        
        # Store the compiled style sheet
        self._compiled_styles[style_name] = style_sheet
        
        return style_sheet
        
    def _compile_control_styles(self) -> str:
        """
        Compile style sheet for UI controls.
        
        Returns:
            Compiled style sheet as a string
        """
        if "control" not in self._style_definitions:
            return ""
            
        controls = self._style_definitions["control"]
        style_sheet = ""
        
        # Example: Style for QPushButton
        if "button" in controls:
            button_style = controls["button"]
            style_sheet += "QPushButton {\n"
            style_sheet += f"    background-color: {self._color_manager.get_color('background.secondary')};\n"
            style_sheet += f"    color: {self._color_manager.get_color('text.primary')};\n"
            style_sheet += f"    border: 1px solid {self._color_manager.get_color('accent.primary')};\n"
            
            if "border_radius" in button_style:
                style_sheet += f"    border-radius: {button_style['border_radius']};\n"
                
            if "padding" in button_style:
                style_sheet += f"    padding: {button_style['padding']};\n"
                
            if "font_weight" in button_style:
                style_sheet += f"    font-weight: {button_style['font_weight']};\n"
                
            style_sheet += "}\n\n"
            
            # Hover state
            style_sheet += "QPushButton:hover {\n"
            style_sheet += f"    background-color: {self._color_manager.get_color('accent.primary')};\n"
            style_sheet += f"    color: {self._color_manager.get_color('background.primary')};\n"
            style_sheet += "}\n\n"
            
            # Pressed state
            style_sheet += "QPushButton:pressed {\n"
            style_sheet += f"    background-color: {self._color_manager.get_color('accent.secondary')};\n"
            style_sheet += "}\n\n"
            
        # Example: Style for QLabel
        if "label" in controls:
            label_style = controls["label"]
            style_sheet += "QLabel {\n"
            style_sheet += f"    color: {self._color_manager.get_color('text.primary')};\n"
            
            if "padding" in label_style:
                style_sheet += f"    padding: {label_style['padding']};\n"
                
            if "font_weight" in label_style:
                style_sheet += f"    font-weight: {label_style['font_weight']};\n"
                
            style_sheet += "}\n\n"
            
        # Example: Style for QSlider
        if "slider" in controls:
            slider_style = controls["slider"]
            style_sheet += "QSlider::groove:horizontal {\n"
            style_sheet += f"    background: {self._color_manager.get_color('background.tertiary')};\n"
            
            if "groove_height" in slider_style:
                style_sheet += f"    height: {slider_style['groove_height']};\n"
                
            style_sheet += "}\n\n"
            
            style_sheet += "QSlider::handle:horizontal {\n"
            style_sheet += f"    background: {self._color_manager.get_color('accent.primary')};\n"
            
            if "handle_size" in slider_style:
                size = slider_style['handle_size'].replace('px', '')
                style_sheet += f"    width: {size}px;\n"
                style_sheet += f"    margin: -{int(int(size) / 4)}px 0;\n"
                
            style_sheet += f"    border-radius: {int(int(slider_style.get('handle_size', '16').replace('px', '')) / 2)}px;\n"
            style_sheet += "}\n\n"
            
        return style_sheet
        
    def _compile_graph_styles(self) -> str:
        """
        Compile style sheet for graphs and plots.
        
        Returns:
            Compiled style sheet as a string
        """
        if "graph" not in self._style_definitions:
            return ""
            
        graphs = self._style_definitions["graph"]
        style_sheet = ""
        
        # Style for plot widgets would be defined here
        # This is just a placeholder as actual implementation would depend on your specific graphing widgets
        style_sheet += "/* Graph Styles */\n"
        
        return style_sheet
        
    def get_style_sheet(self, style_name: str) -> str:
        """
        Get a compiled style sheet by name.
        
        Args:
            style_name: Name of the style to get
            
        Returns:
            Compiled style sheet as a string
        """
        return self._compile_style_sheet(style_name)
        
    def get_complete_style_sheet(self) -> str:
        """
        Get a complete style sheet with all styles.
        
        Returns:
            Complete style sheet as a string
        """
        style_sheet = ""
        
        # Add global application styles
        style_sheet += "/* Global Application Styles */\n"
        style_sheet += f"QWidget {{ background-color: {self._color_manager.get_color('background.primary')}; }}\n\n"
        
        # Add control styles
        style_sheet += "/* Control Styles */\n"
        style_sheet += self.get_style_sheet("control")
        
        # Add graph styles
        style_sheet += "/* Graph Styles */\n"
        style_sheet += self.get_style_sheet("graph")
        
        return style_sheet
        
    def apply_application_style(self) -> None:
        """
        Apply the complete style sheet to the application.
        """
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.get_complete_style_sheet())
            
    def apply_widget_style(self, widget, style_name: str) -> None:
        """
        Apply a specific style to a widget.
        
        Args:
            widget: Widget to apply the style to
            style_name: Name of the style to apply
        """
        widget.setStyleSheet(self.get_style_sheet(style_name))
        
    def register_observer(self, observer_id: str, callback: Callable[[], None]) -> None:
        """
        Register an observer to be notified when styles are updated.
        
        Args:
            observer_id: Unique identifier for the observer
            callback: Function to call when styles are updated
        """
        self._observers[observer_id] = callback
        self.styles_updated.connect(callback)
        
    def unregister_observer(self, observer_id: str) -> None:
        """
        Unregister an observer.
        
        Args:
            observer_id: Identifier of the observer to unregister
        """
        if observer_id in self._observers:
            self.styles_updated.disconnect(self._observers[observer_id])
            del self._observers[observer_id]
            
    def save_style_overrides(self, style_name: str, overrides: Dict[str, Any]) -> bool:
        """
        Save custom style overrides for a specific style.
        
        Args:
            style_name: Name of the style to override
            overrides: Dictionary of style overrides
            
        Returns:
            bool: True if the overrides were saved successfully, False otherwise
        """
        # Get current overrides
        style_overrides = self._settings.value("theme/style_overrides", {})
        if not isinstance(style_overrides, dict):
            style_overrides = {}
            
        # Update with new overrides
        style_overrides[style_name] = overrides
        
        # Save to settings
        self._settings.setValue("theme/style_overrides", style_overrides)
        
        # Apply overrides to current definitions
        if style_name in self._style_definitions:
            self._merge_style_definitions(self._style_definitions[style_name], overrides)
            
            # Clear compiled styles to force regeneration
            if style_name in self._compiled_styles:
                del self._compiled_styles[style_name]
                
            # Apply the new styles
            self.apply_application_style()
            
            # Notify observers
            self.styles_updated.emit()
            
        return True
        
    def reset_style_overrides(self, style_name: Optional[str] = None) -> None:
        """
        Reset style overrides to defaults.
        
        Args:
            style_name: Name of the style to reset, or None to reset all
        """
        if style_name:
            # Reset specific style
            style_overrides = self._settings.value("theme/style_overrides", {})
            if isinstance(style_overrides, dict) and style_name in style_overrides:
                del style_overrides[style_name]
                self._settings.setValue("theme/style_overrides", style_overrides)
                
                # Reload the style definition
                if style_name in self._style_definitions:
                    del self._style_definitions[style_name]
                self._load_style_definition(style_name)
                
                # Clear compiled style
                if style_name in self._compiled_styles:
                    del self._compiled_styles[style_name]
        else:
            # Reset all styles
            self._settings.remove("theme/style_overrides")
            
            # Reload all style definitions
            self._style_definitions = {}
            self._load_style_definitions()
            
            # Clear all compiled styles
            self._compiled_styles = {}
            
        # Apply the new styles
        self.apply_application_style()
        
        # Notify observers
        self.styles_updated.emit()