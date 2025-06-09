"""
Workflow execution engine with thread-safe background processing.
Handles workflow validation, execution, and status management.
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future
import traceback
from datetime import datetime

from workflow.execution import WorkflowExecution
from workflow.serializer import WorkflowSerializer
from nodes.node_factory import NodeFactory

class WorkflowEngine:
    """Thread-safe workflow execution engine."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the workflow engine."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.node_factory = NodeFactory()
        self.serializer = WorkflowSerializer()
        
        # Active executions
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_lock = threading.Lock()
        
        # Engine state
        self.is_running = True
        
    def execute_workflow(self, workflow_data: Dict, 
                        on_log: Optional[Callable] = None,
                        on_node_update: Optional[Callable] = None,
                        on_complete: Optional[Callable] = None) -> str:
        """Execute a workflow asynchronously."""
        execution_id = str(uuid.uuid4())
        
        # Create execution instance
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_data=workflow_data,
            node_factory=self.node_factory,
            on_log=on_log,
            on_node_update=on_node_update
        )
        
        # Store execution
        with self.execution_lock:
            self.active_executions[execution_id] = execution
        
        # Submit for execution
        future = self.executor.submit(self._execute_workflow_internal, execution, on_complete)
        execution.future = future
        
        if on_log:
            on_log("INFO", f"Workflow execution started", None, {"execution_id": execution_id})
        
        return execution_id
    
    def _execute_workflow_internal(self, execution: WorkflowExecution, 
                                 on_complete: Optional[Callable] = None):
        """Internal workflow execution method."""
        start_time = time.time()
        success = False
        error_message = ""
        
        try:
            # Validate workflow
            validation_errors = self.validate_workflow(execution.workflow_data)
            if validation_errors:
                raise ValueError(f"Workflow validation failed: {', '.join(validation_errors)}")
            
            # Execute the workflow
            execution.execute()
            success = True
            
            if execution.on_log:
                duration = time.time() - start_time
                execution.on_log("SUCCESS", f"Workflow completed in {duration:.2f}s")
            
        except Exception as e:
            error_message = str(e)
            if execution.on_log:
                execution.on_log("ERROR", f"Workflow execution failed: {error_message}")
                execution.on_log("DEBUG", traceback.format_exc())
        
        finally:
            # Clean up
            with self.execution_lock:
                if execution.execution_id in self.active_executions:
                    del self.active_executions[execution.execution_id]
            
            # Notify completion
            if on_complete:
                try:
                    on_complete(success, error_message)
                except Exception as e:
                    print(f"Error in completion callback: {e}")
    
    def stop_execution(self, execution_id: Optional[str] = None):
        """Stop a specific execution or all executions."""
        with self.execution_lock:
            if execution_id:
                # Stop specific execution
                if execution_id in self.active_executions:
                    execution = self.active_executions[execution_id]
                    execution.stop()
                    if hasattr(execution, 'future'):
                        execution.future.cancel()
            else:
                # Stop all executions
                for execution in self.active_executions.values():
                    execution.stop()
                    if hasattr(execution, 'future'):
                        execution.future.cancel()
                
                self.active_executions.clear()
    
    def stop_all_executions(self):
        """Stop all active executions and shutdown engine."""
        self.is_running = False
        self.stop_execution()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
    
    def validate_workflow(self, workflow_data: Dict) -> List[str]:
        """Validate a workflow and return list of errors."""
        errors = []
        
        try:
            nodes = workflow_data.get("nodes", {})
            connections = workflow_data.get("connections", {})
            
            # Validate nodes
            for node_id, node_data in nodes.items():
                node_errors = self._validate_node(node_id, node_data)
                errors.extend(node_errors)
            
            # Validate connections
            for connection_id, connection_data in connections.items():
                connection_errors = self._validate_connection(connection_id, connection_data, nodes)
                errors.extend(connection_errors)
            
            # Check for circular dependencies
            circular_errors = self._check_circular_dependencies(nodes, connections)
            errors.extend(circular_errors)
            
            # Check for disconnected nodes
            if nodes and not connections:
                errors.append("Workflow has nodes but no connections")
            
        except Exception as e:
            errors.append(f"Workflow validation error: {str(e)}")
        
        return errors
    
    def _validate_node(self, node_id: str, node_data: Dict) -> List[str]:
        """Validate a single node."""
        errors = []
        
        # Check required fields
        if not node_data.get("type"):
            errors.append(f"Node {node_id}: Missing node type")
        
        if not node_data.get("position"):
            errors.append(f"Node {node_id}: Missing position")
        
        # Validate node type exists
        node_type = node_data.get("type")
        if node_type and not self.node_factory.is_valid_node_type(node_type):
            errors.append(f"Node {node_id}: Unknown node type '{node_type}'")
        
        # Validate node properties
        if node_type:
            try:
                node_info = self.node_factory.get_node_info(node_type)
                required_props = node_info.get("required_properties", [])
                node_props = node_data.get("properties", {})
                
                for required_prop in required_props:
                    if required_prop not in node_props:
                        errors.append(f"Node {node_id}: Missing required property '{required_prop}'")
                        
            except Exception as e:
                errors.append(f"Node {node_id}: Property validation error: {str(e)}")
        
        return errors
    
    def _validate_connection(self, connection_id: str, connection_data: Dict, 
                           nodes: Dict) -> List[str]:
        """Validate a single connection."""
        errors = []
        
        # Check required fields
        required_fields = ["from_node", "from_pin", "to_node", "to_pin"]
        for field in required_fields:
            if field not in connection_data:
                errors.append(f"Connection {connection_id}: Missing field '{field}'")
        
        # Check if referenced nodes exist
        from_node = connection_data.get("from_node")
        to_node = connection_data.get("to_node")
        
        if from_node and from_node not in nodes:
            errors.append(f"Connection {connection_id}: Source node '{from_node}' not found")
        
        if to_node and to_node not in nodes:
            errors.append(f"Connection {connection_id}: Target node '{to_node}' not found")
        
        # Validate pin compatibility
        if from_node and to_node and from_node in nodes and to_node in nodes:
            pin_errors = self._validate_pin_compatibility(connection_data, nodes)
            errors.extend(pin_errors)
        
        return errors
    
    def _validate_pin_compatibility(self, connection_data: Dict, nodes: Dict) -> List[str]:
        """Validate that connected pins are compatible."""
        errors = []
        
        try:
            from_node_data = nodes[connection_data["from_node"]]
            to_node_data = nodes[connection_data["to_node"]]
            
            from_pin = connection_data["from_pin"]
            to_pin = connection_data["to_pin"]
            
            # Find output pin in source node
            from_outputs = from_node_data.get("outputs", [])
            from_pin_info = next((p for p in from_outputs if p["name"] == from_pin), None)
            
            if not from_pin_info:
                errors.append(f"Output pin '{from_pin}' not found in source node")
                return errors
            
            # Find input pin in target node
            to_inputs = to_node_data.get("inputs", [])
            to_pin_info = next((p for p in to_inputs if p["name"] == to_pin), None)
            
            if not to_pin_info:
                errors.append(f"Input pin '{to_pin}' not found in target node")
                return errors
            
            # Check type compatibility
            from_type = from_pin_info.get("type", "any")
            to_type = to_pin_info.get("type", "any")
            
            if not self._are_types_compatible(from_type, to_type):
                errors.append(f"Incompatible types: {from_type} -> {to_type}")
        
        except Exception as e:
            errors.append(f"Pin compatibility check error: {str(e)}")
        
        return errors
    
    def _are_types_compatible(self, from_type: str, to_type: str) -> bool:
        """Check if two pin types are compatible."""
        # "any" type is compatible with everything
        if from_type == "any" or to_type == "any":
            return True
        
        # Exact match
        if from_type == to_type:
            return True
        
        # Define compatibility rules
        compatibility_rules = {
            "string": ["text"],
            "text": ["string"],
            "number": ["integer", "float"],
            "integer": ["number", "float"],
            "float": ["number", "integer"],
            "object": ["json", "dict"],
            "json": ["object", "dict"],
            "dict": ["object", "json"]
        }
        
        compatible_types = compatibility_rules.get(from_type, [])
        return to_type in compatible_types
    
    def _check_circular_dependencies(self, nodes: Dict, connections: Dict) -> List[str]:
        """Check for circular dependencies in the workflow."""
        errors = []
        
        try:
            # Build adjacency list
            graph = {node_id: [] for node_id in nodes.keys()}
            
            for connection in connections.values():
                from_node = connection["from_node"]
                to_node = connection["to_node"]
                if from_node in graph:
                    graph[from_node].append(to_node)
            
            # Use DFS to detect cycles
            visited = set()
            rec_stack = set()
            
            def has_cycle(node):
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if has_cycle(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            for node_id in nodes.keys():
                if node_id not in visited:
                    if has_cycle(node_id):
                        errors.append("Circular dependency detected in workflow")
                        break
        
        except Exception as e:
            errors.append(f"Circular dependency check error: {str(e)}")
        
        return errors
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of a specific execution."""
        with self.execution_lock:
            execution = self.active_executions.get(execution_id)
            if execution:
                return {
                    "execution_id": execution_id,
                    "status": execution.status,
                    "current_node": execution.current_node_id,
                    "progress": execution.get_progress(),
                    "start_time": execution.start_time,
                    "errors": execution.errors
                }
        return None
    
    def get_all_execution_statuses(self) -> List[Dict]:
        """Get status of all active executions."""
        statuses = []
        with self.execution_lock:
            for execution_id in self.active_executions.keys():
                status = self.get_execution_status(execution_id)
                if status:
                    statuses.append(status)
        return statuses
    
    def is_execution_running(self, execution_id: str) -> bool:
        """Check if a specific execution is still running."""
        with self.execution_lock:
            return execution_id in self.active_executions
    
    def has_active_executions(self) -> bool:
        """Check if there are any active executions."""
        with self.execution_lock:
            return len(self.active_executions) > 0
    
    def get_engine_stats(self) -> Dict:
        """Get engine statistics."""
        with self.execution_lock:
            return {
                "active_executions": len(self.active_executions),
                "max_workers": self.max_workers,
                "is_running": self.is_running,
                "executor_shutdown": self.executor._shutdown
            }
