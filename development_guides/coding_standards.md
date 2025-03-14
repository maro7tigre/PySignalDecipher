# Coding Standards

Coding conventions and standards for the PySignalDecipher project.

## 1. Code Organization

### 1.1 File Structure

- One class per file (with closely related helper classes when appropriate)
- Files named after the primary class they contain
- Use of `__init__.py` files to create clean public APIs for modules

### 1.2 File and Directory Naming

- **Python Files**: Use lowercase with underscores for separation (snake_case)
  - Example: `signal_processor.py`, `device_factory.py`
  - Files containing a single class should be named after the class but in snake_case
    (e.g., class `SignalProcessor` goes in `signal_processor.py`)
  
- **Directories**: Use lowercase with underscores for separation (snake_case)
  - Example: `signal_processing/`, `test_helpers/`
  
- **Test Files**: Prefix with `test_` followed by the name of the module being tested
  - Example: `test_signal_processor.py`, `test_device_factory.py`
  
- **Resource Files**: Use lowercase with descriptive names
  - Example: `dark_theme.json`, `default_layout.json`
  
- **Documentation Files**: Use lowercase with underscores, `.md` extension for Markdown
  - Example: `setup_guide.md`, `api_reference.md`
  
- **Configuration Files**: Use lowercase with descriptive names that indicate purpose
  - Example: `logging_config.json`, `app_settings.json`

### 1.3 Import Organization

Imports should be organized in the following order, separated by a blank line:
1. Standard library imports
2. Third-party library imports
3. Local application imports

## 2. Naming Conventions

- **Classes**: CamelCase (e.g., `SignalProcessor`)
- **Functions/Methods**: snake_case (e.g., `process_signal`)
- **Variables**: snake_case (e.g., `current_signal`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_SAMPLE_RATE`)
- **Private Members**: Prefixed with underscore (e.g., `_internal_data`)
- **Properties**: snake_case, same as regular variables

## 3. Commenting and Documentation

### 3.1 Docstrings

All modules, classes, methods, and functions should have docstrings:

```python
def analyze_frequency(signal, sample_rate):
    """
    Perform frequency analysis on the given signal.
    
    Args:
        signal (numpy.ndarray): Time-domain signal to analyze
        sample_rate (float): Sample rate in Hz
        
    Returns:
        tuple: Frequencies and magnitudes (numpy.ndarray)
        
    Raises:
        ValueError: If signal is empty or sample_rate is zero
    """
```

### 3.2 Special Comment Tags

For enhanced code navigation and task tracking:

- **# MARK: [description]**: Marks significant sections of code (appears in VS Code minimap)
  - Example: `# MARK: - Signal Processing Functions`

- **# TODO: [description]**: Indicates incomplete/future work
  - Example: `# TODO: Implement adaptive filtering algorithm`

- **# FIXME: [description]**: Highlights code that needs repair
  - Example: `# FIXME: Memory leak when processing large signals`

- **# NOTE: [description]**: Important information about the code
  - Example: `# NOTE: This algorithm assumes normalized input`

### 3.3 Comment Style

- Use complete sentences with proper capitalization and punctuation
- Focus on *why* rather than *what* (the code shows what, comments explain why)
- Keep comments up-to-date with code changes
- Use block comments for complex algorithms or non-obvious logic

## 4. Code Style

- Follow PEP 8 guidelines for Python code style
- Maximum line length of 100 characters
- Use type hints for function parameters and return values
- Prefer explicit over implicit
- Use context managers (`with` statements) for resource management

## 5. Error Handling

- Use exceptions for error conditions, not for flow control
- Create custom exception classes for application-specific errors
- Include informative error messages
- Log exceptions appropriately before re-raising or handling

## 6. Testing Strategy

- Unit tests for all non-UI components
- Integration tests for component interactions
- UI tests for critical workflows
- Test coverage targeting 80%+ for core components