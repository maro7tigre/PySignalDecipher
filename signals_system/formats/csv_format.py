"""
CSV Format Implementation

This module implements the CSV format handler for signal data.
CSV is a widely compatible format for tabular data that can easily be imported
into other applications like Excel, MATLAB, or pandas.
"""

import csv
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


class CsvFormat(SignalFormat):
    """
    CSV format handler for signal data.
    
    This format stores signal data as CSV with optional metadata as comments.
    The default structure is:
    
    # metadata: key=value
    # created_at: 2023-01-01T00:00:00.000000
    timestamp,value1,value2,...
    0.0,1.0,2.0,...
    0.001,1.1,2.1,...
    ...
    """
    
    # Constants
    COMMENT_CHAR = "#"
    METADATA_PREFIX = "# metadata: "
    
    @property
    def name(self) -> str:
        return "CSV"
    
    @property
    def extensions(self) -> List[str]:
        return [".csv"]
    
    @property
    def capabilities(self) -> List[FormatCapability]:
        return [
            FormatCapability.METADATA,
            FormatCapability.STREAMING,
            FormatCapability.MULTI_CHANNEL,
            FormatCapability.PARTIAL_READ
        ]
    
    def _metadata_to_comments(self, metadata: Dict[str, Any]) -> List[str]:
        """Convert metadata dictionary to comment lines."""
        comments = []
        
        # Add general metadata line
        comments.append(f"{self.METADATA_PREFIX}format=csv,version=1.0")
        
        # Add creation timestamp if not present
        if "created_at" not in metadata:
            metadata = {**metadata, "created_at": datetime.now().isoformat()}
        
        # Add each metadata item as a comment
        for key, value in metadata.items():
            comments.append(f"{self.COMMENT_CHAR} {key}: {value}")
            
        return comments
    
    def _comments_to_metadata(self, comments: List[str]) -> Dict[str, Any]:
        """Extract metadata from comment lines."""
        metadata = {}
        
        for line in comments:
            # Skip non-comment lines
            if not line.startswith(self.COMMENT_CHAR):
                continue
                
            # Remove comment char and split by colon
            content = line[len(self.COMMENT_CHAR):].strip()
            
            # Look for key-value pairs
            if ":" in content:
                key, value = content.split(":", 1)
                metadata[key.strip()] = value.strip()
                
        return metadata
    
    def serialize(self, 
                 data: np.ndarray, 
                 timestamps: np.ndarray = None, 
                 metadata: Dict[str, Any] = None) -> bytes:
        """Serialize signal data to CSV bytes."""
        try:
            with io.StringIO() as output:
                # Write metadata as comments
                for comment in self._metadata_to_comments(metadata or {}):
                    output.write(comment + "\n")
                
                # Create CSV writer
                writer = csv.writer(output, lineterminator="\n")
                
                # Determine if we're dealing with multi-channel data
                is_multi_channel = len(data.shape) > 1
                
                # Write header
                if is_multi_channel:
                    num_channels = data.shape[1]
                    header = ["timestamp"] + [f"channel_{i}" for i in range(num_channels)]
                else:
                    header = ["timestamp", "value"]
                    
                writer.writerow(header)
                
                # Generate timestamps if not provided
                if timestamps is None:
                    # Default to 1000 Hz if not specified in metadata
                    sample_rate = metadata.get("sample_rate", 1000.0) if metadata else 1000.0
                    start_time = metadata.get("start_time", 0.0) if metadata else 0.0
                    timestamps = np.arange(len(data)) / sample_rate + start_time
                
                # Write data rows
                if is_multi_channel:
                    for i, (time, values) in enumerate(zip(timestamps, data)):
                        writer.writerow([time] + values.tolist())
                else:
                    for i, (time, value) in enumerate(zip(timestamps, data)):
                        writer.writerow([time, value])
                
                # Return as bytes
                return output.getvalue().encode('utf-8')
                
        except Exception as e:
            raise SignalFormatError(f"CSV serialization failed: {e}") from e
    
    def deserialize(self, 
                   data: bytes) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """Deserialize CSV bytes to signal data."""
        try:
            # Parse CSV
            text = data.decode('utf-8')
            lines = text.splitlines()
            
            # Extract comments and data lines
            comments = []
            data_lines = []
            
            for line in lines:
                if line.startswith(self.COMMENT_CHAR):
                    comments.append(line)
                else:
                    data_lines.append(line)
            
            # Extract metadata from comments
            metadata = self._comments_to_metadata(comments)
            
            # Parse CSV data
            with io.StringIO("\n".join(data_lines)) as csv_data:
                reader = csv.reader(csv_data)
                
                # Read header
                header = next(reader, None)
                if not header:
                    raise SignalFormatError("CSV file has no header")
                
                # Extract timestamp and values from each row
                timestamps = []
                values = []
                
                for row in reader:
                    if not row:  # Skip empty rows
                        continue
                        
                    try:
                        timestamps.append(float(row[0]))
                        
                        # Handle multi-channel vs single-channel data
                        if len(row) > 2:
                            values.append([float(v) for v in row[1:]])
                        else:
                            values.append(float(row[1]))
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Skipping invalid CSV row: {row}, error: {e}")
                
                # Convert to numpy arrays
                timestamps_array = np.array(timestamps)
                
                # Handle multi-channel data
                if values and isinstance(values[0], list):
                    values_array = np.array(values)
                else:
                    values_array = np.array(values)
                
                return values_array, timestamps_array, metadata
                
        except Exception as e:
            raise SignalFormatError(f"CSV deserialization failed: {e}") from e
    
    def read_file(self, 
                 file_path: str, 
                 mode: ReadMode = ReadMode.FULL,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 start_sample: Optional[int] = None,
                 end_sample: Optional[int] = None,
                 chunk_size: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Read signal data from a CSV file."""
        try:
            # For TIME_RANGE mode, we can optimize by using a line-by-line approach
            if mode == ReadMode.TIME_RANGE and (start_time is not None or end_time is not None):
                return self._read_file_time_range(file_path, start_time, end_time)
            
            # For SAMPLE_RANGE mode, we might still need to read everything
            # but we can optimize by skipping rows when reading
            elif mode == ReadMode.SAMPLE_RANGE and (start_sample is not None or end_sample is not None):
                return self._read_file_sample_range(file_path, start_sample, end_sample)
                
            # For CHUNK mode, we might read just a portion of the file
            elif mode == ReadMode.CHUNK and chunk_size is not None:
                return self._read_file_chunk(file_path, chunk_size)
            
            # Default: read the entire file
            with open(file_path, 'rb') as f:
                data = f.read()
                
            return self.deserialize(data)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise SignalFormatError(f"Failed to read CSV file: {e}") from e
    
    def _read_file_time_range(self, 
                             file_path: str, 
                             start_time: Optional[float], 
                             end_time: Optional[float]) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Read a specific time range from a CSV file."""
        timestamps = []
        values = []
        metadata = {}
        is_multi_channel = None
        
        with open(file_path, 'r') as f:
            # Read and process the file line by line
            for line in f:
                # Extract metadata from comments
                if line.startswith(self.COMMENT_CHAR):
                    key_value = self._comments_to_metadata([line])
                    metadata.update(key_value)
                    continue
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Parse CSV row
                row = next(csv.reader([line]))
                
                # Check if this is the header row
                if line.lower().startswith('timestamp') or 'time' in line.lower().split(',')[0]:
                    # Determine if we have multi-channel data
                    is_multi_channel = len(row) > 2
                    continue
                
                try:
                    # Extract timestamp
                    timestamp = float(row[0])
                    
                    # Skip rows outside our time range
                    if start_time is not None and timestamp < start_time:
                        continue
                    if end_time is not None and timestamp > end_time:
                        break  # Assuming timestamps are sorted
                    
                    # Record the timestamp
                    timestamps.append(timestamp)
                    
                    # Extract values
                    if is_multi_channel:
                        values.append([float(v) for v in row[1:]])
                    else:
                        values.append(float(row[1]))
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping invalid CSV row: {row}, error: {e}")
        
        # Convert to numpy arrays
        timestamps_array = np.array(timestamps)
        
        # Handle multi-channel data
        if values and isinstance(values[0], list):
            values_array = np.array(values)
        else:
            values_array = np.array(values)
        
        return values_array, timestamps_array, metadata
    
    def _read_file_sample_range(self, 
                               file_path: str, 
                               start_sample: Optional[int], 
                               end_sample: Optional[int]) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Read a specific sample range from a CSV file."""
        # For simplicity, we'll read everything and then slice
        # A more optimized version would skip rows when reading
        with open(file_path, 'rb') as f:
            data = f.read()
            
        signal_data, timestamps, metadata = self.deserialize(data)
        
        # Apply sample range slicing
        start_idx = start_sample or 0
        end_idx = end_sample if end_sample is not None else len(signal_data)
        
        return signal_data[start_idx:end_idx], timestamps[start_idx:end_idx], metadata
    
    def _read_file_chunk(self, 
                        file_path: str, 
                        chunk_size: int) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """Read a chunk of data from a CSV file."""
        # For simplicity, just read from the beginning
        # A more advanced implementation would track state between calls
        return self._read_file_sample_range(file_path, 0, chunk_size)
    
    def write_file(self, 
                  file_path: str, 
                  data: np.ndarray, 
                  timestamps: Optional[np.ndarray] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  append: bool = False,
                  compression: Optional[str] = None) -> None:
        """Write signal data to a CSV file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Handle append mode
            if append and os.path.exists(file_path):
                # Read existing data
                existing_data, existing_timestamps, existing_metadata = self.read_file(file_path)
                
                # Combine data
                data = np.concatenate([existing_data, data])
                
                if timestamps is not None and existing_timestamps is not None:
                    timestamps = np.concatenate([existing_timestamps, timestamps])
                elif existing_timestamps is not None:
                    timestamps = existing_timestamps
                
                # Update metadata
                if existing_metadata:
                    metadata = {**existing_metadata, **(metadata or {})}
                
                # Write mode will be 'w' to create a new file
                write_mode = 'w'
            else:
                # Create new file
                write_mode = 'w'
            
            # Serialize data
            serialized = self.serialize(data, timestamps, metadata)
            
            # Write to file
            with open(file_path, write_mode, encoding='utf-8') as f:
                f.write(serialized.decode('utf-8'))
                
        except Exception as e:
            raise SignalFormatError(f"Failed to write CSV file: {e}") from e
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a CSV file without loading all data."""
        try:
            metadata = {}
            
            with open(file_path, 'r') as f:
                # Read until we find a non-comment line
                for line in f:
                    if line.startswith(self.COMMENT_CHAR):
                        key_value = self._comments_to_metadata([line])
                        metadata.update(key_value)
                    else:
                        # We've read all metadata
                        break
            
            return metadata
            
        except Exception as e:
            raise SignalFormatError(f"Failed to extract metadata from CSV file: {e}") from e
    
    def get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """Get structure information about the CSV file."""
        try:
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            # Get file stats
            file_stats = os.stat(file_path)
            
            # Count lines and determine if multi-channel
            total_lines = 0
            header_cols = 0
            is_multi_channel = False
            
            with open(file_path, 'r') as f:
                for line in f:
                    if not line.startswith(self.COMMENT_CHAR) and line.strip():
                        # Check if this is the header
                        if total_lines == 0 or 'timestamp' in line.lower() or 'time' in line.lower().split(',')[0]:
                            header_cols = len(next(csv.reader([line])))
                            is_multi_channel = header_cols > 2
                        
                        total_lines += 1
            
            # Build structure info
            structure = {
                "file_size_bytes": file_stats.st_size,
                "total_lines": total_lines,
                "modification_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "creation_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "is_multi_channel": is_multi_channel,
                "num_channels": header_cols - 1 if header_cols > 0 else 0,
            }
            
            # Add metadata-derived fields if available
            if "sample_rate" in metadata:
                structure["sample_rate"] = metadata["sample_rate"]
            if "duration" in metadata:
                structure["duration"] = metadata["duration"]
            
            return structure
            
        except Exception as e:
            raise SignalFormatError(f"Failed to analyze CSV file structure: {e}") from e
    
    def write_chunk(self, 
                   file_handle: BinaryIO, 
                   data: np.ndarray,
                   timestamps: Optional[np.ndarray] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """Write a chunk of data to an open CSV file."""
        try:
            # For the first chunk, write metadata and header
            if file_handle.tell() == 0:
                # Serialize with metadata as comments
                serialized = self.serialize(data, timestamps, metadata)
                bytes_written = file_handle.write(serialized)
            else:
                # For subsequent chunks, just write the data without headers
                # Create a CSV writer using an in-memory buffer
                with io.StringIO() as output:
                    writer = csv.writer(output, lineterminator="\n")
                    
                    # Determine if we're dealing with multi-channel data
                    is_multi_channel = len(data.shape) > 1
                    
                    # Generate timestamps if not provided
                    if timestamps is None:
                        # Default to 1000 Hz if not specified
                        sample_rate = metadata.get("sample_rate", 1000.0) if metadata else 1000.0
                        start_time = metadata.get("start_time", 0.0) if metadata else 0.0
                        timestamps = np.arange(len(data)) / sample_rate + start_time
                    
                    # Write data rows only (no header)
                    if is_multi_channel:
                        for i, (time, values) in enumerate(zip(timestamps, data)):
                            writer.writerow([time] + values.tolist())
                    else:
                        for i, (time, value) in enumerate(zip(timestamps, data)):
                            writer.writerow([time, value])
                    
                    # Write to file handle
                    csv_data = output.getvalue()
                    bytes_written = file_handle.write(csv_data.encode('utf-8'))
            
            file_handle.flush()
            return bytes_written
            
        except Exception as e:
            raise SignalFormatError(f"Failed to write CSV chunk: {e}") from e
    
    def read_chunk(self, 
                  file_handle: BinaryIO, 
                  chunk_size: int = 1024,
                  offset: Optional[int] = None) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Dict[str, Any]]]:
        """Read a chunk of data from an open CSV file."""
        try:
            # Set position if specified
            if offset is not None:
                file_handle.seek(offset)
            
            # Read lines
            lines = []
            metadata = {}
            count = 0
            
            while count < chunk_size:
                line = file_handle.readline().decode('utf-8')
                if not line:  # End of file
                    break
                    
                # Process metadata
                if line.startswith(self.COMMENT_CHAR):
                    key_value = self._comments_to_metadata([line])
                    metadata.update(key_value)
                    continue
                
                lines.append(line)
                count += 1
            
            # Parse as CSV
            if lines:
                with io.StringIO("".join(lines)) as csv_data:
                    reader = csv.reader(csv_data)
                    
                    # Check for header
                    first_row = next(reader, None)
                    if not first_row:
                        return np.array([]), np.array([]), metadata
                    
                    # Check if first row is header
                    is_header = any(['time' in col.lower() for col in first_row])
                    
                    # Track rows for data
                    timestamps = []
                    values = []
                    
                    # Process first row if it's not header
                    if not is_header:
                        try:
                            timestamps.append(float(first_row[0]))
                            
                            if len(first_row) > 2:  # Multi-channel
                                values.append([float(v) for v in first_row[1:]])
                            else:
                                values.append(float(first_row[1]))
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Invalid CSV row: {first_row}, error: {e}")
                    
                    # Process remaining rows
                    for row in reader:
                        if not row:  # Skip empty rows
                            continue
                            
                        try:
                            timestamps.append(float(row[0]))
                            
                            # Handle multi-channel vs single-channel
                            if len(row) > 2:
                                values.append([float(v) for v in row[1:]])
                            else:
                                values.append(float(row[1]))
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Invalid CSV row: {row}, error: {e}")
                    
                    # Convert to numpy arrays
                    timestamps_array = np.array(timestamps)
                    
                    # Handle multi-channel data
                    if values and isinstance(values[0], list):
                        values_array = np.array(values)
                    else:
                        values_array = np.array(values)
                    
                    return values_array, timestamps_array, metadata
            
            # No data read
            return np.array([]), np.array([]), metadata
            
        except Exception as e:
            raise SignalFormatError(f"Failed to read CSV chunk: {e}") from e