#!/usr/bin/env python3
"""
MCP Integration for Context-Aware Agent
Connects the agent connection manager with MCP memory system
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from context_aware_agent import get_agent, get_agent_status, execute_command_with_context

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPAgentIntegration:
    """Integrates context-aware agent with MCP memory system"""
    
    def __init__(self):
        self.agent = get_agent()
        self.memory_keys = {
            "connection_context": "agent_connection_context",
            "command_history": "agent_command_history",
            "environment_state": "agent_environment_state"
        }
    
    def store_connection_context_in_mcp(self, mcp_memory_store_func):
        """Store connection context in MCP memory"""
        try:
            context_data = self.agent.get_connection_status()
            context_json = json.dumps(context_data, indent=2)
            
            # Store in MCP memory
            mcp_memory_store_func(
                key=self.memory_keys["connection_context"],
                value=context_json
            )
            
            logger.info("Connection context stored in MCP memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store connection context in MCP: {e}")
            return False
    
    def load_connection_context_from_mcp(self, mcp_memory_retrieve_func):
        """Load connection context from MCP memory"""
        try:
            # Retrieve from MCP memory
            context_json = mcp_memory_retrieve_func(
                key=self.memory_keys["connection_context"]
            )
            
            if context_json:
                context_data = json.loads(context_json)
                
                # Restore connection settings if available
                if context_data.get('connection_type') == 'ssh':
                    self.agent.setup_ssh_connection(
                        host=context_data.get('ssh_host'),
                        user=context_data.get('ssh_user'),
                        key_path=context_data.get('ssh_key_path'),
                        port=context_data.get('ssh_port', 22)
                    )
                elif context_data.get('connection_type') == 'runpod':
                    self.agent.setup_runpod_connection(
                        pod_id=context_data.get('runpod_pod_id'),
                        key_path=context_data.get('ssh_key_path')
                    )
                
                logger.info("Connection context loaded from MCP memory")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load connection context from MCP: {e}")
            return False
    
    def store_command_history(self, command_result: Dict[str, Any], mcp_memory_store_func, mcp_memory_retrieve_func):
        """Store command execution history in MCP memory"""
        try:
            # Get existing history
            try:
                history_json = mcp_memory_retrieve_func(
                    key=self.memory_keys["command_history"]
                )
                history = json.loads(history_json) if history_json else []
            except:
                history = []
            
            # Add new command result
            history.append(command_result)
            
            # Keep only last 50 commands
            if len(history) > 50:
                history = history[-50:]
            
            # Store updated history
            mcp_memory_store_func(
                key=self.memory_keys["command_history"],
                value=json.dumps(history, indent=2)
            )
            
            logger.info("Command history updated in MCP memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store command history in MCP: {e}")
            return False
    
    def get_command_history_from_mcp(self, mcp_memory_retrieve_func):
        """Get command execution history from MCP memory"""
        try:
            history_json = mcp_memory_retrieve_func(
                key=self.memory_keys["command_history"]
            )
            
            if history_json:
                return json.loads(history_json)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get command history from MCP: {e}")
            return []
    
    def update_environment_state(self, mcp_memory_store_func):
        """Update current environment state in MCP memory"""
        try:
            env_info = self.agent.get_environment_info()
            
            mcp_memory_store_func(
                key=self.memory_keys["environment_state"],
                value=json.dumps(env_info, indent=2)
            )
            
            logger.info("Environment state updated in MCP memory")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update environment state in MCP: {e}")
            return False
    
    def execute_command_with_mcp_logging(self, command: str, explanation: Optional[str] = None,
                                        timeout: int = 300, is_background: bool = False,
                                        mcp_memory_store_func=None, mcp_memory_retrieve_func=None):
        """Execute command with MCP logging"""
        try:
            # Execute the command
            result = execute_command_with_context(command, explanation, timeout, is_background)
            
            # Log to MCP memory if functions provided
            if mcp_memory_store_func and mcp_memory_retrieve_func:
                self.store_command_history(result, mcp_memory_store_func, mcp_memory_retrieve_func)
                self.update_environment_state(mcp_memory_store_func)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute command with MCP logging: {e}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Execution failed: {str(e)}",
                "environment": "unknown",
                "command": command,
                "explanation": explanation,
                "success": False,
                "timestamp": time.time()
            }
    
    def get_agent_summary(self) -> Dict[str, Any]:
        """Get comprehensive agent summary"""
        try:
            status = get_agent_status()
            env_info = self.agent.get_environment_info()
            
            return {
                "connection_status": status,
                "environment_info": env_info,
                "memory_keys": self.memory_keys,
                "is_connected": self.agent.test_connection(),
                "agent_ready": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent summary: {e}")
            return {
                "connection_status": {},
                "environment_info": {},
                "memory_keys": self.memory_keys,
                "is_connected": False,
                "agent_ready": False,
                "error": str(e)
            }
    
    def refresh_agent_context(self, file_list=None, mcp_memory_retrieve_func=None) -> Dict[str, Any]:
        """Refresh agent context: read key files and MCP memory for agent or UI use"""
        import os
        import builtins
        if file_list is None:
            file_list = [
                "README.md",
                "agent_context.json",
                "AI_ACTION_LOG.md",
                "NEXT_SESSION_CONTEXT.md",
                "CURRENT_STATUS_COMPLETE.md",
                "DEPLOYMENT.md"
            ]
        context_cache = {}
        for fname in file_list:
            fpath = os.path.join(os.getcwd(), fname)
            if os.path.exists(fpath):
                try:
                    with builtins.open(fpath, "r", encoding="utf-8") as f:
                        content = f.read(2000)
                    context_cache[fname] = content
                except Exception as e:
                    context_cache[fname] = f"ERROR: {e}"
            else:
                context_cache[fname] = None
        mcp_mem = {}
        if mcp_memory_retrieve_func:
            try:
                # If a callable is provided, fetch all keys/values
                mcp_mem = mcp_memory_retrieve_func()
            except Exception as e:
                mcp_mem = {"error": str(e)}
        return {"files": context_cache, "mcp_memory": mcp_mem}

# Global MCP integration instance
mcp_agent_integration = MCPAgentIntegration()

def get_mcp_integration() -> MCPAgentIntegration:
    """Get the global MCP integration instance"""
    return mcp_agent_integration

def mcp_execute_command(command: str, explanation: Optional[str] = None,
                       timeout: int = 300, is_background: bool = False,
                       store_func=None, retrieve_func=None) -> Dict[str, Any]:
    """Execute command with MCP integration - main entry point"""
    return mcp_agent_integration.execute_command_with_mcp_logging(
        command, explanation, timeout, is_background, store_func, retrieve_func
    )

def mcp_store_context(store_func):
    """Store connection context in MCP memory"""
    return mcp_agent_integration.store_connection_context_in_mcp(store_func)

def mcp_load_context(retrieve_func):
    """Load connection context from MCP memory"""
    return mcp_agent_integration.load_connection_context_from_mcp(retrieve_func)

def mcp_get_agent_summary() -> Dict[str, Any]:
    """Get agent summary for MCP integration"""
    return mcp_agent_integration.get_agent_summary()

def refresh_agent_context(file_list=None, mcp_memory_retrieve_func=None):
    """Global utility to refresh agent context/memory for any project"""
    return mcp_agent_integration.refresh_agent_context(file_list, mcp_memory_retrieve_func)

if __name__ == "__main__":
    # Test MCP integration
    print("MCP Agent Integration Test")
    print("=" * 40)
    
    # Get integration instance
    integration = get_mcp_integration()
    
    # Get agent summary
    summary = integration.get_agent_summary()
    print(f"Agent Summary:")
    print(json.dumps(summary, indent=2))
    
    # Test command execution (without MCP functions)
    print("\nTesting command execution...")
    result = integration.execute_command_with_mcp_logging(
        "echo 'Hello from MCP-integrated agent!'",
        "Testing MCP integration"
    )
    
    print(f"Command result:")
    print(f"  Success: {result['success']}")
    print(f"  Environment: {result['environment']}")
    print(f"  Output: {result['stdout'].strip()}")
    
    if result['stderr']:
        print(f"  Error: {result['stderr'].strip()}")
