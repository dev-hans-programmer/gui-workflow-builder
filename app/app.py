"""
Main application class for the Workflow Builder.
Handles application lifecycle, theme management, and component coordination.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
import logging
from pathlib import Path

from app.themes import ThemeManager
from ui.main_window import MainWindow
from workflow.engine import WorkflowEngine
from utils.file_manager import FileManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WorkflowBuilderApp:
    """Main application class for the Workflow Builder."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Workflow Builder Application")
        
        # Initialize core components
        self.theme_manager = ThemeManager()
        self.workflow_engine = WorkflowEngine()
        self.file_manager = FileManager()
        
        # Set appearance mode and theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize main window
        self.main_window: Optional[MainWindow] = None
        
        self._setup_application()
    
    def _setup_application(self):
        """Setup the main application window and components."""
        try:
            self.main_window = MainWindow(
                theme_manager=self.theme_manager,
                workflow_engine=self.workflow_engine,
                file_manager=self.file_manager
            )
            
            # Setup window protocol handlers
            self.main_window.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            self.logger.info("Application setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup application: {e}")
            raise
    
    def _on_closing(self):
        """Handle application closing event."""
        self.logger.info("Application closing...")
        
        # Save current workflow if modified
        if self.main_window and self.main_window.canvas.has_unsaved_changes():
            response = tk.messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            
            if response is True:  # Yes - save and close
                if not self.main_window.save_workflow():
                    return  # Cancel closing if save failed
            elif response is None:  # Cancel - don't close
                return
            # No - close without saving
        
        # Stop workflow engine
        self.workflow_engine.stop_all_executions()
        
        # Destroy the window
        if self.main_window:
            self.main_window.destroy()
        
        self.logger.info("Application closed successfully")
    
    def run(self):
        """Run the application main loop."""
        if not self.main_window:
            raise RuntimeError("Application not properly initialized")
        
        self.logger.info("Starting application main loop")
        
        try:
            # Start the main event loop
            self.main_window.mainloop()
            
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            raise
        finally:
            self.logger.info("Application main loop ended")
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.theme_manager:
            self.theme_manager.toggle_theme()
            if self.main_window:
                self.main_window.apply_theme()
