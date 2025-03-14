# PySignalDecipher: Advanced Signal Analysis & Protocol Reverse Engineering Platform

## 1. Project Overview

PySignalDecipher is a comprehensive signal analysis application designed for advanced signal processing, protocol decoding, and reverse engineering. Built with Python and leveraging PyVISA for hardware integration, this platform connects to oscilloscopes (specifically the Rigol) and provides a powerful suite of tools for real-time signal capture, analysis, transformation, and protocol decoding.

The platform is designed for engineers, researchers, and reverse engineering specialists who need to analyze complex signals, identify and decode communication protocols, separate mixed signals, and detect patterns within waveforms. PySignalDecipher aims to provide professional-grade capabilities while maintaining an intuitive, non-overwhelming user interface.

## 2. System Architecture

### 2.1 Core Components

The application is built using a modular architecture with these primary components:

1. **Hardware Interface Layer**
   - PyVISA-based communication with oscilloscopes
   - Hardware abstraction layer for device configuration
   - Real-time data streaming and acquisition control

2. **Signal Management System**
   - Registry for all signal sources (live, virtual, uploaded)
   - Version tracking for signal transformations
   - Signal relationship management (parent-child)
   - Import/export functionality for various formats

3. **Signal Processing Engine**
   - Filtering operations (LP, HP, BP, etc.)
   - Transformation tools (FFT, wavelet, etc.)
   - Signal mathematics (add, subtract, multiply)
   - Custom processing chain support

4. **Protocol Analysis Module**
   - Standard protocol decoders (RS232, I2C, SPI, etc.)
   - Parameter inference (baud rate, bit length)
   - Custom protocol definition capability
   - Error-tolerant decoding for noisy signals

5. **Pattern Recognition System**
   - Template-based pattern matching
   - Frequency and time-domain pattern detection
   - Pattern extraction and removal
   - Anomaly detection in regular patterns

6. **Workspace Management System**
   - Project saving/loading
   - Configuration management
   - Signal and analysis history
   - Export of results and reports

7. **Multi-Window GUI Framework**
   - Flexible, dockable window system
   - Theme and display customization
   - Window synchronization for related views
   - Multi-monitor support

### 2.2 Architecture Diagram

```
┌─────────────────┐     ┌─────────────────────────────────────────┐
│  Rigol DS1202Z  │◄───►│           Hardware Interface            │
└─────────────────┘     │             (PyVISA Layer)              │
                        └─────────────────┬───────────────────────┘
                                          │
                        ┌─────────────────▼────────────────────────┐
                        │         Signal Management System         │
                        └┬────────────┬───────────┬───────────┬────┘
                         │            │           │           │
         ┌───────────────▼─┐  ┌───────▼────┐   ┌──▼─────────┐ │
         │Signal Processing│  │  Protocol  │   │ Pattern    │ │
         │     Engine      │  │  Analysis  │   │Recognition │ │
         └─┬─────────┬─────┘  └──┬─────────┘   └──────┬─────┘ │
           │         │           │                    │       │
           │         │           │                    │       │
┌──────────▼─────────▼───────────▼────────────────────▼───────▼──────┐
│                  Workspace Management System                       │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────────────┐
│                Multi-Window GUI Framework                          │
└────────────────────────────────────────────────────────────────────┘
```

## 3. Key Features

### 3.1 Signal Acquisition & Management

- **Multi-Channel Support**: Capture from multiple oscilloscope channels simultaneously
- **Trigger Configuration**: Advanced trigger options for precise captures
- **Signal Import/Export**: Support for various file formats (.csv, .wav, binary)
- **Signal Metadata**: Store and track acquisition parameters and signal history

### 3.2 Signal Processing & Transformation

- **Digital Filters**: Low-pass, high-pass, band-pass, notch with adjustable parameters
- **Spectral Analysis**: FFT with various window functions, spectrogram visualization
- **Signal Mathematics**: Add, subtract, multiply, integrate, differentiate signals
- **Statistical Analysis**: Histograms, probability distributions, SNR measurements

### 3.3 Protocol Decoding & Analysis

