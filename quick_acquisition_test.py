# -*- coding: utf-8 -*-
"""
Oscilloscope Continuous Acquisition Test for PySignalDecipher.

This tool tests the limits of continuous signal acquisition from a Rigol oscilloscope,
evaluating maximum sampling rates, duration capabilities, and bottlenecks.
It benchmarks different acquisition methods and storage formats for optimization.
"""

import sys
import time
import os
import numpy as np
import pandas as pd
import pyvisa
import matplotlib
matplotlib.use('QtAgg')  # Set the backend to be compatible with PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox, QTextEdit, QCheckBox,
    QStatusBar, QMessageBox, QFileDialog, QSlider, QSpinBox,
    QDoubleSpinBox, QProgressBar, QTabWidget, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Slot, Signal, QThread, QTimer, QElapsedTimer
import psutil
import h5py
import multiprocessing as mp


# MARK: - Constants and Configuration

# Sample rate and memory depth options specific to Rigol DS1000Z Series
SAMPLE_RATES = {
    "Low (50 MSa/s)": 50e6,
    "Medium (100 MSa/s)": 100e6,
    "High (500 MSa/s)": 500e6,
    "Maximum (1 GSa/s)": 1e9,
    "Auto": 0  # Let the oscilloscope decide
}

MEMORY_DEPTHS = {
    "Normal (12K)": 12000,
    "Medium (120K)": 120000,
    "Deep (1.2M)": 1200000,
    "Maximum (12M)": 12000000,
    "Auto": 0  # Let oscilloscope decide
}

FILE_FORMATS = {
    "CSV (.csv)": "csv",
    "NumPy Binary (.npy)": "npy",
    "HDF5 (.h5)": "h5"
}


# MARK: - Helper Classes

class PerformanceMonitor:
    """Monitor and track system performance metrics during acquisition."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.reset()
    
    def reset(self):
        """Reset all performance metrics."""
        self.start_time = None
        self.end_time = None
        self.cpu_usage = []
        self.memory_usage = []
        self.data_transfer_rate = []
        self.data_points_captured = 0
        self.sample_rate_achieved = 0
        self.bottleneck_identified = "Unknown"
    
    def start(self):
        """Start performance monitoring."""
        self.reset()
        self.start_time = time.time()
    
    def update(self, data_size):
        """
        Update performance metrics with current system state.
        
        Args:
            data_size (int): Size of data captured in this update in bytes
        """
        # Record system metrics
        self.cpu_usage.append(psutil.cpu_percent(interval=None))
        self.memory_usage.append(psutil.virtual_memory().percent)
        
        # Calculate data transfer rate if we have multiple data points
        if self.data_transfer_rate:
            elapsed = time.time() - (self.start_time + sum(self.data_transfer_rate))
            if elapsed > 0:
                transfer_rate = data_size / elapsed
                self.data_transfer_rate.append(transfer_rate)
        else:
            # First data point, can't calculate rate yet
            self.data_transfer_rate.append(0)
        
        # Update total data captured
        self.data_points_captured += data_size / 4  # Assuming 4 bytes per data point
    
    def stop(self):
        """Stop performance monitoring and calculate final metrics."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if duration > 0:
            self.sample_rate_achieved = self.data_points_captured / duration
        
        # Identify the bottleneck based on collected metrics
        avg_cpu = np.mean(self.cpu_usage) if self.cpu_usage else 0
        avg_memory = np.mean(self.memory_usage) if self.memory_usage else 0
        avg_transfer = np.mean(self.data_transfer_rate[1:]) if len(self.data_transfer_rate) > 1 else 0
        
        if avg_cpu > 80:
            self.bottleneck_identified = "CPU processing power"
        elif avg_memory > 80:
            self.bottleneck_identified = "System memory (RAM)"
        elif avg_transfer < 5e6:  # Less than 5MB/s
            self.bottleneck_identified = "USB/VISA data transfer"
        else:
            self.bottleneck_identified = "Oscilloscope acquisition capabilities"
    
    def get_summary(self):
        """
        Get a summary of the performance monitoring results.
        
        Returns:
            str: Summary text of performance metrics
        """
        if self.start_time is None or self.end_time is None:
            return "No performance data available."
        
        duration = self.end_time - self.start_time
        avg_cpu = np.mean(self.cpu_usage) if self.cpu_usage else 0
        avg_memory = np.mean(self.memory_usage) if self.memory_usage else 0
        avg_transfer = np.mean(self.data_transfer_rate[1:]) if len(self.data_transfer_rate) > 1 else 0
        
        # Create a formatted performance summary
        summary = "PERFORMANCE ANALYSIS RESULTS\n"
        summary += "=" * 50 + "\n\n"
        
        # Format metrics in aligned columns
        metrics = [
            ("Test Duration", f"{duration:.2f} seconds"),
            ("Total Data Points", f"{self.data_points_captured:,.0f}"),
            ("Achieved Sample Rate", f"{self.sample_rate_achieved/1e6:.2f} MSa/s"),
            ("Average CPU Usage", f"{avg_cpu:.1f}%"),
            ("Average Memory Usage", f"{avg_memory:.1f}%"),
            ("Data Transfer Rate", f"{avg_transfer/1e6:.2f} MB/s"),
            ("Identified Bottleneck", f"{self.bottleneck_identified}")
        ]
        
        # Find the max width of the first column for alignment
        max_key_width = max(len(key) for key, _ in metrics)
        
        # Format each line with proper alignment
        for key, value in metrics:
            summary += f"{key:<{max_key_width + 4}} : {value}\n"
            
        return summary


