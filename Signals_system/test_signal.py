"""
Test suite for the Signal Processing System.

This module contains tests for validating the functionality of the
signal processing system components including providers, serialization,
averaging, and event handling.
"""

import os
import io
import json
import pytest
import numpy as np
import threading
import time
from unittest.mock import MagicMock, patch

# Import the signal processing system
# Assuming the system is in a module called 'signal_processing'
# If your module name is different, update this import
from signal_processing import (
    SignalConfig, SignalFrame, SignalEventType,
    FileSignalProvider, LiveSignalProvider,
    JsonSerializer, JsonDeserializer,
    AveragingEngine, SignalProcessor, 
    EventDispatcher, SignalProcessingSystem
)

# ----- Test Fixtures -----

@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return SignalConfig(
        mode="file",
        start_time=0.0,
        duration=10.0,
        window_size=1.0,
        window_type="rolling",
        serialization_format="json"
    )

@pytest.fixture
def sample_data():
    """Create sample signal data for testing."""
    # Simple sine wave
    t = np.linspace(0, 10, 1000)
    data = np.sin(2 * np.pi * t)
    return data

@pytest.fixture
def sample_frame(sample_data):
    """Create a sample signal frame for testing."""
    return SignalFrame(
        data=sample_data,
        timestamp_start=0.0,
        timestamp_end=10.0,
        sample_rate=100.0,
        metadata={"channel": "test"}
    )

@pytest.fixture
def mock_file():
    """Create a mock file with signal data."""
    # Create metadata
    metadata = {
        "sample_rate": 100.0,
        "total_samples": 1000,
        "sample_size_bytes": 8,
        "channel": "test"
    }
    
    # Create data (simple sine wave)
    t = np.linspace(0, 10, 1000)
    data = np.sin(2 * np.pi * t)
    
    # Serialize metadata
    metadata_json = json.dumps(metadata)
    metadata_bytes = metadata_json.encode('utf-8')
    
    # Serialize data
    data_list = data.tolist()
    frame_dict = {
        'data': data_list,
        'timestamp_start': 0.0,
        'timestamp_end': 10.0,
        'sample_rate': 100.0,
        'metadata': metadata
    }
    data_json = json.dumps(frame_dict)
    data_bytes = data_json.encode('utf-8')
    
    # Create file-like object
    mock_file = io.BytesIO()
    
    # Write header size
    header_size = len(metadata_bytes)
    mock_file.write(header_size.to_bytes(4, byteorder='little'))
    
    # Write header
    mock_file.write(metadata_bytes)
    
    # Write data
    mock_file.write(data_bytes)
    
    # Reset file position
    mock_file.seek(0)
    
    return mock_file

@pytest.fixture
def mock_connection():
    """Create a mock connection for live signal provider."""
    connection = MagicMock()
    
    # Create metadata
    metadata = {
        "sample_rate": 100.0,
        "channel": "test_live"
    }
    metadata_json = json.dumps(metadata)
    connection.receive_metadata.return_value = metadata_json.encode('utf-8')
    
    # Create sample data
    t = np.linspace(0, 1, 100)
    data = np.sin(2 * np.pi * t)
    data_list = data.tolist()
    frame_dict = {
        'data': data_list,
        'timestamp_start': 0.0,
        'timestamp_end': 1.0,
        'sample_rate': 100.0,
        'metadata': metadata
    }
    data_json = json.dumps(frame_dict)
    connection.receive_data.return_value = data_json.encode('utf-8')
    
    return connection

# ----- Test Serialization -----

def test_json_serializer(sample_frame):
    """Test that JsonSerializer correctly serializes signal frames."""
    # Arrange
    serializer = JsonSerializer()
    
    # Act
    serialized = serializer.serialize(sample_frame)
    deserializer = JsonDeserializer()
    deserialized = deserializer.deserialize(serialized)
    
    # Assert
    assert len(deserialized) == len(sample_frame.data)
    assert np.allclose(deserialized, sample_frame.data, rtol=1e-05, atol=1e-08)

# ----- Test Averaging Engine -----

def test_averaging_engine_rolling_window(sample_config, sample_data):
    """Test that AveragingEngine correctly computes rolling averages."""
    # Arrange
    sample_config.window_type = "rolling"
    sample_config.window_size = 100  # samples
    engine = AveragingEngine(sample_config)
    
    # Create multiple frames with slightly different data
    frames = []
    for i in range(5):
        # Add some noise to the data
        noisy_data = sample_data + 0.1 * np.random.randn(len(sample_data))
        frame = SignalFrame(
            data=noisy_data,
            timestamp_start=i * 1.0,
            timestamp_end=(i + 1) * 1.0,
            sample_rate=100.0,
            metadata={}
        )
        frames.append(frame)
    
    # Act & Assert
    for i, frame in enumerate(frames):
        avg = engine.add_frame(frame)
        assert avg is not None
        
        # For the first frame, the average should be equal to the data
        if i == 0:
            assert np.allclose(avg, frame.data)
        else:
            # For subsequent frames, the average should be different from the frame data
            assert not np.allclose(avg, frame.data)