- **Standard Protocol Support**: RS232/UART, I2C, SPI, CAN, USB, etc.
- **Intelligent Parameter Detection**: Auto-detection of baud rates, data formats
- **Error Tolerance**: Configurable error margins for noisy signals
- **Protocol Timing Analysis**: Analyze timing aspects of protocols
- **Custom Protocol Definition**: Create and save definitions for proprietary protocols
- **Bidirectional Conversion**: Generate reference signals from known data and compare against captured waveforms
- **Protocol Simulation**: Input known data values to see how they would appear as signals

### 3.4 Pattern Recognition & Removal

- **Template Creation**: Select and define signal patterns of interest
- **Auto detect paterns** :  Automatically detect repeating paterns in your signal
- **Pattern Matching**: Find occurrences of patterns throughout the signal
- **Pattern Extraction**: Remove/seperate identified patterns from signals
- **Residual Analysis**: Analyze remaining signal components after pattern removal
- **Pattern Library**: Save and reuse pattern definitions

### 3.5 Signal Separation

- **Rule-Based Separation**: Define criteria for identifying component signals
- **Frequency Domain Separation**: Isolate signals based on spectral characteristics(degital/analog, frequency, amplitude....)
- **Adaptive Filtering**: Dynamically adjust separation parameters
- **Interactive Separation**: Manual guidance of separation algorithms
- **Source Separation**: Advanced algorithms for mixed signal separation

### 3.6 Advanced Analysis Tools

- **Correlation Analysis**: Cross-correlation between signals
- **Eye Diagram Analysis**: For digital communication quality assessment
- **Jitter Analysis**: Measure and characterize timing variations
- **Signal Quality Metrics**: SNR, THD, SINAD measurements
- **Statistical Tools**: Histogram, PDF, CDF analysis

### 3.7 Signal Origin Detection

- **Source Localization**: Determine which end of a cable/bus originated a signal
- **Propagation Analysis**: Measure signal propagation times and characteristics
- **Direction Finding**: Identify signal direction based on phase relationships
- **Reflection Mapping**: Analyze reflections to locate discontinuities
- **Time-Domain Reflectometry**: Cable and transmission line analysis techniques
- **Multi-Point Correlation**: Compare signals across different test points

## 4. User Interface Design

### 4.1 UI Philosophy

The UI is designed around these principles:
- **Modular Windows**: Separate specialized functions into dedicated views
- **Progressive Disclosure**: Start with essential tools, reveal complexity as needed
- **Contextual Controls**: Show only relevant controls for current task
- **Visual Feedback**: Clear indication of signal relationships and transformations
- **Customizable Layout**: Arrange windows according to workflow needs

### 4.2 Tabbed Module Architecture

The interface is organized around a tab-based system, where each tab represents a completely separate workspace with dedicated tools for specific tasks. This approach maintains comprehensive functionality while preventing user overwhelm by compartmentalizing tools into task-specific workspaces.

