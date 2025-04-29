"""
Tests for the signals_system.formats package

This module contains tests for the signal format handlers and utilities.
"""

import os
import sys
import pytest
import numpy as np
import tempfile
from pathlib import Path
import io
import json
import csv

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from signals_system.formats import base
from signals_system.formats.base import SignalData, TimeRange, FormatCapability, SignalFormatError
from signals_system.formats.json_format import JsonFormat
from signals_system.formats.csv_format import CsvFormat


class TestSignalData:
    """Tests for the SignalData class"""

    def test_initialization(self):
        """Test basic initialization of SignalData"""
        # Simple single-channel data
        values = np.array([1.0, 2.0, 3.0])
        data = SignalData(values=values)
        
        assert data.values is values
        assert data.timestamps is None
        assert data.metadata == {}
        assert data.num_samples == 3
        assert data.num_channels == 1
        assert data.duration is None
        
        # Data with timestamps
        timestamps = np.array([0.0, 0.1, 0.2])
        data_with_time = SignalData(values=values, timestamps=timestamps)
        
        assert data_with_time.values is values
        assert data_with_time.timestamps is timestamps
        assert data_with_time.duration == 0.2
        assert data_with_time.sample_rate == pytest.approx(10.0)
        
        # Multi-channel data
        multi_values = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        multi_data = SignalData(values=multi_values)
        
        assert multi_data.num_channels == 2
        assert multi_data.num_samples == 3
    
    def test_slicing(self):
        """Test slicing functionality"""
        # Create test data
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        timestamps = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
        metadata = {"sample_rate": 10.0, "test_key": "test_value"}
        data = SignalData(values=values, timestamps=timestamps, metadata=metadata)
        
        # Test slice by indices
        sliced = data.slice(1, 4)
        assert np.array_equal(sliced.values, np.array([2.0, 3.0, 4.0]))
        assert np.array_equal(sliced.timestamps, np.array([0.1, 0.2, 0.3]))
        assert sliced.metadata == metadata  # Metadata should be copied
        
        # Test slice by time range
        time_range = TimeRange(start=0.15, end=0.35)
        time_sliced = data.time_slice(time_range)
        assert np.array_equal(time_sliced.values, np.array([3.0, 4.0]))
        assert np.array_equal(time_sliced.timestamps, np.array([0.2, 0.3]))
    
    def test_properties(self):
        """Test property calculations"""
        # Test sample rate calculation from metadata
        values = np.array([1.0, 2.0, 3.0])
        metadata = {"sample_rate": 1000.0}
        data = SignalData(values=values, metadata=metadata)
        assert data.sample_rate == 1000.0
        
        # Test sample rate calculation from timestamps
        timestamps = np.array([0.0, 0.001, 0.002])
        data = SignalData(values=values, timestamps=timestamps)
        assert data.sample_rate == pytest.approx(1000.0)
        
        # Test no sample rate
        data = SignalData(values=values)
        assert data.sample_rate is None


class TestTimeRange:
    """Tests for the TimeRange class"""
    
    def test_initialization(self):
        """Test TimeRange initialization"""
        # Test with both start and end
        time_range = TimeRange(start=1.0, end=2.0)
        assert time_range.start == 1.0
        assert time_range.end == 2.0
        
        # Test with only start
        time_range = TimeRange(start=1.0)
        assert time_range.start == 1.0
        assert time_range.end is None
        
        # Test with only end
        time_range = TimeRange(end=2.0)
        assert time_range.start is None
        assert time_range.end == 2.0
        
        # Test empty range
        time_range = TimeRange()
        assert time_range.start is None
        assert time_range.end is None
    
    def test_representation(self):
        """Test string representation"""
        time_range = TimeRange(start=1.0, end=2.0)
        assert repr(time_range) == "TimeRange(start=1.0, end=2.0)"


