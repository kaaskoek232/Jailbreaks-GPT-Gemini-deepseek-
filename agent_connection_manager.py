#!/usr/bin/env python3
"""
Agent Connection Manager - Dynamic SSH/RunPod Connection Awareness
Provides context-aware terminal command execution for the AI agent.
"""

import os
import sys
import json
import subprocess
import socket
import time
from typing import Dict, Optional, List, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionContext:
    """Manages connection context for dynamic environment awareness"""
    
    def __init__(self):
        self.connection_type = "local"  # local, ssh, runpod
        self.ssh_host = None
        self.ssh_user = None
        self.ssh_key_path = None
        self.ssh_port = 22
        self.runpod_pod_id = None
        self.working_directory = None
        self.environment_vars = {}
        self.last_check = None
        
    def alert_context_awareness(self, level: int, message: str):
        """Context awareness alerting: 1=info, 2=warning, 3=critical"""
        if level == 1:
            logger.info(f"[Context-Awareness][L1] {message}")
        elif level == 2:
            logger.warning(f"[Context-Awareness][L2] {message}")
        elif level == 3:
            logger.error(f"[Context-Awareness][L3-CRITICAL] {message}")
        # Optionally, trigger external alerting here

    def smart_detect_context(self) -> str:
        """Smarter context detection: use network, file, and fallback clues."""
        prev_type = self.connection_type
        # 1. Try SSH: check if known SSH host is reachable
        if self.ssh_host and self.ssh_user:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.ssh_host, self.ssh_port))
                sock.close()
                if result == 0:
                    self.connection_type = "ssh"
                    if prev_type != self.connection_type:
                        self.alert_context_awareness(1, f"Context switched to SSH ({self.ssh_user}@{self.ssh_host}:{self.ssh_port}) [network detected]")
                    return "ssh"
            except Exception as e:
                self.alert_context_awareness(2, f"SSH network check failed: {e}")
        # 2. Try RunPod: check for known RunPod file or port
        if self.runpod_pod_id:
            runpod_marker = f"/workspace/{self.runpod_pod_id}_marker.txt"
            if os.path.exists(runpod_marker):
                self.connection_type = "runpod"
                if prev_type != self.connection_type:
                    self.alert_context_awareness(1, f"Context switched to RunPod (marker file detected)")
                return "runpod"
        # 3. Fallback: if working directory is /workspace, assume RunPod
        if self.working_directory == "/workspace":
            self.connection_type = "runpod"
            if prev_type != self.connection_type:
                self.alert_context_awareness(1, "Context switched to RunPod (workspace dir)")
            return "runpod"
        # 4. Default to local
        self.connection_type = "local"
        if prev_type != self.connection_type:
            self.alert_context_awareness(1, "Context switched to local (fallback)")
        return "local"

    # Replace detect_environment with smart_detect_context in all usages
    def detect_environment(self) -> str:
        return self.smart_detect_context()
    
    def setup_ssh_connection(self, host: str, user: str, key_path: Optional[str] = None, port: int = 22):
        """Setup SSH connection parameters"""
        self.connection_type = "ssh"
        self.ssh_host = host
        self.ssh_user = user
        self.ssh_key_path = key_path
        self.ssh_port = port
        logger.info(f"SSH connection configured: {user}@{host}:{port}")
    
    def setup_runpod_connection(self, pod_id: str, ssh_key_path: Optional[str] = None):
        """Setup RunPod connection parameters"""
        self.connection_type = "runpod"
        self.runpod_pod_id = pod_id
        self.ssh_key_path = ssh_key_path
        # RunPod typically uses SSH on port 22
        self.ssh_port = 22
        logger.info(f"RunPod connection configured: pod {pod_id}")
    
    def test_connection(self) -> bool:
        """Test if connection is active and working"""
        try:
            if self.connection_type == "local":
                # Test local command execution
                if os.name == 'nt':  # Windows
                    result = subprocess.run(['powershell.exe', '-Command', 'echo test'], capture_output=True, timeout=5)
                else:  # Unix-like
                    result = subprocess.run(['echo', 'test'], capture_output=True, timeout=5)
                return result.returncode == 0
            
            elif self.connection_type == "ssh" and self.ssh_host:
                # Test SSH connection
                ssh_cmd = self._build_ssh_command(['echo', 'test'])
                result = subprocess.run(ssh_cmd, capture_output=True, timeout=10)
                return result.returncode == 0
            
            elif self.connection_type == "runpod" and self.runpod_pod_id:
                # Test RunPod connection
                runpod_cmd = self._build_runpod_command(['echo', 'test'])
                result = subprocess.run(runpod_cmd, capture_output=True, timeout=10)
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _build_ssh_command(self, base_cmd: List[str]) -> List[str]:
        """Build SSH command with proper parameters"""
        if not self.ssh_host or not self.ssh_user:
            raise ValueError("SSH host and user must be configured")
        
        ssh_cmd = ['ssh']
        
        # Add key if specified
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            ssh_cmd.extend(['-i', self.ssh_key_path])
        
        # Add port if not default
        if self.ssh_port != 22:
            ssh_cmd.extend(['-p', str(self.ssh_port)])
        
        # Add host
        ssh_cmd.append(f"{self.ssh_user}@{self.ssh_host}")
          # Add the actual command
        if isinstance(base_cmd, list):
            ssh_cmd.append(' '.join(base_cmd))
        else:
            ssh_cmd.append(str(base_cmd))
        
        return ssh_cmd
    
    def _build_runpod_command(self, base_cmd: List[str]) -> List[str]:
        """Build RunPod SSH command"""
        if not self.runpod_pod_id:
            raise ValueError("RunPod pod ID must be configured")
        
        # Try multiple RunPod SSH formats as they may vary
        possible_hosts = [
            f"{self.runpod_pod_id}-22.pods.runpod.net",  # Standard format
            f"{self.runpod_pod_id}-8888.pods.runpod.net",  # Alternative port
            f"{self.runpod_pod_id}.pods.runpod.net",  # Simple format
            f"ssh.runpod.io"  # Direct RunPod SSH gateway (if exists)
        ]
        
        # For now, use the first format and let connection test handle failures
        runpod_host = possible_hosts[0]
        
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
        
        # Add key if specified
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            ssh_cmd.extend(['-i', self.ssh_key_path])
        
        # Add RunPod host
        ssh_cmd.append(f"root@{runpod_host}")
        
        # Add the actual command
        if isinstance(base_cmd, list):
            ssh_cmd.append(' '.join(base_cmd))
        else:
            ssh_cmd.append(str(base_cmd))
        
        return ssh_cmd
    
    def check_context_health(self):
        """Layer 2/3: Alert if context is lost or ambiguous, or lost for >N seconds"""
        now = time.time()
        if self.connection_type not in ("local", "ssh", "runpod"):
            self.alert_context_awareness(2, f"Ambiguous or lost context: {self.connection_type}")
        if self.last_check and (now - self.last_check) > 120:
            self.alert_context_awareness(3, f"Context lost for {int(now - self.last_check)} seconds!")

    def execute_command(self, command: str, timeout: int = 300) -> Tuple[int, str, str]:
        """Execute command in the appropriate environment with context health check"""
        self.check_context_health()
        try:
            if self.connection_type == "local":
                # Execute locally
                if os.name == 'nt':  # Windows
                    result = subprocess.run(
                        ['powershell.exe', '-Command', command],
                        capture_output=True,
                        timeout=timeout,
                        text=True
                    )
                else:  # Unix-like
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        timeout=timeout,
                        text=True
                    )
                
                return result.returncode, result.stdout, result.stderr
            
            elif self.connection_type == "ssh":
                # Execute via SSH
                ssh_cmd = self._build_ssh_command([command])
                result = subprocess.run(
                    ssh_cmd,
                    capture_output=True,
                    timeout=timeout,
                    text=True
                )
                
                return result.returncode, result.stdout, result.stderr
            
            elif self.connection_type == "runpod":
                # Execute via RunPod SSH
                runpod_cmd = self._build_runpod_command([command])
                result = subprocess.run(
                    runpod_cmd,
                    capture_output=True,
                    timeout=timeout,
                    text=True
                )
                
                return result.returncode, result.stdout, result.stderr
            
            else:
                raise ValueError(f"Unknown connection type: {self.connection_type}")
                
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", f"Command execution failed: {str(e)}"
    
    def get_context_info(self) -> Dict[str, any]:
        """Get current connection context information"""
        return {
            "connection_type": self.connection_type,
            "ssh_host": self.ssh_host,
            "ssh_user": self.ssh_user,
            "ssh_port": self.ssh_port,
            "runpod_pod_id": self.runpod_pod_id,
            "working_directory": self.working_directory,
            "last_check": self.last_check,
            "is_connected": self.test_connection()
        }
    
    def to_json(self) -> str:
        """Serialize connection context to JSON"""
        context = self.get_context_info()
        context['ssh_key_path'] = self.ssh_key_path  # Include key path but not the key itself
        return json.dumps(context, indent=2)
    
    def from_json(self, json_str: str):
        """Load connection context from JSON"""
        try:
            data = json.loads(json_str)
            self.connection_type = data.get('connection_type', 'local')
            self.ssh_host = data.get('ssh_host')
            self.ssh_user = data.get('ssh_user')
            self.ssh_port = data.get('ssh_port', 22)
            self.ssh_key_path = data.get('ssh_key_path')
            self.runpod_pod_id = data.get('runpod_pod_id')
            self.working_directory = data.get('working_directory')
            self.last_check = data.get('last_check')
        except Exception as e:
            logger.error(f"Failed to load connection context: {e}")

