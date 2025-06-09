"""
Processing nodes for data transformation and manipulation.
Provides nodes for text processing, mathematical operations, filtering, etc.
"""

import re
import json
import math
import time
import threading
from typing import Dict, Any, List, Union
from datetime import datetime, timedelta
import operator
import ast

from nodes.base_node import BaseNode, NodeSchema, SimpleNode
from workflow.execution import ExecutionContext

class TextProcessorNode(SimpleNode):
    """Node for text processing operations."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("text_processor", "Text Processor",
                          "Performs various text processing operations", "Processing", "📝")
                .add_input("text", "string", "Input text to process", True)
                .add_output("result", "string", "Processed text")
                .add_output("length", "number", "Length of processed text")
                .add_property("operation", "select", "Operation",
                            "Text operation to perform", "uppercase", True,
                            ["uppercase", "lowercase", "title_case", "strip", "reverse",
                             "remove_spaces", "replace", "extract_numbers", "word_count"])
                .add_property("find_text", "string", "Find Text",
                            "Text to find (for replace operation)", "")
                .add_property("replace_text", "string", "Replace Text",
                            "Text to replace with", "")
                .add_property("regex_pattern", "string", "Regex Pattern",
                            "Regular expression pattern", ""))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        text = self.get_input_value(inputs, "text", "")
        operation = self.get_property("operation", "uppercase")
        find_text = self.get_property("find_text", "")
        replace_text = self.get_property("replace_text", "")
        regex_pattern = self.get_property("regex_pattern", "")
        
        result = text
        
        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "title_case":
            result = text.title()
        elif operation == "strip":
            result = text.strip()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "remove_spaces":
            result = re.sub(r'\s+', '', text)
        elif operation == "replace":
            if find_text:
                result = text.replace(find_text, replace_text)
        elif operation == "extract_numbers":
            numbers = re.findall(r'\d+', text)
            result = " ".join(numbers)
        elif operation == "word_count":
            word_count = len(text.split())
            result = str(word_count)
        
        # Apply regex if pattern is provided
        if regex_pattern:
            try:
                matches = re.findall(regex_pattern, result)
                result = " ".join(matches) if matches else ""
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {str(e)}")
        
        return self.create_output(
            result=result,
            length=len(result)
        )

class MathNode(SimpleNode):
    """Node for mathematical operations."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("math", "Math Operations",
                          "Performs mathematical calculations", "Processing", "🧮")
                .add_input("a", "number", "First number", True)
                .add_input("b", "number", "Second number")
                .add_output("result", "number", "Calculation result")
                .add_output("formatted", "string", "Formatted result")
                .add_property("operation", "select", "Operation",
                            "Mathematical operation to perform", "add", True,
                            ["add", "subtract", "multiply", "divide", "power", 
                             "modulo", "sqrt", "abs", "round", "floor", "ceil"])
                .add_property("precision", "number", "Decimal Precision",
                            "Number of decimal places", 2))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        a = self.get_input_value(inputs, "a", 0)
        b = self.get_input_value(inputs, "b", 0)
        operation = self.get_property("operation", "add")
        precision = int(self.get_property("precision", 2))
        
        # Convert to numbers
        try:
            a = float(a)
            if b is not None:
                b = float(b)
        except (ValueError, TypeError):
            raise ValueError("Inputs must be valid numbers")
        
        result = 0
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a / b
        elif operation == "power":
            result = a ** b
        elif operation == "modulo":
            if b == 0:
                raise ValueError("Cannot calculate modulo with zero")
            result = a % b
        elif operation == "sqrt":
            if a < 0:
                raise ValueError("Cannot calculate square root of negative number")
            result = math.sqrt(a)
        elif operation == "abs":
            result = abs(a)
        elif operation == "round":
            result = round(a, precision)
        elif operation == "floor":
            result = math.floor(a)
        elif operation == "ceil":
            result = math.ceil(a)
        
        # Format result
        formatted = f"{result:.{precision}f}" if precision > 0 else str(int(result))
        
        return self.create_output(
            result=result,
            formatted=formatted
        )

