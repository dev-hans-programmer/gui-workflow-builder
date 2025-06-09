"""
Workflow execution implementation with topological sorting and data flow.
Handles individual workflow execution with node dependencies and data passing.
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
import traceback
import copy

# Import moved to avoid circular dependency
from utils.geometry import Point

class ExecutionContext:
    """Context for workflow execution containing shared data and state."""
    
    def __init__(self):
        """Initialize execution context."""
        self.data_store: Dict[str, Any] = {}
        self.global_variables: Dict[str, Any] = {}
        self.execution_id: str = ""
        self.start_time: datetime = datetime.now()
        self.lock = threading.Lock()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the context store."""
        with self.lock:
            return self.data_store.get(key, default)
    
    def set_data(self, key: str, value: Any):
        """Set data in the context store."""
        with self.lock:
            self.data_store[key] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a global variable."""
        with self.lock:
            return self.global_variables.get(name, default)
    
    def set_variable(self, name: str, value: Any):
        """Set a global variable."""
        with self.lock:
            self.global_variables[name] = value

class WorkflowExecution:
    """Handles execution of a single workflow with dependency management."""
    
    def __init__(self, execution_id: str, workflow_data: Dict, 
                 node_factory: Any,
                 on_log: Optional[Callable] = None,
                 on_node_update: Optional[Callable] = None):
        """Initialize workflow execution."""
        self.execution_id = execution_id
        self.workflow_data = workflow_data
        self.node_factory = node_factory
        self.on_log = on_log
        self.on_node_update = on_node_update
        
        # Execution state
        self.status = "pending"
        self.current_node_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.errors: List[str] = []
        self.stop_requested = False
        
        # Execution context
        self.context = ExecutionContext()
        self.context.execution_id = execution_id
        
        # Node execution tracking
        self.completed_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.node_outputs: Dict[str, Dict[str, Any]] = {}
        
        # Execution order
        self.execution_order: List[str] = []
        
    def execute(self):
        """Execute the workflow."""
        self.start_time = datetime.now()
        self.status = "running"
        
        try:
            self._log("INFO", "Starting workflow execution")
            
            # Build execution order
            self.execution_order = self._build_execution_order()
            
            if not self.execution_order:
                self._log("WARNING", "No nodes to execute")
                self.status = "completed"
                return
            
            self._log("INFO", f"Execution order: {' -> '.join(self.execution_order)}")
            
            # Execute nodes in order
            for node_id in self.execution_order:
                if self.stop_requested:
                    self._log("INFO", "Execution stopped by request")
                    self.status = "stopped"
                    return
                
                try:
                    self._execute_node(node_id)
                    self.completed_nodes.add(node_id)
                    
                except Exception as e:
                    error_msg = f"Node {node_id} failed: {str(e)}"
                    self.errors.append(error_msg)
                    self.failed_nodes.add(node_id)
                    self._log("ERROR", error_msg)
                    self._log("DEBUG", traceback.format_exc())
                    
                    # Check if this is a critical failure
                    if self._is_critical_node(node_id):
                        self._log("ERROR", "Critical node failed, stopping execution")
                        self.status = "failed"
                        return
            
            # Check final status
            if self.failed_nodes:
                self.status = "completed_with_errors"
                self._log("WARNING", f"Execution completed with {len(self.failed_nodes)} failed nodes")
            else:
                self.status = "completed"
                self._log("SUCCESS", "Workflow execution completed successfully")
        
        except Exception as e:
            self.status = "failed"
            error_msg = f"Workflow execution failed: {str(e)}"
            self.errors.append(error_msg)
            self._log("ERROR", error_msg)
            self._log("DEBUG", traceback.format_exc())
        
        finally:
            self.end_time = datetime.now()
            self.current_node_id = None
    
    def _build_execution_order(self) -> List[str]:
        """Build the execution order using topological sort."""
        nodes = self.workflow_data.get("nodes", {})
        connections = self.workflow_data.get("connections", {})
        
        # Build dependency graph
        dependencies = {node_id: set() for node_id in nodes.keys()}
        
        for connection in connections.values():
            from_node = connection.get("from_node")
            to_node = connection.get("to_node")
            
            if from_node and to_node and from_node in nodes and to_node in nodes:
                dependencies[to_node].add(from_node)
        
        # Topological sort using Kahn's algorithm
        in_degree = {node_id: len(deps) for node_id, deps in dependencies.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort queue to ensure deterministic execution order
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            # Update in-degrees
            for node_id, deps in dependencies.items():
                if current in deps:
                    in_degree[node_id] -= 1
                    if in_degree[node_id] == 0:
                        queue.append(node_id)
        
        # Check for circular dependencies
        if len(result) != len(nodes):
            remaining_nodes = set(nodes.keys()) - set(result)
            raise ValueError(f"Circular dependency detected involving nodes: {remaining_nodes}")
        
        return result
    
    def _execute_node(self, node_id: str):
        """Execute a single node."""
        self.current_node_id = node_id
        
        node_data = self.workflow_data["nodes"][node_id]
        node_type = node_data["type"]
        
        self._log("INFO", f"Executing node: {node_type}", node_id)
        self._update_node_status(node_id, "running")
        
        start_time = time.time()
        
        try:
            # Create node instance
            node_instance = self.node_factory.create_node_instance(node_type, node_id, node_data)
            
            # Prepare input data
            input_data = self._prepare_node_inputs(node_id)
            
            # Execute the node
            output_data = node_instance.execute(input_data, self.context)
            
            # Store outputs
            self.node_outputs[node_id] = output_data or {}
            
            execution_time = time.time() - start_time
            self._log("SUCCESS", f"Node completed in {execution_time:.3f}s", node_id)
            self._update_node_status(node_id, "success")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_node_status(node_id, "error")
            raise e
    
    def _prepare_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """Prepare input data for a node based on its connections."""
        input_data = {}
        connections = self.workflow_data.get("connections", {})
        
        # Find all connections that feed into this node
        for connection in connections.values():
            if connection.get("to_node") == node_id:
                from_node = connection.get("from_node")
                from_pin = connection.get("from_pin")
                to_pin = connection.get("to_pin")
                
                if from_node in self.node_outputs:
                    # Get output data from source node
                    source_outputs = self.node_outputs[from_node]
                    
                    if from_pin in source_outputs:
                        input_data[to_pin] = source_outputs[from_pin]
                        
                        # Log data transfer
                        data_size = len(str(source_outputs[from_pin]))
                        self._log("DEBUG", f"Data transfer: {from_pin} -> {to_pin} ({data_size} chars)", 
                                node_id, {"from_node": from_node, "data_type": type(source_outputs[from_pin]).__name__})
        
        return input_data
    
    def _is_critical_node(self, node_id: str) -> bool:
        """Check if a node is critical for workflow execution."""
        # For now, consider all nodes non-critical
        # This could be extended to mark certain nodes as critical
        node_data = self.workflow_data["nodes"].get(node_id, {})
        return node_data.get("properties", {}).get("critical", False)
    
    def _log(self, level: str, message: str, node_id: Optional[str] = None, 
             details: Optional[Dict] = None):
        """Log a message."""
        if self.on_log:
            self.on_log(level, message, node_id, details)
    
    def _update_node_status(self, node_id: str, status: str):
        """Update node visual status."""
        if self.on_node_update:
            self.on_node_update(node_id, status)
    
    def stop(self):
        """Request execution stop."""
        self.stop_requested = True
        self.status = "stopping"
        self._log("INFO", "Stop requested")
    
    def get_progress(self) -> float:
        """Get execution progress as percentage."""
        if not self.execution_order:
            return 0.0
        
        completed = len(self.completed_nodes) + len(self.failed_nodes)
        return (completed / len(self.execution_order)) * 100.0
    
    def get_duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if not self.start_time:
            return None
        
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "progress": self.get_progress(),
            "total_nodes": len(self.execution_order),
            "completed_nodes": len(self.completed_nodes),
            "failed_nodes": len(self.failed_nodes),
            "errors": self.errors,
            "current_node": self.current_node_id
        }
    
    def get_node_output(self, node_id: str, pin_name: Optional[str] = None) -> Any:
        """Get output data from a specific node."""
        if node_id not in self.node_outputs:
            return None
        
        node_outputs = self.node_outputs[node_id]
        
        if pin_name is not None:
            return node_outputs.get(pin_name)
        else:
            return node_outputs
    
    def has_node_completed(self, node_id: str) -> bool:
        """Check if a node has completed execution."""
        return node_id in self.completed_nodes
    
    def has_node_failed(self, node_id: str) -> bool:
        """Check if a node has failed execution."""
        return node_id in self.failed_nodes
    
    def get_execution_path(self) -> List[Dict[str, Any]]:
        """Get the execution path with timing information."""
        path = []
        
        for i, node_id in enumerate(self.execution_order):
            node_data = self.workflow_data["nodes"].get(node_id, {})
            
            path_entry = {
                "order": i + 1,
                "node_id": node_id,
                "node_type": node_data.get("type", "unknown"),
                "status": "completed" if node_id in self.completed_nodes else 
                         "failed" if node_id in self.failed_nodes else "pending"
            }
            
            path.append(path_entry)
        
        return path