class DataStorageManager:
    """Manage data storage for oscilloscope waveform data."""
    
    def __init__(self, format_type="csv"):
        """
        Initialize the data storage manager.
        
        Args:
            format_type (str): Storage format type (csv, npy, h5)
        """
        self.format_type = format_type
        self.file_path = None
        self.benchmark_results = {}
        
        # File handles for streaming
        self._csv_file = None
        self._h5_file = None
        self._dataset = None
        self._chunk_size = 1000000  # Default chunk size for HDF5
        
        # Performance tracking
        self._write_times = []
    
    def prepare_file(self, base_path, channels, expected_points=0):
        """
        Prepare file for data storage.
        
        Args:
            base_path (str): Base file path (without extension)
            channels (list): List of channel numbers to record
            expected_points (int): Expected number of data points (for pre-allocation)
            
        Returns:
            str: Full file path with extension
        """
        # Add appropriate extension
        if self.format_type == "csv":
            self.file_path = f"{base_path}.csv"
            # For CSV, create the file and write header
            self._csv_file = open(self.file_path, 'w')
            header = "Time"
            for ch in channels:
                header += f",Channel{ch}"
            self._csv_file.write(header + "\n")
            
        elif self.format_type == "npy":
            self.file_path = f"{base_path}.npy"
            # For NPY, we'll create the file when we have data
            
        elif self.format_type == "h5":
            self.file_path = f"{base_path}.h5"
            # Create HDF5 file with groups for each channel
            self._h5_file = h5py.File(self.file_path, 'w')
            
            # Create datasets with chunking for efficient appending
            chunk_size = min(expected_points, self._chunk_size) if expected_points > 0 else self._chunk_size
            
            # Create a time dataset
            self._h5_file.create_dataset(
                "time", 
                shape=(0,), 
                maxshape=(None,), 
                chunks=(chunk_size,),
                dtype='float32'
            )
            
            # Create datasets for each channel
            for ch in channels:
                self._h5_file.create_dataset(
                    f"channel{ch}", 
                    shape=(0,), 
                    maxshape=(None,), 
                    chunks=(chunk_size,),
                    dtype='float32'
                )
        
        return self.file_path
    
    def write_data(self, time_values, voltage_values_by_channel):
        """
        Write data to the storage file.
        
        Args:
            time_values (np.ndarray): Array of time values
            voltage_values_by_channel (dict): Dictionary mapping channel numbers to voltage arrays
            
        Returns:
            float: Write operation time in seconds
        """
        start_time = time.time()
        
        if self.format_type == "csv":
            # Create a structured array for CSV export
            data_to_write = np.column_stack([time_values] + 
                                         [voltage_values_by_channel[ch] for ch in sorted(voltage_values_by_channel.keys())])
            
            # Write to CSV line by line
            for row in data_to_write:
                row_str = ",".join([f"{val:.6e}" for val in row])
                self._csv_file.write(row_str + "\n")
            
            # Ensure data is flushed to disk
            self._csv_file.flush()
            
        elif self.format_type == "npy":
            # For NPY, we either create or append to the file
            if os.path.exists(self.file_path):
                # Load existing data
                existing_data = np.load(self.file_path, allow_pickle=True).item()
                
                # Append new data
                for ch in voltage_values_by_channel:
                    if ch in existing_data:
                        existing_data[ch] = np.append(existing_data[ch], voltage_values_by_channel[ch])
                    else:
                        existing_data[ch] = voltage_values_by_channel[ch]
                
                if 'time' in existing_data:
                    existing_data['time'] = np.append(existing_data['time'], time_values)
                else:
                    existing_data['time'] = time_values
                
                # Save back to file
                np.save(self.file_path, existing_data)
            else:
                # Create new dictionary with channel data
                data_dict = {'time': time_values}
                for ch in voltage_values_by_channel:
                    data_dict[f'channel{ch}'] = voltage_values_by_channel[ch]
                
                # Save to file
                np.save(self.file_path, data_dict)
            
        elif self.format_type == "h5":
            # Get current sizes
            time_dataset = self._h5_file['time']
            current_size = len(time_dataset)
            new_size = current_size + len(time_values)
            
            # Resize time dataset and add data
            time_dataset.resize((new_size,))
            time_dataset[current_size:new_size] = time_values
            
            # Do the same for each channel dataset
            for ch in voltage_values_by_channel:
                channel_dataset = self._h5_file[f'channel{ch}']
                channel_dataset.resize((new_size,))
                channel_dataset[current_size:new_size] = voltage_values_by_channel[ch]
            
            # Flush to ensure data is written
            self._h5_file.flush()
        
        # Calculate and record write time
        write_time = time.time() - start_time
        self._write_times.append(write_time)
        
        return write_time
    
    def close(self):
        """Close any open file handles."""
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
        
        if self._h5_file:
            self._h5_file.close()
            self._h5_file = None
    
    def run_format_benchmark(self, time_values, voltage_values_by_channel):
        """
        Benchmark different file formats for the given data.
        
        Args:
            time_values (np.ndarray): Array of time values
            voltage_values_by_channel (dict): Dictionary mapping channel numbers to voltage arrays
            
        Returns:
            dict: Benchmark results with format types and metrics
        """
        results = {}
        
        # Get data size in bytes
        data_size = time_values.nbytes
        for ch in voltage_values_by_channel:
            data_size += voltage_values_by_channel[ch].nbytes
        
        for format_type in ['csv', 'npy', 'h5']:
            # Create a temporary file for the benchmark
            temp_path = os.path.join(os.path.dirname(self.file_path) if self.file_path else '.', 
                                    f'benchmark_temp_{format_type}')
            
            # Save original format type
            original_format = self.format_type
            self.format_type = format_type
            
            # Prepare file
            self.prepare_file(temp_path, voltage_values_by_channel.keys())
            
            # Write data and time it
            start_time = time.time()
            self.write_data(time_values, voltage_values_by_channel)
            write_time = time.time() - start_time
            
            # Close file
            self.close()
            
            # Get file size
            if format_type == 'csv':
                file_size = os.path.getsize(f"{temp_path}.csv")
            elif format_type == 'npy':
                file_size = os.path.getsize(f"{temp_path}.npy")
            else:  # h5
                file_size = os.path.getsize(f"{temp_path}.h5")
            
            # Calculate metrics
            compression_ratio = data_size / file_size if file_size > 0 else 0
            write_speed = data_size / write_time if write_time > 0 else 0
            
            # Store results
            results[format_type] = {
                'write_time': write_time,
                'file_size': file_size,
                'compression_ratio': compression_ratio,
                'write_speed': write_speed
            }
            
            # Delete the temporary file
            try:
                if format_type == 'csv':
                    os.remove(f"{temp_path}.csv")
                elif format_type == 'npy':
                    os.remove(f"{temp_path}.npy")
                else:  # h5
                    os.remove(f"{temp_path}.h5")
            except:
                pass
            
            # Restore original format
            self.format_type = original_format
        
        self.benchmark_results = results
        return results
    
    def get_benchmark_summary(self):
        """
        Get a summary of the format benchmark results.
        
        Returns:
            str: Formatted summary text
        """
        if not self.benchmark_results:
            return "No benchmark data available."
        
        summary = "FILE FORMAT BENCHMARK RESULTS\n"
        summary += "=" * 50 + "\n\n"
        
        # Find the largest file size for relative comparison
        max_size = max(res['file_size'] for res in self.benchmark_results.values())
        
        # Calculate column widths for proper alignment
        col_widths = {
            'format': max(len(fmt.upper()) for fmt in self.benchmark_results.keys()) + 2,
            'size': 12,
            'speed': 14,
            'relative': 14
        }
        
        # Create header
        header = (
            f"{'Format':<{col_widths['format']}} "
            f"{'Size (MB)':<{col_widths['size']}} "
            f"{'Speed (MB/s)':<{col_widths['speed']}} "
            f"{'Relative Size':<{col_widths['relative']}}"
        )
        summary += header + "\n"
        summary += "=" * len(header) + "\n"
        
        # Add rows
        for fmt, results in self.benchmark_results.items():
            size_mb = results['file_size'] / (1024 * 1024)
            speed_mb = results['write_speed'] / (1024 * 1024)
            rel_size = results['file_size'] / max_size if max_size > 0 else 0
            
            row = (
                f"{fmt.upper():<{col_widths['format']}} "
                f"{size_mb:.2f}{'':>{col_widths['size'] - 7}} "
                f"{speed_mb:.2f}{'':>{col_widths['speed'] - 7}} "
                f"{rel_size:.2f}x{'':>{col_widths['relative'] - 5}}"
            )
            summary += row + "\n"
        
        # Add recommendations section
        summary += "\nRECOMMENDATIONS\n"
        summary += "-" * 30 + "\n"
        
        fastest = max(self.benchmark_results.items(), key=lambda x: x[1]['write_speed'])[0]
        smallest = min(self.benchmark_results.items(), key=lambda x: x[1]['file_size'])[0]
        
        if fastest == smallest:
            summary += f"• Use {fastest.upper()} format for best overall performance.\n"
        else:
            summary += f"• For maximum speed: {fastest.upper()}\n"
            summary += f"• For smallest file size: {smallest.upper()}\n"
            
            # Balanced recommendation
            balance_score = {}
            for fmt, results in self.benchmark_results.items():
                # Normalize metrics between 0 and 1
                speed_score = results['write_speed'] / max(res['write_speed'] for res in self.benchmark_results.values())
                size_score = min(res['file_size'] for res in self.benchmark_results.values()) / results['file_size']
                # Combined score with more weight on speed
                balance_score[fmt] = 0.7 * speed_score + 0.3 * size_score
            
            best_balance = max(balance_score.items(), key=lambda x: x[1])[0]
            summary += f"• For best balance of speed and size: {best_balance.upper()}\n"
        
        return summary


# MARK: - Thread Classes

class OscilloscopeConnectionThread(QThread):
    """Thread for connecting to the oscilloscope without blocking the UI."""
    
    connection_successful = Signal(object, str)  # Signal emits scope object and idn
    connection_failed = Signal(str, list)        # Signal emits error message and available devices
    
    def __init__(self, address):
        """
        Initialize oscilloscope connection thread.
        
        Args:
            address (str): VISA address for the oscilloscope
        """
        super().__init__()
        self._address = address
        
    def run(self):
        """Connect to the oscilloscope using PyVISA."""
        rm = pyvisa.ResourceManager()
        try:
            # Open a connection to the oscilloscope with appropriate settings
            scope = rm.open_resource(self._address)
            
            # Configure for stable communication
            scope.timeout = 30000  # 30 seconds timeout for long operations
            scope.read_termination = '\n'
            scope.write_termination = '\n'
            
            # Clear the device to start with a clean state
            scope.write('*CLS')
            
            # Query the oscilloscope for identification
            idn = scope.query('*IDN?')
            self.connection_successful.emit(scope, idn)
        except pyvisa.VisaIOError as e:
            # List all connected devices if there's an error
            available_devices = rm.list_resources()
            self.connection_failed.emit(str(e), available_devices)