class TestFormatRegistry:
    """Tests for the FormatRegistry class"""
    
    def test_registration(self):
        """Test format registration and retrieval"""
        # Create a test registry
        registry = base.FormatRegistry()
        
        # Register format classes
        registry.register(JsonFormat)
        registry.register(CsvFormat)
        
        # Test get_format by name
        json_format = registry.get_format("json")
        assert isinstance(json_format, JsonFormat)
        
        csv_format = registry.get_format("CSV")  # Case insensitive
        assert isinstance(csv_format, CsvFormat)
        
        # Test get_for_extension
        json_format = registry.get_for_extension(".json")
        assert isinstance(json_format, JsonFormat)
        
        csv_format = registry.get_for_extension("csv")  # With or without dot
        assert isinstance(csv_format, CsvFormat)
        
        # Test get_for_file
        json_format = registry.get_for_file("test.json")
        assert isinstance(json_format, JsonFormat)
        
        csv_format = registry.get_for_file(Path("test.csv"))
        assert isinstance(csv_format, CsvFormat)
    
    def test_find_with_capability(self):
        """Test finding formats with specific capabilities"""
        # Create a test registry
        registry = base.FormatRegistry()
        
        # Register format classes
        registry.register(JsonFormat)
        registry.register(CsvFormat)
        
        # Find formats with streaming capability
        streaming_formats = registry.find_with_capability(FormatCapability.STREAMING)
        assert len(streaming_formats) == 2
        assert isinstance(streaming_formats[0], (JsonFormat, CsvFormat))
        assert isinstance(streaming_formats[1], (JsonFormat, CsvFormat))
        
        # Find formats with random access capability
        random_access_formats = registry.find_with_capability(FormatCapability.RANDOM_ACCESS)
        assert len(random_access_formats) == 1
        assert isinstance(random_access_formats[0], CsvFormat)
    
    def test_global_registry(self):
        """Test the global registry instance"""
        # The global registry should be pre-populated with built-in formats
        format_classes = [f.__class__.__name__.lower() for f in base.registry.find_with_capability(FormatCapability.METADATA)]
        assert "jsonformat" in format_classes
        assert "csvformat" in format_classes


