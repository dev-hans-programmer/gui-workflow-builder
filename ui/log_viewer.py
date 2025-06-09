"""
Modern log viewer with real-time updates and beautiful styling.
Provides filtered logging, auto-scroll, and export functionality.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Dict, Optional, Callable
from datetime import datetime
import threading
import queue
from app.themes import ThemeManager

class LogEntry:
    """Represents a single log entry."""
    
    def __init__(self, timestamp: datetime, level: str, message: str, 
                 node_id: Optional[str] = None, details: Optional[Dict] = None):
        """Initialize a log entry."""
        self.timestamp = timestamp
        self.level = level.upper()
        self.message = message
        self.node_id = node_id
        self.details = details or {}
    
    def to_string(self) -> str:
        """Convert log entry to string format."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        node_str = f"[{self.node_id[:8]}...]" if self.node_id else "[SYSTEM]"
        return f"{time_str} {node_str} {self.level}: {self.message}"

class LogViewer(ctk.CTkFrame):
    """Modern log viewer with real-time updates and filtering."""
    
    def __init__(self, parent, theme_manager: ThemeManager):
        """Initialize the log viewer."""
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        
        # Log state
        self.log_entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.log_queue = queue.Queue()
        self.auto_scroll = True
        self.max_entries = 1000
        
        # Filter settings
        self.filter_level = "ALL"
        self.filter_text = ""
        self.filter_node = ""
        
        self._create_header()
        self._create_filter_controls()
        self._create_log_display()
        self._create_controls()
        
        # Start log processing thread
        self._start_log_processor()
    
    def _create_header(self):
        """Create the log viewer header."""
        self.header_frame = ctk.CTkFrame(self, height=40)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📋 Execution Logs",
            font=("Arial", 12, "bold")
        )
        self.title_label.pack(side="left", padx=10, pady=10)
        
        # Entry count
        self.count_label = ctk.CTkLabel(
            self.header_frame,
            text="0 entries",
            font=("Arial", 10)
        )
        self.count_label.pack(side="right", padx=10, pady=10)
    
    def _create_filter_controls(self):
        """Create filter and search controls."""
        self.filter_frame = ctk.CTkFrame(self, height=50)
        self.filter_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.filter_frame.pack_propagate(False)
        
        # Level filter
        self.level_label = ctk.CTkLabel(self.filter_frame, text="Level:")
        self.level_label.pack(side="left", padx=(10, 5), pady=15)
        
        self.level_filter = ctk.CTkComboBox(
            self.filter_frame,
            values=["ALL", "ERROR", "WARNING", "INFO", "DEBUG"],
            width=80,
            command=self._on_filter_changed
        )
        self.level_filter.pack(side="left", padx=5, pady=15)
        self.level_filter.set("ALL")
        
        # Search box
        self.search_label = ctk.CTkLabel(self.filter_frame, text="Search:")
        self.search_label.pack(side="left", padx=(15, 5), pady=15)
        
        self.search_entry = ctk.CTkEntry(
            self.filter_frame,
            placeholder_text="Filter messages...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5, pady=15)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # Auto-scroll toggle
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.autoscroll_check = ctk.CTkCheckBox(
            self.filter_frame,
            text="Auto-scroll",
            variable=self.autoscroll_var,
            command=self._on_autoscroll_changed
        )
        self.autoscroll_check.pack(side="right", padx=10, pady=15)
    
    def _create_log_display(self):
        """Create the main log display area."""
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Text widget with scrollbar
        self.log_text = ctk.CTkTextbox(
            self.display_frame,
            wrap="word",
            state="disabled",
            font=("Courier", 10)
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure text tags for different log levels
        self._configure_log_tags()
    
    def _create_controls(self):
        """Create control buttons."""
        self.controls_frame = ctk.CTkFrame(self, height=40)
        self.controls_frame.pack(fill="x", padx=5, pady=5)
        self.controls_frame.pack_propagate(False)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            self.controls_frame,
            text="🗑️ Clear",
            width=80,
            height=30,
            command=self.clear_logs
        )
        self.clear_btn.pack(side="left", padx=10, pady=5)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.controls_frame,
            text="💾 Export",
            width=80,
            height=30,
            command=self.export_logs
        )
        self.export_btn.pack(side="left", padx=5, pady=5)
        
        # Pause/Resume button
        self.pause_var = tk.BooleanVar(value=False)
        self.pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏸️ Pause",
            width=80,
            height=30,
            command=self._toggle_pause
        )
        self.pause_btn.pack(side="left", padx=5, pady=5)
        
        # Status indicator
        self.status_label = ctk.CTkLabel(
            self.controls_frame,
            text="● Ready",
            font=("Arial", 10)
        )
        self.status_label.pack(side="right", padx=10, pady=5)
    
    def _configure_log_tags(self):
        """Configure text tags for different log levels."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Configure tags in the text widget
        self.log_text.tag_config("ERROR", foreground=colors["error"])
        self.log_text.tag_config("WARNING", foreground=colors["warning"])
        self.log_text.tag_config("INFO", foreground=colors["info"])
        self.log_text.tag_config("DEBUG", foreground=colors["text_secondary"])
        self.log_text.tag_config("SUCCESS", foreground=colors["success"])
        self.log_text.tag_config("TIMESTAMP", foreground=colors["text_secondary"])
        self.log_text.tag_config("NODE", foreground=colors["accent_primary"])
    
    def _start_log_processor(self):
        """Start the background log processing thread."""
        def process_logs():
            while True:
                try:
                    # Process queued log entries
                    entries_processed = 0
                    while not self.log_queue.empty() and entries_processed < 50:
                        entry = self.log_queue.get_nowait()
                        self._add_log_entry_internal(entry)
                        entries_processed += 1
                    
                    # Update display if entries were processed
                    if entries_processed > 0:
                        self.after(0, self._update_display)
                    
                    # Small delay to prevent excessive CPU usage
                    threading.Event().wait(0.1)
                    
                except Exception as e:
                    print(f"Log processor error: {e}")
        
        log_thread = threading.Thread(target=process_logs, daemon=True)
        log_thread.start()
    
    def add_log(self, level: str, message: str, node_id: Optional[str] = None, 
                details: Optional[Dict] = None):
        """Add a log entry (thread-safe)."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            node_id=node_id,
            details=details
        )
        
        # Add to queue for processing
        self.log_queue.put(entry)
    
    def _add_log_entry_internal(self, entry: LogEntry):
        """Add log entry to internal storage."""
        self.log_entries.append(entry)
        
        # Limit number of entries
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        
        # Apply filters
        if self._entry_matches_filters(entry):
            self.filtered_entries.append(entry)
            
            # Limit filtered entries too
            if len(self.filtered_entries) > self.max_entries:
                self.filtered_entries = self.filtered_entries[-self.max_entries:]
    
    def _entry_matches_filters(self, entry: LogEntry) -> bool:
        """Check if entry matches current filters."""
        # Level filter
        if self.filter_level != "ALL" and entry.level != self.filter_level:
            return False
        
        # Text filter
        if self.filter_text:
            if (self.filter_text.lower() not in entry.message.lower() and
                self.filter_text.lower() not in (entry.node_id or "").lower()):
                return False
        
        # Node filter
        if self.filter_node and entry.node_id != self.filter_node:
            return False
        
        return True
    
    def _update_display(self):
        """Update the log display."""
        if self.pause_var.get():
            return
        
        # Enable text widget for modification
        self.log_text.configure(state="normal")
        
        # Clear and rebuild display (more efficient for filtering)
        self.log_text.delete("1.0", "end")
        
        # Add filtered entries
        for entry in self.filtered_entries[-500:]:  # Show last 500 entries
            self._insert_log_entry(entry)
        
        # Disable text widget
        self.log_text.configure(state="disabled")
        
        # Auto-scroll to bottom
        if self.auto_scroll:
            self.log_text.see("end")
        
        # Update count
        self.count_label.configure(
            text=f"{len(self.filtered_entries)} / {len(self.log_entries)} entries"
        )
    
    def _insert_log_entry(self, entry: LogEntry):
        """Insert a single log entry into the text widget."""
        # Format timestamp
        time_str = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Insert timestamp
        self.log_text.insert("end", time_str, "TIMESTAMP")
        self.log_text.insert("end", " ")
        
        # Insert node ID
        if entry.node_id:
            node_str = f"[{entry.node_id[:8]}...]"
        else:
            node_str = "[SYSTEM]"
        
        self.log_text.insert("end", node_str, "NODE")
        self.log_text.insert("end", " ")
        
        # Insert level
        level_str = f"{entry.level}:"
        self.log_text.insert("end", level_str, entry.level)
        self.log_text.insert("end", " ")
        
        # Insert message
        self.log_text.insert("end", entry.message)
        self.log_text.insert("end", "\n")
    
    def _on_filter_changed(self, value):
        """Handle filter level change."""
        self.filter_level = value
        self._apply_filters()
    
    def _on_search_changed(self, event):
        """Handle search text change."""
        self.filter_text = self.search_entry.get()
        self._apply_filters()
    
    def _on_autoscroll_changed(self):
        """Handle auto-scroll toggle."""
        self.auto_scroll = self.autoscroll_var.get()
    
    def _apply_filters(self):
        """Reapply all filters to log entries."""
        self.filtered_entries.clear()
        
        for entry in self.log_entries:
            if self._entry_matches_filters(entry):
                self.filtered_entries.append(entry)
        
        self._update_display()
    
    def _toggle_pause(self):
        """Toggle pause/resume of log updates."""
        paused = self.pause_var.get()
        self.pause_var.set(not paused)
        
        if self.pause_var.get():
            self.pause_btn.configure(text="▶️ Resume")
            self.status_label.configure(text="⏸️ Paused")
        else:
            self.pause_btn.configure(text="⏸️ Pause")
            self.status_label.configure(text="● Running")
            self._update_display()
    
    def clear_logs(self):
        """Clear all log entries."""
        self.log_entries.clear()
        self.filtered_entries.clear()
        
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        
        self.count_label.configure(text="0 entries")
        
        # Clear the queue
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break
        
        self.add_log("INFO", "Log cleared", None)
    
    def export_logs(self):
        """Export logs to a file."""
        from tkinter import filedialog
        
        if not self.log_entries:
            tk.messagebox.showwarning("Warning", "No logs to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".log",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# Workflow Builder Execution Log\n")
                    f.write(f"# Exported: {datetime.now().isoformat()}\n")
                    f.write(f"# Total entries: {len(self.log_entries)}\n\n")
                    
                    for entry in self.log_entries:
                        f.write(entry.to_string() + "\n")
                        
                        # Add details if available
                        if entry.details:
                            for key, value in entry.details.items():
                                f.write(f"  {key}: {value}\n")
                            f.write("\n")
                
                self.add_log("INFO", f"Logs exported to {file_path}")
                
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to export logs: {str(e)}")
    
    def apply_theme(self):
        """Apply the current theme to the log viewer."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Update main frame
        self.configure(fg_color=colors["panel_bg"])
        
        # Update header
        self.header_frame.configure(fg_color=colors["panel_bg"])
        self.title_label.configure(text_color=colors["text_primary"])
        self.count_label.configure(text_color=colors["text_secondary"])
        
        # Update filter controls
        self.filter_frame.configure(fg_color=colors["bg_secondary"])
        self.level_label.configure(text_color=colors["text_primary"])
        self.search_label.configure(text_color=colors["text_primary"])
        
        self.level_filter.configure(
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text_primary"]
        )
        
        self.search_entry.configure(
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text_primary"]
        )
        
        self.autoscroll_check.configure(text_color=colors["text_primary"])
        
        # Update log display
        self.display_frame.configure(fg_color=colors["bg_secondary"])
        self.log_text.configure(
            fg_color=colors["input_bg"],
            text_color=colors["text_primary"]
        )
        
        # Update controls
        self.controls_frame.configure(fg_color=colors["panel_bg"])
        self.status_label.configure(text_color=colors["text_secondary"])
        
        # Reconfigure text tags
        self._configure_log_tags()
        
        # Force display update
        self._update_display()
    
    def get_logs_for_node(self, node_id: str) -> List[LogEntry]:
        """Get all log entries for a specific node."""
        return [entry for entry in self.log_entries if entry.node_id == node_id]
    
    def set_node_filter(self, node_id: Optional[str]):
        """Set filter to show logs for a specific node."""
        self.filter_node = node_id or ""
        self._apply_filters()
    
    def add_execution_start(self, workflow_name: str):
        """Log workflow execution start."""
        self.add_log("INFO", f"🚀 Starting workflow execution: {workflow_name}")
    
    def add_execution_complete(self, success: bool, duration: float):
        """Log workflow execution completion."""
        if success:
            self.add_log("SUCCESS", f"✅ Workflow completed successfully in {duration:.2f}s")
        else:
            self.add_log("ERROR", f"❌ Workflow execution failed after {duration:.2f}s")
    
    def add_node_start(self, node_id: str, node_type: str):
        """Log node execution start."""
        self.add_log("INFO", f"▶️ Executing {node_type}", node_id)
    
    def add_node_complete(self, node_id: str, node_type: str, duration: float):
        """Log node execution completion."""
        self.add_log("SUCCESS", f"✅ Completed {node_type} in {duration:.3f}s", node_id)
    
    def add_node_error(self, node_id: str, node_type: str, error: str):
        """Log node execution error."""
        self.add_log("ERROR", f"❌ {node_type} failed: {error}", node_id)
    
    def add_connection_data(self, from_node: str, to_node: str, data_type: str, size: int):
        """Log data transfer between nodes."""
        self.add_log("DEBUG", f"📡 Data transfer: {data_type} ({size} bytes)", 
                    details={"from": from_node, "to": to_node})
