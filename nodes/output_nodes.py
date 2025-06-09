"""
Output nodes for saving and sending data to various destinations.
Provides nodes for file output, API calls, notifications, etc.
"""

import os
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime
import csv
import io

from nodes.base_node import BaseNode, NodeSchema, SimpleNode
from workflow.execution import Any

class TextOutputNode(SimpleNode):
    """Node for outputting text data."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("text_output", "Text Output",
                          "Displays or stores text output", "Output", "📄")
                .add_input("text", "string", "Text to output", True)
                .add_output("output", "string", "The output text")
                .add_output("length", "number", "Length of output text")
                .add_property("prefix", "string", "Prefix",
                            "Text to prepend", "")
                .add_property("suffix", "string", "Suffix",
                            "Text to append", "")
                .add_property("format", "select", "Format",
                            "Output format", "plain", True,
                            ["plain", "uppercase", "lowercase", "title"]))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        text = self.get_input_value(inputs, "text", "")
        prefix = self.get_property("prefix", "")
        suffix = self.get_property("suffix", "")
        format_type = self.get_property("format", "plain")
        
        # Apply formatting
        if format_type == "uppercase":
            text = text.upper()
        elif format_type == "lowercase":
            text = text.lower()
        elif format_type == "title":
            text = text.title()
        
        # Add prefix and suffix
        output = f"{prefix}{text}{suffix}"
        
        return self.create_output(
            output=output,
            length=len(output)
        )

class FileOutputNode(SimpleNode):
    """Node for writing data to files."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("file_output", "File Output",
                          "Writes data to a file", "Output", "💾")
                .add_input("data", "any", "Data to write", True)
                .add_output("file_path", "string", "Path of written file")
                .add_output("bytes_written", "number", "Number of bytes written")
                .add_property("file_path", "file", "File Path",
                            "Path where to save the file", "", True)
                .add_property("format", "select", "Format",
                            "Output format", "text", True,
                            ["text", "json", "csv"])
                .add_property("encoding", "string", "Encoding",
                            "Text encoding", "utf-8")
                .add_property("append", "boolean", "Append",
                            "Append to existing file", False))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        file_path = self.get_property("file_path", "")
        format_type = self.get_property("format", "text")
        encoding = self.get_property("encoding", "utf-8")
        append = self.get_property("append", False)
        
        if not file_path:
            raise ValueError("File path is required")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Format data based on type
        if format_type == "json":
            if isinstance(data, (dict, list)):
                content = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                content = json.dumps({"data": data}, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            content = self._format_as_csv(data)
        else:  # text
            content = str(data)
        
        # Write to file
        mode = "a" if append else "w"
        try:
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
                if append and not content.endswith('\n'):
                    f.write('\n')
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return self.create_output(
                file_path=file_path,
                bytes_written=file_size
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to write file: {str(e)}")
    
    def _format_as_csv(self, data: Any) -> str:
        """Format data as CSV."""
        output = io.StringIO()
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, list):
            # Simple list
            writer = csv.writer(output)
            for item in data:
                writer.writerow([item])
        else:
            # Single value
            writer = csv.writer(output)
            writer.writerow([data])
        
        return output.getvalue()

class APIOutputNode(SimpleNode):
    """Node for sending data via HTTP API."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("api_output", "API Output",
                          "Sends data to HTTP API endpoints", "Output", "🌐")
                .add_input("data", "any", "Data to send", True)
                .add_output("response", "string", "API response")
                .add_output("status_code", "number", "HTTP status code")
                .add_output("success", "boolean", "Whether request was successful")
                .add_property("url", "string", "URL",
                            "API endpoint URL", "", True)
                .add_property("method", "select", "HTTP Method",
                            "HTTP method to use", "POST", True,
                            ["GET", "POST", "PUT", "DELETE", "PATCH"])
                .add_property("headers", "text", "Headers",
                            "JSON object with request headers", "{}")
                .add_property("timeout", "number", "Timeout",
                            "Request timeout in seconds", 30)
                .add_property("data_key", "string", "Data Key",
                            "Key name for data in request body", "data"))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        url = self.get_property("url", "")
        method = self.get_property("method", "POST").upper()
        headers_text = self.get_property("headers", "{}")
        timeout = self.get_property("timeout", 30)
        data_key = self.get_property("data_key", "data")
        
        if not url:
            raise ValueError("URL is required")
        
        # Parse headers
        try:
            headers = json.loads(headers_text) if headers_text.strip() else {}
        except json.JSONDecodeError:
            raise ValueError("Headers must be valid JSON")
        
        # Prepare request body
        if method in ["POST", "PUT", "PATCH"]:
            if data_key:
                payload = {data_key: data}
            else:
                payload = data if isinstance(data, dict) else {"data": data}
        else:
            payload = None
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            success = 200 <= response.status_code < 300
            
            return self.create_output(
                response=response.text,
                status_code=response.status_code,
                success=success
            )
            
        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {str(e)}")

class DatabaseOutputNode(SimpleNode):
    """Node for writing data to databases."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("database_output", "Database Output",
                          "Writes data to database tables", "Output", "🗄️")
                .add_input("data", "any", "Data to insert/update", True)
                .add_output("rows_affected", "number", "Number of rows affected")
                .add_output("success", "boolean", "Whether operation was successful")
                .add_property("connection_string", "string", "Connection String",
                            "Database connection string", "", True)
                .add_property("table_name", "string", "Table Name",
                            "Name of the table", "", True)
                .add_property("operation", "select", "Operation",
                            "Database operation", "insert", True,
                            ["insert", "update", "upsert"])
                .add_property("key_field", "string", "Key Field",
                            "Field to use as key for updates", "id"))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        data = self.get_input_value(inputs, "data")
        connection_string = self.get_property("connection_string", "")
        table_name = self.get_property("table_name", "")
        operation = self.get_property("operation", "insert")
        key_field = self.get_property("key_field", "id")
        
        if not connection_string or not table_name:
            raise ValueError("Connection string and table name are required")
        
        # For demo purposes, simulate database operation
        # In real implementation, you would use appropriate database drivers
        
        if isinstance(data, list):
            rows_affected = len(data)
        elif isinstance(data, dict):
            rows_affected = 1
        else:
            rows_affected = 1
        
        # Simulate operation based on type
        success = True
        
        return self.create_output(
            rows_affected=rows_affected,
            success=success
        )