class TestJsonFormat:
    """Tests for the JsonFormat class"""
    
    def test_basic_properties(self):
        """Test basic properties of JsonFormat"""
        json_format = JsonFormat()
        
        assert json_format.name == "JSON"
        assert ".json" in json_format.extensions
        assert ".jsn" in json_format.extensions
        assert FormatCapability.METADATA in json_format.capabilities
        assert FormatCapability.STREAMING in json_format.capabilities
    
    def test_read_write(self):
        """Test reading and writing JSON files"""
        # Create test data
        values = np.array([1.0, 2.0, 3.0])
        timestamps = np.array([0.0, 0.1, 0.2])
        metadata = {"sample_rate": 10.0, "test_key": "test_value"}
        data = SignalData(values=values, timestamps=timestamps, metadata=metadata)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write to file
            json_format = JsonFormat()
            json_format.write(tmp_path, data)
            
            # Read from file
            read_data = json_format.read(tmp_path)
            
            # Verify data integrity
            assert np.array_equal(read_data.values, values)
            assert np.array_equal(read_data.timestamps, timestamps)
            assert "sample_rate" in read_data.metadata
            assert read_data.metadata["sample_rate"] == 10.0
            assert read_data.metadata["test_key"] == "test_value"
            
            # Test append mode
            new_values = np.array([4.0, 5.0])
            new_timestamps = np.array([0.3, 0.4])
            new_data = SignalData(values=new_values, timestamps=new_timestamps, metadata={"new_key": "new_value"})
            
            json_format.write(tmp_path, new_data, append=True)
            
            # Read the combined data
            combined_data = json_format.read(tmp_path)
            assert combined_data.num_samples == 5
            assert combined_data.metadata["new_key"] == "new_value"
            assert combined_data.metadata["test_key"] == "test_value"
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_get_metadata(self):
        """Test extracting metadata from JSON files"""
        # Create test data
        values = np.array([1.0, 2.0, 3.0])
        metadata = {"test_key": "test_value", "sample_rate": 10.0}
        data = SignalData(values=values, metadata=metadata)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write to file
            json_format = JsonFormat()
            json_format.write(tmp_path, data)
            
            # Extract metadata
            extracted_metadata = json_format.get_metadata(tmp_path)
            
            # Verify metadata
            assert "test_key" in extracted_metadata
            assert extracted_metadata["test_key"] == "test_value"
            assert extracted_metadata["sample_rate"] == 10.0
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_streaming(self):
        """Test streaming operations with JSON format"""
        # Create test data chunks
        chunk1 = SignalData(
            values=np.array([1.0, 2.0, 3.0]),
            timestamps=np.array([0.0, 0.1, 0.2]),
            metadata={"chunk": 1}
        )
        
        chunk2 = SignalData(
            values=np.array([4.0, 5.0]),
            timestamps=np.array([0.3, 0.4]),
            metadata={"chunk": 2}
        )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Open stream for writing
            json_format = JsonFormat()
            stream = json_format.open_stream(tmp_path, 'w')
            
            # Write chunks
            json_format.write_chunk(stream, chunk1)
            json_format.write_chunk(stream, chunk2)
            
            # Close the stream
            json_format.close_stream(stream)
            
            # Open for reading
            stream = json_format.open_stream(tmp_path, 'r')
            
            # Read first chunk
            read_chunk1 = json_format.read_chunk(stream)
            assert read_chunk1 is not None
            assert np.array_equal(read_chunk1.values, chunk1.values)
            assert read_chunk1.metadata["chunk"] == 1
            
            # Read second chunk
            read_chunk2 = json_format.read_chunk(stream)
            assert read_chunk2 is not None
            assert np.array_equal(read_chunk2.values, chunk2.values)
            assert read_chunk2.metadata["chunk"] == 2
            
            # End of stream
            assert json_format.read_chunk(stream) is None
            
            # Close the stream
            json_format.close_stream(stream)
            
        finally:
            # Clean up
            os.unlink(tmp_path)


