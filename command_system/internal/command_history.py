"""
Command history tracking for undo/redo functionality.
"""

class CommandHistory:
    """
    Tracks command history for undo/redo operations.
    Maintains two stacks: one for executed commands and one for undone commands.
    """
    
    def __init__(self):
        """Initialize empty command history."""
        self._executed_commands = []  # Stack of executed commands
        self._undone_commands = []    # Stack of undone commands
        
    def add_command(self, command):
        """
        Add a command to the history.
        Clears the undone commands stack since a new command creates a new branch.
        
        Args:
            command: The command to add
        """
        self._executed_commands.append(command)
        self._undone_commands.clear()  # Clear redo stack
        
    def undo(self):
        """
        Move the most recent command from executed to undone stack.
        
        Returns:
            The command that was undone, or None if no commands to undo
        """
        if not self._executed_commands:
            return None
            
        command = self._executed_commands.pop()
        self._undone_commands.append(command)
        return command
        
    def redo(self):
        """
        Move the most recently undone command back to the executed stack.
        
        Returns:
            The command that was redone, or None if no commands to redo
        """
        if not self._undone_commands:
            return None
            
        command = self._undone_commands.pop()
        self._executed_commands.append(command)
        return command
        
    def clear(self):
        """Clear both command stacks."""
        self._executed_commands.clear()
        self._undone_commands.clear()
        
    def can_undo(self):
        """
        Check if there are commands that can be undone.
        
        Returns:
            bool: True if there are commands that can be undone
        """
        return len(self._executed_commands) > 0
        
    def can_redo(self):
        """
        Check if there are commands that can be redone.
        
        Returns:
            bool: True if there are commands that can be redone
        """
        return len(self._undone_commands) > 0
        
    def get_executed_commands(self):
        """
        Get the list of executed commands.
        
        Returns:
            list: Copy of executed commands list
        """
        return self._executed_commands.copy()
        
    def get_undone_commands(self):
        """
        Get the list of undone commands.
        
        Returns:
            list: Copy of undone commands list
        """
        return self._undone_commands.copy()
        
    def serialize(self):
        """
        Serialize command history.
        
        Returns:
            dict: Serialized history state
        """
        return {
            "executed": [cmd.serialize() for cmd in self._executed_commands],
            "undone": [cmd.serialize() for cmd in self._undone_commands]
        }
        
    def deserialize(self, state, registry):
        """
        Restore command history from serialized state.
        
        Args:
            state (dict): Serialized history state
            registry: Object registry for resolving references
            
        Returns:
            bool: True if history was restored successfully
        """
        from command_system.internal.serialization import deserialize_command
        
        try:
            self.clear()
            
            # Deserialize executed commands
            for cmd_state in state.get("executed", []):
                command = deserialize_command(cmd_state, registry)
                if command:
                    self._executed_commands.append(command)
                    
            # Deserialize undone commands
            for cmd_state in state.get("undone", []):
                command = deserialize_command(cmd_state, registry)
                if command:
                    self._undone_commands.append(command)
                    
            return True
        except Exception as e:
            print(f"Error deserializing command history: {e}")
            self.clear()
            return False