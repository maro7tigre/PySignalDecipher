"""
CSV Format Implementation

This module implements the CSV format handler for signal data.
CSV provides a human-readable format with wide compatibility across tools.
"""

import csv
import numpy as np
from typing import Dict, Any, List, Optional, Union, BinaryIO, Tuple, Iterator
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


class CsvFormat(SignalFormat):
    """
    CSV format handler for signal data.
    
    This format stores signal data as CSV with optional metadata as comments.
    Structure:
    # metadata: key=value
    # created_at: 2023-01-01T00:00:00.000Z
    timestamp,value1,value2,...
    0.0,1.0,2.0,...
    0.001,1.1,2.1,...
    """
    
    # Constants
    COMMENT_CHAR = "#"
    METADATA_PREFIX = "# metadata:"
    
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
            FormatCapability.RANDOM_ACCESS,
            FormatCapability.MULTI_CHANNEL
        ]
    
    def _metadata_from_comments(self, lines: List[str]) -> Dict[str, Any]:
        """Extract metadata from comment lines."""
        metadata = {}
        
        for line in lines:
            if not line.startswith(self.COMMENT_CHAR):
                continue
                
            content = line[len(self.COMMENT_CHAR):].strip()
            
            if ":" in content:
                key, value = content.split(":", 1)
                metadata[key.strip()] = value.strip()
                
        return metadata
    
    def _comments_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Convert metadata to comment lines."""
        comments = []
        
        # Add format indicator
        comments.append(f"{self.METADATA_PREFIX} format=csv,version=1.0")
        
        # Add creation timestamp if not present
        if "created_at" not in metadata:
            metadata = {**metadata, "created_at": datetime.now().isoformat()}
        
        # Add each metadata item as a comment
        for key, value in metadata.items():
            comments.append(f"{self.COMMENT_CHAR} {key}: {value}")
            
        return comments
    
    def _parse_csv_content(self, content: str) -> Tuple[Dict[str, Any], np.ndarray, Optional[np.ndarray]]:
        """Parse CSV content into metadata, values, and timestamps."""
        # Split into lines and filter empty lines
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        
        # Separate comments and data
        comment_lines = [line for line in lines if line.startswith(self.COMMENT_CHAR)]
        data_lines = [line for line in lines if not line.startswith(self.COMMENT_CHAR)]
        
        # Extract metadata
        metadata = self._metadata_from_comments(comment_lines)
        
        # Parse CSV data
        if not data_lines:
            raise SignalFormatError("CSV file has no data rows")
        
        csv_reader = csv.reader(data_lines)
        rows = list(csv_reader)
        
        # Get header and data rows
        header = rows[0]
        data_rows = rows[1:]
        
        # Check if first column contains timestamps
        has_timestamps = header[0].lower().startswith('time') or 'timestamp' in header[0].lower()
        
        # Process data rows
        timestamps = []
        values = []
        
        # Determine if multi-channel (more than 2 columns)
        is_multi_channel = len(header) > 2
        
        for row in data_rows:
            if not row:
                continue
            
            try:
                if has_timestamps:
                    timestamps.append(float(row[0]))
                    
                    # Handle multi-channel vs single-channel
                    if is_multi_channel:
                        values.append([float(v) for v in row[1:]])
                    else:
                        values.append(float(row[1]))
                else:
                    # No timestamps, all columns are values
                    if len(row) > 1:
                        values.append([float(v) for v in row])
                    else:
                        values.append(float(row[0]))
            except (ValueError, IndexError) as e:
                # Skip invalid rows but log warning
                import logging
                logging.warning(f"Skipping invalid CSV row: {row}, error: {e}")
        
        # Convert to numpy arrays
        values_array = np.array(values)
        timestamps_array = np.array(timestamps) if timestamps else None
        
        return metadata, values_array, timestamps_array
    
    def _create_csv_content(self, data: SignalData) -> str:
        """Create CSV content from SignalData."""
        buffer = io.StringIO()
        
        # Write metadata as comments
        for comment in self._comments_from_metadata(data.metadata):
            buffer.write(comment + "\n")
        
        # Create CSV writer
        writer = csv.writer(buffer, lineterminator="\n")
        
        # Determine if multi-channel
        is_multi_channel = len(data.values.shape) > 1
        
        # Write header
        if is_multi_channel:
            channel_count = data.values.shape[1]
            header = ["timestamp"] + [f"channel_{i}" for i in range(channel_count)]
        else:
            header = ["timestamp", "value"]
        
        writer.writerow(header)
        
        # Write data rows
        if data.timestamps is None:
            # Generate timestamps if not provided
            sample_rate = data.metadata.get("sample_rate", 1000.0)
            start_time = data.metadata.get("start_time", 0.0)
            timestamps = np.arange(len(data.values)) / sample_rate + start_time
        else:
            timestamps = data.timestamps
        
        if is_multi_channel:
            for i, (time, values) in enumerate(zip(timestamps, data.values)):
                writer.writerow([time] + values.tolist())
        else:
            for time, value in zip(timestamps, data.values):
                writer.writerow([time, value])
        
        return buffer.getvalue()
    
    def read(self, source: Union[str, Path, BinaryIO], time_range: Optional[TimeRange] = None) -> SignalData:
        """
        Read signal data from a CSV source.
        
        Args:
            source: File path or file-like object
            time_range: Optional time range to filter by
            
        Returns:
            SignalData object
        """
        try:
            # Handle different source types
            if isinstance(source, (str, Path)):
                with open(source, 'r', encoding='utf-8', newline='') as f:
                    content = f.read()
            else:
                # File-like object
                pos = source.tell()
                source.seek(0)
                content = source.read().decode('utf-8')
                source.seek(pos)
            
            # Parse the content
            metadata, values, timestamps = self._parse_csv_content(content)
            
            # Create SignalData
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
                e = SignalFormatError(f"Failed to read CSV: {str(e)}")
            raise e
    
    def write(self, destination: Union[str, Path, BinaryIO], data: SignalData, append: bool = False) -> None:
        """
        Write signal data to a CSV destination.
        
        Args:
            destination: File path or file-like object
            data: SignalData to write
            append: Whether to append to existing data
        """
        try:
            # Handle append mode
            if append and isinstance(destination, (str, Path)) and os.path.exists(destination):
                existing_data = self.read(destination)
                
                # Combine data
                combined_values = np.concatenate([existing_data.values, data.values])
                
                combined_timestamps = None
                if existing_data.timestamps is not None and data.timestamps is not None:
                    combined_timestamps = np.concatenate([existing_data.timestamps, data.timestamps])
                
                # Merge metadata
                combined_metadata = {**existing_data.metadata, **data.metadata}
                
                # Create combined signal data
                data = SignalData(
                    values=combined_values,
                    timestamps=combined_timestamps,
                    metadata=combined_metadata
                )
            
            # Create CSV content
            content = self._create_csv_content(data)
            
            # Write to destination
            if isinstance(destination, (str, Path)):
                # Ensure directory exists
                if isinstance(destination, str):
                    destination_path = Path(destination)
                else:
                    destination_path = destination
                    
                os.makedirs(destination_path.parent, exist_ok=True)
                
                with open(destination, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
            else:
                # File-like object
                destination.write(content.encode('utf-8'))
                destination.flush()
                
        except Exception as e:
            raise SignalFormatError(f"Failed to write CSV: {str(e)}")
    
    def get_metadata(self, source: Union[str, Path, BinaryIO]) -> Dict[str, Any]:
        """
        Extract metadata from a CSV source without loading all data.
        
        More efficient than the default implementation - only reads comment lines.
        """
        try:
            # Read only the beginning of the file
            if isinstance(source, (str, Path)):
                with open(source, 'r', encoding='utf-8') as f:
                    # Read until we find a non-comment line
                    comment_lines = []
                    for line in f:
                        if line.strip().startswith(self.COMMENT_CHAR):
                            comment_lines.append(line.strip())
                        else:
                            break
            else:
                # File-like object
                pos = source.tell()
                source.seek(0)
                
                comment_lines = []
                line = source.readline().decode('utf-8').strip()
                while line.startswith(self.COMMENT_CHAR):
                    comment_lines.append(line)
                    line = source.readline().decode('utf-8').strip()
                    if not line:  # End of file
                        break
                
                source.seek(pos)  # Restore position
            
            return self._metadata_from_comments(comment_lines)
            
        except Exception as e:
            raise SignalFormatError(f"Failed to extract metadata from CSV: {str(e)}")
    
    def read_time_range(self, source: Union[str, Path, BinaryIO], time_range: TimeRange) -> SignalData:
        """
        Read a specific time range from a CSV source (more efficient implementation).
        
        For CSV files, we can optimize by scanning line-by-line and only keeping
        rows that fall within the time range.
        """
        if time_range.start is None and time_range.end is None:
            return self.read(source)
            
        try:
            # Process line by line
            if isinstance(source, (str, Path)):
                with open(source, 'r', encoding='utf-8', newline='') as f:
                    return self._read_time_range_from_file(f, time_range)
            else:
                # File-like object
                pos = source.tell()
                source.seek(0)
                
                content = source.read().decode('utf-8')
                source.seek(pos)  # Restore position
                
                f = io.StringIO(content)
                return self._read_time_range_from_file(f, time_range)
                
        except Exception as e:
            if not isinstance(e, SignalFormatError):
                e = SignalFormatError(f"Failed to read CSV time range: {str(e)}")
            raise e
    
    def _read_time_range_from_file(self, file, time_range: TimeRange) -> SignalData:
        """Helper to read time range from a file-like object."""
        # Read comment lines for metadata
        comment_lines = []
        header = None
        timestamps = []
        values = []
        
        # Track if we've found the timestamp column
        timestamp_col = 0
        
        for line in file:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(self.COMMENT_CHAR):
                comment_lines.append(line)
                continue
            
            # Parse as CSV row
            row = next(csv.reader([line]))
            
            # Check if this is the header
            if header is None:
                header = row
                # Validate we have a timestamp column
                if not (header[0].lower().startswith('time') or 'timestamp' in header[0].lower()):
                    raise SignalFormatError("CSV file must have timestamp as first column for time range reading")
                continue
            
            # Extract timestamp
            try:
                timestamp = float(row[timestamp_col])
                
                # Skip if before start time
                if time_range.start is not None and timestamp < time_range.start:
                    continue
                # Exit loop if past end time
                if time_range.end is not None and timestamp > time_range.end:
                    break
                
                # If we got here, timestamp is in range
                timestamps.append(timestamp)
                
                # Extract values
                if len(row) > 2:  # Multi-channel
                    values.append([float(v) for v in row[1:]])
                else:
                    values.append(float(row[1]))
                    
            except (ValueError, IndexError) as e:
                # Skip invalid rows
                import logging
                logging.warning(f"Skipping invalid CSV row: {row}, error: {e}")
        
        # Extract metadata
        metadata = self._metadata_from_comments(comment_lines)
        
        # Convert to arrays
        timestamps_array = np.array(timestamps)
        values_array = np.array(values)
        
        # Create signal data
        return SignalData(
            values=values_array,
            timestamps=timestamps_array,
            metadata=metadata
        )
    
    # --- Streaming support ---
    
    def write_chunk(self, stream: BinaryIO, data: SignalData) -> None:
        """
        Write a chunk of data to a CSV stream.
        
        For first chunk, writes comments and header.
        For subsequent chunks, writes only data rows.
        """
        try:
            # Check if this is the first write to the stream
            is_first_chunk = stream.tell() == 0
            
            if is_first_chunk:
                # Write full CSV with metadata and header
                content = self._create_csv_content(data)
                stream.write(content.encode('utf-8'))
            else:
                # Write only the data rows without header or metadata
                buffer = io.StringIO()
                writer = csv.writer(buffer, lineterminator="\n")
                
                is_multi_channel = len(data.values.shape) > 1
                
                # Write data rows
                if data.timestamps is None:
                    # Generate timestamps if not provided
                    sample_rate = data.metadata.get("sample_rate", 1000.0)
                    start_time = data.metadata.get("start_time", 0.0)
                    timestamps = np.arange(len(data.values)) / sample_rate + start_time
                else:
                    timestamps = data.timestamps
                
                if is_multi_channel:
                    for i, (time, values) in enumerate(zip(timestamps, data.values)):
                        writer.writerow([time] + values.tolist())
                else:
                    for time, value in zip(timestamps, data.values):
                        writer.writerow([time, value])
                
                stream.write(buffer.getvalue().encode('utf-8'))
            
            stream.flush()
            
        except Exception as e:
            raise SignalFormatError(f"Failed to write CSV chunk: {str(e)}")
    
    def read_chunk(self, stream: BinaryIO) -> Optional[SignalData]:
        """
        Read a chunk of data from a CSV stream.
        
        Reads up to 1000 data rows or until end of file.
        For first chunk, parses metadata and header.
        """
        try:
            # Track position to restore if needed
            start_pos = stream.tell()
            
            # Read first line to check position in file
            first_line = stream.readline().decode('utf-8').strip()
            if not first_line:  # End of file
                return None
            
            # For first chunk, handle metadata and header
            if start_pos == 0:
                # Go back to beginning
                stream.seek(0)
                
                # Read comment lines for metadata
                comment_lines = []
                while True:
                    pos = stream.tell()
                    line = stream.readline().decode('utf-8').strip()
                    if not line:
                        break
                    if line.startswith(self.COMMENT_CHAR):
                        comment_lines.append(line)
                    else:
                        # Found the header line
                        header = next(csv.reader([line]))
                        break
                
                # Extract metadata
                metadata = self._metadata_from_comments(comment_lines)
            else:
                # For subsequent chunks, we don't have metadata
                metadata = {}
                # Go back to read the first line again (could be header or data)
                stream.seek(start_pos)
                line = stream.readline().decode('utf-8').strip()
                # Check if this is still the header
                if line.lower().startswith('time') or 'timestamp' in line.lower().split(',')[0]:
                    # This is the header, no data yet in this chunk
                    return SignalData(
                        values=np.array([]),
                        timestamps=np.array([]),
                        metadata=metadata
                    )
                else:
                    # This is a data line, rewind to read it again
                    stream.seek(start_pos)
            
            # Read data rows (up to 1000)
            timestamps = []
            values = []
            is_multi_channel = None
            max_rows = 1000
            rows_read = 0
            
            while rows_read < max_rows:
                pos = stream.tell()
                line = stream.readline().decode('utf-8').strip()
                
                if not line:  # End of file
                    break
                
                if line.startswith(self.COMMENT_CHAR) or line.lower().startswith('time') or 'timestamp' in line.lower().split(',')[0]:
                    # Skip comment lines and header
                    continue
                
                # Parse as CSV row
                row = next(csv.reader([line]))
                
                try:
                    # Extract timestamp and values
                    timestamp = float(row[0])
                    timestamps.append(timestamp)
                    
                    # Detect if multi-channel on first data row
                    if is_multi_channel is None:
                        is_multi_channel = len(row) > 2
                    
                    if is_multi_channel:
                        values.append([float(v) for v in row[1:]])
                    else:
                        values.append(float(row[1]))
                    
                    rows_read += 1
                    
                except (ValueError, IndexError) as e:
                    # Skip invalid rows
                    import logging
                    logging.warning(f"Skipping invalid CSV row: {row}, error: {e}")
            
            # If no data was read, return empty signal
            if not timestamps:
                return SignalData(
                    values=np.array([]),
                    timestamps=np.array([]),
                    metadata=metadata
                )
            
            # Convert to arrays
            timestamps_array = np.array(timestamps)
            values_array = np.array(values)
            
            # Create signal data
            return SignalData(
                values=values_array,
                timestamps=timestamps_array,
                metadata=metadata
            )
            
        except Exception as e:
            if not isinstance(e, SignalFormatError):
                raise SignalFormatError(f"Failed to read CSV chunk: {str(e)}")
            raise e
    
    def close_stream(self, stream: BinaryIO) -> None:
        """Close a CSV stream."""
        try:
            stream.close()
        except Exception as e:
            raise SignalFormatError(f"Failed to close CSV stream: {str(e)}")