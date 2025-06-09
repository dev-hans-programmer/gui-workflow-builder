"""
Icon management system for the Workflow Builder application.
Provides SVG-based icons with theme support and easy access.
"""

import base64
from typing import Dict, Optional, Tuple
from io import BytesIO

class IconRegistry:
    """Registry for managing application icons."""
    
    def __init__(self):
        """Initialize the icon registry."""
        self.icons: Dict[str, str] = {}
        self._load_default_icons()
    
    def _load_default_icons(self):
        """Load default SVG icons for the application."""
        
        # File operations icons
        self.icons["file_new"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="12" y1="18" x2="12" y2="12"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
        </svg>
        '''
        
        self.icons["file_open"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2l5 0 2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        '''
        
        self.icons["file_save"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17,21 17,13 7,13 7,21"/>
            <polyline points="7,3 7,8 15,8"/>
        </svg>
        '''
        
        # Execution control icons
        self.icons["play"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5,3 19,12 5,21"/>
        </svg>
        '''
        
        self.icons["stop"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="6" y="6" width="12" height="12"/>
        </svg>
        '''
        
        self.icons["pause"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="6" y="4" width="4" height="16"/>
            <rect x="14" y="4" width="4" height="16"/>
        </svg>
        '''
        
        # Theme and view icons
        self.icons["theme_toggle"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        '''
        
        self.icons["settings"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1m17-4a4 4 0 0 1-8 0 4 4 0 0 1 8 0zM7 17a4 4 0 0 1-8 0 4 4 0 0 1 8 0z"/>
        </svg>
        '''
        
        # Node type icons
        self.icons["node_input"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9,17 4,12 9,7"/>
            <path d="M20 18v-2a4 4 0 0 0-4-4H4"/>
        </svg>
        '''
        
        self.icons["node_output"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15,7 20,12 15,17"/>
            <path d="M4 6v2a4 4 0 0 0 4 4h12"/>
        </svg>
        '''
        
        self.icons["node_process"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <rect x="7" y="7" width="3" height="9"/>
            <rect x="14" y="7" width="3" height="5"/>
        </svg>
        '''
        
        # Connection and flow icons
        self.icons["connection"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 3h12l4 6-4 6H6l-4-6z"/>
        </svg>
        '''
        
        self.icons["arrow_right"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12,5 19,12 12,19"/>
        </svg>
        '''
        
        # Status icons
        self.icons["status_success"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22,4 12,14.01 9,11.01"/>
        </svg>
        '''
        
        self.icons["status_error"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        '''
        
        self.icons["status_warning"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        '''
        
        self.icons["status_info"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        '''
        
        # Navigation icons
        self.icons["menu"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
        '''
        
        self.icons["close"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        '''
        
        self.icons["expand"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6,9 12,15 18,9"/>
        </svg>
        '''
        
        self.icons["collapse"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="18,15 12,9 6,15"/>
        </svg>
        '''
        
        # Tools and utilities
        self.icons["search"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
        </svg>
        '''
        
        self.icons["filter"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46"/>
        </svg>
        '''
        
        self.icons["export"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        '''
        
        self.icons["import"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17,8 12,3 7,8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        '''
        
        # Zoom and view controls
        self.icons["zoom_in"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
            <line x1="11" y1="8" x2="11" y2="14"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
        '''
        
        self.icons["zoom_out"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
            <line x1="8" y1="11" x2="14" y2="11"/>
        </svg>
        '''
        
        self.icons["fit_screen"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
        </svg>
        '''
        
        # Node-specific icons
        self.icons["text_node"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="4,7 4,4 20,4 20,7"/>
            <line x1="9" y1="20" x2="15" y2="20"/>
            <line x1="12" y1="4" x2="12" y2="20"/>
        </svg>
        '''
        
        self.icons["number_node"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="9" x2="20" y2="9"/>
            <line x1="4" y1="15" x2="20" y2="15"/>
            <line x1="10" y1="3" x2="8" y2="21"/>
            <line x1="16" y1="3" x2="14" y2="21"/>
        </svg>
        '''
        
        self.icons["api_node"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        '''
        
        self.icons["database_node"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
        '''
        
        self.icons["timer_node"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12,6 12,12 16,14"/>
        </svg>
        '''
        
        # Log and debug icons
        self.icons["log"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10,9 9,9 8,9"/>
        </svg>
        '''
        
        self.icons["clear"] = '''
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3,6 5,6 21,6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            <line x1="10" y1="11" x2="10" y2="17"/>
            <line x1="14" y1="11" x2="14" y2="17"/>
        </svg>
        '''
    
    def get_icon(self, name: str, size: Tuple[int, int] = (16, 16), 
                 color: Optional[str] = None) -> str:
        """Get an icon as SVG string with optional customization."""
        if name not in self.icons:
            return self._get_default_icon(size)
        
        svg = self.icons[name]
        
        # Update size
        svg = svg.replace('width="16"', f'width="{size[0]}"')
        svg = svg.replace('height="16"', f'height="{size[1]}"')
        
        # Update color if specified
        if color:
            svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
            svg = svg.replace('fill="none"', f'fill="{color}"')
        
        return svg.strip()
    
    def _get_default_icon(self, size: Tuple[int, int]) -> str:
        """Return a default icon when requested icon is not found."""
        return f'''
        <svg width="{size[0]}" height="{size[1]}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="16"/>
            <line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        '''
    
    def get_icon_base64(self, name: str, size: Tuple[int, int] = (16, 16),
                       color: Optional[str] = None) -> str:
        """Get an icon as base64 encoded data URL."""
        svg = self.get_icon(name, size, color)
        svg_bytes = svg.encode('utf-8')
        base64_string = base64.b64encode(svg_bytes).decode('utf-8')
        return f"data:image/svg+xml;base64,{base64_string}"
    
    def register_icon(self, name: str, svg_content: str):
        """Register a custom icon."""
        self.icons[name] = svg_content
    
    def list_icons(self) -> list:
        """Get list of all available icon names."""
        return list(self.icons.keys())
    
    def create_themed_icon(self, name: str, theme_colors: Dict[str, str],
                          size: Tuple[int, int] = (16, 16)) -> Dict[str, str]:
        """Create themed versions of an icon."""
        if name not in self.icons:
            return {}
        
        themed_icons = {}
        for theme_name, color in theme_colors.items():
            themed_icons[theme_name] = self.get_icon(name, size, color)
        
        return themed_icons

# Global icon registry instance
icon_registry = IconRegistry()

# Convenience functions
def get_icon(name: str, size: Tuple[int, int] = (16, 16), 
             color: Optional[str] = None) -> str:
    """Get an icon from the global registry."""
    return icon_registry.get_icon(name, size, color)

def get_icon_base64(name: str, size: Tuple[int, int] = (16, 16),
                   color: Optional[str] = None) -> str:
    """Get an icon as base64 data URL from the global registry."""
    return icon_registry.get_icon_base64(name, size, color)

def register_custom_icon(name: str, svg_content: str):
    """Register a custom icon in the global registry."""
    icon_registry.register_icon(name, svg_content)

def list_available_icons() -> list:
    """List all available icons."""
    return icon_registry.list_icons()

# Theme-specific icon utilities
class ThemedIconProvider:
    """Provides theme-aware icon management."""
    
    def __init__(self, theme_manager):
        """Initialize with theme manager."""
        self.theme_manager = theme_manager
        self.icon_cache: Dict[str, str] = {}
    
    def get_themed_icon(self, name: str, size: Tuple[int, int] = (16, 16)) -> str:
        """Get icon with current theme colors."""
        cache_key = f"{name}_{size}_{self.theme_manager.current_theme}"
        
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Get theme colors
        colors = self.theme_manager.get_current_theme()["colors"]
        icon_color = colors.get("text_primary", "#000000")
        
        # Get themed icon
        icon = get_icon(name, size, icon_color)
        
        # Cache the result
        self.icon_cache[cache_key] = icon
        
        return icon
    
    def clear_cache(self):
        """Clear the icon cache (useful when theme changes)."""
        self.icon_cache.clear()
    
    def get_status_icon(self, status: str, size: Tuple[int, int] = (16, 16)) -> str:
        """Get appropriate icon for status with theme colors."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        status_icons = {
            "success": ("status_success", colors.get("success", "#28a745")),
            "error": ("status_error", colors.get("error", "#dc3545")),
            "warning": ("status_warning", colors.get("warning", "#ffc107")),
            "info": ("status_info", colors.get("info", "#17a2b8")),
            "running": ("play", colors.get("info", "#17a2b8"))
        }
        
        icon_name, color = status_icons.get(status, ("status_info", colors.get("text_primary", "#000000")))
        return get_icon(icon_name, size, color)
    
    def get_node_type_icon(self, node_type: str, size: Tuple[int, int] = (16, 16)) -> str:
        """Get appropriate icon for node type."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        node_type_icons = {
            "text_input": "text_node",
            "number_input": "number_node", 
            "file_input": "file_open",
            "api_input": "api_node",
            "database_input": "database_node",
            "timer": "timer_node",
            "text_output": "text_node",
            "file_output": "file_save",
            "api_output": "api_node",
            "database_output": "database_node",
            "text_processor": "node_process",
            "math": "number_node",
            "filter": "filter",
            "transform": "node_process",
            "conditional": "node_process",
            "delay": "timer_node",
            "script": "node_process"
        }
        
        icon_name = node_type_icons.get(node_type, "node_process")
        icon_color = colors.get("accent_primary", "#007acc")
        
        return get_icon(icon_name, size, icon_color)

# Icon creation utilities
def create_node_icon(node_type: str, theme_colors: Dict[str, str]) -> str:
    """Create a themed icon for a specific node type."""
    provider = ThemedIconProvider(None)
    provider.theme_manager = type('MockTheme', (), {
        'get_current_theme': lambda: {"colors": theme_colors},
        'current_theme': 'mock'
    })()
    
    return provider.get_node_type_icon(node_type)

def create_button_icon(icon_name: str, button_state: str, theme_colors: Dict[str, str]) -> str:
    """Create a themed icon for button states."""
    state_colors = {
        "normal": theme_colors.get("text_primary", "#000000"),
        "hover": theme_colors.get("accent_hover", "#1e90ff"),
        "active": theme_colors.get("accent_active", "#0066aa"),
        "disabled": theme_colors.get("text_disabled", "#606060")
    }
    
    color = state_colors.get(button_state, state_colors["normal"])
    return get_icon(icon_name, (16, 16), color)

# Export commonly used icons as constants
ICON_PLAY = "play"
ICON_STOP = "stop"
ICON_PAUSE = "pause"
ICON_SAVE = "file_save"
ICON_OPEN = "file_open"
ICON_NEW = "file_new"
ICON_SETTINGS = "settings"
ICON_THEME = "theme_toggle"
ICON_SUCCESS = "status_success"
ICON_ERROR = "status_error"
ICON_WARNING = "status_warning"
ICON_INFO = "status_info"
ICON_SEARCH = "search"
ICON_FILTER = "filter"
ICON_EXPORT = "export"
ICON_IMPORT = "import"
ICON_CLEAR = "clear"
ICON_EXPAND = "expand"
ICON_COLLAPSE = "collapse"
ICON_ZOOM_IN = "zoom_in"
ICON_ZOOM_OUT = "zoom_out"
ICON_FIT_SCREEN = "fit_screen"
