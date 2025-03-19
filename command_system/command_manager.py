"""
Command manager for coordinating command execution and history.
"""
from command_system.internal.command_history import CommandHistory
from command_system.internal.registry import Registry
from command_system.command import PropertyCommand


class CommandManager:
    """
    Singleton manager for command execution and history tracking.
    Provides methods to execute, undo, and redo commands.
    Also handles project serialization.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = CommandManager()
        return cls._instance
    
    def __init__(self):
        if CommandManager._instance is not None:
            raise RuntimeError("Use CommandManager.get_instance() to get the singleton instance")
            
        CommandManager._instance = self
        self._history = CommandHistory()
        self._registry = Registry.get_instance()
        self._project = None
        self._auto_commands_enabled = False
        self._observables = {}
        self._property_observers = {}
    
    def execute(self, command):
        """
        Execute a command and add it to the history.
        
        Args:
            command (Command): Command to execute
            
        Returns:
            bool: True if command executed successfully
        """
        try:
            command.execute()
            self._history.add_command(command)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    
    def undo(self):
        """
        Undo the most recent command in the history.
        
        Returns:
            bool: True if a command was undone
        """
        command = self._history.undo()
        if command:
            try:
                command.undo()
                return True
            except Exception as e:
                print(f"Error undoing command: {e}")
                # Re-add the command since undo failed
                self._history.redo()
        return False
    
    def redo(self):
        """
        Redo the most recently undone command.
        
        Returns:
            bool: True if a command was redone
        """
        command = self._history.redo()
        if command:
            try:
                command.execute()
                return True
            except Exception as e:
                print(f"Error redoing command: {e}")
                # Remove the command since redo failed
                self._history.undo()
        return False
    
    def clear(self):
        """Clear command history and registry."""
        self._history.clear()
        self._observables = {}
        self._property_observers = {}
    
    def can_undo(self):
        """Check if there are commands that can be undone."""
        return self._history.can_undo()
    
    def can_redo(self):
        """Check if there are commands that can be redone."""
        return self._history.can_redo()
    
    def set_project(self, project):
        """
        Set the current project.
        
        Args:
            project: Project object
        """
        self._project = project
        
    def get_project(self):
        """
        Get the current project.
        
        Returns:
            Current project object
        """
        return self._project
        
    def save_project(self, file_path):
        """
        Save the current project with command history.
        
        Args:
            file_path (str): Path to save the project
            
        Returns:
            bool: True if project was saved successfully
        """
        if not self._project:
            return False
            
        from command_system.internal.storage.json_storage import JsonStorage
        
        try:
            # Create storage
            storage = JsonStorage(file_path)
            
            # Serialize project and command history
            serialized = {
                "project": self._registry.serialize_object(self._project),
                "history": self._history.serialize()
            }
            
            # Save to file
            storage.save(serialized)
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def load_project(self, file_path):
        """
        Load a project with command history.
        
        Args:
            file_path (str): Path to load the project from
            
        Returns:
            Project object if successful, None otherwise
        """
        from command_system.internal.storage.json_storage import JsonStorage
        from command_system.internal.serialization import deserialize_object
        
        try:
            # Create storage
            storage = JsonStorage(file_path)
            
            # Load from file
            serialized = storage.load()
            
            if not serialized:
                return None
                
            # Clear current state
            self.clear()
            
            # Deserialize project
            project = deserialize_object(serialized["project"], self._registry)
            self._project = project
            
            # Deserialize command history
            self._history.deserialize(serialized["history"], self._registry)
            
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def enable_auto_commands(self):
        """Enable automatic command generation for property changes."""
        self._auto_commands_enabled = True
    
    def disable_auto_commands(self):
        """Disable automatic command generation for property changes."""
        self._auto_commands_enabled = False
    
    def is_auto_commands_enabled(self):
        """Check if automatic commands are enabled."""
        return self._auto_commands_enabled
    
    def register_observable(self, observable):
        """
        Register an observable object for property change tracking.
        
        Args:
            observable (Observable): Observable object to register
        """
        obj_id = observable.get_id()
        
        # Don't re-register
        if obj_id in self._observables:
            return
            
        self._observables[obj_id] = observable
        self._registry.register_object(observable)
        
        # Watch for property changes
        self._property_observers[obj_id] = {}
        
        # Add observer for each property that's an ObservableProperty
        from command_system.observable import ObservableProperty
        
        for name, prop in type(observable).__dict__.items():
            if isinstance(prop, ObservableProperty):
                self._property_observers[obj_id][name] = observable.add_property_observer(
                    name, self._on_property_changed
                )
    
    def unregister_observable(self, observable):
        """
        Unregister an observable object from property change tracking.
        
        Args:
            observable (Observable): Observable object to unregister
        """
        obj_id = observable.get_id()
        
        if obj_id in self._observables:
            # Remove property observers
            if obj_id in self._property_observers:
                for prop_name, observer_id in self._property_observers[obj_id].items():
                    observable.remove_property_observer(prop_name, observer_id)
                del self._property_observers[obj_id]
                
            # Remove from observables
            del self._observables[obj_id]
            
    def _on_property_changed(self, property_name, old_value, new_value):
        """
        Called when a property changes on an observed object.
        Creates and executes a PropertyCommand if auto-commands are enabled.
        
        Args:
            property_name (str): Name of the property that changed
            old_value: Previous value
            new_value: New value
        """
        if not self._auto_commands_enabled:
            return
            
        # Find the observable object
        for obj_id, observable in self._observables.items():
            if property_name in self._property_observers.get(obj_id, {}):
                # Create and execute a command
                cmd = PropertyCommand(observable, property_name, new_value)
                cmd.old_value = old_value
                
                # Add directly to history without executing again
                self._history.add_command(cmd)
                break


def get_command_manager():
    """
    Get the singleton CommandManager instance.
    
    Returns:
        CommandManager: Singleton instance
    """
    return CommandManager.get_instance()