"""
Input nodes for reading data from various sources.
Provides nodes for text input, file reading, API calls, etc.
"""

import os
import json
import requests
import time
from typing import Dict, Any
from datetime import datetime
import threading

from nodes.base_node import BaseNode, NodeSchema, SimpleNode
# Import moved to avoid circular dependency

class TextInputNode(SimpleNode):
    """Node for inputting static text data."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("text_input", "Text Input", 
                          "Provides static text input to the workflow", "Input", "📝")
                .add_output("text", "string", "The input text")
                .add_property("text", "text", "Input Text", 
                            "Enter the text to output", "", True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        text = self.get_property("text", "")
        return self.create_output(text=text)

class NumberInputNode(SimpleNode):
    """Node for inputting numeric values."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("number_input", "Number Input",
                          "Provides numeric input to the workflow", "Input", "🔢")
                .add_output("number", "number", "The input number")
                .add_property("value", "number", "Number Value",
                            "Enter the numeric value", 0, True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        value = self.get_property("value", 0)
        return self.create_output(number=value)

class FileInputNode(SimpleNode):
    """Node for reading data from files."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("file_input", "File Input",
                          "Reads content from a file", "Input", "📁")
                .add_output("content", "string", "File content as text")
                .add_output("filename", "string", "Name of the file")
                .add_output("size", "number", "File size in bytes")
                .add_property("file_path", "file", "File Path",
                            "Path to the file to read", "", True)
                .add_property("encoding", "string", "Encoding",
                            "Text encoding (e.g., utf-8)", "utf-8"))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        file_path = self.get_property("file_path", "")
        encoding = self.get_property("encoding", "utf-8")
        
        if not file_path:
            raise ValueError("File path is required")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            file_stats = os.stat(file_path)
            filename = os.path.basename(file_path)
            
            return self.create_output(
                content=content,
                filename=filename,
                size=file_stats.st_size
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {str(e)}")

class APIInputNode(SimpleNode):
    """Node for making HTTP API requests."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("api_input", "API Input",
                          "Makes HTTP requests to APIs", "Input", "🌐")
                .add_output("response", "string", "Response body")
                .add_output("status_code", "number", "HTTP status code")
                .add_output("headers", "object", "Response headers")
                .add_property("url", "string", "URL", 
                            "API endpoint URL", "", True)
                .add_property("method", "select", "HTTP Method",
                            "HTTP method to use", "GET", True, 
                            ["GET", "POST", "PUT", "DELETE", "PATCH"])
                .add_property("headers", "text", "Headers",
                            "JSON object with request headers", "{}")
                .add_property("body", "text", "Request Body",
                            "Request body (for POST/PUT)", "")
                .add_property("timeout", "number", "Timeout",
                            "Request timeout in seconds", 30))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        url = self.get_property("url", "")
        method = self.get_property("method", "GET").upper()
        headers_text = self.get_property("headers", "{}")
        body = self.get_property("body", "")
        timeout = self.get_property("timeout", 30)
        
        if not url:
            raise ValueError("URL is required")
        
        # Parse headers
        try:
            headers = json.loads(headers_text) if headers_text.strip() else {}
        except json.JSONDecodeError:
            raise ValueError("Headers must be valid JSON")
        
        # Prepare request data
        request_kwargs = {
            "url": url,
            "method": method,
            "headers": headers,
            "timeout": timeout
        }
        
        if method in ["POST", "PUT", "PATCH"] and body:
            # Try to parse as JSON, otherwise send as text
            try:
                request_kwargs["json"] = json.loads(body)
            except json.JSONDecodeError:
                request_kwargs["data"] = body
        
        try:
            response = requests.request(**request_kwargs)
            
            return self.create_output(
                response=response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")

class DatabaseInputNode(SimpleNode):
    """Node for querying databases."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("database_input", "Database Input",
                          "Executes database queries", "Input", "🗄️")
                .add_output("data", "list", "Query results as list of records")
                .add_output("count", "number", "Number of records returned")
                .add_property("connection_string", "string", "Connection String",
                            "Database connection string", "", True)
                .add_property("query", "text", "SQL Query",
                            "SQL query to execute", "", True)
                .add_property("parameters", "text", "Parameters",
                            "JSON object with query parameters", "{}"))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        connection_string = self.get_property("connection_string", "")
        query = self.get_property("query", "")
        parameters_text = self.get_property("parameters", "{}")
        
        if not connection_string or not query:
            raise ValueError("Connection string and query are required")
        
        # Parse parameters
        try:
            parameters = json.loads(parameters_text) if parameters_text.strip() else {}
        except json.JSONDecodeError:
            raise ValueError("Parameters must be valid JSON")
        
        # For demo purposes, return mock data
        # In real implementation, you would use appropriate database drivers
        mock_data = [
            {"id": 1, "name": "Sample Record 1", "timestamp": datetime.now().isoformat()},
            {"id": 2, "name": "Sample Record 2", "timestamp": datetime.now().isoformat()}
        ]
        
        return self.create_output(
            data=mock_data,
            count=len(mock_data)
        )

class TimerNode(SimpleNode):
    """Node that triggers at specified intervals."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("timer", "Timer",
                          "Generates periodic triggers", "Input", "⏰")
                .add_output("timestamp", "string", "Current timestamp")
                .add_output("tick_count", "number", "Number of ticks elapsed")
                .add_property("interval", "number", "Interval",
                            "Interval in seconds", 1.0, True)
                .add_property("max_ticks", "number", "Max Ticks",
                            "Maximum number of ticks (0 = unlimited)", 0))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        interval = self.get_property("interval", 1.0)
        max_ticks = self.get_property("max_ticks", 0)
        
        # Get current tick count from context
        tick_key = f"timer_{self.node_id}_ticks"
        tick_count = context.get_data(tick_key, 0)
        
        # Check if we've reached max ticks
        if max_ticks > 0 and tick_count >= max_ticks:
            raise StopIteration("Timer has reached maximum ticks")
        
        # Wait for interval (in real implementation, this would be handled differently)
        if tick_count > 0:  # Don't wait on first tick
            time.sleep(interval)
        
        # Increment tick count
        tick_count += 1
        context.set_data(tick_key, tick_count)
        
        return self.create_output(
            timestamp=datetime.now().isoformat(),
            tick_count=tick_count
        )