class EmailNode(SimpleNode):
    """Node for sending emails."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("email", "Email",
                          "Sends emails via SMTP", "Output", "📧")
                .add_input("subject", "string", "Email subject")
                .add_input("body", "string", "Email body", True)
                .add_input("attachments", "list", "List of file paths to attach")
                .add_output("sent", "boolean", "Whether email was sent")
                .add_output("message_id", "string", "Message ID")
                .add_property("smtp_server", "string", "SMTP Server",
                            "SMTP server hostname", "smtp.gmail.com", True)
                .add_property("smtp_port", "number", "SMTP Port",
                            "SMTP server port", 587)
                .add_property("username", "string", "Username",
                            "SMTP username/email", "", True)
                .add_property("password", "string", "Password",
                            "SMTP password/app password", "", True)
                .add_property("to_email", "string", "To Email",
                            "Recipient email address", "", True)
                .add_property("from_name", "string", "From Name",
                            "Sender display name", "")
                .add_property("use_tls", "boolean", "Use TLS",
                            "Use TLS encryption", True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        subject = self.get_input_value(inputs, "subject", "No Subject")
        body = self.get_input_value(inputs, "body", "")
        attachments = self.get_input_value(inputs, "attachments", [])
        
        smtp_server = self.get_property("smtp_server", "smtp.gmail.com")
        smtp_port = int(self.get_property("smtp_port", 587))
        username = self.get_property("username", "")
        password = self.get_property("password", "")
        to_email = self.get_property("to_email", "")
        from_name = self.get_property("from_name", "")
        use_tls = self.get_property("use_tls", True)
        
        if not all([username, password, to_email, body]):
            raise ValueError("Username, password, to_email, and body are required")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{username}>" if from_name else username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            attachment = MIMEText(f.read())
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            msg.attach(attachment)
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            server.login(username, password)
            
            text = msg.as_string()
            server.sendmail(username, to_email, text)
            server.quit()
            
            # Generate message ID
            message_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(text) % 10000}"
            
            return self.create_output(
                sent=True,
                message_id=message_id
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {str(e)}")

class NotificationNode(SimpleNode):
    """Node for sending system notifications."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("notification", "Notification",
                          "Sends system notifications", "Output", "🔔")
                .add_input("message", "string", "Notification message", True)
                .add_input("title", "string", "Notification title")
                .add_output("sent", "boolean", "Whether notification was sent")
                .add_property("notification_type", "select", "Type",
                            "Type of notification", "info", True,
                            ["info", "warning", "error", "success"])
                .add_property("sound", "boolean", "Sound",
                            "Play notification sound", True)
                .add_property("timeout", "number", "Timeout",
                            "Notification timeout in seconds", 5))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        message = self.get_input_value(inputs, "message", "")
        title = self.get_input_value(inputs, "title", "Workflow Notification")
        notification_type = self.get_property("notification_type", "info")
        sound = self.get_property("sound", True)
        timeout = self.get_property("timeout", 5)
        
        if not message:
            raise ValueError("Message is required")
        
        try:
            # Try to send system notification (cross-platform)
            sent = self._send_system_notification(title, message, notification_type)
            
            return self.create_output(sent=sent)
            
        except Exception as e:
            # Fall back to console output
            print(f"[{notification_type.upper()}] {title}: {message}")
            return self.create_output(sent=False)
    
    def _send_system_notification(self, title: str, message: str, notification_type: str) -> bool:
        """Send system notification using available methods."""
        try:
            # Try plyer for cross-platform notifications
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=self.get_property("timeout", 5)
            )
            return True
        except ImportError:
            pass
        
        # Platform-specific fallbacks
        import platform
        system = platform.system()
        
        if system == "Windows":
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=5)
                return True
            except ImportError:
                pass
        
        elif system == "Darwin":  # macOS
            try:
                os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
                return True
            except:
                pass
        
        elif system == "Linux":
            try:
                os.system(f'notify-send "{title}" "{message}"')
                return True
            except:
                pass
        
        return False

