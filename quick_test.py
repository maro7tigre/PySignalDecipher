# -*- coding: utf-8 -*-
"""
Oscilloscope Quick Test Utility for PySignalDecipher.

A simple GUI tool to verify oscilloscope connectivity and capture waveforms.
This module provides a standalone application for testing oscilloscope connections
and capturing data, which can be used during development or by end users.
"""

import sys
import time
import numpy as np
import pyvisa
import matplotlib
matplotlib.use('QtAgg')  # Set the backend to be compatible with PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox, QTextEdit, QCheckBox,
    QStatusBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Slot, Signal, QThread, QTimer


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


class WaveformCaptureThread(QThread):
    """Thread for capturing waveform data without blocking the UI."""
    
    capture_complete = Signal(tuple)  # Signal emits channel, times, voltages
    capture_error = Signal(str, str)  # Signal emits channel, error message
    
    def __init__(self, scope, channel):
        """
        Initialize waveform capture thread.
        
        Args:
            scope: PyVISA resource for the oscilloscope
            channel (int): Channel number to capture from
        """
        super().__init__()
        self._scope = scope
        self._channel = channel
        
    def run(self):
        """Capture waveform data from the specified channel."""
        try:
            times, voltages = self._get_waveform_data(self._scope, self._channel)
            self.capture_complete.emit((self._channel, times, voltages))
        except Exception as e:
            self.capture_error.emit(str(self._channel), str(e))
            
    def _get_waveform_data(self, scope, channel):
        """
        Get waveform data from specified channel.
        
        Args:
            scope: PyVISA resource for the oscilloscope
            channel (int): Channel number to capture from
            
        Returns:
            tuple: (times, voltages) arrays
            
        Raises:
            ValueError: If the channel is not enabled or if data retrieval fails
        """
        # Check if channel is enabled
        channel_state = scope.query(f":CHAN{channel}:DISP?").strip()
        if channel_state != "1" and channel_state.lower() != "on":
            raise ValueError(f"Channel {channel} is not enabled on the oscilloscope. Please enable it first.")
            
        # Configure waveform acquisition
        # Set waveform source
        scope.write(f":WAV:SOUR CHAN{channel}")
        
        # Waveform mode determines the data resolution
        scope.write(":WAV:MODE NORM")  # Screen data only (faster)
        
        # Data format 
        scope.write(":WAV:FORM BYTE")  # 8-bit resolution, most efficient
        
        # Get the waveform preamble - critical for correct scaling
        preamble_str = scope.query(":WAV:PRE?")
        preamble = preamble_str.strip().split(',')
        
        try:
            # Extract scaling factors from preamble
            if len(preamble) >= 10:
                # X-axis scaling factors
                x_increment = float(preamble[4])  # Time between points
                x_origin = float(preamble[5])     # First point time
                x_reference = float(preamble[6])  # Referenced position
                
                # Y-axis scaling factors
                y_increment = float(preamble[7])  # Voltage per level
                y_origin = float(preamble[8])     # Ground level offset
                y_reference = float(preamble[9])  # Reference level
            else:
                raise ValueError("Preamble doesn't have enough elements")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Error parsing preamble: {e}")
        
        # Get the raw waveform data
        scope.write(":WAV:DATA?")
        raw_data = scope.read_raw()
        
        # Remove header bytes and extract data
        if raw_data[0:1] != b'#':
            raise ValueError("Invalid response format")
            
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
        
        # Initial setup with empty subplot area
        self.fig.tight_layout()
    
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
    
    def clear_channel(self, channel):
        """
        Remove a channel from the plot.
        
        Args:
            channel (int): Channel number to remove
        """
        if channel in self._channel_data:
            del self._channel_data[channel]
            
            # Readjust the layout
            self._adjust_layout()
            
            # Redraw
            self.fig.tight_layout()
            self.draw()
    
    def clear_all(self):
        """Clear all channels from the plot."""
        self._channel_data = {}
        
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


# MARK: - Main Application