# Global connection context instance
connection_context = ConnectionContext()

def get_connection_context() -> ConnectionContext:
    """Get the global connection context"""
    return connection_context

def execute_context_aware_command(command: str, timeout: int = 300) -> Tuple[int, str, str]:
    """Execute command with automatic context awareness"""
    # Auto-detect environment if not already done
    if not connection_context.last_check:
        connection_context.detect_environment()
        connection_context.last_check = time.time()
    
    return connection_context.execute_command(command, timeout)

def setup_ssh_context(host: str, user: str, key_path: Optional[str] = None, port: int = 22):
    """Setup SSH connection context"""
    connection_context.setup_ssh_connection(host, user, key_path, port)

def setup_runpod_context(pod_id: str, key_path: Optional[str] = None):
    """Setup RunPod connection context"""
    connection_context.setup_runpod_connection(pod_id, key_path)

def get_context_status() -> Dict[str, any]:
    """Get current connection status"""
    return connection_context.get_context_info()

if __name__ == "__main__":
    # Test the connection manager
    print("Agent Connection Manager Test")
    print("=" * 40)
    
    # Detect environment
    env_type = connection_context.detect_environment()
    print(f"Detected environment: {env_type}")
    
    # Test connection
    is_connected = connection_context.test_connection()
    print(f"Connection test: {'PASS' if is_connected else 'FAIL'}")
    
    # Show context info
    context_info = connection_context.get_context_info()
    print(f"Context info: {json.dumps(context_info, indent=2)}")
    
    # Test command execution
    print("\nTesting command execution...")
    returncode, stdout, stderr = execute_context_aware_command("echo 'Hello from agent!'")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout.strip()}")
    if stderr:
        print(f"Error: {stderr.strip()}")
