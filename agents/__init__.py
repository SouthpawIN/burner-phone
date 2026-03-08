"""
Three-Agent System - Edge Intelligence Layer
Provides Frontend, Planner, PhoneControl, and VoiceActivation agents
"""

from agents.frontend import FrontendAgent
from agents.planner import PlannerAgent  
from agents.orchestrator import ThreeAgentOrchestrator
from agents.phone_control import PhoneControlAgent
from agents.voice_activation import VoiceActivationSystem, ActivationMethod, ActivationEvent

__all__ = [
    "FrontendAgent",
    "PlannerAgent",
    "ThreeAgentOrchestrator",
    "PhoneControlAgent",
    "VoiceActivationSystem",
    "ActivationMethod",
    "ActivationEvent",
]

__version__ = "0.2.0"
