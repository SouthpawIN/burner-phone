"""Universal Device Backends for Hermes Phone Agent"""

from .device_base import (
    DeviceBackend,
    DeviceConfig,
    create_backend,
    detect_device_type
)
from .termux_backend import TermuxBackend
from .adb_backend import ADBBackend
from .emulator_backend import EmulatorBackend

__all__ = [
    'DeviceBackend',
    'DeviceConfig', 
    'create_backend',
    'detect_device_type',
    'TermuxBackend',
    'ADBBackend',
    'EmulatorBackend'
]