class TestCsvFormat:
    """Tests for the CsvFormat class"""
    
    def test_basic_properties(self):
        """Test basic properties of CsvFormat"""
        csv_format = CsvFormat()
        
        assert csv_format.name == "CSV"
        assert ".csv" in csv_format.extensions
        assert FormatCapability.METADATA in csv_format.capabilities
        assert FormatCapability.STREAMING in csv_format.capabilities
        assert FormatCapability.RANDOM_ACCESS in csv_format.capabilities
        assert FormatCapability.MULTI_CHANNEL in csv_format.capabilities
    
    def test_metadata_handling(self):
        """Test handling of metadata in comments"""
        csv_format = CsvFormat()
        
        # Test metadata extraction from comments
        comments = [
            "# metadata: format=csv,version=1.0",
            "# created_at: 2023-01-01T00:00:00.000Z",
            "# sample_rate: 1000.0"
        ]
        
        metadata = csv_format._metadata_from_comments(comments)
        assert "metadata" in metadata
        assert "created_at" in metadata
        assert metadata["sample_rate"] == "1000.0"
        
        # Test comment generation from metadata
        metadata = {
            "sample_rate": 1000.0,
            "channel_count": 2
        }
        
        comments = csv_format._comments_from_metadata(metadata)
        assert any("sample_rate: 1000.0" in comment for comment in comments)
        assert any("channel_count: 2" in comment for comment in comments)
        assert any("created_at:" in comment for comment in comments)
    
    def test_read_write(self):
        """Test reading and writing CSV files"""
        # Create test data
        values = np.array([1.0, 2.0, 3.0])
        timestamps = np.array([0.0, 0.1, 0.2])
        metadata = {"sample_rate": 10.0, "test_key": "test_value"}
        data = SignalData(values=values, timestamps=timestamps, metadata=metadata)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write to file
            csv_format = CsvFormat()
            csv_format.write(tmp_path, data)
            
            # Read from file
            read_data = csv_format.read(tmp_path)
            
            # Verify data integrity
            assert np.array_equal(read_data.values, values)
            assert np.array_equal(read_data.timestamps, timestamps)
            assert "sample_rate" in read_data.metadata
            assert read_data.metadata["test_key"] == "test_value"
            
            # Test append mode
            new_values = np.array([4.0, 5.0])
            new_timestamps = np.array([0.3, 0.4])
            new_data = SignalData(values=new_values, timestamps=new_timestamps, metadata={"new_key": "new_value"})
            
            csv_format.write(tmp_path, new_data, append=True)
            
            # Read the combined data
            combined_data = csv_format.read(tmp_path)
            assert combined_data.num_samples == 5
            assert combined_data.metadata["new_key"] == "new_value"
            assert combined_data.metadata["test_key"] == "test_value"
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_multi_channel(self):
        """Test handling multi-channel data in CSV"""
        # Create multi-channel test data
        values = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        timestamps = np.array([0.0, 0.1, 0.2])
        metadata = {"sample_rate": 10.0, "channel_count": 2}
        data = SignalData(values=values, timestamps=timestamps, metadata=metadata)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write to file
            csv_format = CsvFormat()
            csv_format.write(tmp_path, data)
            
            # Read from file
            read_data = csv_format.read(tmp_path)
            
            # Verify data integrity
            assert read_data.values.shape == values.shape
            assert np.array_equal(read_data.values, values)
            assert np.array_equal(read_data.timestamps, timestamps)
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_get_metadata(self):
        """Test extracting metadata from CSV files"""
        # Create a CSV file with metadata
        csv_content = (
            "# metadata: format=csv,version=1.0\n"
            "# created_at: 2023-01-01T00:00:00.000Z\n"
            "# sample_rate: 1000.0\n"
            "timestamp,value\n"
            "0.0,1.0\n"
            "0.001,2.0\n"
        )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content.encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Extract metadata
            csv_format = CsvFormat()
            metadata = csv_format.get_metadata(tmp_path)
            
            # Verify metadata
            assert "metadata" in metadata
            assert "created_at" in metadata
            assert metadata["sample_rate"] == "1000.0"
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_read_time_range(self):
        """Test reading specific time ranges from CSV"""
        # Create test data
        csv_content = (
            "# metadata: format=csv,version=1.0\n"
            "# sample_rate: 1000.0\n"
            "timestamp,value\n"
            "0.0,1.0\n"
            "0.1,2.0\n"
            "0.2,3.0\n"
            "0.3,4.0\n"
            "0.4,5.0\n"
        )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(csv_content.encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Read a specific time range
            csv_format = CsvFormat()
            time_range = TimeRange(start=0.15, end=0.35)
            data = csv_format.read_time_range(tmp_path, time_range)
            
            # Verify data
            assert data.num_samples == 2  # Should include 0.2 and 0.3
            assert np.array_equal(data.values, np.array([3.0, 4.0]))
            assert np.array_equal(data.timestamps, np.array([0.2, 0.3]))
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    def test_streaming(self):
        """Test streaming operations with CSV format"""
        # Create test data chunks
        chunk1 = SignalData(
            values=np.array([1.0, 2.0, 3.0]),
            timestamps=np.array([0.0, 0.1, 0.2]),
            metadata={"chunk": "1"}
        )
        
        chunk2 = SignalData(
            values=np.array([4.0, 5.0]),
            timestamps=np.array([0.3, 0.4]),
            metadata={"chunk": "2"}
        )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        
        # Open stream for writing
        csv_format = CsvFormat()
        stream = None
        
        try:
            stream = csv_format.open_stream(tmp_path, 'w')
            
            # Write chunks
            csv_format.write_chunk(stream, chunk1)
            csv_format.write_chunk(stream, chunk2)
            
            # Close the stream
            csv_format.close_stream(stream)
            stream = None
            
            # Open for reading
            stream = csv_format.open_stream(tmp_path, 'r')
            
            # Read first chunk
            read_chunk1 = csv_format.read_chunk(stream)
            assert read_chunk1 is not None
            assert read_chunk1 is not None
            assert read_chunk1.num_samples == 3
            assert np.array_equal(read_chunk1.values, chunk1.values)
            
            # Read second chunk
            read_chunk2 = csv_format.read_chunk(stream)
            assert read_chunk2 is not None
            assert read_chunk2.num_samples == 2
            assert np.array_equal(read_chunk2.values, chunk2.values)
            
            # End of stream
            assert csv_format.read_chunk(stream) is None
            
            # Close the stream
            if stream:
                csv_format.close_stream(stream)
                stream = None
            
        finally:
            # Make sure stream is closed before trying to delete the file
            if stream:
                try:
                    csv_format.close_stream(stream)
                except:
                    pass
            
            try:
                # Clean up - use a small delay if needed on Windows
                if os.name == 'nt':  # Windows
                    import time
                    time.sleep(0.1)
                os.unlink(tmp_path)
            except PermissionError:
                # On Windows, sometimes the file handle isn't released immediately
                # We'll log this but not fail the test
                import logging
                logging.warning(f"Could not delete temporary file {tmp_path}")


def test_validation():
    """Test format validation"""
    # Create a valid JSON file
    json_data = {
        "metadata": {"sample_rate": 1000.0},
        "data": [1.0, 2.0, 3.0],
        "timestamps": [0.0, 0.001, 0.002]
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(json.dumps(json_data).encode('utf-8'))
        json_path = tmp.name
    
    # Create a valid CSV file
    csv_content = (
        "# metadata: format=csv,version=1.0\n"
        "# sample_rate: 1000.0\n"
        "timestamp,value\n"
        "0.0,1.0\n"
        "0.001,2.0\n"
        "0.002,3.0\n"
    )
    
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(csv_content.encode('utf-8'))
        csv_path = tmp.name
    
    # Create an invalid file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp.write(b"This is not valid JSON or CSV")
        invalid_path = tmp.name
    
    try:
        # Test JSON format validation
        json_format = JsonFormat()
        assert json_format.validate(json_path) is True
        assert json_format.validate(invalid_path) is False
        
        # Test CSV format validation
        csv_format = CsvFormat()
        assert csv_format.validate(csv_path) is True
        assert csv_format.validate(invalid_path) is False
        
    finally:
        # Clean up
        for path in [json_path, csv_path, invalid_path]:
            try:
                os.unlink(path)
            except:
                pass


def test_register_builtin_formats():
    """Test registration of built-in formats"""
    # Create a fresh registry
    test_registry = base.FormatRegistry()
    
    # Register built-in formats
    from signals_system.formats.json_format import JsonFormat
    from signals_system.formats.csv_format import CsvFormat
    
    test_registry.register(JsonFormat)
    test_registry.register(CsvFormat)
    
    # Check that formats were registered
    format_classes = [f.__class__.__name__.lower() for f in test_registry.find_with_capability(FormatCapability.METADATA)]
    assert "jsonformat" in format_classes
    assert "csvformat" in format_classes


def test_edge_cases():
    """Test edge cases and error handling"""
    # Test empty data
    empty_values = np.array([])
    empty_data = SignalData(values=empty_values)
    assert empty_data.num_samples == 0
    
    # Test format error handling
    with pytest.raises(SignalFormatError):
        invalid_json = '{"not valid": json'
        json_format = JsonFormat()
        buffer = io.BytesIO(invalid_json.encode('utf-8'))
        json_format.read(buffer)
    
    # Test TimeRange with missing timestamps
    values = np.array([1.0, 2.0, 3.0])
    data = SignalData(values=values)  # No timestamps
    
    with pytest.raises(ValueError):
        time_range = TimeRange(start=0.1, end=0.2)
        data.time_slice(time_range)


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-vs", __file__])