def test_averaging_engine_exponential(sample_config, sample_data):
    """Test that AveragingEngine correctly computes exponential averages."""
    # Arrange
    sample_config.window_type = "exponential"
    engine = AveragingEngine(sample_config)
    
    # Create two frames with different data
    frame1 = SignalFrame(
        data=sample_data,
        timestamp_start=0.0,
        timestamp_end=1.0,
        sample_rate=100.0,
        metadata={}
    )
    
    # Second frame has an offset
    frame2 = SignalFrame(
        data=sample_data + 1.0,
        timestamp_start=1.0,
        timestamp_end=2.0,
        sample_rate=100.0,
        metadata={}
    )
    
    # Act
    avg1 = engine.add_frame(frame1)
    avg2 = engine.add_frame(frame2)
    
    # Assert
    assert avg1 is not None
    assert avg2 is not None
    
    # First average should match the first frame
    assert np.allclose(avg1, frame1.data)
    
    # Second average should be between the first and second frame's data
    assert np.all(avg2 > frame1.data)  # Greater than first frame
    assert np.all(avg2 < frame2.data)  # Less than second frame

# ----- Test Signal Processor -----

def test_signal_processor_change_detection(sample_config):
    """Test that SignalProcessor correctly detects changes."""
    # Arrange
    sample_config.change_threshold = 0.5
    processor = SignalProcessor(sample_config)
    
    # Create a mock callback
    callback = MagicMock()
    processor.register_change_callback(callback)
    
    # Create two datasets with a large difference
    data1 = np.zeros(100)
    data2 = np.ones(100)  # Difference = 1.0, which is > threshold
    
    # Act
    processor.process(data1)  # First process, no callback expected
    processor.process(data2)  # Second process, callback expected
    
    # Assert
    callback.assert_called_once()
    args, _ = callback.call_args
    assert args[0] is not None  # Data
    assert args[1] > sample_config.change_threshold  # Change magnitude

# ----- Test Event Dispatcher -----

def test_event_dispatcher():
    """Test that EventDispatcher correctly dispatches events."""
    # Arrange
    dispatcher = EventDispatcher()
    callback1 = MagicMock()
    callback2 = MagicMock()
    
    # Register callbacks
    dispatcher.register_listener(SignalEventType.NEW_FRAME, callback1)
    dispatcher.register_listener(SignalEventType.AVERAGE_UPDATED, callback2)
    
    # Act
    test_data = np.array([1, 2, 3])
    dispatcher.dispatch_event(SignalEventType.NEW_FRAME, test_data)
    
    # Assert
    callback1.assert_called_once_with(test_data)
    callback2.assert_not_called()

# ----- Test File Signal Provider -----

def test_file_signal_provider(sample_config, mock_file):
    """Test that FileSignalProvider correctly reads signal data from a file."""
    # Arrange
    with patch('builtins.open', return_value=mock_file):
        provider = FileSignalProvider(sample_config, "test_file.dat")
        
        # Act
        success = provider.open()
        frame = provider.get_frame()
        metadata = provider.get_metadata()
        provider.close()
        
        # Assert
        assert success
        assert frame is not None
        assert frame.data is not None
        assert len(frame.data) > 0
        assert metadata is not None
        assert 'sample_rate' in metadata

# ----- Test Live Signal Provider -----

def test_live_signal_provider(sample_config, mock_connection):
    """Test that LiveSignalProvider correctly receives signal data."""
    # Arrange
    connection_factory = lambda **kwargs: mock_connection
    provider = LiveSignalProvider(sample_config, connection_factory)
    
    # Act
    try:
        success = provider.open()
        
        # Wait for first frame
        time.sleep(0.1)
        
        frame = provider.get_frame()
        metadata = provider.get_metadata()
        
    finally:
        provider.close()
    
    # Assert
    assert success
    assert frame is not None
    assert frame.data is not None
    assert len(frame.data) > 0
    assert metadata is not None
    assert 'channel' in metadata
    assert metadata['channel'] == 'test_live'

# ----- Test Signal Processing System -----

def test_signal_processing_system(sample_config, mock_file):
    """Test the complete signal processing system with a file provider."""
    # Arrange
    with patch('builtins.open', return_value=mock_file):
        # Create system
        system = SignalProcessingSystem(sample_config)
        
        # Mock callbacks
        new_frame_callback = MagicMock()
        average_callback = MagicMock()
        change_callback = MagicMock()
        
        # Register callbacks
        system.register_event_listener(SignalEventType.NEW_FRAME, new_frame_callback)
        system.register_event_listener(SignalEventType.AVERAGE_UPDATED, average_callback)
        system.register_event_listener(SignalEventType.SIGNAL_CHANGED, change_callback)
        
        # Initialize with file provider
        success = system.initialize(
            lambda: FileSignalProvider(sample_config, "test_file.dat")
        )
        
        # Act
        try:
            system.start()
            
            # Wait for processing
            time.sleep(0.5)
            
        finally:
            system.stop()
        
        # Assert
        assert success
        assert new_frame_callback.called
        assert average_callback.called


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-vsx", __file__])