# Workspaces package for PySignalDecipher with command system integration

from .base_workspace import BaseWorkspace
from .basic_workspace import BasicSignalWorkspace
from .protocol_workspace import ProtocolDecoderWorkspace
from .pattern_workspace import PatternRecognitionWorkspace
from .separation_workspace import SignalSeparationWorkspace
from .origin_workspace import SignalOriginWorkspace
from .advanced_workspace import AdvancedAnalysisWorkspace

__all__ = [
    'BaseWorkspace',
    'BasicSignalWorkspace',
    'ProtocolDecoderWorkspace',
    'PatternRecognitionWorkspace',
    'SignalSeparationWorkspace',
    'SignalOriginWorkspace',
    'AdvancedAnalysisWorkspace',
]