class FilterNode(SimpleNode):
    """Node for filtering data based on conditions."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("filter", "Data Filter",
                          "Filters data based on conditions", "Processing", "🔍")
                .add_input("data", "any", "Input data to filter", True)
                .add_output("filtered", "any", "Filtered data")
                .add_output("count", "number", "Number of items after filtering")
                .add_property("filter_type", "select", "Filter Type",
                            "Type of filter to apply", "contains", True,
                            ["contains", "equals", "greater_than", "less_than",
                             "starts_with", "ends_with", "regex", "custom"])
                .add_property("filter_value", "string", "Filter Value",
                            "Value to filter by", "", True)
                .add_property("case_sensitive", "boolean", "Case Sensitive",
                            "Whether filtering is case sensitive", False)
                .add_property("filter_key", "string", "Filter Key",
                            "Key to filter on (for objects)", ""))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        filter_type = self.get_property("filter_type", "contains")
        filter_value = self.get_property("filter_value", "")
        case_sensitive = self.get_property("case_sensitive", False)
        filter_key = self.get_property("filter_key", "")
        
        if data is None:
            return self.create_output(filtered=None, count=0)
        
        # Handle different data types
        if isinstance(data, str):
            filtered = self._filter_string(data, filter_type, filter_value, case_sensitive)
        elif isinstance(data, list):
            filtered = self._filter_list(data, filter_type, filter_value, case_sensitive, filter_key)
        elif isinstance(data, dict):
            filtered = self._filter_dict(data, filter_type, filter_value, case_sensitive, filter_key)
        else:
            # For other types, convert to string and filter
            filtered = self._filter_string(str(data), filter_type, filter_value, case_sensitive)
        
        count = len(filtered) if isinstance(filtered, (list, dict)) else (1 if filtered else 0)
        
        return self.create_output(
            filtered=filtered,
            count=count
        )
    
    def _filter_string(self, data: str, filter_type: str, filter_value: str, case_sensitive: bool) -> str:
        """Filter string data."""
        text = data if case_sensitive else data.lower()
        value = filter_value if case_sensitive else filter_value.lower()
        
        if filter_type == "contains":
            return data if value in text else ""
        elif filter_type == "equals":
            return data if text == value else ""
        elif filter_type == "starts_with":
            return data if text.startswith(value) else ""
        elif filter_type == "ends_with":
            return data if text.endswith(value) else ""
        elif filter_type == "regex":
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return data if re.search(filter_value, data, flags) else ""
            except re.error:
                raise ValueError(f"Invalid regex pattern: {filter_value}")
        
        return data
    
    def _filter_list(self, data: List, filter_type: str, filter_value: str, 
                     case_sensitive: bool, filter_key: str) -> List:
        """Filter list data."""
        filtered = []
        
        for item in data:
            # Get the value to check
            if filter_key and isinstance(item, dict):
                check_value = str(item.get(filter_key, ""))
            else:
                check_value = str(item)
            
            # Apply filter
            if self._matches_filter(check_value, filter_type, filter_value, case_sensitive):
                filtered.append(item)
        
        return filtered
    
    def _filter_dict(self, data: Dict, filter_type: str, filter_value: str,
                     case_sensitive: bool, filter_key: str) -> Dict:
        """Filter dictionary data."""
        if filter_key:
            # Filter based on specific key
            check_value = str(data.get(filter_key, ""))
            if self._matches_filter(check_value, filter_type, filter_value, case_sensitive):
                return data
            else:
                return {}
        else:
            # Filter based on all values
            for value in data.values():
                check_value = str(value)
                if self._matches_filter(check_value, filter_type, filter_value, case_sensitive):
                    return data
            return {}
    
    def _matches_filter(self, text: str, filter_type: str, filter_value: str, case_sensitive: bool) -> bool:
        """Check if text matches the filter."""
        if not case_sensitive:
            text = text.lower()
            filter_value = filter_value.lower()
        
        if filter_type == "contains":
            return filter_value in text
        elif filter_type == "equals":
            return text == filter_value
        elif filter_type == "starts_with":
            return text.startswith(filter_value)
        elif filter_type == "ends_with":
            return text.endswith(filter_value)
        elif filter_type == "greater_than":
            try:
                return float(text) > float(filter_value)
            except ValueError:
                return False
        elif filter_type == "less_than":
            try:
                return float(text) < float(filter_value)
            except ValueError:
                return False
        elif filter_type == "regex":
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(filter_value, text, flags))
            except re.error:
                return False
        
        return False

class TransformNode(SimpleNode):
    """Node for data transformation operations."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("transform", "Data Transform",
                          "Transforms data between different formats", "Processing", "🔄")
                .add_input("data", "any", "Input data to transform", True)
                .add_output("result", "any", "Transformed data")
                .add_output("type", "string", "Output data type")
                .add_property("transform_type", "select", "Transform Type",
                            "Type of transformation", "json_to_string", True,
                            ["json_to_string", "string_to_json", "list_to_string",
                             "string_to_list", "csv_to_json", "flatten", "unflatten"])
                .add_property("separator", "string", "Separator",
                            "Separator for string/list conversion", ",")
                .add_property("json_indent", "number", "JSON Indent",
                            "Indentation for JSON formatting", 2))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        transform_type = self.get_property("transform_type", "json_to_string")
        separator = self.get_property("separator", ",")
        json_indent = int(self.get_property("json_indent", 2))
        
        result = data
        output_type = type(data).__name__
        
        try:
            if transform_type == "json_to_string":
                if isinstance(data, (dict, list)):
                    result = json.dumps(data, indent=json_indent)
                    output_type = "string"
                else:
                    result = str(data)
                    output_type = "string"
            
            elif transform_type == "string_to_json":
                if isinstance(data, str):
                    result = json.loads(data)
                    output_type = type(result).__name__
            
            elif transform_type == "list_to_string":
                if isinstance(data, list):
                    result = separator.join(str(item) for item in data)
                    output_type = "string"
            
            elif transform_type == "string_to_list":
                if isinstance(data, str):
                    result = [item.strip() for item in data.split(separator)]
                    output_type = "list"
            
            elif transform_type == "csv_to_json":
                if isinstance(data, str):
                    lines = data.strip().split('\n')
                    if lines:
                        headers = [h.strip() for h in lines[0].split(',')]
                        result = []
                        for line in lines[1:]:
                            values = [v.strip() for v in line.split(',')]
                            if len(values) == len(headers):
                                result.append(dict(zip(headers, values)))
                        output_type = "list"
            
            elif transform_type == "flatten":
                if isinstance(data, dict):
                    result = self._flatten_dict(data)
                    output_type = "dict"
                elif isinstance(data, list):
                    result = self._flatten_list(data)
                    output_type = "list"
            
            elif transform_type == "unflatten":
                if isinstance(data, dict):
                    result = self._unflatten_dict(data)
                    output_type = "dict"
        
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Transformation failed: {str(e)}")
        
        return self.create_output(
            result=result,
            type=output_type
        )
    
    def _flatten_dict(self, data: Dict, parent_key: str = "", sep: str = ".") -> Dict:
        """Flatten nested dictionary."""
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep).items())
            else:
                items.append((new_key, value))
        return dict(items)
    
    def _flatten_list(self, data: List) -> List:
        """Flatten nested list."""
        result = []
        for item in data:
            if isinstance(item, list):
                result.extend(self._flatten_list(item))
            else:
                result.append(item)
        return result
    
    def _unflatten_dict(self, data: Dict, sep: str = ".") -> Dict:
        """Unflatten dictionary."""
        result = {}
        for key, value in data.items():
            keys = key.split(sep)
            current = result
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        return result

