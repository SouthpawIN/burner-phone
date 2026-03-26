#!/usr/bin/env python3
"""
SSH Connection Pool - Persistent connections with automatic keepalive
Dramatically reduces latency by reusing connections instead of creating new ones
"""

import paramiko
import threading
import time
from typing import Optional, Dict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ConnectionInfo:
    """Information about a pooled connection"""
    client: paramiko.SSHClient
    last_used: float = field(default_factory=time.time)
    uses: int = 0


class SSHConnectionPool:
    """Thread-safe SSH connection pool with automatic keepalive"""
    
    # Singleton instance per process
    _instances: Dict[str, "SSHConnectionPool"] = {}
    _lock = threading.Lock()
    
    def __new__(cls, host: str, port: int, username: str, key_path: str,
                 max_connections: int = 3, idle_timeout: float = 60.0):
        """Get or create singleton pool for this host/port combination"""
        instance_key = f"{host}:{port}:{username}"
        
        with cls._lock:
            if instance_key not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[instance_key] = instance
            
            return cls._instances[instance_key]
    
    def __init__(self, host: str, port: int, username: str, key_path: str,
                 max_connections: int = 3, idle_timeout: float = 60.0):
        """Initialize pool (only runs once per host/port)"""
        if self._initialized:
            return
            
        self._initialized = True
        self.host = host
        self.port = port
        self.username = username
        self.key_path = Path(key_path).expanduser()
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        
        # Connection pool state
        self._available: list = []  # Available connections
        self._in_use: Dict[int, ConnectionInfo] = {}  # In-use connections (by thread id)
        self._lock = threading.Lock()
        self._total_created = 0
        self._total_reused = 0
        
        # Auto-cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        print(f"[SSH Pool] Initialized for {self.username}@{self.host}:{self.port} "
              f"(max={max_connections}, idle_timeout={idle_timeout}s)")
    
    @contextmanager
    def connection(self):
        """Context manager for getting a connection from the pool"""
        conn = self._get_connection()
        try:
            yield conn.client
            return True
        except Exception as e:
            print(f"[SSH Pool] Error: {e}")
            return False
        finally:
            self._return_connection(conn)
    
    def _get_connection(self) -> ConnectionInfo:
        """Get a connection from the pool or create a new one"""
        with self._lock:
            # Try to get an available connection
            while self._available:
                conn = self._available.pop(0)
                if self._is_connection_alive(conn.client):
                    conn.uses += 1
                    conn.last_used = time.time()
                    self._total_reused += 1
                    return conn
                else:
                    # Connection dead, create new one
                    pass
            
            # Check if we can create a new connection
            total_connections = len(self._available) + len(self._in_use)
            if total_connections >= self.max_connections:
                # Wait for a connection to become available
                time.sleep(0.1)  # Brief wait
                return self._get_connection()  # Retry
            
            # Create new connection
            print(f"[SSH Pool] Creating new connection (total: {total_connections + 1}/{self.max_connections})")
            conn = self._create_connection()
            conn.uses = 1
            return conn
    
    def _create_connection(self) -> ConnectionInfo:
        """Create a new SSH connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=str(self.key_path),
                timeout=5.0,
                look_for_keys=False
            )
            self._total_created += 1
            return ConnectionInfo(client=client)
        except Exception as e:
            client.close()
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    def _return_connection(self, conn: ConnectionInfo):
        """Return a connection to the pool"""
        with self._lock:
            if self._is_connection_alive(conn.client):
                # Check idle timeout
                idle_time = time.time() - conn.last_used
                if idle_time < self.idle_timeout:
                    self._available.append(conn)
                else:
                    # Close expired connection
                    try:
                        conn.client.close()
                    except:
                        pass
            else:
                # Connection dead, close it
                try:
                    conn.client.close()
                except:
                    pass
    
    def _is_connection_alive(self, client: paramiko.SSHClient) -> bool:
        """Check if a connection is still alive"""
        try:
            # Quick check using a no-op command
            stdin, stdout, stderr = client.exec_command("true", timeout=2.0)
            return stdout.channel.recv_exit_status() == 0
        except Exception as e:
            # Connection likely dead
            return False
    
    def _cleanup_loop(self):
        """Background thread to clean up idle connections"""
        while True:
            time.sleep(10)  # Check every 10 seconds
            with self._lock:
                still_available = []
                now = time.time()
                
                for conn in self._available:
                    idle_time = now - conn.last_used
                    if idle_time < self.idle_timeout:
                        still_available.append(conn)
                    else:
                        # Close idle connection
                        try:
                            conn.client.close()
                            print(f"[SSH Pool] Closed idle connection (idle {idle_time:.0f}s)")
                        except:
                            pass
                
                self._available = still_available
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._available:
                try:
                    conn.client.close()
                except:
                    pass
            self._available.clear()
    
    def stats(self) -> Dict:
        """Return pool statistics"""
        with self._lock:
            return {
                "available": len(self._available),
                "in_use": len(self._in_use),
                "total_created": self._total_created,
                "total_reused": self._total_reused,
                "hit_rate": self._total_reused / max(1, self._total_created + self._total_reused)
            }


# Convenience function for quick usage
def get_ssh_pool(host: str, port: int, username: str, key_path: str, **kwargs):
    """Get or create a connection pool for the given host"""
    return SSHConnectionPool(host, port, username, key_path, **kwargs)
