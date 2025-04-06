"""
Type codes and constants for the ID system.

This module defines the various type codes used to identify different
types of components in the ID system.
"""

#MARK: - Container Type Codes

CONTAINER_TYPE_CODES = {
    't': 'Tab Container',
    'd': 'Dock Container',
    'w': 'Window Container',
    'x': 'Custom Container',
}

#MARK: - Widget Type Codes

WIDGET_TYPE_CODES = {
    # Command widgets
    'le': 'Line Edit Widget',
    'cb': 'Check Box Widget',
    'pb': 'Push Button',
    'rb': 'Radio Button',
    'co': 'Combo Box',
    'sl': 'Slider',
    'sp': 'Spin Box',
    'te': 'Text Edit',
    'lw': 'List Widget',
    'tw': 'Tree Widget',
    'tb': 'Table Widget',
    'cw': 'Custom Widget',
}

# Combined type codes for all widget types (including containers)
ALL_WIDGET_TYPE_CODES = {**CONTAINER_TYPE_CODES, **WIDGET_TYPE_CODES}

#MARK: - Observable Type Codes

OBSERVABLE_TYPE_CODES = {
    'o': 'Observable',
}

#MARK: - Property Type Codes

PROPERTY_TYPE_CODES = {
    'op': 'Observable Property',
}

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