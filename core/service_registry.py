"""
Service Registry for PySignalDecipher.

Provides centralized access to application-wide services and managers.
"""

class ServiceRegistry:
    """
    Central registry for application services.
    
    Provides typed access to shared services and managers that are used
    across different components of the application.
    """
    
    _instance = None
    
    # Service references
    _color_manager = None
    _style_manager = None
    _preferences_manager = None
    _theme_manager = None
    _device_manager = None
    _layout_manager = None
    _dock_manager = None
    
    @classmethod
    def initialize(cls, color_manager=None, style_manager=None, 
                  preferences_manager=None, theme_manager=None,
                  device_manager=None, layout_manager=None,
                  dock_manager=None):
        """
        Initialize the service registry with core services.

        This method should be called once at application startup.

        Args:
            color_manager: ColorManager instance
            style_manager: StyleManager instance
            preferences_manager: PreferencesManager instance
            theme_manager: ThemeManager instance
            device_manager: DeviceManager instance
            layout_manager: LayoutManager instance
            dock_manager: DockManager instance
        """
        if cls._instance is None:
            cls._instance = cls()

        # Store services
        cls._color_manager = color_manager
        cls._style_manager = style_manager
        cls._preferences_manager = preferences_manager
        cls._theme_manager = theme_manager
        cls._device_manager = device_manager
        cls._layout_manager = layout_manager
        cls._dock_manager = dock_manager
    
    @classmethod
    def get_dock_manager(cls):
        """
        Get the application dock manager.
        
        Returns:
            The DockManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._dock_manager is None:
            raise RuntimeError("DockManager not initialized in ServiceRegistry")
        return cls._dock_manager

    @classmethod
    def get_layout_manager(cls):
        """
        Get the application layout manager.

        Returns:
            The LayoutManager instance

        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._layout_manager is None:
            raise RuntimeError("LayoutManager not initialized in ServiceRegistry")
        return cls._layout_manager

    @classmethod
    def get_color_manager(cls):
        """
        Get the application color manager.
        
        Returns:
            The ColorManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._color_manager is None:
            raise RuntimeError("ColorManager not initialized in ServiceRegistry")
        return cls._color_manager
    
    @classmethod
    def get_style_manager(cls):
        """
        Get the application style manager.
        
        Returns:
            The StyleManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._style_manager is None:
            raise RuntimeError("StyleManager not initialized in ServiceRegistry")
        return cls._style_manager
    
    @classmethod
    def get_preferences_manager(cls):
        """
        Get the application preferences manager.
        
        Returns:
            The PreferencesManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._preferences_manager is None:
            raise RuntimeError("PreferencesManager not initialized in ServiceRegistry")
        return cls._preferences_manager
    
    @classmethod
    def get_theme_manager(cls):
        """
        Get the application theme manager.
        
        Returns:
            The ThemeManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._theme_manager is None:
            raise RuntimeError("ThemeManager not initialized in ServiceRegistry")
        return cls._theme_manager
    
    @classmethod
    def get_device_manager(cls):
        """
        Get the application device manager.
        
        Returns:
            The DeviceManager instance
        
        Raises:
            RuntimeError: If the service registry is not initialized
        """
        if cls._device_manager is None:
            raise RuntimeError("DeviceManager not initialized in ServiceRegistry")
        return cls._device_manager