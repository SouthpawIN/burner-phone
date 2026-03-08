#!/usr/bin/env python3
"""
Orchestrator - Coordinates Frontend, Planner, and Hermes agents
Main entry point for the three-agent system
"""

import json
import time
import uuid
from typing import Dict, Any
from pathlib import Path

# Import our agents
from agents.frontend import FrontendAgent
from agents.planner import PlannerAgent

class ThreeAgentOrchestrator:
    """Coordinates the three-agent system"""
    
    def __init__(self, config_path: str = None):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize agents
        self.frontend = FrontendAgent(self.config.get("frontend", {}))
        self.planner = PlannerAgent(self.config.get("planner", {}))
        
        print("[Orchestrator] Three-agent system initialized")
        print(f"  - Frontend: {self.config.get('frontend', {}).get('model', 'qwen-omni')}")
        print(f"  - Planner: {self.config.get('planner', {}).get('model', 'senter-omni')}")
        print(f"  - Hermes: qwopus (server-side)")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "server": {
                "address": "100.84.195.22",
                "port": 8080
            },
            "frontend": {
                "model": "qwen-omni",
                "max_context": 8192
            },
            "planner": {
                "model": "senter-omni",
                "escalation_threshold": 0.7
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                # Deep merge configs
                for key in user_config:
                    if isinstance(user_config[key], dict) and key in default_config:
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]
        
        return default_config
    
    def process(self, user_input: str, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main processing pipeline"""
        start_time = time.time()
        task_id = str(uuid.uuid4())[:8]
        
        result = {
            "task_id": task_id,
            "input": user_input,
            "pipeline": [],
            "final_response": None,
            "total_latency_ms": 0
        }
        
        # Stage 1: Frontend Agent - Quick routing and simple tasks
        frontend_start = time.time()
        frontend_result = self.frontend.process(user_input)
        frontend_time = (time.time() - frontend_start) * 1000
        
        result["pipeline"].append({
            "agent": "frontend",
            "task_type": frontend_result.get("task_type"),
            "latency_ms": int(frontend_time)
        })
        
        # If frontend can handle it directly, return early
        if not frontend_result.get("needs_planner", False):
            result["final_response"] = frontend_result.get("response")
            result["total_latency_ms"] = int((time.time() - start_time) * 1000)
            return result
        
        # Stage 2: Planner Agent - Complex task orchestration
        planner_start = time.time()
        context = conversation_context or {"task_id": task_id}
        planner_result = self.planner.process(user_input, context)
        planner_time = (time.time() - planner_start) * 1000
        
        result["pipeline"].append({
            "agent": "planner",
            "complexity": planner_result.get("complexity", 0),
            "escalated": planner_result.get("escalate", False),
            "source": planner_result.get("source"),
            "latency_ms": int(planner_time)
        })
        
        # Get final response from planner
        result["final_response"] = planner_result.get("response")
        result["total_latency_ms"] = int((time.time() - start_time) * 1000)
        
        return result
    
    def run_demo(self):
        """Run demonstration with sample inputs"""
        demo_inputs = [
            "What's the weather today?",
            "Search for Python debugging tips",
            "Turn on bedroom lights",
            "Help me understand this complex algorithm optimization problem",
        ]
        
        print("
" + "="*60)
        print("THREE-AGENT SYSTEM DEMO")
        print("="*60)
        
        for user_input in demo_inputs:
            print(f"
[USER] {user_input}")
            print("-" * 40)
            
            result = self.process(user_input)
            
            print(f"Task ID: {result['task_id']}")
            print(f"Pipeline:")
            for stage in result["pipeline"]:
                agent_name = stage.get("agent", "unknown").upper()
                latency = stage.get("latency_ms", 0)
                print(f"  → {agent_name}: {latency}ms")
                if "task_type" in stage:
                    print(f"     Task Type: {stage['task_type']}")
                if "complexity" in stage:
                    print(f"     Complexity: {stage['complexity']:.2f}")
                    print(f"     Escalated: {stage.get('escalate', False)}")
            
            print(f"
Final Response: {result['final_response']}")
            print(f"Total Latency: {result['total_latency_ms']}ms")
            print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Three-Agent System Orchestrator")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--input", type=str, help="Single input to process")
    
    args = parser.parse_args()
    
    orchestrator = ThreeAgentOrchestrator(config_path=args.config)
    
    if args.demo:
        orchestrator.run_demo()
    elif args.input:
        result = orchestrator.process(args.input)
        print(json.dumps(result, indent=2))
    else:
        # Interactive mode
        print("
[Orchestrator] Ready! Enter queries (or 'quit' to exit)")
        print("="*60)
        
        while True:
            try:
                user_input = input("
[USER] ").strip()
                if user_input.lower() in ("quit", "exit", "q"):
                    break
                
                if not user_input:
                    continue
                    
                result = orchestrator.process(user_input)
                print(f"
[RESPONSE] {result['final_response']}")
                print(f"[LATENCY] {result['total_latency_ms']}ms")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
