"""
Modern toolbar with gradient styling and smooth animations.
Provides workflow controls and theme switching.
"""

import customtkinter as ctk
from typing import Callable, Optional
from app.themes import ThemeManager

class Toolbar(ctk.CTkFrame):
    """Modern toolbar with beautiful styling and smooth interactions."""
    
    def __init__(self, parent, theme_manager: ThemeManager,
                 on_new: Callable, on_open: Callable, on_save: Callable,
                 on_save_as: Callable, on_run: Callable, on_stop: Callable,
                 on_toggle_theme: Callable):
        """Initialize the toolbar."""
        super().__init__(parent, height=60)
        
        self.theme_manager = theme_manager
        self.on_new = on_new
        self.on_open = on_open
        self.on_save = on_save
        self.on_save_as = on_save_as
        self.on_run = on_run
        self.on_stop = on_stop
        self.on_toggle_theme = on_toggle_theme
        
        self.execution_running = False
        
        self._create_toolbar_sections()
        self._setup_layout()
        
    def _create_toolbar_sections(self):
        """Create different sections of the toolbar."""
        # File operations section
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.new_btn = ctk.CTkButton(
            self.file_frame,
            text="📄 New",
            width=80,
            height=35,
            command=self.on_new,
            corner_radius=8
        )
        
        self.open_btn = ctk.CTkButton(
            self.file_frame,
            text="📁 Open",
            width=80,
            height=35,
            command=self.on_open,
            corner_radius=8
        )
        
        self.save_btn = ctk.CTkButton(
            self.file_frame,
            text="💾 Save",
            width=80,
            height=35,
            command=self.on_save,
            corner_radius=8
        )
        
        self.save_as_btn = ctk.CTkButton(
            self.file_frame,
            text="💾 Save As",
            width=90,
            height=35,
            command=self.on_save_as,
            corner_radius=8
        )
        
        # Separator
        self.separator1 = ctk.CTkFrame(self, width=2, height=40)
        
        # Execution section
        self.execution_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.run_btn = ctk.CTkButton(
            self.execution_frame,
            text="▶️ Run",
            width=80,
            height=35,
            command=self.on_run,
            corner_radius=8
        )
        
        self.stop_btn = ctk.CTkButton(
            self.execution_frame,
            text="⏹️ Stop",
            width=80,
            height=35,
            command=self.on_stop,
            corner_radius=8,
            state="disabled"
        )
        
        # Separator
        self.separator2 = ctk.CTkFrame(self, width=2, height=40)
        
        # View section
        self.view_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.theme_btn = ctk.CTkButton(
            self.view_frame,
            text="🌓 Theme",
            width=90,
            height=35,
            command=self.on_toggle_theme,
            corner_radius=8
        )
        
        # Status section (right-aligned)
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="● Ready",
            font=("Arial", 12, "bold")
        )
        
        # Title section (center)
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="Workflow Builder",
            font=("Arial", 16, "bold")
        )
    
    def _setup_layout(self):
        """Setup the layout of toolbar sections."""
        # Configure grid weights
        self.grid_columnconfigure(4, weight=1)  # Title section expands
        
        # File operations
        self.file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.new_btn.grid(row=0, column=0, padx=2)
        self.open_btn.grid(row=0, column=1, padx=2)
        self.save_btn.grid(row=0, column=2, padx=2)
        self.save_as_btn.grid(row=0, column=3, padx=2)
        
        # Separator
        self.separator1.grid(row=0, column=1, padx=10, pady=10)
        
        # Execution controls
        self.execution_frame.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.run_btn.grid(row=0, column=0, padx=2)
        self.stop_btn.grid(row=0, column=1, padx=2)
        
        # Separator
        self.separator2.grid(row=0, column=3, padx=10, pady=10)
        
        # Title (center)
        self.title_frame.grid(row=0, column=4, pady=10, sticky="")
        self.title_label.pack()
        
        # View controls
        self.view_frame.grid(row=0, column=5, padx=10, pady=10, sticky="e")
        self.theme_btn.grid(row=0, column=0, padx=2)
        
        # Status (right)
        self.status_frame.grid(row=0, column=6, padx=10, pady=10, sticky="e")
        self.status_indicator.pack()
        
        # Prevent frame from shrinking
        self.grid_propagate(False)
    
    def apply_theme(self):
        """Apply the current theme to toolbar elements."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Update toolbar background
        self.configure(fg_color=colors["toolbar_bg"])
        
        # Update separators
        self.separator1.configure(fg_color=colors["panel_border"])
        self.separator2.configure(fg_color=colors["panel_border"])
        
        # Update status indicator color based on execution state
        if self.execution_running:
            self.status_indicator.configure(text_color=colors["info"])
        else:
            self.status_indicator.configure(text_color=colors["success"])
        
        # Update title color
        self.title_label.configure(text_color=colors["text_primary"])
        
        # Update button hover effects
        self._setup_button_hover_effects()
    
    def _setup_button_hover_effects(self):
        """Setup hover effects for toolbar buttons."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        buttons = [
            self.new_btn, self.open_btn, self.save_btn, self.save_as_btn,
            self.run_btn, self.stop_btn, self.theme_btn
        ]
        
        for button in buttons:
            # Add hover animation
            button.bind("<Enter>", lambda e, btn=button: self._on_button_hover(btn, True))
            button.bind("<Leave>", lambda e, btn=button: self._on_button_hover(btn, False))
    
    def _on_button_hover(self, button: ctk.CTkButton, is_hover: bool):
        """Handle button hover animations."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        if is_hover:
            # Smooth scale animation
            self._animate_button_scale(button, 1.05)
        else:
            # Return to normal scale
            self._animate_button_scale(button, 1.0)
    
    def _animate_button_scale(self, button: ctk.CTkButton, scale: float):
        """Animate button scaling effect."""
        # Simple scaling effect using configure
        # In a more advanced implementation, this could use actual animations
        if scale > 1.0:
            button.configure(border_width=2)
        else:
            button.configure(border_width=0)
    
    def set_execution_state(self, running: bool):
        """Update the execution state of the toolbar."""
        self.execution_running = running
        
        if running:
            self.run_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_indicator.configure(text="● Running")
            
            # Add pulse animation to status
            self._pulse_status_indicator()
        else:
            self.run_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.status_indicator.configure(text="● Ready")
        
        # Update colors
        self.apply_theme()
    
    def _pulse_status_indicator(self):
        """Add a pulsing animation to the status indicator when running."""
        if self.execution_running:
            colors = self.theme_manager.get_current_theme()["colors"]
            
            # Alternate between normal and bright colors
            current_color = str(self.status_indicator.cget("text_color"))
            
            if current_color == colors["info"]:
                new_color = colors["accent_hover"]
            else:
                new_color = colors["info"]
            
            self.status_indicator.configure(text_color=new_color)
            
            # Schedule next pulse
            self.after(500, self._pulse_status_indicator)
    
    def update_title(self, title: str):
        """Update the toolbar title."""
        self.title_label.configure(text=title)
    
    def set_file_operations_enabled(self, enabled: bool):
        """Enable/disable file operation buttons."""
        state = "normal" if enabled else "disabled"
        
        self.new_btn.configure(state=state)
        self.open_btn.configure(state=state)
        self.save_btn.configure(state=state)
        self.save_as_btn.configure(state=state)
    
    def show_tooltip(self, widget, text: str):
        """Show a tooltip for a widget."""
        # TODO: Implement modern tooltip system
        pass
    
    def add_custom_button(self, text: str, command: Callable, section: str = "view"):
        """Add a custom button to the specified section."""
        if section == "view":
            button = ctk.CTkButton(
                self.view_frame,
                text=text,
                width=80,
                height=35,
                command=command,
                corner_radius=8
            )
            
            # Get current column count and add button
            column_count = len(self.view_frame.grid_slaves())
            button.grid(row=0, column=column_count, padx=2)
            
            return button
        
        return None
