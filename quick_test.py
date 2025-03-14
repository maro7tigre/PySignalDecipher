# -*- coding: utf-8 -*-
"""
Oscilloscope Quick Test Utility for PySignalDecipher.

A simple GUI tool to verify oscilloscope connectivity and capture waveforms.
This module provides a standalone application for testing oscilloscope connections
and capturing data, which can be used during development or by end users.
"""

import sys
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
from PySide6.QtCore import Qt, Slot, Signal, QThread


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
        self.address = address
        
    def run(self):
        """Connect to the oscilloscope using PyVISA."""
        rm = pyvisa.ResourceManager()
        try:
            # Open a connection to the oscilloscope with appropriate settings
            scope = rm.open_resource(self.address)
            
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
        self.scope = scope
        self.channel = channel
        
    def run(self):
        """Capture waveform data from the specified channel."""
        try:
            times, voltages = self._get_waveform_data(self.scope, self.channel)
            self.capture_complete.emit((self.channel, times, voltages))
        except Exception as e:
            self.capture_error.emit(str(self.channel), str(e))
            
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
        self.colors = ['yellow', 'blue', 'red', 'green']
        
        # Store channel data and axes objects
        self.channel_data = {}
        self.axes = {}
        
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
        self.channel_data[channel] = (times, voltages)
        
        # Adjust the subplot layout based on the number of channels
        self._adjust_layout()
        
        # Get or create axis for this channel
        if channel not in self.axes:
            # Create new subplot for this channel
            idx = len(self.axes) + 1
            ax = self.fig.add_subplot(len(self.channel_data), 1, idx)
            self.axes[channel] = ax
        
        # Get color for this channel
        color_idx = (channel - 1) % len(self.colors)
        
        # Clear current axis and plot data
        ax = self.axes[channel]
        ax.clear()
        ax.plot(times, voltages, color=self.colors[color_idx])
        ax.set_title(f'Channel {channel}')
        ax.set_ylabel('Voltage (V)')
        
        # Only show x-axis label on the bottom plot
        if channel == max(self.channel_data.keys()):
            ax.set_xlabel('Time (s)')
        
        ax.grid(True)
        
        # Update figure layout
        self.fig.tight_layout()
        self.draw()
    
    def _adjust_layout(self):
        """Adjust the subplot layout based on the number of channels."""
        # Clear all existing axes
        for ax in list(self.axes.values()):
            self.fig.delaxes(ax)
        
        # Create new set of axes
        self.axes = {}
        
        # Create a subplot for each channel
        channel_nums = sorted(self.channel_data.keys())
        for i, channel in enumerate(channel_nums):
            ax = self.fig.add_subplot(len(channel_nums), 1, i+1)
            self.axes[channel] = ax
            
            # Plot data
            times, voltages = self.channel_data[channel]
            color_idx = (channel - 1) % len(self.colors)
            ax.plot(times, voltages, color=self.colors[color_idx])
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
        if channel in self.channel_data:
            del self.channel_data[channel]
            
            # Readjust the layout
            self._adjust_layout()
            
            # Redraw
            self.fig.tight_layout()
            self.draw()
    
    def clear_all(self):
        """Clear all channels from the plot."""
        self.channel_data = {}
        
        # Clear all existing axes
        for ax in list(self.axes.values()):
            self.fig.delaxes(ax)
        
        self.axes = {}
        self.draw()
    
    def save_plot(self, filename):
        """
        Save the current plot to a file.
        
        Args:
            filename (str): Path to save the file
        """
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')