```
┌─────────────────────────────────────────────────────────────────────┐
│ ┌─────┐ ┌───────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────┐ │
│ │Basic│ │Protocol Decode│ │Pattern Rec.│ │Signal Split.│ │Advanced│ │
└─┬─────┴─┬───────────────┴─┬────────────┴─┬─────────────┴─┬────────┴─┘
  │       │                 │              │               │
  │       │                 │              │               │
  ▼       ▼                 ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    Active Module Workspace                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Each tab opens a specialized workspace designed for a specific analysis workflow:

#### 4.2.1 Basic Signal Workspace

The starting point for most signal analysis tasks:

- **Control Panel**: Hardware connection and acquisition settings
- **Channel Display**: Multi-channel waveform visualization with basic measurements
- **Signal Timeline**: Navigate through captured signal history
- **Quick Measurements**: Common measurements (frequency, amplitude, etc.)
- **Basic Filters**: Simple noise reduction and signal conditioning


#### 4.2.2 Protocol Decoder Workspace

Specialized environment for protocol analysis and reverse engineering:

- **Protocol Selection**: Library of standard protocols with configuration options
- **Parameter Tuning**: Adjust baud rates, bit formats, etc. with visual feedback
- **Decoded Data View**: View interpreted data in various formats (hex, ASCII, binary)
- **Timing Correlation**: Link decoded data to original signal features
- **Custom Protocol Builder**: Tools for defining new protocol specifications
- **Error Analysis**: Identify and correct decoding errors
- **Reference Signal Generation**: Generate ideal waveforms from known data for comparison

#### 4.2.3 Pattern Recognition & Removal Workspace

Dedicated environment for identifying and manipulating signal patterns:

- **Pattern Selection Tools**: Methods for defining patterns of interest
- **Pattern Matching**: Detection algorithms with configurable parameters
- **Pattern Library**: Save and reuse identified patterns
- **Pattern Removal**: Tools for subtracting or filtering out patterns
- **Residual Analysis**: Examine what remains after pattern removal
- **Pattern Statistics**: Frequency of occurrence and variation metrics

#### 4.2.4 Signal Separation Workspace

Tools for isolating and extracting component signals:

- **Separation Methods**: Different algorithms for signal separation
- **Rule Builder**: Visual interface for defining separation criteria
- **Component Viewer**: Display and analyze separated components
- **Interactive Guides**: Manual assistance for separation algorithms
- **Frequency Analysis**: Spectral view of original and separated signals
- **Component Export**: Save separated signals as new sources

#### 4.2.5 Signal Origin Analyzer Workspace

Specialized workspace for determining the source of signals in a system by analyzing dual-channel inputs:

- **Differential Analysis**: Compare signals from two test points to determine direction
- **Time Delay Measurement**: Calculate propagation delays with high precision
- **Source Identification**: Pinpoint which component is generating specific signals
- **Reflection Analysis**: Identify reflections and calculate distances to discontinuities
- **Signal Path Mapping**: Visualize signal propagation through a system
- **Fault Location**: Determine the physical location of faults in cables or circuits

#### 4.2.6 Advanced Analysis Workspace

Complex tools for specialized analysis needs:

- **Signal Flow Canvas**: Visual programming interface for custom processing
- **Advanced Filters**: Sophisticated filtering and transform options
- **Correlation Tools**: Cross-correlation between multiple signals
- **Statistical Analysis**: In-depth signal statistics and distributions
- **Scripting Interface**: Custom Python script execution for automation
- **Batch Processing**: Apply operations to multiple signals

### 4.3 Workspace Interaction and Common Elements

While each tab provides a dedicated workspace, the system maintains these consistent elements:

1. **Global Signal Repository**: Access all signals from any workspace tab
2. **Cross-Workspace References**: Use results from one workspace in another
3. **Consistent Tools**: Common tools maintain the same behavior across workspaces
4. **Status Indicators**: Hardware status, processing status, and memory usage
5. **Quick Access Toolbar**: Frequently used functions available in all workspaces

### 4.4 User Experience Benefits of Tabbed Workspaces

The tabbed module approach offers several key advantages:

1. **Task-Focused Interfaces**: Each workspace presents only the tools relevant to a specific analysis task, reducing cognitive load and interface clutter.

2. **Progressive Complexity**: Users can start with the basic workspace and move to specialized modules as their needs evolve, creating a natural learning progression.

3. **Efficient Screen Use**: Each workspace optimizes its layout for its specific purpose, maximizing the utility of available screen space.

4. **Workflow Optimization**: Tabs follow the natural progression of signal analysis tasks, from basic acquisition to specialized analysis.

5. **Contextual Tool Access**: Tools appear in the context where they're most useful, with appropriate options and parameters for the specific task.

6. **Reduced Visual Overwhelm**: By compartmentalizing functionality, users aren't presented with dozens of tools and options simultaneously.

7. **Specialized Visualizations**: Each workspace can implement visualizations specifically designed for its analytical purpose.

8. **Customization Within Boundaries**: Users can customize each workspace while maintaining the overall organizational structure.

9. **Clear Mental Model**: The tab metaphor creates a clear mental model of separate tools for separate jobs, aiding in learning and mastery.

10. **Easy Navigation**: Users can quickly switch between completely different analysis modes with a single click rather than reconfiguring a complex interface.

## 5. Workflow Examples

### 5.1 Protocol Reverse Engineering Workflow

1. **Signal Capture**: Acquire signal from oscilloscope
2. **Signal Cleanup**: Apply appropriate filtering to reduce noise
3. **Protocol Detection**: Run auto-detection of common protocols
4. **Parameter Tuning**: Adjust protocol parameters for accurate decoding
5. **Data Extraction**: View and export decoded protocol data
6. **Documentation**: Save protocol parameters and example captures

### 5.2 Pattern Removal Workflow

1. **Signal Capture**: Acquire complex signal with multiple components
2. **Pattern Selection**: Identify a repeating pattern in the signal
3. **Pattern Refinement**: Adjust detection parameters for accuracy
4. **Pattern Removal**: Generate a new signal with the pattern removed
5. **Residual Analysis**: Analyze the remaining signal components
6. **Iterative Cleaning**: Repeat for other identified patterns

### 5.3 Signal Separation Workflow

1. **Signal Capture**: Acquire mixed signal from source
2. **Spectral Analysis**: View frequency components of the signal
3. **Separation Rule Definition**: Create rules for identifying components
4. **Interactive Separation**: Guide the separation process with feedback
5. **Component Analysis**: Analyze each separated component
6. **Protocol Analysis**: Run protocol detection on isolated components

### 5.4 Protocol Verification Workflow

1. **Signal Capture**: Acquire signal from communication channel
2. **Protocol Detection**: Identify protocol parameters and decode data
3. **Known Data Entry**: Input expected data values for comparison
4. **Reference Generation**: Generate ideal protocol waveforms from known data
5. **Signal Comparison**: Overlay reference and actual signals
6. **Deviation Analysis**: Identify timing or voltage deviations between signals
7. **Parameter Refinement**: Adjust protocol parameters to improve matching

### 5.5 Custom Protocol Definition

1. **Signal Capture**: Acquire unknown protocol signal
2. **Timing Analysis**: Measure bit intervals and frame patterns
3. **Protocol Builder**: Define frame structure and bit encoding
4. **Test Decoding**: Apply custom definition to the signal
5. **Parameter Optimization**: Refine parameters for clean decoding
6. **Protocol Saving**: Store custom protocol for future use

### 5.5 Signal Origin Detection Workflow

1. **Dual-Channel Setup**: Connect probes to different points in the system
2. **Synchronized Capture**: Acquire signals from both channels simultaneously
3. **Phase Comparison**: Analyze phase relationships between the channels
4. **Timing Analysis**: Measure propagation delays and signal characteristics
5. **Source Determination**: Calculate likely signal source and direction
6. **Distance Calculation**: For transmission line analysis, calculate distance to features
7. **Fault Localization**: If applicable, determine locations of discontinuities or faults

## 6. Technical Specifications

### 6.1 Software Stack

- **Language**: Python 3.9+
- **Hardware Interface**: PyVISA with appropriate backends
- **GUI Framework**: PySide6 (Qt for Python)
- **Signal Processing**: NumPy, SciPy, PyWavelets
- **Plotting**: PyQtGraph for performance-critical displays
- **Protocol Libraries**: Custom implementations + community libraries
- **Data Management**: HDF5 for efficient signal storage

### 6.2 Performance Considerations

- **Multi-threading**: Separate UI from processing threads
- **GPU Acceleration**: Optional for FFT and other intensive operations
- **Memory Management**: Efficient handling of large signal datasets
- **Streaming Processing**: Process signals in chunks for reduced memory usage

### 6.3 Extensibility

- **Plugin System**: Support for user-created extensions
- **Python API**: Scriptable interface for automation
- **Custom DSP**: Interface for user-defined processing algorithms
- **Hardware Support**: Extensible to additional oscilloscope models

## 7. Conclusion

PySignalDecipher represents a comprehensive approach to signal analysis and protocol reverse engineering. By combining powerful DSP capabilities with an intuitive, task-oriented interface, the application aims to provide experts with the tools they need while remaining accessible to new users.

The modular architecture ensures that the system can evolve over time, with new protocols, analysis methods, and visualization techniques added as needed. The focus on flexible, customizable workflows allows users to adapt the tool to their specific needs rather than forcing them into rigid usage patterns.

This project leverages Python's rich ecosystem of scientific and engineering libraries while providing the performance needed for real-time signal analysis through careful optimization and hardware acceleration where appropriate.

---