class ConditionalNode(SimpleNode):
    """Node for conditional logic and branching."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("conditional", "Conditional",
                          "Performs conditional logic operations", "Processing", "🔀")
                .add_input("value_a", "any", "First value", True)
                .add_input("value_b", "any", "Second value")
                .add_input("true_value", "any", "Value to output if condition is true")
                .add_input("false_value", "any", "Value to output if condition is false")
                .add_output("result", "any", "Result based on condition")
                .add_output("condition", "boolean", "Condition result")
                .add_property("operator", "select", "Operator",
                            "Comparison operator", "equals", True,
                            ["equals", "not_equals", "greater_than", "less_than",
                             "greater_equal", "less_equal", "contains", "is_empty"])
                .add_property("case_sensitive", "boolean", "Case Sensitive",
                            "Case sensitive comparison for strings", True))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        value_a = self.get_input_value(inputs, "value_a")
        value_b = self.get_input_value(inputs, "value_b")
        true_value = self.get_input_value(inputs, "true_value", True)
        false_value = self.get_input_value(inputs, "false_value", False)
        operator_type = self.get_property("operator", "equals")
        case_sensitive = self.get_property("case_sensitive", True)
        
        # Evaluate condition
        condition = self._evaluate_condition(value_a, value_b, operator_type, case_sensitive)
        
        # Select result based on condition
        result = true_value if condition else false_value
        
        return self.create_output(
            result=result,
            condition=condition
        )
    
    def _evaluate_condition(self, a: Any, b: Any, operator_type: str, case_sensitive: bool) -> bool:
        """Evaluate the condition based on operator."""
        # Handle string comparisons
        if isinstance(a, str) and isinstance(b, str) and not case_sensitive:
            a = a.lower()
            b = b.lower()
        
        try:
            if operator_type == "equals":
                return a == b
            elif operator_type == "not_equals":
                return a != b
            elif operator_type == "greater_than":
                return float(a) > float(b)
            elif operator_type == "less_than":
                return float(a) < float(b)
            elif operator_type == "greater_equal":
                return float(a) >= float(b)
            elif operator_type == "less_equal":
                return float(a) <= float(b)
            elif operator_type == "contains":
                return str(b) in str(a)
            elif operator_type == "is_empty":
                if a is None:
                    return True
                if isinstance(a, (str, list, dict)):
                    return len(a) == 0
                return False
        except (ValueError, TypeError):
            # If numeric comparison fails, fall back to string comparison
            if operator_type in ["greater_than", "less_than", "greater_equal", "less_equal"]:
                return str(a) > str(b) if operator_type.startswith("greater") else str(a) < str(b)
        
        return False

class DelayNode(SimpleNode):
    """Node for adding delays in workflow execution."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("delay", "Delay",
                          "Adds a delay in workflow execution", "Processing", "⏳")
                .add_input("data", "any", "Data to pass through")
                .add_output("data", "any", "Same data after delay")
                .add_output("delay_time", "number", "Actual delay time in seconds")
                .add_property("delay_seconds", "number", "Delay (seconds)",
                            "Number of seconds to delay", 1.0, True)
                .add_property("delay_type", "select", "Delay Type",
                            "Type of delay", "fixed", True,
                            ["fixed", "random"])
                .add_property("max_delay", "number", "Max Delay",
                            "Maximum delay for random type", 5.0))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        delay_seconds = self.get_property("delay_seconds", 1.0)
        delay_type = self.get_property("delay_type", "fixed")
        max_delay = self.get_property("max_delay", 5.0)
        
        # Calculate actual delay
        if delay_type == "random":
            import random
            actual_delay = random.uniform(delay_seconds, max_delay)
        else:
            actual_delay = delay_seconds
        
        # Perform delay
        start_time = time.time()
        time.sleep(actual_delay)
        end_time = time.time()
        
        actual_delay_time = end_time - start_time
        
        return self.create_output(
            data=data,
            delay_time=actual_delay_time
        )