class LogOutputNode(SimpleNode):
    """Node for logging messages."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("log_output", "Log Output",
                          "Logs messages to the workflow log", "Output", "📝")
                .add_input("message", "string", "Message to log", True)
                .add_input("data", "any", "Additional data to log")
                .add_output("logged", "boolean", "Whether message was logged")
                .add_property("log_level", "select", "Log Level",
                            "Logging level", "INFO", True,
                            ["DEBUG", "INFO", "WARNING", "ERROR"])
                .add_property("include_timestamp", "boolean", "Include Timestamp",
                            "Include timestamp in log", True)
                .add_property("include_data", "boolean", "Include Data",
                            "Include additional data in log", True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        message = self.get_input_value(inputs, "message", "")
        data = self.get_input_value(inputs, "data")
        log_level = self.get_property("log_level", "INFO")
        include_timestamp = self.get_property("include_timestamp", True)
        include_data = self.get_property("include_data", True)
        
        if not message:
            raise ValueError("Message is required")
        
        # Format log message
        log_message = message
        
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {log_message}"
        
        if include_data and data is not None:
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, indent=2)
            else:
                data_str = str(data)
            log_message += f"\nData: {data_str}"
        
        # Log to workflow execution context
        # This would integrate with the main logging system
        print(f"[{log_level}] {log_message}")
        
        return self.create_output(logged=True)

class WebhookNode(SimpleNode):
    """Node for sending webhook notifications."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("webhook", "Webhook",
                          "Sends webhook notifications", "Output", "🔗")
                .add_input("payload", "any", "Webhook payload", True)
                .add_output("response", "string", "Webhook response")
                .add_output("status_code", "number", "HTTP status code")
                .add_output("success", "boolean", "Whether webhook was successful")
                .add_property("webhook_url", "string", "Webhook URL",
                            "URL to send webhook to", "", True)
                .add_property("secret", "string", "Secret",
                            "Webhook secret for signing", "")
                .add_property("content_type", "select", "Content Type",
                            "Request content type", "application/json", True,
                            ["application/json", "application/x-www-form-urlencoded"])
                .add_property("timeout", "number", "Timeout",
                            "Request timeout in seconds", 30))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        payload = self.get_input_value(inputs, "payload")
        webhook_url = self.get_property("webhook_url", "")
        secret = self.get_property("secret", "")
        content_type = self.get_property("content_type", "application/json")
        timeout = self.get_property("timeout", 30)
        
        if not webhook_url:
            raise ValueError("Webhook URL is required")
        
        # Prepare headers
        headers = {"Content-Type": content_type}
        
        # Add signature if secret is provided
        if secret:
            import hmac
            import hashlib
            
            payload_str = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)
            signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Signature-SHA256"] = f"sha256={signature}"
        
        try:
            if content_type == "application/json":
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
            else:
                response = requests.post(
                    webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=timeout
                )
            
            success = 200 <= response.status_code < 300
            
            return self.create_output(
                response=response.text,
                status_code=response.status_code,
                success=success
            )
            
        except requests.RequestException as e:
            raise RuntimeError(f"Webhook request failed: {str(e)}")

class VariableOutputNode(SimpleNode):
    """Node for setting global variables."""
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return (NodeSchema("variable_output", "Variable Output",
                          "Sets a global variable value", "Output", "📥")
                .add_input("value", "any", "Value to store", True)
                .add_output("stored", "boolean", "Whether value was stored")
                .add_output("previous_value", "any", "Previous variable value")
                .add_property("variable_name", "string", "Variable Name",
                            "Name of the variable to set", "", True)
                .add_property("overwrite", "boolean", "Overwrite",
                            "Overwrite existing variable", True))
    
    def process(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        value = self.get_input_value(inputs, "value")
        variable_name = self.get_property("variable_name", "")
        overwrite = self.get_property("overwrite", True)
        
        if not variable_name:
            raise ValueError("Variable name is required")
        
        # Get previous value
        previous_value = context.get_variable(variable_name)
        
        # Set variable if overwrite is true or variable doesn't exist
        stored = False
        if overwrite or previous_value is None:
            context.set_variable(variable_name, value)
            stored = True
        
        return self.create_output(
            stored=stored,
            previous_value=previous_value
        )
