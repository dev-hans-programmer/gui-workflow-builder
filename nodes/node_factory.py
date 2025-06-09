"""
Node factory for creating and managing node types.
Provides a registry system for extensible node creation.
"""

from typing import Dict, List, Type, Any, Optional
import importlib
import pkgutil
from pathlib import Path

from nodes.base_node import BaseNode, NodeSchema
from nodes.input_nodes import *
from nodes.processing_nodes import *
from nodes.output_nodes import *

class NodeFactory:
    """Factory for creating and managing workflow nodes."""
    
    def __init__(self):
        """Initialize the node factory."""
        self.node_registry: Dict[str, Type[BaseNode]] = {}
        self.node_schemas: Dict[str, NodeSchema] = {}
        self.categories: Dict[str, List[str]] = {}
        
        # Register built-in nodes
        self._register_builtin_nodes()
    
    def _register_builtin_nodes(self):
        """Register all built-in node types."""
        # Import all node modules to trigger registration
        try:
            # Register input nodes
            from nodes.input_nodes import (
                TextInputNode, NumberInputNode, FileInputNode, 
                APIInputNode, DatabaseInputNode, TimerNode
            )
            
            # Register processing nodes
            from nodes.processing_nodes import (
                TextProcessorNode, MathNode, FilterNode,
                TransformNode, ScriptNode, ConditionalNode,
                DelayNode
            )
            
            # Register output nodes
            from nodes.output_nodes import (
                TextOutputNode, FileOutputNode, APIOutputNode,
                DatabaseOutputNode, EmailNode, NotificationNode
            )
            
            # Auto-register all loaded node classes
            self._auto_register_nodes()
            
        except ImportError as e:
            print(f"Warning: Failed to import some node modules: {e}")
    
    def _auto_register_nodes(self):
        """Automatically register all BaseNode subclasses."""
        def get_all_subclasses(cls):
            """Recursively get all subclasses of a class."""
            subclasses = set(cls.__subclasses__())
            for subclass in list(subclasses):
                subclasses.update(get_all_subclasses(subclass))
            return subclasses
        
        # Get all BaseNode subclasses
        node_classes = get_all_subclasses(BaseNode)
        
        for node_class in node_classes:
            # Skip abstract base classes
            if node_class.__name__ in ['BaseNode', 'SimpleNode']:
                continue
            
            try:
                # Get schema from the class
                schema = node_class.get_schema()
                self.register_node(node_class, schema)
            except Exception as e:
                print(f"Warning: Failed to register node {node_class.__name__}: {e}")
    
    def register_node(self, node_class: Type[BaseNode], schema: NodeSchema):
        """Register a node type with its schema."""
        node_type = schema.node_type
        
        # Store in registry
        self.node_registry[node_type] = node_class
        self.node_schemas[node_type] = schema
        
        # Add to category
        category = schema.category
        if category not in self.categories:
            self.categories[category] = []
        
        if node_type not in self.categories[category]:
            self.categories[category].append(node_type)
    
    def create_node(self, node_type: str, node_id: str) -> Dict[str, Any]:
        """Create node data dictionary for a given type."""
        if node_type not in self.node_schemas:
            raise ValueError(f"Unknown node type: {node_type}")
        
        schema = self.node_schemas[node_type]
        
        # Create basic node data
        node_data = {
            "id": node_id,
            "type": node_type,
            "title": schema.title,
            "position": {"x": 0, "y": 0},
            "properties": {},
            "inputs": [pin.to_dict() for pin in schema.inputs],
            "outputs": [pin.to_dict() for pin in schema.outputs]
        }
        
        # Set default property values
        for prop_name, prop_config in schema.properties.items():
            default_value = prop_config.get("default")
            if default_value is not None:
                node_data["properties"][prop_name] = default_value
        
        return node_data
    
    def create_node_instance(self, node_type: str, node_id: str, 
                           node_data: Dict[str, Any]) -> BaseNode:
        """Create an actual node instance for execution."""
        if node_type not in self.node_registry:
            raise ValueError(f"Unknown node type: {node_type}")
        
        node_class = self.node_registry[node_type]
        return node_class(node_id, node_data)
    
    def get_node_info(self, node_type: str) -> Dict[str, Any]:
        """Get information about a node type."""
        if node_type not in self.node_schemas:
            raise ValueError(f"Unknown node type: {node_type}")
        
        schema = self.node_schemas[node_type]
        return schema.to_dict()
    
    def get_node_categories(self) -> Dict[str, List[str]]:
        """Get all node categories and their types."""
        return self.categories.copy()
    
    def get_nodes_in_category(self, category: str) -> List[str]:
        """Get all node types in a specific category."""
        return self.categories.get(category, [])
    
    def is_valid_node_type(self, node_type: str) -> bool:
        """Check if a node type is valid and registered."""
        return node_type in self.node_registry
    
    def get_all_node_types(self) -> List[str]:
        """Get list of all registered node types."""
        return list(self.node_registry.keys())
    
    def get_node_schema(self, node_type: str) -> Optional[NodeSchema]:
        """Get the schema for a specific node type."""
        return self.node_schemas.get(node_type)
    
    def search_nodes(self, query: str) -> List[str]:
        """Search for nodes by name, description, or category."""
        query_lower = query.lower()
        matching_nodes = []
        
        for node_type, schema in self.node_schemas.items():
            # Search in title, description, and category
            if (query_lower in schema.title.lower() or
                query_lower in schema.description.lower() or
                query_lower in schema.category.lower() or
                query_lower in node_type.lower()):
                matching_nodes.append(node_type)
        
        return matching_nodes
    
    def get_compatible_nodes(self, output_type: str) -> List[str]:
        """Get nodes that can accept a specific output type as input."""
        compatible_nodes = []
        
        for node_type, schema in self.node_schemas.items():
            for input_pin in schema.inputs:
                if self._are_types_compatible(output_type, input_pin.type):
                    compatible_nodes.append(node_type)
                    break
        
        return compatible_nodes
    
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
            "dict": ["object", "json"],
            "list": ["array"],
            "array": ["list"]
        }
        
        compatible_types = compatibility_rules.get(from_type, [])
        return to_type in compatible_types
    
    def validate_node_data(self, node_type: str, node_data: Dict[str, Any]) -> List[str]:
        """Validate node data against its schema."""
        errors = []
        
        if node_type not in self.node_schemas:
            errors.append(f"Unknown node type: {node_type}")
            return errors
        
        schema = self.node_schemas[node_type]
        properties = node_data.get("properties", {})
        
        # Check required properties
        for required_prop in schema.required_properties:
            if required_prop not in properties:
                errors.append(f"Missing required property: {required_prop}")
        
        # Validate property types and values
        for prop_name, prop_value in properties.items():
            if prop_name in schema.properties:
                prop_config = schema.properties[prop_name]
                validation_errors = self._validate_property_value(
                    prop_name, prop_value, prop_config
                )
                errors.extend(validation_errors)
        
        return errors
    
    def _validate_property_value(self, prop_name: str, value: Any, 
                                config: Dict[str, Any]) -> List[str]:
        """Validate a single property value."""
        errors = []
        prop_type = config.get("type", "string")
        
        # Type validation
        type_map = {
            "string": str,
            "text": str,
            "number": (int, float),
            "integer": int,
            "float": float,
            "boolean": bool,
            "list": list,
            "object": dict
        }
        
        expected_type = type_map.get(prop_type)
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"Property '{prop_name}' must be of type {prop_type}")
        
        # Options validation
        options = config.get("options", [])
        if options and value not in options:
            errors.append(f"Property '{prop_name}' must be one of: {options}")
        
        # Range validation for numbers
        if prop_type in ["number", "integer", "float"] and isinstance(value, (int, float)):
            min_val = config.get("min")
            max_val = config.get("max")
            
            if min_val is not None and value < min_val:
                errors.append(f"Property '{prop_name}' must be >= {min_val}")
            
            if max_val is not None and value > max_val:
                errors.append(f"Property '{prop_name}' must be <= {max_val}")
        
        return errors
    
    def export_node_documentation(self) -> str:
        """Export documentation for all registered nodes."""
        doc_lines = ["# Workflow Builder - Node Documentation\n"]
        
        for category, node_types in self.categories.items():
            doc_lines.append(f"## {category.title()} Nodes\n")
            
            for node_type in sorted(node_types):
                schema = self.node_schemas[node_type]
                doc_lines.append(f"### {schema.title}")
                doc_lines.append(f"**Type:** `{node_type}`")
                doc_lines.append(f"**Description:** {schema.description}")
                doc_lines.append("")
                
                if schema.inputs:
                    doc_lines.append("**Inputs:**")
                    for input_pin in schema.inputs:
                        required = " (required)" if input_pin.required else ""
                        doc_lines.append(f"- `{input_pin.name}` ({input_pin.type}){required}: {input_pin.description}")
                    doc_lines.append("")
                
                if schema.outputs:
                    doc_lines.append("**Outputs:**")
                    for output_pin in schema.outputs:
                        doc_lines.append(f"- `{output_pin.name}` ({output_pin.type}): {output_pin.description}")
                    doc_lines.append("")
                
                if schema.properties:
                    doc_lines.append("**Properties:**")
                    for prop_name, prop_config in schema.properties.items():
                        required = " (required)" if prop_name in schema.required_properties else ""
                        doc_lines.append(f"- `{prop_name}` ({prop_config['type']}){required}: {prop_config.get('description', '')}")
                    doc_lines.append("")
                
                doc_lines.append("---\n")
        
        return "\n".join(doc_lines)
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """Get statistics about the node factory."""
        return {
            "total_nodes": len(self.node_registry),
            "categories": len(self.categories),
            "nodes_per_category": {cat: len(nodes) for cat, nodes in self.categories.items()},
            "registered_types": list(self.node_registry.keys())
        }