class QuickTestApp(QMainWindow):
    """Main application window for oscilloscope quick test."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        
        # Initialize instance variables
        self._scope = None
        self._capture_threads = []
        self._current_capture_index = 0
        self._live_mode_enabled = False
        self._live_update_timer = QTimer(self)
        self._live_update_timer.timeout.connect(self._update_live_waveforms)
        
        # Set up the user interface
        self._setup_ui()
        self._connect_signals()
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher - Oscilloscope Quick Test")
        self.resize(900, 600)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        main_layout = QVBoxLayout(self._central_widget)
        
        # Create the connection group
        connection_group = self._create_connection_group()
        
        # Create the device info group
        device_group = self._create_device_info_group()
        
        # Create the capture controls group
        capture_group = self._create_capture_group()
        
        # Create the plot widget
        self._plot_widget = WaveformPlotter(self._central_widget, width=8, height=4)
        
        # Create status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready. Please connect to an oscilloscope.")
        
        # Add widgets to main layout
        main_layout.addWidget(connection_group)
        main_layout.addWidget(device_group)
        main_layout.addWidget(capture_group)
        main_layout.addWidget(self._plot_widget, 1)
    
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
        self._device_info.setMaximumHeight(100)
        
        device_layout.addWidget(self._device_info)
        device_group.setLayout(device_layout)
        
        return device_group
    
    def _create_capture_group(self):
        """
        Create the capture controls group box.
        
        Returns:
            QGroupBox: The capture controls group box
        """
        capture_group = QGroupBox("Capture Controls")
        capture_layout = QVBoxLayout()
        
        # Channel selection checkboxes
        channel_layout = QHBoxLayout()
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
        
        # Button row
        button_layout = QHBoxLayout()
        self._capture_button = QPushButton("Capture Waveforms")
        self._live_button = QPushButton("Live Mode: OFF")
        self._live_button.setCheckable(True)
        self._save_button = QPushButton("Save Plot")
        self._clear_button = QPushButton("Clear Plot")
        
        button_layout.addWidget(self._capture_button)
        button_layout.addWidget(self._live_button)
        button_layout.addWidget(self._save_button)
        button_layout.addWidget(self._clear_button)
        
        # Add layouts to main capture layout
        capture_layout.addLayout(channel_layout)
        capture_layout.addLayout(button_layout)
        capture_group.setLayout(capture_layout)
        
        # Initial state
        self._capture_button.setEnabled(False)
        self._live_button.setEnabled(False)
        self._save_button.setEnabled(False)
        self._clear_button.setEnabled(False)
        
        return capture_group
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        self._connect_button.clicked.connect(self._connect_to_scope)
        self._refresh_button.clicked.connect(self._populate_device_list)
        self._capture_button.clicked.connect(self._capture_waveforms)
        self._live_button.clicked.connect(self._toggle_live_mode)
        self._save_button.clicked.connect(self._save_plot)
        self._clear_button.clicked.connect(self._clear_plot)
    
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
        
        # Enable capture controls
        self._capture_button.setEnabled(True)
        self._live_button.setEnabled(True)
        self._save_button.setEnabled(True)
        self._clear_button.setEnabled(True)
        self._connect_button.setText("Disconnect")
        self._connect_button.setEnabled(True)
        self._connect_button.clicked.disconnect(self._connect_to_scope)
        self._connect_button.clicked.connect(self._disconnect_from_scope)
        
        # Configure oscilloscope for optimal performance
        try:
            # Clear any pending operations
            self._scope.write('*CLS')
            
            # Run acquisition to get fresh data
            self._scope.write(':RUN')
            
            # Update status message
            self._status_bar.showMessage("Connected and configured for acquisition.")
        except Exception as e:
            print(f"Error configuring scope: {e}")
            # This is not fatal, so we continue
    
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
        # Stop live mode if running
        if self._live_mode_enabled:
            self._toggle_live_mode()
        
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
        self._capture_button.setEnabled(False)
        self._live_button.setEnabled(False)
        self._save_button.setEnabled(False)
        self._clear_button.setEnabled(False)
        self._connect_button.setText("Connect")
        self._connect_button.clicked.disconnect(self._disconnect_from_scope)
        self._connect_button.clicked.connect(self._connect_to_scope)
        
        self._status_bar.showMessage("Disconnected from oscilloscope.")
    
    @Slot()
    def _toggle_live_mode(self):
        """Toggle the live mode on/off."""
        if not self._scope:
            return
        
        if not self._live_mode_enabled:
            # Start live mode
            # Get selected channels
            channels = self._get_selected_channels()
            
            if not channels:
                QMessageBox.warning(self, "Live Mode Error", "Please select at least one channel.")
                self._live_button.setChecked(False)
                return
            
            # Filter enabled channels
            enabled_channels = self._filter_enabled_channels(channels)
            
            if not enabled_channels:
                QMessageBox.warning(self, "Live Mode Error", 
                                   "None of the selected channels are enabled on the oscilloscope. "
                                   "Please enable at least one channel from the oscilloscope's front panel.")
                self._live_button.setChecked(False)
                return
            
            # Store selected channels
            self._live_channels = enabled_channels
            
            # Make sure scope is running
            try:
                self._scope.write(':RUN')
            except Exception as e:
                print(f"Error setting scope to RUN: {e}")
            
            # Start the timer
            self._live_update_timer.start(200)  # Update every 200ms
            self._live_mode_enabled = True
            self._live_button.setText("Live Mode: ON")
            
            # Disable capture button while live mode is on
            self._capture_button.setEnabled(False)
            
            self._status_bar.showMessage("Live mode started.")
        else:
            # Stop live mode
            self._live_update_timer.stop()
            self._live_mode_enabled = False
            self._live_button.setText("Live Mode: OFF")
            
            # Re-enable capture button
            self._capture_button.setEnabled(True)
            
            self._status_bar.showMessage("Live mode stopped.")
    
    def _update_live_waveforms(self):
        """Update the waveforms in live mode."""
        if not self._scope or not self._live_mode_enabled:
            return
        
        try:
            # Process each enabled channel
            for channel in self._live_channels:
                try:
                    # Get waveform data - using simplified version for speed
                    times, voltages = self._get_waveform_data_fast(channel)
                    
                    # Update the plot
                    self._plot_widget.update_plot(channel, times, voltages)
                except Exception as e:
                    print(f"Error updating channel {channel}: {e}")
                    # Don't show error message in status bar during live updates
                    # to avoid flickering, just print to console
            
            # Process application events to keep UI responsive
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error in live update: {e}")
            # If there's a critical error, stop live mode
            self._toggle_live_mode()
            self._status_bar.showMessage(f"Live mode stopped due to error: {e}")
    
    def _get_waveform_data_fast(self, channel):
        """
        Simplified waveform data acquisition for live mode (optimized for speed).
        
        Args:
            channel (int): Channel to capture
            
        Returns:
            tuple: (times, voltages) arrays
        """
        # Configure waveform acquisition (minimal commands)
        self._scope.write(f":WAV:SOUR CHAN{channel}")
        self._scope.write(":WAV:FORM BYTE")
        
        # Get the preamble only if needed (cache it for performance)
        preamble_str = self._scope.query(":WAV:PRE?")
        preamble = preamble_str.strip().split(',')
        
        # Extract scaling factors
        x_increment = float(preamble[4])
        x_origin = float(preamble[5])
        y_increment = float(preamble[7])
        y_origin = float(preamble[8])
        y_reference = float(preamble[9])
        
        # Get the raw data
        self._scope.write(":WAV:DATA?")
        raw_data = self._scope.read_raw()
        
        # Process header
        n = int(raw_data[1:2])
        data_size = int(raw_data[2:2+n])
        header_len = 2 + n
        
        # Extract and convert data
        data = raw_data[header_len:header_len+data_size]
        data_array = np.frombuffer(data, dtype=np.uint8)
        
        # Convert to voltages
        voltages = (data_array - y_origin - y_reference) * y_increment
        
        # Generate time axis
        times = np.arange(0, len(voltages)) * x_increment + x_origin
        
        return times, voltages
    
    @Slot()
    def _capture_waveforms(self):
        """Capture waveforms from the selected channels."""
        if not self._scope:
            return
        
        # Get selected channels
        channels = self._get_selected_channels()
        
        if not channels:
            QMessageBox.warning(self, "Capture Error", "Please select at least one channel.")
            return
        
        # First check which channels are actually enabled on the device
        enabled_channels = self._filter_enabled_channels(channels)
        
        if not enabled_channels:
            QMessageBox.warning(self, "Capture Error", 
                               "None of the selected channels are enabled on the oscilloscope. "
                               "Please enable at least one channel from the oscilloscope's front panel.")
            return
        
        # Disable capture button during capture
        self._capture_button.setEnabled(False)
        self._status_bar.showMessage(f"Capturing data from channels {enabled_channels}...")
        
        # Stop acquisition first to ensure stable data during retrieval
        try:
            self._scope.write(':STOP')
        except Exception as e:
            print(f"Error stopping acquisition: {e}")
        
        # Start capture threads sequentially to avoid resource conflicts
        self._capture_threads = []
        
        # Create all threads first without starting them
        for channel in enabled_channels:
            thread = WaveformCaptureThread(self._scope, channel)
            thread.capture_complete.connect(self._on_capture_complete)
            thread.capture_error.connect(self._on_capture_error)
            self._capture_threads.append(thread)
        
        # Start the first thread
        if self._capture_threads:
            self._current_capture_index = 0
            self._capture_threads[0].start()
    
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
    
    def _filter_enabled_channels(self, channels):
        """
        Filter the list of channels to only include those enabled on the device.
        
        Args:
            channels (list): List of channel numbers to check
            
        Returns:
            list: Channel numbers that are enabled on the device
        """
        enabled_channels = []
        try:
            for channel in channels:
                try:
                    channel_state = self._scope.query(f":CHAN{channel}:DISP?").strip()
                    if channel_state == "1" or channel_state.lower() == "on":
                        enabled_channels.append(channel)
                    else:
                        self._status_bar.showMessage(f"Channel {channel} is not enabled on the oscilloscope.", 3000)
                except Exception as e:
                    print(f"Error checking channel {channel} state: {e}")
                except Exception as e:
                    # If we can't check, proceed with user selection
                    print(f"Error checking channel states: {e}")
                    return channels
            return enabled_channels
        except Exception as e:
            # If we can't check, proceed with user selection
            print(f"Error checking channel states: {e}")
            return channels
    
    @Slot(tuple)
    def _on_capture_complete(self, data):
        """
        Handle completed waveform capture.
        
        Args:
            data (tuple): Tuple of (channel, times, voltages)
        """
        channel, times, voltages = data
        
        # Check if we actually got data
        if len(times) == 0 or len(voltages) == 0:
            self._status_bar.showMessage(f"No data received from channel {channel}.")
        else:
            self._plot_widget.update_plot(channel, times, voltages)
            self._status_bar.showMessage(f"Captured data from channel {channel}.")
        
        # Start the next thread if there are more channels to process
        self._current_capture_index += 1
        if self._current_capture_index < len(self._capture_threads):
            # Start the next thread
            self._capture_threads[self._current_capture_index].start()
        else:
            # All threads have been processed
            self._finish_capture_process()
    
    @Slot(str, str)
    def _on_capture_error(self, channel, error_msg):
        """
        Handle waveform capture error.
        
        Args:
            channel (str): Channel that had the error
            error_msg (str): Error message
        """
        QMessageBox.warning(self, "Capture Error", 
                           f"Error capturing data from channel {channel}: {error_msg}")
        
        # Continue to the next thread even if this one failed
        self._current_capture_index += 1
        if self._current_capture_index < len(self._capture_threads):
            # Start the next thread
            self._capture_threads[self._current_capture_index].start()
        else:
            # All threads have been processed
            self._finish_capture_process(has_errors=True)
    
    def _finish_capture_process(self, has_errors=False):
        """
        Complete the capture process.
        
        Args:
            has_errors (bool): Whether there were errors during capture
        """
        # Resume acquisition
        try:
            self._scope.write(':RUN')
        except Exception as e:
            print(f"Error resuming acquisition: {e}")
            
        self._capture_button.setEnabled(True)
        if has_errors:
            self._status_bar.showMessage("Capture completed with errors.")
        else:
            self._status_bar.showMessage("Capture complete.")
    
    @Slot()
    def _save_plot(self):
        """Save the current plot to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                self._plot_widget.save_plot(file_path)
                self._status_bar.showMessage(f"Plot saved to {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Error saving plot: {str(e)}")
    
    @Slot()
    def _clear_plot(self):
        """Clear the current plot."""
        self._plot_widget.clear_all()
        self._status_bar.showMessage("Plot cleared.")
    
    def closeEvent(self, event):
        """
        Handle window close event to clean up resources.
        
        Args:
            event: Close event from the window system
        """
        # Stop live mode if running
        if self._live_mode_enabled:
            self._toggle_live_mode()
            
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
    main_window = QuickTestApp()
    main_window.show()
    
    # Now that the UI is fully initialized and shown, populate the device list
    main_window._populate_device_list()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()