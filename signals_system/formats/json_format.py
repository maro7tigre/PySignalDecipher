"""
JSON Format Implementation

This module implements the JSON format handler for signal data.
It provides a clean, human-readable format with good metadata support.
"""

import json
import numpy as np
from typing import Dict, Any, List, Optional, Union, BinaryIO
import io
import os
from datetime import datetime
from pathlib import Path

from .base import (
    SignalFormat,
    SignalData,
    TimeRange,
    FormatCapability,
    SignalFormatError
)


class JsonFormat(SignalFormat):
    """
    JSON format handler for signal data.
    
    This format stores signal data as structured JSON with the following format:
    {
        "metadata": {
            "format_version": "1.0",
            "created_at": "2023-01-01T00:00:00.000Z",
            ... (other metadata)
        },
        "data": [1.0, 2.0, 3.0, ...],  # For single-channel
        # OR for multi-channel:
        "data": [[1.0, 2.0], [1.1, 2.1], ...],
        "timestamps": [0.0, 0.001, 0.002, ...]
    }
    """
    
    @property
    def name(self) -> str:
        return "JSON"
    
    @property
    def extensions(self) -> List[str]:
        return [".json", ".jsn"]
    
    @property
    def capabilities(self) -> List[FormatCapability]:
        return [
            FormatCapability.METADATA,
            FormatCapability.STREAMING
        ]
    
    def read(self, source: Union[str, Path, BinaryIO], time_range: Optional[TimeRange] = None) -> SignalData:
        """
        Read signal data from a JSON source.
        
        Args:
            source: File path or file-like object
            time_range: Optional time range to filter by
            
        Returns:
            SignalData object
            
        Raises:
            SignalFormatError: If reading fails
        """
        try:
            # Handle different source types
            if isinstance(source, (str, Path)):
                with open(source, 'rb') as f:
                    content = f.read()
            else:
                # Assume it's a file-like object
                pos = source.tell()
                source.seek(0)
                content = source.read()
                source.seek(pos)  # Restore position
            
            # Parse the JSON
            try:
                json_data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise SignalFormatError(f"Invalid JSON: {str(e)}")
            
            # Extract components
            if "data" not in json_data:
                raise SignalFormatError("Missing 'data' field in JSON")
            
            # Convert to numpy arrays
            values = np.array(json_data["data"])
            timestamps = np.array(json_data.get("timestamps")) if "timestamps" in json_data else None
            metadata = json_data.get("metadata", {})
            
            # Create the signal data
            signal_data = SignalData(
                values=values,
                timestamps=timestamps,
                metadata=metadata
            )
            
            # Apply time range filter if specified
            if time_range is not None and timestamps is not None:
                signal_data = signal_data.time_slice(time_range)
            
            return signal_data
            
        except Exception as e:
            if not isinstance(e, SignalFormatError):
                e = SignalFormatError(f"Failed to read JSON: {str(e)}")
            raise e
    
    def write(self, destination: Union[str, Path, BinaryIO], data: SignalData, append: bool = False) -> None:
        """
        Write signal data to a JSON destination.
        
        Args:
            destination: File path or file-like object
            data: SignalData to write
            append: Whether to append to existing data
            
        Raises:
            SignalFormatError: If writing fails
        """
        try:
            # Handle append mode
            if append:
                if isinstance(destination, (str, Path)):
                    if os.path.exists(destination):
                        existing_data = self.read(destination)
                        
                        # Combine data
                        combined_values = np.concatenate([existing_data.values, data.values])
                        combined_timestamps = None
                        if existing_data.timestamps is not None and data.timestamps is not None:
                            combined_timestamps = np.concatenate([existing_data.timestamps, data.timestamps])
                        
                        # Update metadata
                        combined_metadata = {**existing_data.metadata, **data.metadata}
                        
                        # Create new SignalData
                        data = SignalData(
                            values=combined_values,
                            timestamps=combined_timestamps,
                            metadata=combined_metadata
                        )
                else:
                    # For file-like objects, appending doesn't make sense without reading first
                    raise SignalFormatError("Append mode not supported for file-like objects")
            
            # Create the JSON structure
            output = {
                "metadata": {
                    "format_version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    **data.metadata
                },
                "data": data.values.tolist()
            }
            
            # Add timestamps if available
            if data.timestamps is not None:
                output["timestamps"] = data.timestamps.tolist()
            
            # Convert to JSON string
            json_str = json.dumps(output, indent=2)
            
            # Write to destination
            if isinstance(destination, (str, Path)):
                with open(destination, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            else:
                # Assume it's a file-like object
                destination.write(json_str.encode('utf-8'))
                destination.flush()
                
        except Exception as e:
            raise SignalFormatError(f"Failed to write JSON: {str(e)}")
    
    def get_metadata(self, source: Union[str, Path, BinaryIO]) -> Dict[str, Any]:
        """
        Extract metadata from a JSON source.
        
        Args:
            source: File path or file-like object
            
        Returns:
            Dictionary of metadata
            
        Raises:
            SignalFormatError: If metadata extraction fails
        """
        try:
            # For JSON, we need to read the file but we can avoid converting arrays
            if isinstance(source, (str, Path)):
                with open(source, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            else:
                # Assume it's a file-like object
                pos = source.tell()
                source.seek(0)
                content = source.read()
                source.seek(pos)  # Restore position
                json_data = json.loads(content.decode('utf-8'))
            
            return json_data.get("metadata", {})
            
        except Exception as e:
            raise SignalFormatError(f"Failed to extract metadata from JSON: {str(e)}")
    
    # --- Streaming support ---
    
    def write_chunk(self, stream: BinaryIO, data: SignalData) -> None:
        """
        Write a chunk of data to a JSON stream.
        
        For JSON, this implementation uses a line-delimited JSON approach
        where each chunk is a complete JSON object written on a new line.
        
        Args:
            stream: Open file handle
            data: Signal data chunk to write
            
        Raises:
            SignalFormatError: If writing fails
        """
        try:
            # Create a minimal JSON structure for the chunk
            chunk_json = {
                "metadata": data.metadata,
                "data": data.values.tolist()
            }
            
            # Add timestamps if available
            if data.timestamps is not None:
                chunk_json["timestamps"] = data.timestamps.tolist()
            
            # Convert to JSON string and add newline
            json_line = json.dumps(chunk_json) + "\n"
            
            # Write to stream
            stream.write(json_line.encode('utf-8'))
            stream.flush()
            
        except Exception as e:
            raise SignalFormatError(f"Failed to write JSON chunk: {str(e)}")
    
    def read_chunk(self, stream: BinaryIO) -> Optional[SignalData]:
        """
        Read a chunk of data from a JSON stream.
        
        Reads a line from the stream and parses it as a JSON object.
        
        Args:
            stream: Open file handle
            
        Returns:
            Signal data chunk or None if end of stream
            
        Raises:
            SignalFormatError: If reading fails
        """
        try:
            # Read a line from the stream
            line = stream.readline()
            
            # Check for end of file
            if not line:
                return None
            
            # Parse the JSON
            try:
                chunk_json = json.loads(line.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise SignalFormatError(f"Invalid JSON in chunk: {str(e)}")
            
            # Extract data
            if "data" not in chunk_json:
                raise SignalFormatError("Missing 'data' field in JSON chunk")
            
            # Convert to numpy arrays
            values = np.array(chunk_json["data"])
            timestamps = np.array(chunk_json.get("timestamps")) if "timestamps" in chunk_json else None
            metadata = chunk_json.get("metadata", {})
            
            # Create signal data
            return SignalData(
                values=values,
                timestamps=timestamps,
                metadata=metadata
            )
            
        except Exception as e:
            if not isinstance(e, SignalFormatError):
                raise SignalFormatError(f"Failed to read JSON chunk: {str(e)}")
            raise e