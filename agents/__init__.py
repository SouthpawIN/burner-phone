"""
Three-Agent System - Edge Intelligence Layer
Provides Frontend and Planner agents for distributed AI
"""

from agents.frontend import FrontendAgent
from agents.planner import PlannerAgent  
from agents.orchestrator import ThreeAgentOrchestrator

__all__ = [
    "FrontendAgent",
    "PlannerAgent",
    "ThreeAgentOrchestrator",
]

__version__ = "0.1.0"
