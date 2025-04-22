"""
JSON Format Implementation

This module implements the JSON format handler for signal data.
"""

import json
import os
import numpy as np
from typing import Dict, Any, List, Optional, BinaryIO, Tuple
import logging
from datetime import datetime
import io

from .base import (
    SignalFormat, 
    FormatCapability, 
    ReadMode, 
    SignalFormatError
)

logger = logging.getLogger(__name__)


class JsonFormat(SignalFormat):
    """
    JSON format handler for signal data.
    
    This format stores signal data as JSON with a simple structure containing
    metadata and the signal data itself.
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
            FormatCapability.STREAMING,
            FormatCapability.MULTI_CHANNEL
        ]
    
    def serialize(self, 
                 data: np.ndarray, 
                 timestamps: np.ndarray = None, 
                 metadata: Dict[str, Any] = None) -> bytes:
        """Serialize signal data to JSON bytes."""
        try:
            # Create data structure with sensible defaults
            output = {
                "metadata": {
                    "format_version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    **(metadata or {})
                },
                "data": data.tolist()
            }
            
            # Add timestamps if provided
            if timestamps is not None:
                output["timestamps"] = timestamps.tolist()
            
            # Serialize to JSON
            return json.dumps(output).encode('utf-8')
            
        except Exception as e:
            raise SignalFormatError(f"JSON serialization failed: {e}") from e
    
    def deserialize(self, 
                   data: bytes) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """Deserialize JSON bytes to signal data."""
        try:
            # Parse JSON
            parsed = json.loads(data.decode('utf-8'))
            
            # Extract components with validation
            if "data" not in parsed:
                raise SignalFormatError("Missing 'data' field in JSON")
            
            # Convert to numpy arrays
            signal_data = np.array(parsed["data"])
            timestamps = np.array(parsed.get("timestamps")) if "timestamps" in parsed else None
            metadata = parsed.get("metadata", {})
            
            return signal_data, timestamps, metadata
            
        except json.JSONDecodeError as e:
            raise SignalFormatError(f"Invalid JSON: {e}") from e
        except Exception as e:
            raise SignalFormatError(f"JSON deserialization failed: {e}") from e
    
    def read_file(self, 
                 file_path: str, 
                 mode: ReadMode = ReadMode.FULL,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 start_sample: Optional[int] = None,
                 end_sample: Optional[int] = None,
                 chunk_size: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Read signal data from a JSON file."""
        try:
            # For small files, the simplest approach is to read everything and then slice
            with open(file_path, 'rb') as f:
                data = f.read()
            
            signal_data, timestamps, metadata = self.deserialize(data)
            
            # Apply time/sample filtering based on mode
            if mode == ReadMode.TIME_RANGE and timestamps is not None:
                # Filter by time range if timestamps are available
                mask = np.ones(len(timestamps), dtype=bool)
                if start_time is not None:
                    mask = mask & (timestamps >= start_time)
                if end_time is not None:
                    mask = mask & (timestamps <= end_time)
                
                signal_data = signal_data[mask]
                timestamps = timestamps[mask]
                
            elif mode == ReadMode.SAMPLE_RANGE:
                # Filter by sample range
                start_idx = start_sample or 0
                end_idx = end_sample if end_sample is not None else len(signal_data)
                
                signal_data = signal_data[start_idx:end_idx]
                if timestamps is not None:
                    timestamps = timestamps[start_idx:end_idx]
            
            # Note: CHUNK mode isn't well-suited for simple JSON files
            # but we could implement it for streaming JSON formats
            
            return signal_data, timestamps, metadata
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise SignalFormatError(f"Failed to read JSON file: {e}") from e
    
    def write_file(self, 
                  file_path: str, 
                  data: np.ndarray, 
                  timestamps: Optional[np.ndarray] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  append: bool = False,
                  compression: Optional[str] = None) -> None:
        """Write signal data to a JSON file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # For append mode, we need to read existing data first
            if append and os.path.exists(file_path):
                existing_data, existing_timestamps, existing_metadata = self.read_file(file_path)
                
                # Combine existing and new data
                data = np.concatenate([existing_data, data])
                
                if timestamps is not None and existing_timestamps is not None:
                    timestamps = np.concatenate([existing_timestamps, timestamps])
                elif existing_timestamps is not None:
                    timestamps = existing_timestamps
                
                # Merge metadata, with new values taking precedence
                if existing_metadata:
                    merged_metadata = {**existing_metadata, **(metadata or {})}
                    metadata = merged_metadata
            
            # Serialize and write to file
            serialized = self.serialize(data, timestamps, metadata)
            
            with open(file_path, 'wb') as f:
                f.write(serialized)
                
        except Exception as e:
            raise SignalFormatError(f"Failed to write JSON file: {e}") from e
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a JSON file without loading all data."""
        try:
            # For JSON, we unfortunately need to parse the entire file
            # to get the metadata, but we can avoid converting arrays
            with open(file_path, 'r') as f:
                parsed = json.load(f)
            
            return parsed.get("metadata", {})
            
        except Exception as e:
            raise SignalFormatError(f"Failed to extract metadata from JSON file: {e}") from e
    
    def get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """Get structure information about the JSON file."""
        try:
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            # Get file stats
            file_stats = os.stat(file_path)
            
            # Read a small sample to determine data structure
            with open(file_path, 'rb') as f:
                # Read first 16KB which should be enough for structure
                sample_data = f.read(16 * 1024)
            
            signal_data, timestamps, _ = self.deserialize(sample_data)
            
            # Determine structure from the sample
            structure = {
                "file_size_bytes": file_stats.st_size,
                "modification_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "creation_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "data_type": str(signal_data.dtype),
                "has_timestamps": timestamps is not None,
            }
            
            # Add metadata-derived fields if available
            if "sample_rate" in metadata:
                structure["sample_rate"] = metadata["sample_rate"]
            if "duration" in metadata:
                structure["duration"] = metadata["duration"]
            if "num_channels" in metadata:
                structure["num_channels"] = metadata["num_channels"]
            
            return structure
            
        except Exception as e:
            raise SignalFormatError(f"Failed to analyze JSON file structure: {e}") from e
    
    def write_chunk(self, 
                   file_handle: BinaryIO, 
                   data: np.ndarray,
                   timestamps: Optional[np.ndarray] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """Write a chunk of data to an open JSON file."""
        try:
            # For simple JSON format, we don't support true chunking
            # We just write the entire data as one chunk
            chunk_data = self.serialize(data, timestamps, metadata)
            bytes_written = file_handle.write(chunk_data)
            file_handle.flush()
            return bytes_written
            
        except Exception as e:
            raise SignalFormatError(f"Failed to write JSON chunk: {e}") from e
    
    def read_chunk(self, 
                  file_handle: BinaryIO, 
                  chunk_size: int = 1024,
                  offset: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """Read a chunk of data from an open JSON file."""
        try:
            # For simple JSON format, we don't support true chunking
            # We just read the entire file
            if offset is not None:
                file_handle.seek(offset)
            
            data = file_handle.read()
            return self.deserialize(data)
            
        except Exception as e:
            raise SignalFormatError(f"Failed to read JSON chunk: {e}") from e
    
    def finalize_file(self, file_handle: BinaryIO) -> None:
        """Finalize a JSON file after writing."""
        # For simple JSON, there's nothing to finalize
        file_handle.flush()


# Register the format when this module is imported
def register():
    from .base import format_registry
    format_registry.register_format(JsonFormat())