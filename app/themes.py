"""
Theme management system for the Workflow Builder.
Provides modern color schemes and theme switching functionality.
"""

from typing import Dict, Any
import customtkinter as ctk

class ThemeManager:
    """Manages application themes and color schemes."""
    
    def __init__(self):
        """Initialize theme manager with default dark theme."""
        self.current_theme = "dark"
        self._setup_themes()
    
    def _setup_themes(self):
        """Setup predefined themes with modern color schemes."""
        self.themes = {
            "dark": {
                "name": "Dark Professional",
                "mode": "dark",
                "colors": {
                    # Primary colors
                    "bg_primary": "#1a1a1a",
                    "bg_secondary": "#2d2d2d", 
                    "bg_tertiary": "#3d3d3d",
                    "bg_canvas": "#0f0f0f",
                    
                    # Text colors
                    "text_primary": "#ffffff",
                    "text_secondary": "#b0b0b0",
                    "text_disabled": "#606060",
                    
                    # Accent colors
                    "accent_primary": "#007acc",
                    "accent_hover": "#1e90ff",
                    "accent_active": "#0066aa",
                    
                    # Node colors
                    "node_bg": "#2d2d2d",
                    "node_border": "#4d4d4d",
                    "node_selected": "#007acc",
                    "node_hover": "#3d3d3d",
                    
                    # Connection colors
                    "connection_line": "#007acc",
                    "connection_hover": "#1e90ff",
                    "connection_active": "#00ff00",
                    
                    # Status colors
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "info": "#17a2b8",
                    
                    # Panel colors
                    "panel_bg": "#252525",
                    "panel_border": "#404040",
                    "toolbar_bg": "#1e1e1e",
                    
                    # Input colors
                    "input_bg": "#3d3d3d",
                    "input_border": "#555555",
                    "input_focus": "#007acc"
                }
            },
            
            "light": {
                "name": "Light Professional",
                "mode": "light",
                "colors": {
                    # Primary colors
                    "bg_primary": "#ffffff",
                    "bg_secondary": "#f8f9fa",
                    "bg_tertiary": "#e9ecef",
                    "bg_canvas": "#fafafa",
                    
                    # Text colors
                    "text_primary": "#212529",
                    "text_secondary": "#6c757d",
                    "text_disabled": "#adb5bd",
                    
                    # Accent colors
                    "accent_primary": "#0066cc",
                    "accent_hover": "#0056b3",
                    "accent_active": "#004499",
                    
                    # Node colors
                    "node_bg": "#ffffff",
                    "node_border": "#dee2e6",
                    "node_selected": "#0066cc",
                    "node_hover": "#f8f9fa",
                    
                    # Connection colors
                    "connection_line": "#0066cc",
                    "connection_hover": "#0056b3",
                    "connection_active": "#28a745",
                    
                    # Status colors
                    "success": "#28a745",
                    "warning": "#fd7e14",
                    "error": "#dc3545",
                    "info": "#20c997",
                    
                    # Panel colors
                    "panel_bg": "#f8f9fa",
                    "panel_border": "#dee2e6",
                    "toolbar_bg": "#ffffff",
                    
                    # Input colors
                    "input_bg": "#ffffff",
                    "input_border": "#ced4da",
                    "input_focus": "#0066cc"
                }
            }
        }
    
    def get_current_theme(self) -> Dict[str, Any]:
        """Get the current theme configuration."""
        return self.themes[self.current_theme]
    
    def get_color(self, color_name: str) -> str:
        """Get a specific color from the current theme."""
        theme = self.get_current_theme()
        return theme["colors"].get(color_name, "#000000")
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        
        # Apply the theme to CustomTkinter
        theme_config = self.get_current_theme()
        ctk.set_appearance_mode(theme_config["mode"])
    
    def set_theme(self, theme_name: str):
        """Set a specific theme by name."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            theme_config = self.get_current_theme()
            ctk.set_appearance_mode(theme_config["mode"])
    
    def get_available_themes(self) -> list:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def get_gradient_colors(self, start_color: str, end_color: str, steps: int = 10) -> list:
        """Generate gradient colors between two colors."""
        # Simple gradient generation for smooth transitions
        start_rgb = self._hex_to_rgb(self.get_color(start_color))
        end_rgb = self._hex_to_rgb(self.get_color(end_color))
        
        gradient = []
        for i in range(steps):
            ratio = i / (steps - 1)
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            gradient.append(f"#{r:02x}{g:02x}{b:02x}")
        
        return gradient
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def apply_node_style(self, canvas, item_id: int, node_type: str, state: str = "normal"):
        """Apply theme-specific styling to a canvas node."""
        colors = self.get_current_theme()["colors"]
        
        if state == "selected":
            fill_color = colors["node_selected"]
            outline_color = colors["accent_primary"]
            width = 3
        elif state == "hover":
            fill_color = colors["node_hover"]
            outline_color = colors["accent_hover"]
            width = 2
        else:
            fill_color = colors["node_bg"]
            outline_color = colors["node_border"]
            width = 1
        
        canvas.itemconfig(item_id, fill=fill_color, outline=outline_color, width=width)