class ContinuousAcquisitionThread(QThread):
    """Thread for handling continuous data acquisition from the oscilloscope."""
    
    update_status = Signal(str)
    update_progress = Signal(int)
    acquisition_data = Signal(object)  # Signal emits the acquired data batch
    acquisition_complete = Signal(dict)  # Signal emits the complete results
    acquisition_error = Signal(str)
    
    def __init__(self, scope, channels, duration=3.0, sample_rate=0, memory_depth=0, 
                 storage_manager=None, output_path=None):
        """
        Initialize continuous acquisition thread.
        
        Args:
            scope: PyVISA resource for the oscilloscope
            channels (list): List of channels to acquire data from
            duration (float): Duration to capture in seconds
            sample_rate (float): Target sample rate in Hz (0 for auto)
            memory_depth (int): Memory depth to use (0 for auto)
            storage_manager (DataStorageManager): Manager for storing acquired data
            output_path (str): Base path for output files
        """
        super().__init__()
        self._scope = scope
        self._channels = channels
        self._duration = duration
        self._sample_rate = sample_rate
        self._memory_depth = memory_depth
        self._storage_manager = storage_manager
        self._output_path = output_path
        
        # Initialize data structures
        self._time_values = {}  # Dict to store time arrays for each acquisition
        self._voltage_values = {}  # Dict of dicts to store voltage arrays for each channel
        self._acquisition_count = 0
        
        # Performance monitoring
        self._performance = PerformanceMonitor()
        
        # Streaming mode configuration
        self._streaming_enabled = True
        self._batch_size = 1000000  # Points per batch in streaming mode
        
        # Control flags
        self._stop_requested = False
    
    def run(self):
        """Execute the continuous acquisition process."""
        try:
            self.update_status.emit("Configuring oscilloscope for acquisition...")
            
            # Configure oscilloscope
            self._configure_oscilloscope()
            
            # Start performance monitoring
            self._performance.start()
            
            # Determine acquisition method based on duration and memory constraints
            if self._streaming_enabled:
                # Use streaming acquisition for longer durations
                success = self._streaming_acquisition()
            else:
                # Use single acquisition for short captures
                success = self._single_acquisition()
            
            # Stop performance monitoring
            self._performance.stop()
            
            if not success:
                self.update_status.emit("Acquisition was canceled or encountered an error.")
                return
            
            # Run benchmark on file formats if requested
            self._run_benchmark()
            
            # Prepare results
            results = {
                'duration': self._duration,
                'sample_rate': self._sample_rate,
                'memory_depth': self._memory_depth,
                'channels': self._channels,
                'acquisition_count': self._acquisition_count,
                'total_points': self._performance.data_points_captured,
                'achieved_sample_rate': self._performance.sample_rate_achieved,
                'performance_summary': self._performance.get_summary()
            }
            
            self.acquisition_complete.emit(results)
            
        except Exception as e:
            self.acquisition_error.emit(f"Error during acquisition: {str(e)}")
    
    def _configure_oscilloscope(self):
        """Configure oscilloscope settings for acquisition."""
        self.update_status.emit("Setting up oscilloscope channels...")
        
        # Setup channels
        for ch in self._channels:
            # Ensure channel is enabled
            self._scope.write(f":CHAN{ch}:DISP ON")
        
        # Acquisition settings
        self._scope.write(":ACQ:TYPE NORM")  # Normal acquisition mode
        
        # Set memory depth if specified
        if self._memory_depth > 0:
            self._scope.write(f":ACQ:MDEP {self._memory_depth}")
        
        # Set sample rate if specified
        if self._sample_rate > 0:
            current_rate = float(self._scope.query(":ACQ:SRAT?"))
            if abs(current_rate - self._sample_rate) / self._sample_rate > 0.05:  # >5% difference
                # Adjusting timebase to achieve desired sample rate
                time_scale = self._scope.query(":TIM:SCAL?")
                self.update_status.emit(f"Adjusting timebase to achieve {self._sample_rate/1e6:.1f} MSa/s...")
                
                # This is an approximate calculation - actual behavior depends on the oscilloscope model
                # For more precise control, we'd need to use a lookup table specific to the model
                current_time_scale = float(time_scale)
                new_time_scale = current_time_scale * (current_rate / self._sample_rate)
                
                # Set new timebase
                self._scope.write(f":TIM:SCAL {new_time_scale}")
        
        # Prepare oscilloscope for acquisition
        self._scope.write(":STOP")  # Stop any ongoing acquisition
        self._scope.write(":TRIG:MODE EDGE")  # Basic edge trigger
        self._scope.write(":TRIG:EDGE:SOUR CHAN1")  # Trigger on channel 1
        
        # Run acquisition to ensure fresh data
        self._scope.write(":RUN")
        time.sleep(0.5)  # Allow time for the oscilloscope to start
    
    def _single_acquisition(self):
        """
        Perform a single acquisition covering the entire duration if possible.
        
        Returns:
            bool: Success status
        """
        self.update_status.emit("Preparing for single acquisition...")
        
        # Calculate memory requirements
        sample_rate = float(self._scope.query(":ACQ:SRAT?"))
        points_needed = sample_rate * self._duration
        
        # Check if oscilloscope memory depth is sufficient
        max_memory = float(self._scope.query(":ACQ:MDEP?"))
        if points_needed > max_memory:
            self.update_status.emit(f"Warning: Required points ({points_needed:.0f}) exceeds " +
                                  f"maximum memory depth ({max_memory:.0f})")
            self.update_status.emit("Reducing capture duration to fit available memory.")
            actual_duration = max_memory / sample_rate
            self._duration = actual_duration
        
        # Set timebase to cover the duration (10 horizontal divisions typically)
        time_scale = self._duration / 10.0
        self._scope.write(f":TIM:SCAL {time_scale}")
        
        # Stop any current acquisition
        self._scope.write(":STOP")
        
        # Wait for trigger
        self.update_status.emit("Waiting for trigger event...")
        self._scope.write(":SING")  # Single trigger mode
        
        # Poll until acquisition is complete
        timeout = 30  # seconds
        start_time = time.time()
        while True:
            # Check if we've been asked to stop
            if self._stop_requested:
                return False
            
            # Check if acquisition is complete
            status = self._scope.query(":TRIG:STAT?").strip()
            if status == "STOP":
                break
            
            # Check for timeout
            if time.time() - start_time > timeout:
                self.update_status.emit("Trigger timeout. Forcing acquisition...")
                self._scope.write(":FORC")  # Force trigger
                break
            
            # Sleep to avoid overwhelming the oscilloscope
            time.sleep(0.1)
            
            # Update progress (approximation)
            elapsed = time.time() - start_time
            progress = min(int((elapsed / timeout) * 50), 50)  # Max 50% for trigger wait
            self.update_progress.emit(progress)
        
        # Acquisition complete, retrieve data for each channel
        self.update_status.emit("Retrieving waveform data...")
        
        # For single acquisition, we retrieve full waveforms for all channels
        all_channel_data = {}
        
        for ch_idx, channel in enumerate(self._channels):
            # Update progress
            progress = 50 + int((ch_idx / len(self._channels)) * 50)
            self.update_progress.emit(progress)
            
            # Retrieve waveform
            times, voltages = self._get_waveform_data(channel)
            
            # Store data
            if times is not None and voltages is not None:
                all_channel_data[channel] = voltages
            
                # First channel sets the time values for all channels
                if not self._time_values:
                    self._time_values = times
            
            # Check for stop request
            if self._stop_requested:
                return False
        
        # Save data if storage manager is provided
        if self._storage_manager and self._output_path:
            self.update_status.emit("Saving data to file...")
            
            # Prepare file
            self._storage_manager.prepare_file(self._output_path, self._channels)
            
            # Write data
            self._storage_manager.write_data(self._time_values, all_channel_data)
            
            # Close file
            self._storage_manager.close()
        
        # Update performance metrics
        self._acquisition_count = 1
        total_points = len(self._time_values) * len(self._channels)
        self._performance.data_points_captured = total_points
        
        self.update_progress.emit(100)
        self.update_status.emit("Single acquisition complete.")
        return True
    
    def _streaming_acquisition(self):
        """
        Perform continuous streaming acquisition for the specified duration.
        
        Returns:
            bool: Success status
        """
        self.update_status.emit("Starting streaming acquisition...")
        
        # Configure oscilloscope for continuous acquisition
        self._scope.write(":RUN")
        
        # Initialize data storage
        if self._storage_manager and self._output_path:
            # Calculate expected points for pre-allocation
            sample_rate = float(self._scope.query(":ACQ:SRAT?"))
            expected_points = int(sample_rate * self._duration)
            
            # Prepare file
            self._storage_manager.prepare_file(self._output_path, self._channels, expected_points)
        
        # Start timing
        start_time = time.time()
        elapsed = 0
        
        # Storage for accumulated data
        accumulated_time = np.array([])
        accumulated_voltages = {ch: np.array([]) for ch in self._channels}
        
        # Main acquisition loop
        while elapsed < self._duration and not self._stop_requested:
            # Update progress
            progress = int((elapsed / self._duration) * 100)
            self.update_progress.emit(progress)
            
            # Capture data from each channel
            channel_data = {}
            current_times = None
            
            for channel in self._channels:
                # Get batch of data
                times, voltages = self._get_waveform_data(channel)
                
                if times is not None and voltages is not None:
                    # Store current batch
                    channel_data[channel] = voltages
                    
                    # First channel sets the time values for this batch
                    if current_times is None:
                        current_times = times
                
                # Check if we need to stop
                if self._stop_requested:
                    break
            
            # If we got data, process and save it
            if current_times is not None and len(current_times) > 0:
                # Track performance for this batch
                data_size = current_times.nbytes
                for ch in channel_data:
                    data_size += channel_data[ch].nbytes
                self._performance.update(data_size)
                
                # Save data if storage manager is provided
                if self._storage_manager and self._output_path:
                    self._storage_manager.write_data(current_times, channel_data)
                
                # Accumulate data into memory
                if len(accumulated_time) == 0:
                    accumulated_time = current_times
                else:
                    accumulated_time = np.append(accumulated_time, current_times)
                
                for ch in channel_data:
                    if len(accumulated_voltages[ch]) == 0:
                        accumulated_voltages[ch] = channel_data[ch]
                    else:
                        accumulated_voltages[ch] = np.append(accumulated_voltages[ch], channel_data[ch])
                
                # Emit data for UI update
                self.acquisition_data.emit({
                    'time': current_times,
                    'voltages': channel_data,
                    'elapsed': elapsed,
                    'duration': self._duration
                })
                
                # Increment acquisition count
                self._acquisition_count += 1
            
            # Update elapsed time
            elapsed = time.time() - start_time
            
            # Small sleep to prevent overwhelming the oscilloscope
            time.sleep(0.01)
        
        # Close file if open
        if self._storage_manager:
            self._storage_manager.close()
        
        # Set final progress
        self.update_progress.emit(100)
        
        # Store final data
        self._time_values = accumulated_time
        self._voltage_values = accumulated_voltages
        
        self.update_status.emit(f"Streaming acquisition complete: {self._acquisition_count} batches.")
        return not self._stop_requested
    
    def _get_waveform_data(self, channel):
        """
        Get waveform data from the oscilloscope for a specific channel.
        
        Args:
            channel (int): Channel number to acquire from
            
        Returns:
            tuple: (time_values, voltage_values) arrays or (None, None) on error
        """
        try:
            # Configure waveform acquisition for this channel
            self._scope.write(f":WAV:SOUR CHAN{channel}")
            self._scope.write(":WAV:MODE NORM")  # Screen data for faster acquisition
            self._scope.write(":WAV:FORM BYTE")  # 8-bit resolution for speed
            
            # Get the waveform preamble
            preamble_str = self._scope.query(":WAV:PRE?")
            preamble = preamble_str.strip().split(',')
            
            # Extract scaling factors
            x_increment = float(preamble[4])  # Time between points
            x_origin = float(preamble[5])     # First point time
            x_reference = float(preamble[6])  # Reference position
            y_increment = float(preamble[7])  # Voltage per level
            y_origin = float(preamble[8])     # Ground level offset
            y_reference = float(preamble[9])  # Reference level
            
            # Get the raw waveform data
            self._scope.write(":WAV:DATA?")
            raw_data = self._scope.read_raw()
            
            # Remove header bytes and extract data
            if raw_data[0:1] != b'#':
                return None, None
                
            n = int(raw_data[1:2])  # Number of digits in the length
            data_size = int(raw_data[2:2+n])  # The actual data size
            header_len = 2 + n  # '#' + N + N digits
            
            data = raw_data[header_len:header_len+data_size]
            
            # Convert raw data to numpy array
            data_array = np.frombuffer(data, dtype=np.uint8)
            
            # Apply scaling to get voltage values
            voltages = (data_array - y_origin - y_reference) * y_increment
            
            # Generate time axis
            times = np.arange(0, len(voltages)) * x_increment + x_origin
            
            return times, voltages
            
        except Exception as e:
            self.update_status.emit(f"Error getting waveform data from channel {channel}: {str(e)}")
            return None, None
    
    def _run_benchmark(self):
        """Run benchmarks on different file formats if enabled."""
        # Only run benchmark if we have data and a storage manager
        if (not self._time_values.size if isinstance(self._time_values, np.ndarray) 
            else not self._time_values) or not self._storage_manager:
            return
        
        try:
            self.update_status.emit("Running file format benchmark...")
            
            # Extract some representative data for the benchmark
            # Limit to 1M points to keep benchmark fast
            max_points = 1000000
            if len(self._time_values) > max_points:
                time_sample = self._time_values[:max_points]
                voltage_sample = {ch: self._voltage_values[ch][:max_points] for ch in self._voltage_values}
            else:
                time_sample = self._time_values
                voltage_sample = self._voltage_values
            
            # Run benchmark
            self._storage_manager.run_format_benchmark(time_sample, voltage_sample)
            
        except Exception as e:
            self.update_status.emit(f"Error during benchmark: {str(e)}")
    
    def stop(self):
        """Request acquisition to stop."""
        self._stop_requested = True
        self.update_status.emit("Stop requested. Finishing current operation...")