class VariableInputNode(SimpleNode):
    """Node for reading global variables."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("variable_input", "Variable Input",
                          "Reads a global variable value", "Input", "📤")
                .add_output("value", "any", "Variable value")
                .add_output("exists", "boolean", "Whether variable exists")
                .add_property("variable_name", "string", "Variable Name",
                            "Name of the variable to read", "", True)
                .add_property("default_value", "string", "Default Value",
                            "Default value if variable doesn't exist", ""))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        variable_name = self.get_property("variable_name", "")
        default_value = self.get_property("default_value", "")
        
        if not variable_name:
            raise ValueError("Variable name is required")
        
        # Check if variable exists
        value = context.get_variable(variable_name)
        exists = value is not None
        
        if not exists:
            value = default_value
        
        return self.create_output(
            value=value,
            exists=exists
        )

class JSONInputNode(SimpleNode):
    """Node for inputting JSON data."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("json_input", "JSON Input",
                          "Provides JSON data input", "Input", "📋")
                .add_output("data", "object", "Parsed JSON data")
                .add_output("is_valid", "boolean", "Whether JSON is valid")
                .add_property("json_text", "text", "JSON Data",
                            "JSON formatted text", "{}", True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        json_text = self.get_property("json_text", "{}")
        
        try:
            data = json.loads(json_text)
            is_valid = True
        except json.JSONDecodeError as e:
            # Return error information instead of raising
            data = {"error": str(e), "input": json_text}
            is_valid = False
        
        return self.create_output(
            data=data,
            is_valid=is_valid
        )

class EnvironmentVariableNode(SimpleNode):
    """Node for reading environment variables."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("env_var", "Environment Variable",
                          "Reads system environment variables", "Input", "🌍")
                .add_output("value", "string", "Environment variable value")
                .add_output("exists", "boolean", "Whether variable exists")
                .add_property("var_name", "string", "Variable Name",
                            "Name of environment variable", "", True)
                .add_property("default_value", "string", "Default Value",
                            "Default value if variable doesn't exist", ""))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        var_name = self.get_property("var_name", "")
        default_value = self.get_property("default_value", "")
        
        if not var_name:
            raise ValueError("Variable name is required")
        
        value = os.getenv(var_name, default_value)
        exists = var_name in os.environ
        
        return self.create_output(
            value=value,
            exists=exists
        )
