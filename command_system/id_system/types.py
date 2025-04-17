"""
Type codes and constants for the ID system.

This module defines the various type codes used to identify different
types of components in the ID system with a flexible interface for both
internal and external use.
"""

#MARK: - Container Type Definitions
class ContainerTypeCodes:
    """Container type code definitions."""
    TAB = 't'
    DOCK = 'd'
    WINDOW = 'w'
    CUSTOM = 'x'
    
    @classmethod
    def get_all_codes(cls):
        """Get a tuple of all defined container type codes."""
        return (cls.TAB, cls.DOCK, cls.WINDOW, cls.CUSTOM)
    
    @classmethod
    def is_valid_code(cls, code):
        """Check if a code is a valid container type code."""
        return code in cls.get_all_codes()


#MARK: - Widget Type Definitions
class WidgetTypeCodes:
    """Widget type code definitions."""
    LINE_EDIT = 'le'
    CHECK_BOX = 'cb'
    PUSH_BUTTON = 'pb'
    RADIO_BUTTON = 'rb'
    COMBO_BOX = 'co'
    SLIDER = 'sl'
    SPIN_BOX = 'sp'
    DOUBLE_SPIN_BOX = 'ds'
    TEXT_EDIT = 'te'
    LIST_WIDGET = 'lw'
    TREE_WIDGET = 'tw'
    TABLE_WIDGET = 'tb'
    DATE_EDIT = 'de'
    TIME_EDIT = 'ti'
    DATE_TIME_EDIT = 'dt'
    CUSTOM_WIDGET = 'cw'
    
    @classmethod
    def get_all_codes(cls):
        """Get a tuple of all defined widget type codes."""
        return (
            cls.LINE_EDIT, cls.CHECK_BOX, cls.PUSH_BUTTON, cls.RADIO_BUTTON,
            cls.COMBO_BOX, cls.SLIDER, cls.SPIN_BOX, cls.TEXT_EDIT,
            cls.LIST_WIDGET, cls.TREE_WIDGET, cls.TABLE_WIDGET, cls.CUSTOM_WIDGET
        )
    
    @classmethod
    def is_valid_code(cls, code):
        """Check if a code is a valid widget type code."""
        return code in cls.get_all_codes()


#MARK: - Observable Type Definitions
class ObservableTypeCodes:
    """Observable type code definitions."""
    OBSERVABLE = 'ob'
    
    @classmethod
    def get_all_codes(cls):
        """Get a tuple of all defined observable type codes."""
        return (cls.OBSERVABLE,)
    
    @classmethod
    def is_valid_code(cls, code):
        """Check if a code is a valid observable type code."""
        return code in cls.get_all_codes()


#MARK: - Property Type Definitions
class PropertyTypeCodes:
    """Property type code definitions."""
    OBSERVABLE_PROPERTY = 'op'
    
    @classmethod
    def get_all_codes(cls):
        """Get a tuple of all defined property type codes."""
        return (cls.OBSERVABLE_PROPERTY,)
    
    @classmethod
    def is_valid_code(cls, code):
        """Check if a code is a valid property type code."""
        return code in cls.get_all_codes()


#MARK: - Combined Type Codes
class TypeCodes:
    """Combined type code definitions and utilities."""
    
    @classmethod
    def get_all_widget_codes(cls):
        """Get a tuple of all widget type codes (including containers)."""
        return ContainerTypeCodes.get_all_codes() + WidgetTypeCodes.get_all_codes()
    
    @classmethod
    def get_all_codes(cls):
        """Get a tuple of all defined type codes."""
        return (ContainerTypeCodes.get_all_codes() + 
                WidgetTypeCodes.get_all_codes() + 
                ObservableTypeCodes.get_all_codes() + 
                PropertyTypeCodes.get_all_codes())
    
    @classmethod
    def is_valid_code(cls, code):
        """Check if a code is a valid type code."""
        return (ContainerTypeCodes.is_valid_code(code) or
                WidgetTypeCodes.is_valid_code(code) or
                ObservableTypeCodes.is_valid_code(code) or
                PropertyTypeCodes.is_valid_code(code))
    
    @classmethod
    def get_type_category(cls, code):
        """
        Get the category of a type code.
        
        Returns:
            str: 'container', 'widget', 'observable', 'property', or 'unknown'
        """
        if ContainerTypeCodes.is_valid_code(code):
            return 'container'
        elif WidgetTypeCodes.is_valid_code(code):
            return 'widget'
        elif ObservableTypeCodes.is_valid_code(code):
            return 'observable'
        elif PropertyTypeCodes.is_valid_code(code):
            return 'property'
        else:
            return 'unknown'
    
    @classmethod
    def is_valid_all_widgets(cls, code):
        """Check if all codes are valid widget type codes."""
        return code in cls.get_all_widget_codes()
    
    @classmethod
    def is_valid_widgets(cls, code):
        """Check if all codes are valid widget type codes."""
        return code in WidgetTypeCodes.get_all_codes()
    
    @classmethod
    def is_valid_containers(cls, code):
        """Check if all codes are valid container type codes."""
        return code in ContainerTypeCodes.get_all_codes()
    
    @classmethod
    def is_valid_observers(cls, code):
        """Check if all codes are valid observable type codes."""
        return code in ObservableTypeCodes.get_all_codes()
    
    @classmethod
    def is_valid_properties(cls, code):
        """Check if all codes are valid property type codes."""
        return code in PropertyTypeCodes.get_all_codes()
    


#MARK: - Default values

# Default ID values
DEFAULT_ROOT_CONTAINER_ID = "0"
DEFAULT_ROOT_LOCATION = "0"
DEFAULT_NO_CONTAINER = "0"
DEFAULT_NO_OBSERVABLE = "0"
DEFAULT_NO_CONTROLLER = "0"
DEFAULT_NO_PROPERTY_NAME = "0"

# ID Format separators
ID_SEPARATOR = ":"
LOCATION_SEPARATOR = "-"
PATH_SEPARATOR = "/"

# Special characters that should never appear in IDs
RESERVED_CHARS = ":" + "-" + "/"