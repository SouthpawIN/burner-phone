#!/usr/bin/env python3
"""
Frontend Agent - Quick, responsive interaction layer
Handles simple tasks without breaking conversation flow
"""

import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    WEB_SEARCH = "web_search"
    SMART_HOME = "smart_home"
    APP_CONTROL = "app_control"
    SIMPLE_QA = "simple_qa"
    ESCALATE = "escalate"  # Send to planner

@dataclass
class Task:
    task_id: str
    task_type: TaskType
    content: str
    priority: str = "normal"
    metadata: Dict[str, Any] = None

class FrontendAgent:
    """Handles quick, responsive tasks on the edge"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model", "qwen-omni")
        self.max_context = config.get("max_context", 8192)
        self.server_address = config.get("server", {}).get("address", "100.84.195.22")
        self.server_port = config.get("server", {}).get("port", 8080)
        
        # Simple task patterns for quick routing
        self.patterns = {
            "weather": ["weather", "temperature", "forecast", "degree", "sunny", "rainy"],
            "time": ["time", "date", "day", "what time", "clock"],
            "web_search": ["search for", "find", "look up", "google"],
            "smart_home": ["light", "thermostat", "lock", "unlock", "turn on", "turn off"],
            "app_control": ["open", "launch", "close", "app", "browser"],
        }
        
    def route_task(self, user_input: str) -> TaskType:
        """Quick routing based on simple pattern matching"""
        user_lower = user_input.lower()
        
        # Check for web search patterns
        if any(p in user_lower for p in self.patterns["web_search"]):
            return TaskType.WEB_SEARCH
        
        # Check for smart home
        if any(p in user_lower for p in self.patterns["smart_home"]):
            return TaskType.SMART_HOME
            
        # Check for app control
        if any(p in user_lower for p in self.patterns["app_control"]):
            return TaskType.APP_CONTROL
            
        # Check for simple info queries
        if any(p in user_lower for p in self.patterns["weather"] + self.patterns["time"]):
            return TaskType.SIMPLE_QA
            
        # Default: escalate to planner for anything complex
        return TaskType.ESCALATE
    
    def handle_web_search(self, query: str) -> str:
        """Handle web searches using MCP tools"""
        # This would integrate with MCP web search tool
        # For now, return a placeholder response
        return f"[Web Search] Searching for: {query}"
    
    def handle_smart_home(self, command: str) -> str:
        """Handle smart home commands"""
        # This would integrate with Home Assistant or similar
        return f"[Smart Home] Processing: {command}"
    
    def handle_app_control(self, action: str) -> str:
        """Handle app open/close requests"""
        # This would use phone agent to launch apps
        return f"[App Control] Action: {action}"
    
    def handle_simple_qa(self, question: str) -> str:
        """Handle simple Q&A using local model"""
        # Use Qwen Omni for quick responses
        prompt = f"Provide a brief, direct answer to this question:

{question}

Answer:"
        
        # This would call the local model inference
        # Placeholder for now
        return f"[Simple QA] Answering: {question}"
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """Main processing loop"""
        start_time = time.time()
        
        # Route the task
        task_type = self.route_task(user_input)
        
        response = {
            "task_type": task_type.value,
            "input": user_input,
            "latency_ms": 0,
        }
        
        if task_type == TaskType.WEB_SEARCH:
            response["response"] = self.handle_web_search(user_input)
            
        elif task_type == TaskType.SMART_HOME:
            response["response"] = self.handle_smart_home(user_input)
            
        elif task_type == TaskType.APP_CONTROL:
            response["response"] = self.handle_app_control(user_input)
            
        elif task_type == TaskType.SIMPLE_QA:
            response["response"] = self.handle_simple_qa(user_input)
            
        elif task_type == TaskType.ESCALATE:
            # Signal to planner agent
            response["response"] = "Escalating to planner for complex task"
            response["needs_planner"] = True
        
        response["latency_ms"] = int((time.time() - start_time) * 1000)
        return response


def main():
    """Test the frontend agent"""
    config = {
        "model": "qwen-omni",
        "max_context": 8192,
        "server": {
            "address": "100.84.195.22",
            "port": 8080
        }
    }
    
    agent = FrontendAgent(config)
    
    test_inputs = [
        "What's the weather today?",
        "Search for latest AI news",
        "Turn on the living room lights",
        "Open Chrome browser",
        "Help me debug this complex Python script"
    ]
    
    for user_input in test_inputs:
        print(f"
Input: {user_input}")
        result = agent.process(user_input)
        print(f"Task Type: {result['task_type']}")
        print(f"Response: {result['response']}")
        print(f"Latency: {result['latency_ms']}ms")


if __name__ == "__main__":
    main()