# MARK: - UI Components

class WaveformPlotter(FigureCanvas):
    """Matplotlib canvas for plotting waveform data."""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Initialize the waveform plotter.
        
        Args:
            parent: Parent widget
            width (float): Figure width in inches
            height (float): Figure height in inches
            dpi (int): Resolution in dots per inch
        """
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Channel colors (oscilloscope standard colors)
        self._colors = ['yellow', 'blue', 'red', 'green']
        
        # Store channel data and axes objects
        self._channel_data = {}
        self._axes = {}
        
        # Add main subplot
        self._main_ax = self.fig.add_subplot(111)
        self._main_ax.set_xlabel('Time (s)')
        self._main_ax.set_ylabel('Voltage (V)')
        self._main_ax.grid(True)
        
        # Initial setup with empty subplot area
        self.fig.tight_layout()
    
    def update_live_plot(self, data):
        """
        Update the plot with new streaming data.
        
        Args:
            data (dict): Dictionary with time, voltages, elapsed and duration
        """
        times = data['time']
        voltages_by_channel = data['voltages']
        
        # Clear current axis
        self._main_ax.clear()
        
        # Plot each channel
        for i, (channel, voltages) in enumerate(voltages_by_channel.items()):
            color_idx = (channel - 1) % len(self._colors)
            self._main_ax.plot(times, voltages, color=self._colors[color_idx], label=f'CH{channel}')
        
        # Add labels and grid
        self._main_ax.set_xlabel('Time (s)')
        self._main_ax.set_ylabel('Voltage (V)')
        self._main_ax.set_title(f'Live Acquisition - {data["elapsed"]:.1f}s / {data["duration"]:.1f}s')
        self._main_ax.grid(True)
        self._main_ax.legend()
        
        # Update figure layout
        self.fig.tight_layout()
        self.draw()
    
    def update_plot(self, channel, times, voltages):
        """
        Update the plot with new waveform data.
        
        Args:
            channel (int): Channel number (1-based)
            times (np.ndarray): Array of time values
            voltages (np.ndarray): Array of voltage values
        """
        # Store data
        self._channel_data[channel] = (times, voltages)
        
        # Adjust the subplot layout based on the number of channels
        self._adjust_layout()
        
        # Get or create axis for this channel
        if channel not in self._axes:
            # Create new subplot for this channel
            idx = len(self._axes) + 1
            ax = self.fig.add_subplot(len(self._channel_data), 1, idx)
            self._axes[channel] = ax
        
        # Get color for this channel
        color_idx = (channel - 1) % len(self._colors)
        
        # Clear current axis and plot data
        ax = self._axes[channel]
        ax.clear()
        ax.plot(times, voltages, color=self._colors[color_idx])
        ax.set_title(f'Channel {channel}')
        ax.set_ylabel('Voltage (V)')
        
        # Only show x-axis label on the bottom plot
        if channel == max(self._channel_data.keys()):
            ax.set_xlabel('Time (s)')
        
        ax.grid(True)
        
        # Update figure layout
        self.fig.tight_layout()
        self.draw()
    
    def _adjust_layout(self):
        """Adjust the subplot layout based on the number of channels."""
        # Clear all existing axes
        for ax in list(self._axes.values()):
            self.fig.delaxes(ax)
        
        # Create new set of axes
        self._axes = {}
        
        # Create a subplot for each channel
        channel_nums = sorted(self._channel_data.keys())
        for i, channel in enumerate(channel_nums):
            ax = self.fig.add_subplot(len(channel_nums), 1, i+1)
            self._axes[channel] = ax
            
            # Plot data
            times, voltages = self._channel_data[channel]
            color_idx = (channel - 1) % len(self._colors)
            ax.plot(times, voltages, color=self._colors[color_idx])
            ax.set_title(f'Channel {channel}')
            ax.set_ylabel('Voltage (V)')
            
            # Only show x-axis label on the bottom plot
            if i == len(channel_nums) - 1:
                ax.set_xlabel('Time (s)')
            
            ax.grid(True)
    
    def clear_all(self):
        """Clear all channels from the plot."""
        self._channel_data = {}
        
        # Clear main axis
        self._main_ax.clear()
        self._main_ax.set_xlabel('Time (s)')
        self._main_ax.set_ylabel('Voltage (V)')
        self._main_ax.grid(True)
        
        # Clear all existing axes
        for ax in list(self._axes.values()):
            self.fig.delaxes(ax)
        
        self._axes = {}
        self.draw()
    
    def save_plot(self, filename):
        """
        Save the current plot to a file.
        
        Args:
            filename (str): Path to save the file
        """
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')


class ChannelWaveformPlotter:
    """Widget containing separate waveform plots for each channel with free zooming and data reduction."""
    
    def __init__(self, parent=None):
        """
        Initialize the channel waveform plotter.
        
        Args:
            parent: Parent widget
        """
        # Main widget and layout
        self._widget = QWidget(parent)
        self._layout = QVBoxLayout(self._widget)
        
        # Time range selection controls
        range_group = QGroupBox("Time Range and Sampling")
        range_layout = QHBoxLayout()
        
        # Min/Max time range selectors
        self._range_label = QLabel("Display Range:")
        self._range_min_spin = QDoubleSpinBox()
        self._range_min_spin.setRange(0, 300)
        self._range_min_spin.setDecimals(3)
        self._range_min_spin.setSingleStep(0.01)
        self._range_min_spin.setPrefix("Start: ")
        self._range_min_spin.setSuffix(" s")
        
        self._range_max_spin = QDoubleSpinBox()
        self._range_max_spin.setRange(0, 300)
        self._range_max_spin.setDecimals(3)
        self._range_max_spin.setSingleStep(0.01)
        self._range_max_spin.setValue(3.0)  # Default 3 seconds
        self._range_max_spin.setPrefix("End: ")
        self._range_max_spin.setSuffix(" s")
        
        # Max points control
        self._max_points_label = QLabel("Max Points:")
        self._max_points_spin = QSpinBox()
        self._max_points_spin.setRange(100, 100000)
        self._max_points_spin.setSingleStep(1000)
        self._max_points_spin.setValue(10000)  # Default 10K points per plot
        
        # Decimation method
        self._decimation_label = QLabel("Reduction Method:")
        self._decimation_combo = QComboBox()
        self._decimation_combo.addItems(["Decimation", "Mean", "Min/Max"])
        
        # Apply button
        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._apply_range_settings)
        
        # Full range button
        self._full_range_button = QPushButton("Show Full Range")
        self._full_range_button.clicked.connect(self._show_full_range)
        
        # Add to range layout
        range_layout.addWidget(self._range_label)
        range_layout.addWidget(self._range_min_spin)
        range_layout.addWidget(self._range_max_spin)
        range_layout.addWidget(self._max_points_label)
        range_layout.addWidget(self._max_points_spin)
        range_layout.addWidget(self._decimation_label)
        range_layout.addWidget(self._decimation_combo)
        range_layout.addWidget(self._apply_button)
        range_layout.addWidget(self._full_range_button)
        
        range_group.setLayout(range_layout)
        self._layout.addWidget(range_group)
        
        # Create chart widgets (one for each channel)
        self._channel_charts = {}
        self._channel_toolbars = {}
        
        for ch in range(1, 3):  # Create charts for channels 1 and 2
            # Create a QGroupBox for this channel
            group = QGroupBox(f"Channel {ch}")
            group_layout = QVBoxLayout()
            
            # Create plot for this channel
            chart = WaveformPlotter(self._widget, width=8, height=3)
            
            # Create a matplotlib toolbar for the chart
            toolbar = matplotlib.backends.backend_qtagg.NavigationToolbar2QT(chart, self._widget)
            
            # Store references
            self._channel_charts[ch] = chart
            self._channel_toolbars[ch] = toolbar
            
            # Add to group layout
            group_layout.addWidget(chart)
            group_layout.addWidget(toolbar)
            group.setLayout(group_layout)
            
            # Add group to main layout
            self._layout.addWidget(group)
        
        # Store signal data
        self._time_values = None
        self._voltage_values = {}
        self._current_range = (0, 3.0)  # Default 0-3 second range
        
        # Status label
        self._status_label = QLabel("No data loaded")
        self._layout.addWidget(self._status_label)
    
    def widget(self):
        """
        Get the widget for this plotter.
        
        Returns:
            QWidget: The main widget
        """
        return self._widget
    
    def update_data(self, times, voltages_by_channel):
        """
        Update the plots with new data.
        
        Args:
            times (np.ndarray): Array of time values
            voltages_by_channel (dict): Dictionary mapping channel numbers to voltage arrays
        """
        # Store data
        self._time_values = times
        self._voltage_values = voltages_by_channel
        
        # Update range controls
        if len(times) > 0:
            min_time = times[0]
            max_time = times[-1]
            
            # Update spinner ranges
            self._range_min_spin.setRange(min_time, max_time)
            self._range_max_spin.setRange(min_time, max_time)
            
            # Set default range to full data
            self._range_min_spin.setValue(min_time)
            self._range_max_spin.setValue(max_time)
            
            # Store current range
            self._current_range = (min_time, max_time)
            
            # Update status
            data_points = len(times)
            channels = ", ".join([f"CH{ch}" for ch in sorted(voltages_by_channel.keys())])
            duration = max_time - min_time
            
            self._status_label.setText(
                f"Data loaded: {data_points:,} points, {duration:.3f} seconds, Channels: {channels}"
            )
        
        # Update charts with full range initially
        self._show_full_range()
    
    def _reduce_data(self, times, voltages, start_time, end_time, max_points):
        """
        Reduce data to a manageable size using the selected method.
        
        Args:
            times (np.ndarray): Array of time values
            voltages (np.ndarray): Array of voltage values
            start_time (float): Start time for the range
            end_time (float): End time for the range
            max_points (int): Maximum number of points to return
            
        Returns:
            tuple: (reduced_times, reduced_voltages)
        """
        # Get indices within the time range
        mask = (times >= start_time) & (times <= end_time)
        range_times = times[mask]
        range_voltages = voltages[mask]
        
        if len(range_times) <= max_points:
            # No reduction needed
            return range_times, range_voltages
        
        # Determine reduction method
        reduction_method = self._decimation_combo.currentText()
        
        if reduction_method == "Decimation":
            # Simple decimation (take every Nth point)
            step = len(range_times) // max_points
            return range_times[::step], range_voltages[::step]
            
        elif reduction_method == "Mean":
            # Average values in bins
            bins = np.linspace(start_time, end_time, max_points + 1)
            digitized = np.digitize(range_times, bins)
            
            reduced_times = []
            reduced_voltages = []
            
            for i in range(1, len(bins)):
                points = digitized == i
                if np.any(points):
                    reduced_times.append(np.mean(range_times[points]))
                    reduced_voltages.append(np.mean(range_voltages[points]))
            
            return np.array(reduced_times), np.array(reduced_voltages)
            
        elif reduction_method == "Min/Max":
            # Keep min/max pairs for each segment
            # This preserves peaks and valleys better than other methods
            samples_per_bin = len(range_times) // (max_points // 2)
            
            reduced_times = []
            reduced_voltages = []
            
            for i in range(0, len(range_times), samples_per_bin):
                if i + samples_per_bin < len(range_times):
                    segment_times = range_times[i:i+samples_per_bin]
                    segment_voltages = range_voltages[i:i+samples_per_bin]
                    
                    # Find min and max points in this segment
                    min_idx = np.argmin(segment_voltages)
                    max_idx = np.argmax(segment_voltages)
                    
                    # Add min and max points to reduced data
                    # Add min first, max second to preserve waveform shape better
                    reduced_times.extend([segment_times[min_idx], segment_times[max_idx]])
                    reduced_voltages.extend([segment_voltages[min_idx], segment_voltages[max_idx]])
            
            return np.array(reduced_times), np.array(reduced_voltages)
        
        # Default to decimation
        step = len(range_times) // max_points
        return range_times[::step], range_voltages[::step]
    
    def _apply_range_settings(self):
        """Apply the current range settings to the plots."""
        if self._time_values is None or not self._voltage_values:
            return
        
        # Get range values
        start_time = self._range_min_spin.value()
        end_time = self._range_max_spin.value()
        max_points = self._max_points_spin.value()
        
        # Ensure start < end
        if start_time >= end_time:
            self._range_max_spin.setValue(start_time + 0.01)
            end_time = start_time + 0.01
        
        # Store current range
        self._current_range = (start_time, end_time)
        
        # Update each channel chart with the reduced data
        for ch in range(1, 3):
            if ch in self._voltage_values:
                # Reduce data for this range
                reduced_times, reduced_voltages = self._reduce_data(
                    self._time_values, 
                    self._voltage_values[ch],
                    start_time,
                    end_time,
                    max_points
                )
                
                # Update the chart
                self._update_channel_chart(ch, reduced_times, reduced_voltages, 
                                         f"Channel {ch} ({start_time:.3f}s - {end_time:.3f}s, {len(reduced_times):,} points)")
    
    def _show_full_range(self):
        """Show the full time range of the data."""
        if self._time_values is None or not self._voltage_values:
            return
        
        # Get full range
        start_time = self._time_values[0]
        end_time = self._time_values[-1]
        
        # Update spinners
        self._range_min_spin.setValue(start_time)
        self._range_max_spin.setValue(end_time)
        
        # Apply the settings
        self._apply_range_settings()
    
    def _update_channel_chart(self, channel, times, voltages, title=None):
        """
        Update a specific channel chart.
        
        Args:
            channel (int): Channel number
            times (np.ndarray): Array of time values
            voltages (np.ndarray): Array of voltage values
            title (str, optional): Chart title. If None, uses default title.
        """
        if channel not in self._channel_charts:
            return
            
        chart = self._channel_charts[channel]
        
        # Clear the plot
        chart._main_ax.clear()
        
        # Plot the channel data
        color_idx = (channel - 1) % len(chart._colors)
        chart._main_ax.plot(
            times, 
            voltages, 
            color=chart._colors[color_idx]
        )
        
        # Add labels and grid
        chart._main_ax.set_xlabel('Time (s)')
        chart._main_ax.set_ylabel('Voltage (V)')
        
        if title:
            chart._main_ax.set_title(title)
        else:
            chart._main_ax.set_title(f'Channel {channel}')
            
        chart._main_ax.grid(True)
        
        # Update the figure
        chart.fig.tight_layout()
        chart.draw()
    
    def _clear_channel_chart(self, channel):
        """
        Clear a specific channel chart.
        
        Args:
            channel (int): Channel number
        """
        if channel not in self._channel_charts:
            return
            
        chart = self._channel_charts[channel]
        chart._main_ax.clear()
        chart._main_ax.set_xlabel('Time (s)')
        chart._main_ax.set_ylabel('Voltage (V)')
        chart._main_ax.set_title(f'Channel {channel} (No Data)')
        chart._main_ax.grid(True)
        chart.fig.tight_layout()
        chart.draw()
    
    def clear_all(self):
        """Clear all data and reset plots."""
        self._time_values = None
        self._voltage_values = {}
        
        # Clear all channel charts
        for ch in self._channel_charts:
            self._clear_channel_chart(ch)
            
        # Reset status
        self._status_label.setText("No data loaded")


# MARK: - Main Application

class ContinuousAcquisitionApp(QMainWindow):
    """Main application window for oscilloscope continuous acquisition testing."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        
        # Initialize instance variables
        self._scope = None
        self._acquisition_thread = None
        self._storage_manager = DataStorageManager()
        
        # Set up the user interface
        self._setup_ui()
        self._connect_signals()
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher - Oscilloscope Continuous Acquisition Test")
        self.resize(1000, 800)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        main_layout = QVBoxLayout(self._central_widget)
        
        # Create tab widget for different sections
        self._tab_widget = QTabWidget()
        
        # Create tabs
        self._setup_tab = self._create_setup_tab()
        self._acquisition_tab = self._create_acquisition_tab()
        self._results_tab = self._create_results_tab()
        
        # Add tabs to widget
        self._tab_widget.addTab(self._setup_tab, "Setup & Connection")
        self._tab_widget.addTab(self._acquisition_tab, "Acquisition")
        self._tab_widget.addTab(self._results_tab, "Results & Analysis")
        
        # Create status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready. Please connect to an oscilloscope.")
        
        # Add widgets to main layout
        main_layout.addWidget(self._tab_widget)
    
    def _create_setup_tab(self):
        """
        Create the setup and connection tab.
        
        Returns:
            QWidget: The setup tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection group
        connection_group = self._create_connection_group()
        
        # Device info group
        device_group = self._create_device_info_group()
        
        # Add widgets to layout
        layout.addWidget(connection_group)
        layout.addWidget(device_group)
        layout.addStretch(1)
        
        return tab
    
    def _create_acquisition_tab(self):
        """
        Create the acquisition configuration tab.
        
        Returns:
            QWidget: The acquisition tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Acquisition parameters group
        params_group = self._create_acquisition_params_group()
        
        # Channel selection group
        channel_group = self._create_channel_selection_group()
        
        # File format group
        file_group = self._create_file_format_group()
        
        # Acquisition controls
        control_group = self._create_acquisition_controls_group()
        
        # Plot widget for live visualization
        self._plot_widget = WaveformPlotter(width=8, height=4)
        
        # Progress bar and status
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        
        self._acquisition_status = QLabel("Ready to start acquisition.")
        
        # Add widgets to layout
        layout.addWidget(params_group)
        layout.addWidget(channel_group)
        layout.addWidget(file_group)
        layout.addWidget(control_group)
        layout.addWidget(self._plot_widget, 1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._acquisition_status)
        
        return tab
    
    def _create_visualization_tab(self):
        """
        Create the visualization tab with separate charts for each channel.
        
        Returns:
            QWidget: The visualization tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create channel waveform plotter
        self._channel_plotter = ChannelWaveformPlotter()
        
        # Controls
        control_layout = QHBoxLayout()
        
        # Save visualization button
        self._save_viz_button = QPushButton("Save Plots")
        self._save_viz_button.clicked.connect(self._save_visualization)
        
        # Clear visualization button
        self._clear_viz_button = QPushButton("Clear Plots")
        self._clear_viz_button.clicked.connect(self._clear_visualization)
        
        # Help label
        help_label = QLabel("Tip: Use the toolbar below each chart to zoom, pan, and explore the signal.")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setStyleSheet("color: #555; font-style: italic;")
        
        control_layout.addWidget(self._save_viz_button)
        control_layout.addWidget(self._clear_viz_button)
        control_layout.addStretch(1)
        
        # Add widgets to layout
        layout.addWidget(help_label)
        layout.addWidget(self._channel_plotter.widget())
        layout.addLayout(control_layout)
        
        return tab
    
    @Slot()
    def _save_visualization(self):
        """Save the current visualization charts to files."""
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Visualization", "", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            # Get base path without extension
            base_path, ext = os.path.splitext(file_path)
            if not ext:
                ext = ".png"  # Default to PNG
            
            # Save channel charts
            saved_files = []
            for ch in self._channel_plotter._channel_charts:
                ch_path = f"{base_path}_ch{ch}{ext}"
                self._channel_plotter._channel_charts[ch].save_plot(ch_path)
                saved_files.append(ch_path)
            
            file_list = ", ".join([os.path.basename(f) for f in saved_files])
            self._status_bar.showMessage(f"Plots saved to: {file_list}")
    
    @Slot()
    def _clear_visualization(self):
        """Clear the visualization charts."""
        self._channel_plotter.clear_all()
        self._status_bar.showMessage("Visualization charts cleared.")
    
    def _create_results_tab(self):
        """
        Create the results and analysis tab with proper tables.
        
        Returns:
            QWidget: The results tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create performance table
        performance_group = QGroupBox("Performance Analysis")
        performance_layout = QVBoxLayout(performance_group)
        
        self._performance_table = QTableWidget()
        self._performance_table.setColumnCount(2)
        self._performance_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self._performance_table.horizontalHeader().setStretchLastSection(True)
        self._performance_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._performance_table.setColumnWidth(0, 200)
        self._performance_table.verticalHeader().setVisible(False)
        self._performance_table.setAlternatingRowColors(True)
        self._performance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        performance_layout.addWidget(self._performance_table)
        
        # Create benchmark table
        benchmark_group = QGroupBox("File Format Benchmark")
        benchmark_layout = QVBoxLayout(benchmark_group)
        
        self._benchmark_table = QTableWidget()
        self._benchmark_table.setColumnCount(4)
        self._benchmark_table.setHorizontalHeaderLabels(["Format", "Size (MB)", "Speed (MB/s)", "Relative Size"])
        self._benchmark_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._benchmark_table.verticalHeader().setVisible(False)
        self._benchmark_table.setAlternatingRowColors(True)
        self._benchmark_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add recommendations label
        self._benchmark_recommendations = QLabel("No benchmark data available.")
        
        benchmark_layout.addWidget(self._benchmark_table)
        benchmark_layout.addWidget(self._benchmark_recommendations)
        
        # Export results button
        self._export_results_button = QPushButton("Export Results Report")
        self._export_results_button.setEnabled(False)
        
        # Add widgets to layout
        layout.addWidget(performance_group, 1)
        layout.addWidget(benchmark_group, 1)
        layout.addWidget(self._export_results_button)
        
        return tab
    
    def _create_connection_group(self):
        """
        Create the connection group box with device selection controls.
        
        Returns:
            QGroupBox: The connection group box
        """
        connection_group = QGroupBox("Oscilloscope Connection")
        connection_layout = QVBoxLayout()
        
        # Device selection layout
        device_selection_layout = QHBoxLayout()
        self._address_label = QLabel("Select Device:")
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(300)
        self._refresh_button = QPushButton("Refresh Devices")
        
        device_selection_layout.addWidget(self._address_label)
        device_selection_layout.addWidget(self._device_combo, 1)
        device_selection_layout.addWidget(self._refresh_button)
        
        # Connect button in its own row
        self._connect_button = QPushButton("Connect")
        self._connect_button.setMinimumHeight(30)
        
        connection_layout.addLayout(device_selection_layout)
        connection_layout.addWidget(self._connect_button)
        connection_group.setLayout(connection_layout)
        
        return connection_group
    
    def _create_device_info_group(self):
        """
        Create the device information group box.
        
        Returns:
            QGroupBox: The device info group box
        """
        device_group = QGroupBox("Device Information")
        device_layout = QVBoxLayout()
        
        self._device_info = QTextEdit()
        self._device_info.setReadOnly(True)
        self._device_info.setMaximumHeight(150)
        
        device_layout.addWidget(self._device_info)
        device_group.setLayout(device_layout)
        
        return device_group
    
    def _create_acquisition_params_group(self):
        """
        Create the acquisition parameters group box.
        
        Returns:
            QGroupBox: The acquisition parameters group box
        """
        params_group = QGroupBox("Acquisition Parameters")
        params_layout = QVBoxLayout()
        
        # Duration control
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (seconds):"))
        self._duration_spin = QDoubleSpinBox()
        self._duration_spin.setRange(0.1, 300.0)
        self._duration_spin.setValue(3.0)
        self._duration_spin.setSingleStep(0.5)
        self._duration_spin.setDecimals(1)
        duration_layout.addWidget(self._duration_spin)
        
        # Sample rate control
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample Rate:"))
        self._sample_rate_combo = QComboBox()
        for name in SAMPLE_RATES:
            self._sample_rate_combo.addItem(name)
        self._sample_rate_combo.setCurrentText("Auto")
        sample_rate_layout.addWidget(self._sample_rate_combo)
        
        # Memory depth control
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory Depth:"))
        self._memory_depth_combo = QComboBox()
        for name in MEMORY_DEPTHS:
            self._memory_depth_combo.addItem(name)
        self._memory_depth_combo.setCurrentText("Auto")
        memory_layout.addWidget(self._memory_depth_combo)
        
        # Add layouts to main params layout
        params_layout.addLayout(duration_layout)
        params_layout.addLayout(sample_rate_layout)
        params_layout.addLayout(memory_layout)
        
        params_group.setLayout(params_layout)
        return params_group
    
    def _create_channel_selection_group(self):
        """
        Create the channel selection group box.
        
        Returns:
            QGroupBox: The channel selection group box
        """
        channel_group = QGroupBox("Channel Selection")
        channel_layout = QHBoxLayout()
        
        # Channel checkboxes
        self._ch1_checkbox = QCheckBox("Channel 1")
        self._ch1_checkbox.setChecked(True)
        self._ch2_checkbox = QCheckBox("Channel 2")
        self._ch2_checkbox.setChecked(True)
        self._ch3_checkbox = QCheckBox("Channel 3")
        self._ch4_checkbox = QCheckBox("Channel 4")
        
        channel_layout.addWidget(self._ch1_checkbox)
        channel_layout.addWidget(self._ch2_checkbox)
        channel_layout.addWidget(self._ch3_checkbox)
        channel_layout.addWidget(self._ch4_checkbox)
        channel_layout.addStretch(1)
        
        channel_group.setLayout(channel_layout)
        return channel_group
    
    def _create_file_format_group(self):
        """
        Create the file format selection group box.
        
        Returns:
            QGroupBox: The file format group box
        """
        file_group = QGroupBox("Data Storage")
        file_layout = QVBoxLayout()
        
        # File format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("File Format:"))
        self._file_format_combo = QComboBox()
        for name in FILE_FORMATS:
            self._file_format_combo.addItem(name)
        format_layout.addWidget(self._file_format_combo)
        
        # Run benchmark checkbox
        self._benchmark_checkbox = QCheckBox("Run Format Benchmark")
        self._benchmark_checkbox.setChecked(True)
        
        # Output file path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Output File:"))
        self._output_path_edit = QTextEdit()
        self._output_path_edit.setMaximumHeight(30)
        self._output_path_edit.setPlaceholderText("Enter file path or use Browse button")
        self._browse_button = QPushButton("Browse...")
        path_layout.addWidget(self._output_path_edit, 1)
        path_layout.addWidget(self._browse_button)
        
        # Add layouts to main file layout
        file_layout.addLayout(format_layout)
        file_layout.addWidget(self._benchmark_checkbox)
        file_layout.addLayout(path_layout)
        
        file_group.setLayout(file_layout)
        return file_group
    
    def _create_acquisition_controls_group(self):
        """
        Create the acquisition controls group box.
        
        Returns:
            QGroupBox: The acquisition controls group box
        """
        control_group = QGroupBox("Acquisition Controls")
        control_layout = QHBoxLayout()
        
        # Start, stop buttons
        self._start_button = QPushButton("Start Acquisition")
        self._start_button.setEnabled(False)
        self._stop_button = QPushButton("Stop Acquisition")
        self._stop_button.setEnabled(False)
        self._clear_button = QPushButton("Clear Results")
        
        control_layout.addWidget(self._start_button)
        control_layout.addWidget(self._stop_button)
        control_layout.addWidget(self._clear_button)
        
        control_group.setLayout(control_layout)
        return control_group
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        # Connection signals
        self._connect_button.clicked.connect(self._connect_to_scope)
        self._refresh_button.clicked.connect(self._populate_device_list)
        
        # Acquisition signals
        self._browse_button.clicked.connect(self._browse_output_file)
        self._start_button.clicked.connect(self._start_acquisition)
        self._stop_button.clicked.connect(self._stop_acquisition)
        self._clear_button.clicked.connect(self._clear_results)
        
        # Results signals
        self._export_results_button.clicked.connect(self._export_results)
        
        # Format signals
        self._file_format_combo.currentTextChanged.connect(self._update_file_format)
    
    def _populate_device_list(self):
        """Populate the device combo box with available VISA resources."""
        self._device_combo.clear()
        self._status_bar.showMessage("Searching for devices...")
        
        try:
            rm = pyvisa.ResourceManager()
            devices = rm.list_resources()
            
            if not devices:
                self._device_combo.addItem("No devices found")
                self._status_bar.showMessage("No devices found.")
                self._connect_button.setEnabled(False)
                return
            
            # Add devices to combo box
            for device in devices:
                self._device_combo.addItem(device)
                
            self._connect_button.setEnabled(True)
            self._status_bar.showMessage(f"Found {len(devices)} device(s).")
            
            # Display in device info text area as well
            device_text = "Available devices:\n" + "\n".join(devices)
            self._device_info.setText(device_text)
            
        except Exception as e:
            self._device_info.setText(f"Error finding devices: {str(e)}")
            self._status_bar.showMessage("Error finding devices.")
            self._connect_button.setEnabled(False)
    
    @Slot()
    def _connect_to_scope(self):
        """Connect to the oscilloscope using the selected address."""
        if self._device_combo.count() == 0 or self._device_combo.currentText() == "No devices found":
            QMessageBox.warning(self, "Connection Error", "No devices available to connect.")
            return
        
        address = self._device_combo.currentText()
        if not address:
            QMessageBox.warning(self, "Connection Error", "Please select a device.")
            return
        
        self._status_bar.showMessage("Connecting to oscilloscope...")
        self._connect_button.setEnabled(False)
        
        # Connect to the oscilloscope in a separate thread
        self._connection_thread = OscilloscopeConnectionThread(address)
        self._connection_thread.connection_successful.connect(self._on_connection_successful)
        self._connection_thread.connection_failed.connect(self._on_connection_failed)
        self._connection_thread.start()
    
    @Slot(object, str)
    def _on_connection_successful(self, scope, idn):
        """
        Handle successful oscilloscope connection.
        
        Args:
            scope: The connected oscilloscope resource
            idn (str): Identification string from the oscilloscope
        """
        self._scope = scope
        self._device_info.setText(f"Connected to: {idn}\nAddress: {self._device_combo.currentText()}")
        self._status_bar.showMessage("Connected to oscilloscope.")
        
        # Query oscilloscope capabilities
        try:
            # Get model information
            model = idn.split(',')[1] if ',' in idn else "Unknown"
            
            # Get sample rate
            sample_rate = float(self._scope.query(":ACQ:SRAT?"))
            
            # Get memory depth
            max_memory = self._scope.query(":ACQ:MDEP?").strip()
            
            # Get number of channels
            channels = "Unknown"
            if "DS1" in model:
                # Logic for Rigol DS1000 series
                if "Z" in model:
                    channels = "4" if "4" in model else "2"
                else:
                    channels = "2"
            
            # Calculate max duration possible at full sample rate
            max_duration = float(max_memory) / sample_rate if max_memory.isdigit() else "Unknown"
            
            # Display capabilities
            capabilities = (
                f"Model: {model}\n"
                f"Sample Rate: {sample_rate/1e6:.1f} MSa/s\n"
                f"Memory Depth: {max_memory} points\n"
                f"Channels: {channels}\n"
                f"Max Duration at Full Rate: {max_duration if isinstance(max_duration, str) else max_duration:.2f} seconds"
            )
            self._device_info.append("\n\nCapabilities:\n" + capabilities)
        except Exception as e:
            self._device_info.append(f"\n\nError querying capabilities: {str(e)}")
        
        # Enable acquisition controls
        self._start_button.setEnabled(True)
        self._connect_button.setText("Disconnect")
        self._connect_button.setEnabled(True)
        self._connect_button.clicked.disconnect(self._connect_to_scope)
        self._connect_button.clicked.connect(self._disconnect_from_scope)
        
        # Switch to acquisition tab
        self._tab_widget.setCurrentIndex(1)
    
    @Slot(str, list)
    def _on_connection_failed(self, error_msg, available_devices):
        """
        Handle failed oscilloscope connection.
        
        Args:
            error_msg (str): Error message from the connection attempt
            available_devices (list): List of available devices
        """
        device_list = "\n".join(available_devices) if available_devices else "No devices found"
        
        error_box = QMessageBox(self)
        error_box.setWindowTitle("Connection Error")
        error_box.setText(f"Failed to connect to the oscilloscope: {error_msg}")
        error_box.setInformativeText("Available devices:\n" + device_list)
        error_box.setIcon(QMessageBox.Warning)
        error_box.exec_()
        
        self._status_bar.showMessage("Connection failed.")
        self._connect_button.setEnabled(True)
    
    @Slot()
    def _disconnect_from_scope(self):
        """Disconnect from the oscilloscope."""
        if self._scope:
            try:
                # Return to local control before closing
                self._scope.write(':KEY:FORC')
                
                # Close the connection
                self._scope.close()
            except:
                pass
            self._scope = None
        
        # Update UI
        self._device_info.clear()
        self._start_button.setEnabled(False)
        self._stop_button.setEnabled(False)
        self._connect_button.setText("Connect")
        self._connect_button.clicked.disconnect(self._disconnect_from_scope)
        self._connect_button.clicked.connect(self._connect_to_scope)
        
        self._status_bar.showMessage("Disconnected from oscilloscope.")
    
    @Slot()
    def _browse_output_file(self):
        """Open file dialog to select output file path."""
        # Get the selected file extension
        format_name = self._file_format_combo.currentText()
        extension = FILE_FORMATS[format_name]
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", "", f"Data Files (*.{extension});;All Files (*)"
        )
        
        if file_path:
            # Remove extension if present
            base_path, _ = os.path.splitext(file_path)
            self._output_path_edit.setText(base_path)
    
    @Slot(str)
    def _update_file_format(self, format_name):
        """
        Update file format in the storage manager.
        
        Args:
            format_name (str): Selected format name
        """
        if format_name in FILE_FORMATS:
            format_type = FILE_FORMATS[format_name]
            self._storage_manager.format_type = format_type
    
    @Slot()
    def _start_acquisition(self):
        """Start continuous acquisition process."""
        # Check if we have selected channels
        channels = self._get_selected_channels()
        if not channels:
            QMessageBox.warning(self, "Acquisition Error", "Please select at least one channel.")
            return
        
        # Check if we have an output path if saving
        output_path = self._output_path_edit.toPlainText().strip()
        if not output_path:
            # Create default output path
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"oscilloscope_data_{timestamp}"
            self._output_path_edit.setText(output_path)
        
        # Get acquisition parameters
        duration = self._duration_spin.value()
        
        # Get sample rate
        sample_rate_key = self._sample_rate_combo.currentText()
        sample_rate = SAMPLE_RATES.get(sample_rate_key, 0)
        
        # Get memory depth
        memory_key = self._memory_depth_combo.currentText()
        memory_depth = MEMORY_DEPTHS.get(memory_key, 0)
        
        # Update file format
        format_name = self._file_format_combo.currentText()
        self._update_file_format(format_name)
        
        # Clear plot and results
        self._plot_widget.clear_all()
        self._progress_bar.setValue(0)
        
        # Update UI
        self._start_button.setEnabled(False)
        self._stop_button.setEnabled(True)
        self._acquisition_status.setText("Preparing acquisition...")
        
        # Create and start acquisition thread
        self._acquisition_thread = ContinuousAcquisitionThread(
            self._scope, channels, duration, sample_rate, memory_depth,
            self._storage_manager, output_path
        )
        
        # Connect signals
        self._acquisition_thread.update_status.connect(self._acquisition_status.setText)
        self._acquisition_thread.update_progress.connect(self._progress_bar.setValue)
        self._acquisition_thread.acquisition_data.connect(self._plot_widget.update_live_plot)
        self._acquisition_thread.acquisition_complete.connect(self._on_acquisition_complete)
        self._acquisition_thread.acquisition_error.connect(self._on_acquisition_error)
        
        # Start acquisition
        self._acquisition_thread.start()
        self._status_bar.showMessage("Acquisition in progress...")
    
    @Slot()
    def _stop_acquisition(self):
        """Stop the acquisition process."""
        if self._acquisition_thread and self._acquisition_thread.isRunning():
            # Request thread to stop
            self._acquisition_thread.stop()
            self._acquisition_status.setText("Stopping acquisition...")
    
    @Slot(dict)
    def _on_acquisition_complete(self, results):
        """
        Handle completed acquisition.
        
        Args:
            results (dict): Acquisition results
        """
        # Update UI
        self._start_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._export_results_button.setEnabled(True)
        
        # Format and display results
        duration = results.get('duration', 0)
        sample_rate = results.get('achieved_sample_rate', 0)
        total_points = results.get('total_points', 0)
        
        # Fill performance table
        self._update_performance_table(results)
        
        # Update benchmark table if available
        if self._storage_manager.benchmark_results:
            self._update_benchmark_table()
        
        # Update status
        self._acquisition_status.setText("Acquisition complete!")
        self._status_bar.showMessage(f"Acquisition complete: {duration:.1f}s at {sample_rate/1e6:.1f} MSa/s, {total_points:,.0f} points captured.")
        
        # Switch to results tab
        self._tab_widget.setCurrentIndex(2)
    
    def _update_performance_table(self, results):
        """
        Update the performance table with acquisition results.
        
        Args:
            results (dict): Acquisition results
        """
        # Clear previous data
        self._performance_table.setRowCount(0)
        
        # Define metrics to display
        metrics = [
            ("Test Duration", f"{results.get('duration', 0):.2f} seconds"),
            ("Total Data Points", f"{results.get('total_points', 0):,.0f}"),
            ("Achieved Sample Rate", f"{results.get('achieved_sample_rate', 0)/1e6:.2f} MSa/s"),
            ("Configured Sample Rate", f"{results.get('sample_rate', 0)/1e6:.2f} MSa/s" if results.get('sample_rate', 0) > 0 else "Auto"),
            ("Memory Depth", f"{results.get('memory_depth', 0):,.0f}" if results.get('memory_depth', 0) > 0 else "Auto"),
            ("Acquisition Count", f"{results.get('acquisition_count', 0):,}"),
            ("Channels", ", ".join([f"CH{ch}" for ch in results.get('channels', [])])),
        ]
        
        # Add additional performance metrics if available
        if hasattr(self._acquisition_thread, '_performance'):
            perf = self._acquisition_thread._performance
            
            # Add CPU and memory usage
            if perf.cpu_usage:
                metrics.append(("Average CPU Usage", f"{np.mean(perf.cpu_usage):.1f}%"))
                metrics.append(("Peak CPU Usage", f"{np.max(perf.cpu_usage):.1f}%"))
            
            if perf.memory_usage:
                metrics.append(("Average Memory Usage", f"{np.mean(perf.memory_usage):.1f}%"))
            
            if perf.data_transfer_rate and len(perf.data_transfer_rate) > 1:
                # Skip first element as it's always 0
                transfer_rate = np.mean(perf.data_transfer_rate[1:]) / (1024 * 1024)  # Convert to MB/s
                metrics.append(("Data Transfer Rate", f"{transfer_rate:.2f} MB/s"))
            
            metrics.append(("Identified Bottleneck", perf.bottleneck_identified))
        
        # Add rows to table
        self._performance_table.setRowCount(len(metrics))
        for i, (key, value) in enumerate(metrics):
            self._performance_table.setItem(i, 0, QTableWidgetItem(key))
            self._performance_table.setItem(i, 1, QTableWidgetItem(value))
            
        # Resize rows to contents
        self._performance_table.resizeRowsToContents()
    
    def _update_benchmark_table(self):
        """Update the benchmark table with file format benchmark results."""
        # Clear previous data
        self._benchmark_table.setRowCount(0)
        
        results = self._storage_manager.benchmark_results
        if not results:
            return
        
        # Find the largest file size for relative comparison
        max_size = max(res['file_size'] for res in results.values())
        
        # Add rows to table
        self._benchmark_table.setRowCount(len(results))
        for i, (fmt, data) in enumerate(results.items()):
            # Format data
            size_mb = data['file_size'] / (1024 * 1024)
            speed_mb = data['write_speed'] / (1024 * 1024)
            rel_size = data['file_size'] / max_size if max_size > 0 else 0
            
            # Add to table
            self._benchmark_table.setItem(i, 0, QTableWidgetItem(fmt.upper()))
            self._benchmark_table.setItem(i, 1, QTableWidgetItem(f"{size_mb:.2f}"))
            self._benchmark_table.setItem(i, 2, QTableWidgetItem(f"{speed_mb:.2f}"))
            self._benchmark_table.setItem(i, 3, QTableWidgetItem(f"{rel_size:.2f}x"))
        
        # Resize rows to contents
        self._benchmark_table.resizeRowsToContents()
        
        # Update recommendations label
        fastest = max(results.items(), key=lambda x: x[1]['write_speed'])[0]
        smallest = min(results.items(), key=lambda x: x[1]['file_size'])[0]
        
        if fastest == smallest:
            recommendations = f"• Recommendation: Use <b>{fastest.upper()}</b> format for best overall performance."
        else:
            # Calculate balanced score
            balance_score = {}
            for fmt, res in results.items():
                # Normalize metrics between 0 and 1
                speed_score = res['write_speed'] / max(r['write_speed'] for r in results.values())
                size_score = min(r['file_size'] for r in results.values()) / res['file_size']
                # Combined score with more weight on speed
                balance_score[fmt] = 0.7 * speed_score + 0.3 * size_score
            
            best_balance = max(balance_score.items(), key=lambda x: x[1])[0]
            
            recommendations = (
                "<b>Recommendations:</b><br>"
                f"• For maximum speed: <b>{fastest.upper()}</b><br>"
                f"• For smallest file size: <b>{smallest.upper()}</b><br>"
                f"• Best balance of speed and size: <b>{best_balance.upper()}</b>"
            )
        
        self._benchmark_recommendations.setText(recommendations)
    
    @Slot(str)
    def _on_acquisition_error(self, error_msg):
        """
        Handle acquisition error.
        
        Args:
            error_msg (str): Error message
        """
        QMessageBox.warning(self, "Acquisition Error", error_msg)
        
        # Reset UI
        self._start_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._acquisition_status.setText(f"Error: {error_msg}")
        self._status_bar.showMessage("Acquisition failed.")
    
    @Slot()
    def _clear_results(self):
        """Clear all results and plots."""
        self._plot_widget.clear_all()
        self._progress_bar.setValue(0)
        self._acquisition_status.setText("Ready to start acquisition.")
        
        # Clear performance table
        self._performance_table.setRowCount(0)
        
        # Clear benchmark table
        self._benchmark_table.setRowCount(0)
        
        # Reset benchmark recommendations
        self._benchmark_recommendations.setText("No benchmark data available.")
        
        # Disable export button
        self._export_results_button.setEnabled(False)
    
    @Slot()
    def _export_results(self):
        """Export results to a report file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results Report", "", "Text Files (*.txt);;HTML Files (*.html);;All Files (*)"
        )
        
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.html':
                self._export_html_report(file_path)
            else:
                self._export_text_report(file_path)
    
    def _export_text_report(self, file_path):
        """
        Export results to a plain text report file.
        
        Args:
            file_path (str): Path to save the report
        """
        try:
            with open(file_path, 'w') as f:
                # Write report header
                f.write("="*60 + "\n")
                f.write("OSCILLOSCOPE CONTINUOUS ACQUISITION TEST RESULTS\n")
                f.write("="*60 + "\n\n")
                
                # Add timestamp
                f.write(f"Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Add device info
                f.write("DEVICE INFORMATION\n")
                f.write("-"*60 + "\n")
                f.write(self._device_info.toPlainText() + "\n\n")
                
                # Add performance results
                f.write("PERFORMANCE ANALYSIS\n")
                f.write("-"*60 + "\n")
                
                # Extract data from performance table
                for row in range(self._performance_table.rowCount()):
                    metric = self._performance_table.item(row, 0).text()
                    value = self._performance_table.item(row, 1).text()
                    f.write(f"{metric}: {value}\n")
                
                f.write("\n")
                
                # Add benchmark results
                f.write("FILE FORMAT BENCHMARK\n")
                f.write("-"*60 + "\n")
                
                # First, write the table header
                f.write(f"{'Format':<10} {'Size (MB)':<12} {'Speed (MB/s)':<14} {'Relative Size':<14}\n")
                f.write("-"*50 + "\n")
                
                # Extract data from benchmark table
                for row in range(self._benchmark_table.rowCount()):
                    format_name = self._benchmark_table.item(row, 0).text()
                    size_mb = self._benchmark_table.item(row, 1).text()
                    speed_mb = self._benchmark_table.item(row, 2).text()
                    rel_size = self._benchmark_table.item(row, 3).text()
                    
                    f.write(f"{format_name:<10} {size_mb:<12} {speed_mb:<14} {rel_size:<14}\n")
                
                f.write("\n")
                
                # Add recommendations
                f.write("RECOMMENDATIONS\n")
                f.write("-"*60 + "\n")
                
                # Get recommendation text (strip HTML tags for text report)
                recommendations = self._benchmark_recommendations.text()
                recommendations = recommendations.replace('<b>', '').replace('</b>', '')
                recommendations = recommendations.replace('<br>', '\n')
                
                f.write(recommendations + "\n\n")
                
                # Add acquisition configuration
                f.write("ACQUISITION CONFIGURATION\n")
                f.write("-"*60 + "\n")
                f.write(f"Duration: {self._duration_spin.value()} seconds\n")
                f.write(f"Sample Rate: {self._sample_rate_combo.currentText()}\n")
                f.write(f"Memory Depth: {self._memory_depth_combo.currentText()}\n")
                f.write(f"File Format: {self._file_format_combo.currentText()}\n")
                
                # Add channels
                channels = []
                if self._ch1_checkbox.isChecked():
                    channels.append("CH1")
                if self._ch2_checkbox.isChecked():
                    channels.append("CH2")
                if self._ch3_checkbox.isChecked():
                    channels.append("CH3")
                if self._ch4_checkbox.isChecked():
                    channels.append("CH4")
                
                f.write(f"Channels: {', '.join(channels)}\n")
            
            self._status_bar.showMessage(f"Results exported to {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error exporting results: {str(e)}")
    
    def _export_html_report(self, file_path):
        """
        Export results to an HTML report file.
        
        Args:
            file_path (str): Path to save the report
        """
        try:
            with open(file_path, 'w') as f:
                # Write HTML header
                f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Oscilloscope Continuous Acquisition Test Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #2980b9;
            margin-top: 30px;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f5f5f5;
            font-weight: bold;
            color: #2c3e50;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .recommendations {
            background-color: #f0f8ff;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }
        .footer {
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }
    </style>
</head>
<body>
""")
                
                # Add header
                f.write(f"<h1>Oscilloscope Continuous Acquisition Test Results</h1>\n")
                f.write(f"<p>Report generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>\n")
                
                # Add device info
                f.write("<h2>Device Information</h2>\n")
                f.write("<pre>" + self._device_info.toPlainText() + "</pre>\n")
                
                # Add performance results
                f.write("<h2>Performance Analysis</h2>\n")
                f.write("<table>\n")
                f.write("  <tr><th>Metric</th><th>Value</th></tr>\n")
                
                # Extract data from performance table
                for row in range(self._performance_table.rowCount()):
                    metric = self._performance_table.item(row, 0).text()
                    value = self._performance_table.item(row, 1).text()
                    f.write(f"  <tr><td>{metric}</td><td>{value}</td></tr>\n")
                
                f.write("</table>\n")
                
                # Add benchmark results
                f.write("<h2>File Format Benchmark</h2>\n")
                f.write("<table>\n")
                f.write("  <tr><th>Format</th><th>Size (MB)</th><th>Speed (MB/s)</th><th>Relative Size</th></tr>\n")
                
                # Extract data from benchmark table
                for row in range(self._benchmark_table.rowCount()):
                    format_name = self._benchmark_table.item(row, 0).text()
                    size_mb = self._benchmark_table.item(row, 1).text()
                    speed_mb = self._benchmark_table.item(row, 2).text()
                    rel_size = self._benchmark_table.item(row, 3).text()
                    
                    f.write(f"  <tr><td>{format_name}</td><td>{size_mb}</td><td>{speed_mb}</td><td>{rel_size}</td></tr>\n")
                
                f.write("</table>\n")
                
                # Add recommendations
                f.write("<h2>Recommendations</h2>\n")
                f.write(f"<div class='recommendations'>{self._benchmark_recommendations.text()}</div>\n")
                
                # Add acquisition configuration
                f.write("<h2>Acquisition Configuration</h2>\n")
                f.write("<table>\n")
                f.write(f"  <tr><td>Duration</td><td>{self._duration_spin.value()} seconds</td></tr>\n")
                f.write(f"  <tr><td>Sample Rate</td><td>{self._sample_rate_combo.currentText()}</td></tr>\n")
                f.write(f"  <tr><td>Memory Depth</td><td>{self._memory_depth_combo.currentText()}</td></tr>\n")
                f.write(f"  <tr><td>File Format</td><td>{self._file_format_combo.currentText()}</td></tr>\n")
                
                # Add channels
                channels = []
                if self._ch1_checkbox.isChecked():
                    channels.append("CH1")
                if self._ch2_checkbox.isChecked():
                    channels.append("CH2")
                if self._ch3_checkbox.isChecked():
                    channels.append("CH3")
                if self._ch4_checkbox.isChecked():
                    channels.append("CH4")
                
                f.write(f"  <tr><td>Channels</td><td>{', '.join(channels)}</td></tr>\n")
                f.write("</table>\n")
                
                # Add footer
                f.write("<div class='footer'><p>Generated by PySignalDecipher - Oscilloscope Continuous Acquisition Test</p></div>\n")
                
                # Close HTML
                f.write("</body>\n</html>")
            
            self._status_bar.showMessage(f"HTML report exported to {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error exporting HTML report: {str(e)}")
    
    def _get_selected_channels(self):
        """
        Get list of selected channels from checkboxes.
        
        Returns:
            list: Channel numbers that are selected
        """
        channels = []
        if self._ch1_checkbox.isChecked():
            channels.append(1)
        if self._ch2_checkbox.isChecked():
            channels.append(2)
        if self._ch3_checkbox.isChecked():
            channels.append(3)
        if self._ch4_checkbox.isChecked():
            channels.append(4)
        return channels
    
    def closeEvent(self, event):
        """
        Handle window close event to clean up resources.
        
        Args:
            event: Close event from the window system
        """
        # Stop acquisition if running
        if self._acquisition_thread and self._acquisition_thread.isRunning():
            self._acquisition_thread.stop()
            self._acquisition_thread.wait(1000)
            
        if self._scope:
            try:
                # Return to local control before closing
                self._scope.write(':KEY:FORC')
                self._scope.close()
            except:
                pass
        
        # Clear any resource locks that might have been left
        try:
            rm = pyvisa.ResourceManager()
            for resource in rm.list_resources():
                try:
                    temp = rm.open_resource(resource)
                    temp.close()
                except:
                    pass
        except:
            pass
            
        event.accept()


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    main_window = ContinuousAcquisitionApp()
    main_window.show()
    
    # Now that the UI is fully initialized and shown, populate the device list
    main_window._populate_device_list()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()