class QuickTestApp(QMainWindow):
    """Main application window for oscilloscope quick test."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        
        # Initialize instance variables
        self.scope = None
        self.capture_threads = []
        self.current_capture_index = 0
        
        # Set up the user interface
        self._setup_ui()
        self._connect_signals()
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher - Oscilloscope Quick Test")
        self.resize(900, 600)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create the connection group
        connection_group = self._create_connection_group()
        
        # Create the device info group
        device_group = self._create_device_info_group()
        
        # Create the capture controls group
        capture_group = self._create_capture_group()
        
        # Create the plot widget
        self.plot_widget = WaveformPlotter(self.central_widget, width=8, height=4)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Please connect to an oscilloscope.")
        
        # Add widgets to main layout
        main_layout.addWidget(connection_group)
        main_layout.addWidget(device_group)
        main_layout.addWidget(capture_group)
        main_layout.addWidget(self.plot_widget, 1)
    
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
        self.address_label = QLabel("Select Device:")
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.refresh_button = QPushButton("Refresh Devices")
        
        device_selection_layout.addWidget(self.address_label)
        device_selection_layout.addWidget(self.device_combo, 1)
        device_selection_layout.addWidget(self.refresh_button)
        
        # Connect button in its own row
        self.connect_button = QPushButton("Connect")
        self.connect_button.setMinimumHeight(30)
        
        connection_layout.addLayout(device_selection_layout)
        connection_layout.addWidget(self.connect_button)
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
        
        self.device_info = QTextEdit()
        self.device_info.setReadOnly(True)
        self.device_info.setMaximumHeight(100)
        
        device_layout.addWidget(self.device_info)
        device_group.setLayout(device_layout)
        
        return device_group
    
    def _create_capture_group(self):
        """
        Create the capture controls group box.
        
        Returns:
            QGroupBox: The capture controls group box
        """
        capture_group = QGroupBox("Capture Controls")
        capture_layout = QHBoxLayout()
        
        self.ch1_checkbox = QCheckBox("Channel 1")
        self.ch1_checkbox.setChecked(True)
        self.ch2_checkbox = QCheckBox("Channel 2")
        self.ch2_checkbox.setChecked(True)
        self.ch3_checkbox = QCheckBox("Channel 3")
        self.ch4_checkbox = QCheckBox("Channel 4")
        self.capture_button = QPushButton("Capture Waveforms")
        self.save_button = QPushButton("Save Plot")
        self.clear_button = QPushButton("Clear Plot")
        
        capture_layout.addWidget(self.ch1_checkbox)
        capture_layout.addWidget(self.ch2_checkbox)
        capture_layout.addWidget(self.ch3_checkbox)
        capture_layout.addWidget(self.ch4_checkbox)
        capture_layout.addWidget(self.capture_button)
        capture_layout.addWidget(self.save_button)
        capture_layout.addWidget(self.clear_button)
        capture_group.setLayout(capture_layout)
        
        # Initial state
        self.capture_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        return capture_group
    
    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.connect_button.clicked.connect(self._connect_to_scope)
        self.refresh_button.clicked.connect(self._populate_device_list)
        self.capture_button.clicked.connect(self._capture_waveforms)
        self.save_button.clicked.connect(self._save_plot)
        self.clear_button.clicked.connect(self._clear_plot)
    
    def _populate_device_list(self):
        """Populate the device combo box with available VISA resources."""
        self.device_combo.clear()
        self.status_bar.showMessage("Searching for devices...")
        
        try:
            rm = pyvisa.ResourceManager()
            devices = rm.list_resources()
            
            if not devices:
                self.device_combo.addItem("No devices found")
                self.status_bar.showMessage("No devices found.")
                self.connect_button.setEnabled(False)
                return
            
            # Add devices to combo box
            for device in devices:
                self.device_combo.addItem(device)
                
            self.connect_button.setEnabled(True)
            self.status_bar.showMessage(f"Found {len(devices)} device(s).")
            
            # Display in device info text area as well
            device_text = "Available devices:\n" + "\n".join(devices)
            self.device_info.setText(device_text)
            
        except Exception as e:
            self.device_info.setText(f"Error finding devices: {str(e)}")
            self.status_bar.showMessage("Error finding devices.")
            self.connect_button.setEnabled(False)
    
    @Slot()
    def _connect_to_scope(self):
        """Connect to the oscilloscope using the selected address."""
        if self.device_combo.count() == 0 or self.device_combo.currentText() == "No devices found":
            QMessageBox.warning(self, "Connection Error", "No devices available to connect.")
            return
        
        address = self.device_combo.currentText()
        if not address:
            QMessageBox.warning(self, "Connection Error", "Please select a device.")
            return
        
        self.status_bar.showMessage("Connecting to oscilloscope...")
        self.connect_button.setEnabled(False)
        
        # Connect to the oscilloscope in a separate thread
        self.connection_thread = OscilloscopeConnectionThread(address)
        self.connection_thread.connection_successful.connect(self._on_connection_successful)
        self.connection_thread.connection_failed.connect(self._on_connection_failed)
        self.connection_thread.start()
    
    @Slot(object, str)
    def _on_connection_successful(self, scope, idn):
        """
        Handle successful oscilloscope connection.
        
        Args:
            scope: The connected oscilloscope resource
            idn (str): Identification string from the oscilloscope
        """
        self.scope = scope
        self.device_info.setText(f"Connected to: {idn}\nAddress: {self.device_combo.currentText()}")
        self.status_bar.showMessage("Connected to oscilloscope.")
        
        # Enable capture controls
        self.capture_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.connect_button.setText("Disconnect")
        self.connect_button.setEnabled(True)
        self.connect_button.clicked.disconnect(self._connect_to_scope)
        self.connect_button.clicked.connect(self._disconnect_from_scope)
        
        # Configure oscilloscope for optimal performance
        try:
            # Clear any pending operations
            self.scope.write('*CLS')
            
            # Run acquisition to get fresh data
            self.scope.write(':RUN')
            
            # Update status message
            self.status_bar.showMessage("Connected and configured for acquisition.")
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
        
        self.status_bar.showMessage("Connection failed.")
        self.connect_button.setEnabled(True)
    
    @Slot()
    def _disconnect_from_scope(self):
        """Disconnect from the oscilloscope."""
        if self.scope:
            try:
                # Return to local control before closing
                self.scope.write(':KEY:FORC')
                
                # Close the connection
                self.scope.close()
            except:
                pass
            self.scope = None
        
        # Update UI
        self.device_info.clear()
        self.capture_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.connect_button.setText("Connect")
        self.connect_button.clicked.disconnect(self._disconnect_from_scope)
        self.connect_button.clicked.connect(self._connect_to_scope)
        
        self.status_bar.showMessage("Disconnected from oscilloscope.")
    
    @Slot()
    def _capture_waveforms(self):
        """Capture waveforms from the selected channels."""
        if not self.scope:
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
        self.capture_button.setEnabled(False)
        self.status_bar.showMessage(f"Capturing data from channels {enabled_channels}...")
        
        # Stop acquisition first to ensure stable data during retrieval
        try:
            self.scope.write(':STOP')
        except Exception as e:
            print(f"Error stopping acquisition: {e}")
        
        # Start capture threads sequentially to avoid resource conflicts
        self.capture_threads = []
        
        # Create all threads first without starting them
        for channel in enabled_channels:
            thread = WaveformCaptureThread(self.scope, channel)
            thread.capture_complete.connect(self._on_capture_complete)
            thread.capture_error.connect(self._on_capture_error)
            self.capture_threads.append(thread)
        
        # Start the first thread
        if self.capture_threads:
            self.current_capture_index = 0
            self.capture_threads[0].start()
    
    def _get_selected_channels(self):
        """
        Get list of selected channels from checkboxes.
        
        Returns:
            list: Channel numbers that are selected
        """
        channels = []
        if self.ch1_checkbox.isChecked():
            channels.append(1)
        if self.ch2_checkbox.isChecked():
            channels.append(2)
        if self.ch3_checkbox.isChecked():
            channels.append(3)
        if self.ch4_checkbox.isChecked():
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
                    channel_state = self.scope.query(f":CHAN{channel}:DISP?").strip()
                    if channel_state == "1" or channel_state.lower() == "on":
                        enabled_channels.append(channel)
                    else:
                        self.status_bar.showMessage(f"Channel {channel} is not enabled on the oscilloscope.", 3000)
                except Exception as e:
                    print(f"Error checking channel {channel} state: {e}")
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
            self.status_bar.showMessage(f"No data received from channel {channel}.")
        else:
            self.plot_widget.update_plot(channel, times, voltages)
            self.status_bar.showMessage(f"Captured data from channel {channel}.")
        
        # Start the next thread if there are more channels to process
        self.current_capture_index += 1
        if self.current_capture_index < len(self.capture_threads):
            # Start the next thread
            self.capture_threads[self.current_capture_index].start()
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
        self.current_capture_index += 1
        if self.current_capture_index < len(self.capture_threads):
            # Start the next thread
            self.capture_threads[self.current_capture_index].start()
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
            self.scope.write(':RUN')
        except Exception as e:
            print(f"Error resuming acquisition: {e}")
            
        self.capture_button.setEnabled(True)
        if has_errors:
            self.status_bar.showMessage("Capture completed with errors.")
        else:
            self.status_bar.showMessage("Capture complete.")
    
    @Slot()
    def _save_plot(self):
        """Save the current plot to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                self.plot_widget.save_plot(file_path)
                self.status_bar.showMessage(f"Plot saved to {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Error saving plot: {str(e)}")
    
    @Slot()
    def _clear_plot(self):
        """Clear the current plot."""
        self.plot_widget.clear_all()
        self.status_bar.showMessage("Plot cleared.")
    
    def closeEvent(self, event):
        """
        Handle window close event to clean up resources.
        
        Args:
            event: Close event from the window system
        """
        if self.scope:
            try:
                # Return to local control before closing
                self.scope.write(':KEY:FORC')
                self.scope.close()
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