class ScriptNode(SimpleNode):
    """Node for executing custom Python scripts."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("script", "Python Script",
                          "Executes custom Python code", "Processing", "🐍")
                .add_input("data", "any", "Input data")
                .add_output("result", "any", "Script output")
                .add_output("output", "string", "Print output")
                .add_property("script", "text", "Python Script",
                            "Python code to execute", "# Process data\nresult = data", True)
                .add_property("timeout", "number", "Timeout",
                            "Script timeout in seconds", 10))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        script = self.get_property("script", "result = data")
        timeout = self.get_property("timeout", 10)
        
        # Prepare execution environment
        import io
        import contextlib
        
        # Capture stdout
        output_buffer = io.StringIO()
        
        # Create safe execution environment
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
            },
            'data': data,
            'context': context,
            'json': json,
            'math': math,
            're': re,
            'datetime': datetime,
        }
        
        local_vars = {}
        
        try:
            # Execute script with timeout
            with contextlib.redirect_stdout(output_buffer):
                # Compile and execute
                compiled_script = compile(script, '<script>', 'exec')
                exec(compiled_script, safe_globals, local_vars)
            
            # Get result
            result = local_vars.get('result', data)
            output = output_buffer.getvalue()
            
            return self.create_output(
                result=result,
                output=output
            )
            
        except SyntaxError as e:
            raise ValueError(f"Script syntax error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Script execution error: {str(e)}")

class AggregateNode(SimpleNode):
    """Node for aggregating data collections."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("aggregate", "Aggregate Data",
                          "Performs aggregation operations on data", "Processing", "📊")
                .add_input("data", "list", "List of data to aggregate", True)
                .add_output("result", "any", "Aggregation result")
                .add_output("count", "number", "Number of items processed")
                .add_property("operation", "select", "Operation",
                            "Aggregation operation", "sum", True,
                            ["sum", "average", "min", "max", "count", "unique",
                             "join", "first", "last"])
                .add_property("field", "string", "Field",
                            "Field to aggregate (for objects)", "")
                .add_property("separator", "string", "Separator",
                            "Separator for join operation", ", "))
    
    def process(self, inputs: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data", [])
        operation = self.get_property("operation", "sum")
        field = self.get_property("field", "")
        separator = self.get_property("separator", ", ")
        
        if not isinstance(data, list):
            raise ValueError("Input data must be a list")
        
        # Extract values to aggregate
        if field and all(isinstance(item, dict) for item in data):
            values = [item.get(field) for item in data if field in item]
        else:
            values = data
        
        count = len(values)
        result = None
        
        if operation == "sum":
            try:
                result = sum(float(v) for v in values if v is not None)
            except (ValueError, TypeError):
                result = 0
        
        elif operation == "average":
            try:
                numeric_values = [float(v) for v in values if v is not None]
                result = sum(numeric_values) / len(numeric_values) if numeric_values else 0
            except (ValueError, TypeError):
                result = 0
        
        elif operation == "min":
            try:
                numeric_values = [float(v) for v in values if v is not None]
                result = min(numeric_values) if numeric_values else None
            except (ValueError, TypeError):
                result = min(values) if values else None
        
        elif operation == "max":
            try:
                numeric_values = [float(v) for v in values if v is not None]
                result = max(numeric_values) if numeric_values else None
            except (ValueError, TypeError):
                result = max(values) if values else None
        
        elif operation == "count":
            result = count
        
        elif operation == "unique":
            result = list(set(str(v) for v in values if v is not None))
        
        elif operation == "join":
            result = separator.join(str(v) for v in values if v is not None)
        
        elif operation == "first":
            result = values[0] if values else None
        
        elif operation == "last":
            result = values[-1] if values else None
        
        return self.create_output(
            result=result,
            count=count
        )
