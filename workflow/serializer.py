"""
Workflow serialization and deserialization with validation.
Handles saving and loading workflows to/from JSON format.
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid

class WorkflowSerializer:
    """Handles workflow serialization with validation and versioning."""
    
    def __init__(self):
        """Initialize the serializer."""
        self.current_version = "1.0"
        self.schema = self._create_workflow_schema()
    
    def _create_workflow_schema(self) -> Dict[str, Any]:
        """Create JSON schema for workflow validation."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Workflow",
            "type": "object",
            "required": ["version", "metadata", "nodes"],
            "properties": {
                "version": {
                    "type": "string",
                    "pattern": r"^\d+\.\d+$"
                },
                "metadata": {
                    "type": "object",
                    "required": ["name", "created_at"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                        "author": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "modified_at": {"type": "string", "format": "date-time"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "nodes": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-f0-9-]+$": {
                            "type": "object",
                            "required": ["id", "type", "position"],
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string", "minLength": 1},
                                "title": {"type": "string"},
                                "position": {
                                    "type": "object",
                                    "required": ["x", "y"],
                                    "properties": {
                                        "x": {"type": "number"},
                                        "y": {"type": "number"}
                                    }
                                },
                                "properties": {"type": "object"},
                                "inputs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["name", "type"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "type": {"type": "string"},
                                            "description": {"type": "string"},
                                            "required": {"type": "boolean"}
                                        }
                                    }
                                },
                                "outputs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["name", "type"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "type": {"type": "string"},
                                            "description": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "connections": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-f0-9-]+$": {
                            "type": "object",
                            "required": ["from_node", "from_pin", "to_node", "to_pin"],
                            "properties": {
                                "from_node": {"type": "string"},
                                "from_pin": {"type": "string"},
                                "to_node": {"type": "string"},
                                "to_pin": {"type": "string"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                },
                "canvas_state": {
                    "type": "object",
                    "properties": {
                        "zoom_level": {"type": "number", "minimum": 0.1, "maximum": 5.0},
                        "pan_offset": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"}
                            }
                        },
                        "viewport": {
                            "type": "object",
                            "properties": {
                                "width": {"type": "number"},
                                "height": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }
    
    def serialize_workflow(self, workflow_data: Dict[str, Any], 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Serialize workflow data to a standardized format."""
        # Prepare metadata
        now = datetime.now().isoformat()
        default_metadata = {
            "name": "Untitled Workflow",
            "description": "",
            "author": "",
            "created_at": now,
            "modified_at": now,
            "tags": []
        }
        
        if metadata:
            default_metadata.update(metadata)
        
        # Build serialized workflow
        serialized = {
            "version": self.current_version,
            "metadata": default_metadata,
            "nodes": self._serialize_nodes(workflow_data.get("nodes", {})),
            "connections": self._serialize_connections(workflow_data.get("connections", {})),
            "canvas_state": workflow_data.get("canvas_state", {})
        }
        
        # Validate against schema
        self.validate_workflow(serialized)
        
        return serialized
    
    def _serialize_nodes(self, nodes: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize nodes with proper structure."""
        serialized_nodes = {}
        
        for node_id, node_data in nodes.items():
            serialized_node = {
                "id": node_id,
                "type": node_data.get("type", "unknown"),
                "position": node_data.get("position", {"x": 0, "y": 0}),
            }
            
            # Optional fields
            if "title" in node_data:
                serialized_node["title"] = node_data["title"]
            
            if "properties" in node_data:
                serialized_node["properties"] = self._serialize_properties(node_data["properties"])
            
            if "inputs" in node_data:
                serialized_node["inputs"] = node_data["inputs"]
            
            if "outputs" in node_data:
                serialized_node["outputs"] = node_data["outputs"]
            
            serialized_nodes[node_id] = serialized_node
        
        return serialized_nodes
    
    def _serialize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize node properties with type preservation."""
        serialized_props = {}
        
        for key, value in properties.items():
            # Handle different property types
            if isinstance(value, (str, int, float, bool, list, dict)):
                serialized_props[key] = value
            else:
                # Convert complex types to string representation
                serialized_props[key] = str(value)
        
        return serialized_props
    
    def _serialize_connections(self, connections: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize connections with validation."""
        serialized_connections = {}
        
        for connection_id, connection_data in connections.items():
            serialized_connection = {
                "from_node": connection_data.get("from_node", ""),
                "from_pin": connection_data.get("from_pin", ""),
                "to_node": connection_data.get("to_node", ""),
                "to_pin": connection_data.get("to_pin", "")
            }
            
            # Optional metadata
            if "metadata" in connection_data:
                serialized_connection["metadata"] = connection_data["metadata"]
            
            serialized_connections[connection_id] = serialized_connection
        
        return serialized_connections
    
    def deserialize_workflow(self, serialized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize workflow data from JSON format."""
        # Validate against schema
        self.validate_workflow(serialized_data)
        
        # Check version compatibility
        version = serialized_data.get("version", "1.0")
        if not self._is_version_compatible(version):
            raise ValueError(f"Incompatible workflow version: {version}")
        
        # Extract workflow components
        workflow_data = {
            "nodes": self._deserialize_nodes(serialized_data.get("nodes", {})),
            "connections": self._deserialize_connections(serialized_data.get("connections", {})),
            "canvas_state": serialized_data.get("canvas_state", {}),
            "metadata": serialized_data.get("metadata", {})
        }
        
        return workflow_data
    
    def _deserialize_nodes(self, nodes_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize nodes with proper type conversion."""
        deserialized_nodes = {}
        
        for node_id, node_data in nodes_data.items():
            deserialized_node = {
                "type": node_data.get("type", "unknown"),
                "position": node_data.get("position", {"x": 0, "y": 0})
            }
            
            # Optional fields
            if "title" in node_data:
                deserialized_node["title"] = node_data["title"]
            
            if "properties" in node_data:
                deserialized_node["properties"] = self._deserialize_properties(node_data["properties"])
            
            if "inputs" in node_data:
                deserialized_node["inputs"] = node_data["inputs"]
            
            if "outputs" in node_data:
                deserialized_node["outputs"] = node_data["outputs"]
            
            deserialized_nodes[node_id] = deserialized_node
        
        return deserialized_nodes
    
    def _deserialize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize node properties with type restoration."""
        # For now, return as-is since JSON preserves basic types
        # This could be extended for complex type restoration
        return properties.copy()
    
    def _deserialize_connections(self, connections_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize connections."""
        return connections_data.copy()
    
    def validate_workflow(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Validate workflow against schema and return errors."""
        errors = []
        
        try:
            jsonschema.validate(workflow_data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        
        # Additional custom validations
        custom_errors = self._perform_custom_validations(workflow_data)
        errors.extend(custom_errors)
        
        return errors
    
    def _perform_custom_validations(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Perform custom validations beyond schema."""
        errors = []
        
        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", {})
        
        # Check that all connection references exist
        for connection_id, connection in connections.items():
            from_node = connection.get("from_node")
            to_node = connection.get("to_node")
            
            if from_node not in nodes:
                errors.append(f"Connection {connection_id}: Source node '{from_node}' not found")
            
            if to_node not in nodes:
                errors.append(f"Connection {connection_id}: Target node '{to_node}' not found")
        
        # Check for duplicate node positions (potential overlaps)
        positions = {}
        for node_id, node in nodes.items():
            pos = node.get("position", {})
            pos_key = f"{pos.get('x', 0)},{pos.get('y', 0)}"
            
            if pos_key in positions:
                errors.append(f"Nodes {positions[pos_key]} and {node_id} have identical positions")
            else:
                positions[pos_key] = node_id
        
        return errors
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if workflow version is compatible."""
        try:
            major, minor = map(int, version.split('.'))
            current_major, current_minor = map(int, self.current_version.split('.'))
            
            # Same major version is compatible
            return major == current_major
        except (ValueError, IndexError):
            return False
    
    def save_to_file(self, workflow_data: Dict[str, Any], file_path: str,
                     metadata: Optional[Dict[str, Any]] = None):
        """Save workflow to JSON file."""
        # Update metadata with file information
        file_metadata = metadata or {}
        file_metadata["modified_at"] = datetime.now().isoformat()
        
        serialized = self.serialize_workflow(workflow_data, file_metadata)
        
        # Write to file with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, file_path: str) -> Dict[str, Any]:
        """Load workflow from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            serialized_data = json.load(f)
        
        return self.deserialize_workflow(serialized_data)
    
    def export_to_format(self, workflow_data: Dict[str, Any], format_type: str) -> str:
        """Export workflow to different formats."""
        if format_type == "json":
            serialized = self.serialize_workflow(workflow_data)
            return json.dumps(serialized, indent=2)
        
        elif format_type == "yaml":
            try:
                import yaml
                serialized = self.serialize_workflow(workflow_data)
                return yaml.dump(serialized, default_flow_style=False)
            except ImportError:
                raise ValueError("PyYAML not available for YAML export")
        
        elif format_type == "summary":
            return self._create_workflow_summary(workflow_data)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _create_workflow_summary(self, workflow_data: Dict[str, Any]) -> str:
        """Create a human-readable summary of the workflow."""
        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", {})
        metadata = workflow_data.get("metadata", {})
        
        summary = []
        summary.append("WORKFLOW SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Name: {metadata.get('name', 'Untitled')}")
        summary.append(f"Description: {metadata.get('description', 'No description')}")
        summary.append(f"Nodes: {len(nodes)}")
        summary.append(f"Connections: {len(connections)}")
        summary.append("")
        
        # Node details
        summary.append("NODES:")
        summary.append("-" * 20)
        for node_id, node in nodes.items():
            node_type = node.get("type", "unknown")
            node_title = node.get("title", node_type)
            summary.append(f"  {node_title} ({node_type}) - {node_id[:8]}...")
        
        summary.append("")
        
        # Connection details
        summary.append("CONNECTIONS:")
        summary.append("-" * 20)
        for connection_id, connection in connections.items():
            from_node = connection.get("from_node", "")[:8]
            to_node = connection.get("to_node", "")[:8]
            from_pin = connection.get("from_pin", "")
            to_pin = connection.get("to_pin", "")
            summary.append(f"  {from_node}...{from_pin} -> {to_node}...{to_pin}")
        
        return "\n".join(summary)
    
    def create_workflow_template(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create an empty workflow template."""
        template = {
            "version": self.current_version,
            "metadata": {
                "name": name,
                "description": description,
                "author": "",
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "tags": []
            },
            "nodes": {},
            "connections": {},
            "canvas_state": {
                "zoom_level": 1.0,
                "pan_offset": {"x": 0, "y": 0}
            }
        }
        
        return template
