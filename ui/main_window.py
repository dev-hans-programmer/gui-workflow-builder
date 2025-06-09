"""
Main window class for the Workflow Builder application.
Provides the primary user interface with modern CustomTkinter styling.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional
import json
from pathlib import Path

from ui.canvas import WorkflowCanvas
from ui.toolbar import Toolbar
from ui.node_palette import NodePalette
from ui.properties_panel import PropertiesPanel
from ui.log_viewer import LogViewer
from workflow.engine import WorkflowEngine
from app.themes import ThemeManager
from utils.file_manager import FileManager

class MainWindow(ctk.CTk):
    """Main application window with modern UI design."""
    
    def __init__(self, theme_manager: ThemeManager, workflow_engine: WorkflowEngine, 
                 file_manager: FileManager):
        """Initialize the main window."""
        super().__init__()
        
        self.theme_manager = theme_manager
        self.workflow_engine = workflow_engine
        self.file_manager = file_manager
        
        self._setup_window()
        self._create_ui_components()
        self._setup_layout()
        self._setup_bindings()
        self.apply_theme()
    
    def _setup_window(self):
        """Configure the main window properties."""
        self.title("Workflow Builder - Professional Visual Editor")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Set window icon and properties
        self.iconname("Workflow Builder")
        
        # Configure grid weights for responsive layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _create_ui_components(self):
        """Create all UI components."""
        # Top toolbar
        self.toolbar = Toolbar(
            self, 
            theme_manager=self.theme_manager,
            on_new=self._new_workflow,
            on_open=self._open_workflow,
            on_save=self._save_workflow,
            on_save_as=self._save_workflow_as,
            on_run=self._run_workflow,
            on_stop=self._stop_workflow,
            on_toggle_theme=self._toggle_theme
        )
        
        # Left panel - Node palette
        self.left_panel = ctk.CTkFrame(self, width=250)
        self.node_palette = NodePalette(
            self.left_panel,
            theme_manager=self.theme_manager,
            on_node_drag_start=self._on_node_drag_start
        )
        
        # Center canvas
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas = WorkflowCanvas(
            self.canvas_frame,
            theme_manager=self.theme_manager,
            workflow_engine=self.workflow_engine,
            on_node_selected=self._on_node_selected,
            on_canvas_changed=self._on_canvas_changed
        )
        
        # Right panel - Properties
        self.right_panel = ctk.CTkFrame(self, width=300)
        self.properties_panel = PropertiesPanel(
            self.right_panel,
            theme_manager=self.theme_manager,
            on_property_changed=self._on_property_changed
        )
        
        # Bottom panel - Log viewer
        self.bottom_panel = ctk.CTkFrame(self, height=200)
        self.log_viewer = LogViewer(
            self.bottom_panel,
            theme_manager=self.theme_manager
        )
        
        # Status bar
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            anchor="w"
        )
    
    def _setup_layout(self):
        """Setup the layout of all components."""
        # Toolbar at top
        self.toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Main content area
        self.left_panel.grid(row=1, column=0, sticky="ns", padx=(5, 2), pady=5)
        self.canvas_frame.grid(row=1, column=1, sticky="nsew", padx=2, pady=5)
        self.right_panel.grid(row=1, column=2, sticky="ns", padx=(2, 5), pady=5)
        
        # Bottom log panel
        self.bottom_panel.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        
        # Status bar
        self.status_bar.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        
        # Configure panel contents
        self.node_palette.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.properties_panel.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_viewer.pack(fill="both", expand=True, padx=10, pady=10)
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # Prevent panels from shrinking
        self.left_panel.grid_propagate(False)
        self.right_panel.grid_propagate(False)
        self.bottom_panel.grid_propagate(False)
    
    def _setup_bindings(self):
        """Setup event bindings."""
        # Keyboard shortcuts
        self.bind("<Control-n>", lambda e: self._new_workflow())
        self.bind("<Control-o>", lambda e: self._open_workflow())
        self.bind("<Control-s>", lambda e: self._save_workflow())
        self.bind("<Control-Shift-S>", lambda e: self._save_workflow_as())
        self.bind("<F5>", lambda e: self._run_workflow())
        self.bind("<F6>", lambda e: self._stop_workflow())
        
        # Focus handling
        self.focus_set()
    
    def apply_theme(self):
        """Apply the current theme to all components."""
        theme = self.theme_manager.get_current_theme()
        colors = theme["colors"]
        
        # Apply theme to all components
        self.toolbar.apply_theme()
        self.node_palette.apply_theme()
        self.canvas.apply_theme()
        self.properties_panel.apply_theme()
        self.log_viewer.apply_theme()
        
        # Update status bar
        self.status_bar.configure(fg_color=colors["panel_bg"])
        self.status_label.configure(text_color=colors["text_primary"])
    
    def _new_workflow(self):
        """Create a new workflow."""
        if self.canvas.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new workflow?"
            )
            if response is True:
                if not self._save_workflow():
                    return
            elif response is None:
                return
        
        self.canvas.clear_canvas()
        self.properties_panel.clear_properties()
        self.log_viewer.clear_logs()
        self.update_status("New workflow created")
        
    def _open_workflow(self):
        """Open an existing workflow."""
        file_path = filedialog.askopenfilename(
            title="Open Workflow",
            filetypes=[("Workflow files", "*.wf.json"), ("All files", "*.*")],
            defaultextension=".wf.json"
        )
        
        if file_path:
            try:
                workflow_data = self.file_manager.load_workflow(file_path)
                self.canvas.load_workflow(workflow_data)
                self.update_status(f"Opened: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open workflow: {str(e)}")
    
    def _save_workflow(self) -> bool:
        """Save the current workflow."""
        if not self.file_manager.current_file_path:
            return self._save_workflow_as()
        
        try:
            workflow_data = self.canvas.get_workflow_data()
            self.file_manager.save_workflow(workflow_data, self.file_manager.current_file_path)
            self.canvas.mark_saved()
            self.update_status(f"Saved: {Path(self.file_manager.current_file_path).name}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save workflow: {str(e)}")
            return False
    
    def _save_workflow_as(self) -> bool:
        """Save the workflow with a new name."""
        file_path = filedialog.asksaveasfilename(
            title="Save Workflow As",
            filetypes=[("Workflow files", "*.wf.json"), ("All files", "*.*")],
            defaultextension=".wf.json"
        )
        
        if file_path:
            try:
                workflow_data = self.canvas.get_workflow_data()
                self.file_manager.save_workflow(workflow_data, file_path)
                self.canvas.mark_saved()
                self.update_status(f"Saved: {Path(file_path).name}")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save workflow: {str(e)}")
                return False
        return False
    
    def _run_workflow(self):
        """Execute the current workflow."""
        if not self.canvas.has_nodes():
            messagebox.showwarning("Warning", "No workflow to execute. Add some nodes first.")
            return
        
        workflow_data = self.canvas.get_workflow_data()
        self.workflow_engine.execute_workflow(
            workflow_data,
            on_log=self.log_viewer.add_log,
            on_node_update=self.canvas.update_node_status,
            on_complete=self._on_workflow_complete
        )
        
        self.update_status("Workflow execution started...")
        self.toolbar.set_execution_state(True)
    
    def _stop_workflow(self):
        """Stop workflow execution."""
        self.workflow_engine.stop_execution()
        self.update_status("Workflow execution stopped")
        self.toolbar.set_execution_state(False)
        self.canvas.clear_node_statuses()
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme_manager.toggle_theme()
        self.apply_theme()
        self.update_status("Theme toggled")
    
    def _on_node_drag_start(self, node_type: str):
        """Handle node drag start from palette."""
        self.canvas.start_node_creation(node_type)
    
    def _on_node_selected(self, node_id: Optional[str]):
        """Handle node selection in canvas."""
        if node_id:
            node_data = self.canvas.get_node_data(node_id)
            self.properties_panel.load_properties(node_data)
        else:
            self.properties_panel.clear_properties()
    
    def _on_property_changed(self, property_name: str, value):
        """Handle property changes in the properties panel."""
        selected_node = self.canvas.get_selected_node()
        if selected_node:
            self.canvas.update_node_property(selected_node, property_name, value)
    
    def _on_canvas_changed(self):
        """Handle canvas changes (for unsaved changes tracking)."""
        self.update_status("Workflow modified")
    
    def _on_workflow_complete(self, success: bool, message: str):
        """Handle workflow execution completion."""
        self.toolbar.set_execution_state(False)
        if success:
            self.update_status("Workflow completed successfully")
        else:
            self.update_status(f"Workflow failed: {message}")
    
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.configure(text=message)
        self.after(100)  # Force update
    
    def save_workflow(self) -> bool:
        """Public method to save workflow (used by app.py)."""
        return self._save_workflow()
