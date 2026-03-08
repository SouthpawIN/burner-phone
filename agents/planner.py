#!/usr/bin/env python3
"""
Planner Agent - Orchestrates complex tasks and builds prompts for Hermes
Decides when to handle locally vs escalate to server-side reasoning
"""

import json
import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

@dataclass
class ComplexTask:
    task_id: str
    user_request: str
    status: TaskStatus
    subtasks: List[Dict[str, Any]]
    context: Dict[str, Any]
    created_at: float
    updated_at: float

class PlannerAgent:
    """Orchestrates complex tasks and interfaces with Hermes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model", "senter-omni")
        self.escalation_threshold = config.get("escalation_threshold", 0.7)
        self.server_address = config.get("server", {}).get("address", "100.84.195.22")
        self.server_port = config.get("server", {}).get("port", 8080)
        
        self.hermes_endpoint = f"http://{self.server_address}:{self.server_port}/api/hermes/reason"
        
        # Active tasks storage
        self.active_tasks: Dict[str, ComplexTask] = {}
        
    def assess_complexity(self, user_request: str) -> float:
        """Assess complexity score (0-1) to decide escalation"""
        # Simple heuristic - would be replaced with actual analysis
        complexity_indicators = {
            "debug": 0.8,
            "fix": 0.7,
            "explain": 0.6,
            "analyze": 0.7,
            "create": 0.5,
            "build": 0.6,
            "design": 0.7,
            "optimize": 0.8,
            "refactor": 0.7,
        }
        
        request_lower = user_request.lower()
        max_score = 0
        
        for keyword, score in complexity_indicators.items():
            if keyword in request_lower:
                max_score = max(max_score, score)
        
        # Longer requests tend to be more complex
        length_score = min(len(user_request) / 500, 0.3)
        
        return min(max_score + length_score, 1.0)
    
    def should_escalate(self, complexity: float) -> bool:
        """Decide whether to escalate to Hermes based on complexity"""
        return complexity >= self.escalation_threshold
    
    def build_hermes_prompt(self, user_request: str, context: Dict[str, Any]) -> str:
        """Build optimized prompt for Hermes reasoning"""
        prompt = f"""You are Hermes, an advanced reasoning engine. Provide detailed, step-by-step analysis.

USER REQUEST:
{user_request}

CONTEXT:
{json.dumps(context, indent=2)}

INSTRUCTIONS:
1. Analyze the request thoroughly
2. Break down into logical steps  
3. Provide detailed reasoning for each step
4. Offer alternatives when applicable
5. Verify your solution

PROVIDE A COMPREHENSIVE RESPONSE WITH REASONING:"""
        return prompt
    
    def send_to_hermes(self, prompt: str, task_type: str = "reasoning") -> Dict[str, Any]:
        """Send reasoning request to Hermes on server"""
        try:
            response = requests.post(
                self.hermes_endpoint,
                json={
                    "prompt": prompt,
                    "task_type": task_type,
                    "timeout": 60
                },
                timeout=70
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Hermes API error: {response.status_code}",
                    "status": TaskStatus.FAILED.value
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Connection failed: {str(e)}",
                "status": TaskStatus.FAILED.value
            }
    
    def create_subtasks(self, user_request: str) -> List[Dict[str, Any]]:
        """Break down request into subtasks"""
        # This would use the local model to decompose tasks
        # Placeholder implementation
        return [
            {"id": 1, "description": "Analyze user request", "status": "pending"},
            {"id": 2, "description": "Determine required tools/actions", "status": "pending"},
            {"id": 3, "description": "Execute and verify", "status": "pending"},
        ]
    
    def process(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main planning loop"""
        start_time = time.time()
        context = context or {}
        
        # Assess complexity
        complexity = self.assess_complexity(user_request)
        
        response = {
            "complexity": complexity,
            "escalate": self.should_escalate(complexity),
            "input": user_request,
            "latency_ms": 0,
        }
        
        if self.should_escalate(complexity):
            # Build and send to Hermes
            prompt = self.build_hermes_prompt(user_request, context)
            hermes_response = self.send_to_hermes(prompt, task_type="reasoning")
            
            response["response"] = hermes_response.get("response", "No response from Hermes")
            response["source"] = "hermes"
        else:
            # Handle locally with subtasks
            subtasks = self.create_subtasks(user_request)
            response["subtasks"] = subtasks
            response["response"] = f"Handling locally with {len(subtasks)} subtasks"
            response["source"] = "local"
        
        response["latency_ms"] = int((time.time() - start_time) * 1000)
        return response


def main():
    """Test the planner agent"""
    config = {
        "model": "senter-omni",
        "escalation_threshold": 0.7,
        "server": {
            "address": "100.84.195.22",
            "port": 8080
        }
    }
    
    planner = PlannerAgent(config)
    
    test_requests = [
        "What time is it?",
        "Set a timer for 5 minutes",
        "Help me debug this async Python code that's deadlocking",
        "Explain quantum computing to a 10 year old"
    ]
    
    for request in test_requests:
        print(f"
Request: {request}")
        result = planner.process(request)
        print(f"Complexity: {result['complexity']:.2f}")
        print(f"Escalate: {result['escalate']}")
        print(f"Source: {result['source']}")
        print(f"Latency: {result['latency_ms']}ms")


if __name__ == "__main__":
    main()
