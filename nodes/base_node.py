"""
Base node class providing the foundation for all workflow nodes.
Defines the interface and common functionality for node execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import uuid
from datetime import datetime

# Import moved to method level to avoid circular dependency

class NodePin:
    """Represents an input or output pin on a node."""
    
    def __init__(self, name: str, pin_type: str, description: str = "",
                 required: bool = False, default_value: Any = None):
        """Initialize a node pin."""
        self.name = name
        self.type = pin_type
        self.description = description
        self.required = required
        self.default_value = default_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pin to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value
        }

class NodeSchema:
    """Defines the schema and metadata for a node type."""
    
    def __init__(self, node_type: str, title: str, description: str,
                 category: str, icon: str = "📦"):
        """Initialize node schema."""
        self.node_type = node_type
        self.title = title
        self.description = description
        self.category = category
        self.icon = icon
        self.inputs: List[NodePin] = []
        self.outputs: List[NodePin] = []
        self.properties: Dict[str, Any] = {}
        self.required_properties: List[str] = []
    
    def add_input(self, name: str, pin_type: str, description: str = "",
                  required: bool = False, default_value: Any = None) -> 'NodeSchema':
        """Add an input pin to the schema."""
        pin = NodePin(name, pin_type, description, required, default_value)
        self.inputs.append(pin)
        return self
    
    def add_output(self, name: str, pin_type: str, description: str = "") -> 'NodeSchema':
        """Add an output pin to the schema."""
        pin = NodePin(name, pin_type, description)
        self.outputs.append(pin)
        return self
    
    def add_property(self, name: str, prop_type: str, title: str = "",
                    description: str = "", default_value: Any = None,
                    required: bool = False, options: Optional[List[str]] = None) -> 'NodeSchema':
        """Add a property to the schema."""
        self.properties[name] = {
            "type": prop_type,
            "title": title or name.replace("_", " ").title(),
            "description": description,
            "default": default_value,
            "options": options if options is not None else []
        }
        
        if required:
            self.required_properties.append(name)
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "type": self.node_type,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "inputs": [pin.to_dict() for pin in self.inputs],
            "outputs": [pin.to_dict() for pin in self.outputs],
            "properties": self.properties,
            "required_properties": self.required_properties
        }

class BaseNode(ABC):
    """Abstract base class for all workflow nodes."""
    
    def __init__(self, node_id: str, node_data: Dict[str, Any]):
        """Initialize the base node."""
        self.node_id = node_id
        self.node_data = node_data
        self.node_type = node_data.get("type", "unknown")
        self.title = node_data.get("title", self.node_type)
        self.properties = node_data.get("properties", {})
        
        # Execution state
        self.execution_start_time: Optional[datetime] = None
        self.execution_end_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
        # Initialize the node
        self._initialize()
    
    def _initialize(self):
        """Initialize the node with default values."""
        schema = self.get_schema()
        
        # Set default property values
        for prop_name, prop_config in schema.properties.items():
            if prop_name not in self.properties:
                default_value = prop_config.get("default")
                if default_value is not None:
                    self.properties[prop_name] = default_value
    
    @classmethod
    @abstractmethod
    def get_schema(cls) -> NodeSchema:
        """Get the schema definition for this node type."""
        pass
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Execute the node with given inputs and context."""
        pass
    
    def pre_execute(self, inputs: Dict[str, Any], context: Any):
        """Called before node execution. Override for custom pre-processing."""
        self.execution_start_time = datetime.now()
        self.last_error = None
        
        # Validate inputs
        self._validate_inputs(inputs)
    
    def post_execute(self, outputs: Dict[str, Any], context: Any):
        """Called after node execution. Override for custom post-processing."""
        self.execution_end_time = datetime.now()
        
        # Validate outputs
        self._validate_outputs(outputs)
    
    def _validate_inputs(self, inputs: Dict[str, Any]):
        """Validate node inputs against schema."""
        schema = self.get_schema()
        errors = []
        
        for input_pin in schema.inputs:
            if input_pin.required and input_pin.name not in inputs:
                # Check if there's a default value
                if input_pin.default_value is not None:
                    inputs[input_pin.name] = input_pin.default_value
                else:
                    errors.append(f"Required input '{input_pin.name}' is missing")
        
        if errors:
            raise ValueError(f"Input validation failed: {'; '.join(errors)}")
    
    def _validate_outputs(self, outputs: Dict[str, Any]):
        """Validate node outputs against schema."""
        if outputs is None:
            return
        
        schema = self.get_schema()
        
        # Check that all declared outputs are present (unless optional)
        for output_pin in schema.outputs:
            if output_pin.name not in outputs:
                # For now, just log missing outputs (they might be optional)
                pass
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """Get a property value with optional default."""
        return self.properties.get(name, default)
    
    def set_property(self, name: str, value: Any):
        """Set a property value."""
        self.properties[name] = value
    
    def get_execution_time(self) -> Optional[float]:
        """Get the execution time in seconds."""
        if self.execution_start_time and self.execution_end_time:
            return (self.execution_end_time - self.execution_start_time).total_seconds()
        return None
    
    def log(self, level: str, message: str, context: Any):
        """Log a message during execution."""
        # This would typically integrate with the logging system
        print(f"[{self.node_id}] {level}: {message}")
    
    def handle_error(self, error: Exception, context: Any):
        """Handle errors during execution."""
        self.last_error = str(error)
        self.log("ERROR", f"Node execution failed: {error}", context)
        raise error
    
    def get_input_value(self, inputs: Dict[str, Any], pin_name: str, default: Any = None) -> Any:
        """Safely get an input value with optional default."""
        return inputs.get(pin_name, default)
    
    def create_output(self, **outputs) -> Dict[str, Any]:
        """Helper method to create output dictionary."""
        return outputs
    
    def validate_property_type(self, prop_name: str, expected_type: type) -> bool:
        """Validate that a property has the expected type."""
        if prop_name not in self.properties:
            return False
        
        value = self.properties[prop_name]
        return isinstance(value, expected_type)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the node's current status."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "execution_time": self.get_execution_time(),
            "last_error": self.last_error,
            "properties_count": len(self.properties)
        }
    
    def clone(self, new_id: Optional[str] = None) -> 'BaseNode':
        """Create a copy of this node with a new ID."""
        new_node_id = new_id if new_id is not None else str(uuid.uuid4())
        
        # Deep copy node data
        import copy
        new_node_data = copy.deepcopy(self.node_data)
        new_node_data["id"] = new_node_id
        
        # Create new instance
        return self.__class__(new_node_id, new_node_data)
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize the node to a dictionary."""
        return {
            "id": self.node_id,
            "type": self.node_type,
            "title": self.title,
            "properties": self.properties.copy(),
            "position": self.node_data.get("position", {"x": 0, "y": 0}),
            "inputs": self.node_data.get("inputs", []),
            "outputs": self.node_data.get("outputs", [])
        }
    
    @classmethod
    def deserialize(cls, node_data: Dict[str, Any]) -> 'BaseNode':
        """Create a node instance from serialized data."""
        node_id = node_data.get("id", str(uuid.uuid4()))
        return cls(node_id, node_data)
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"{self.__class__.__name__}(id={self.node_id}, type={self.node_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the node."""
        return (f"{self.__class__.__name__}(id='{self.node_id}', "
                f"type='{self.node_type}', title='{self.title}')")

class SimpleNode(BaseNode):
    """A simplified base class for nodes with basic functionality."""
    
    def __init__(self, node_id: str, node_data: Dict[str, Any]):
        """Initialize the simple node."""
        super().__init__(node_id, node_data)
    
    def execute(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Execute the node with pre/post processing."""
        try:
            self.pre_execute(inputs, context)
            outputs = self.process(inputs, context)
            self.post_execute(outputs, context)
            return outputs
        except Exception as e:
            self.handle_error(e, context)
            return {}  # Return empty dict on error
    
    @abstractmethod
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Process the inputs and return outputs. Override this method."""
        pass
