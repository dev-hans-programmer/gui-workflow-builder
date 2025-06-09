"""
Node palette with categorized nodes and smooth drag interactions.
Provides a modern interface for selecting and dragging nodes onto the canvas.
"""

import customtkinter as ctk
from typing import Callable, Dict, List
from app.themes import ThemeManager
from nodes.node_factory import NodeFactory

class NodePalette(ctk.CTkFrame):
    """Modern node palette with categorized nodes and drag support."""
    
    def __init__(self, parent, theme_manager: ThemeManager,
                 on_node_drag_start: Callable[[str], None]):
        """Initialize the node palette."""
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.on_node_drag_start = on_node_drag_start
        self.node_factory = NodeFactory()
        
        # Palette state
        self.expanded_categories = set()
        self.node_buttons = {}
        
        self._create_header()
        self._create_scrollable_content()
        self._create_node_categories()
        
    def _create_header(self):
        """Create the palette header."""
        self.header_frame = ctk.CTkFrame(self, height=50)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Node Palette",
            font=("Arial", 14, "bold")
        )
        self.title_label.pack(pady=15)
        
        # Search box
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search nodes...",
            height=30
        )
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
    
    def _create_scrollable_content(self):
        """Create scrollable content area."""
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            label_text=""
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _create_node_categories(self):
        """Create categorized node sections."""
        categories = self.node_factory.get_node_categories()
        
        for category_name, node_types in categories.items():
            self._create_category_section(category_name, node_types)
    
    def _create_category_section(self, category_name: str, node_types: List[str]):
        """Create a collapsible category section."""
        # Category header
        category_frame = ctk.CTkFrame(self.scrollable_frame)
        category_frame.pack(fill="x", pady=2)
        
        # Header with expand/collapse button
        header_frame = ctk.CTkFrame(category_frame, height=40)
        header_frame.pack(fill="x", padx=5, pady=2)
        header_frame.pack_propagate(False)
        
        # Expand/collapse button
        expand_btn = ctk.CTkButton(
            header_frame,
            text="▼" if category_name in self.expanded_categories else "▶",
            width=30,
            height=30,
            command=lambda: self._toggle_category(category_name, expand_btn, content_frame)
        )
        expand_btn.pack(side="left", padx=5, pady=5)
        
        # Category title
        title_label = ctk.CTkLabel(
            header_frame,
            text=category_name.title(),
            font=("Arial", 12, "bold")
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Node count badge
        count_label = ctk.CTkLabel(
            header_frame,
            text=f"({len(node_types)})",
            font=("Arial", 10)
        )
        count_label.pack(side="right", padx=10, pady=5)
        
        # Content frame for nodes
        content_frame = ctk.CTkFrame(category_frame)
        
        if category_name in self.expanded_categories:
            content_frame.pack(fill="x", padx=5, pady=(0, 5))
            self._populate_category_nodes(content_frame, node_types)
        
        # Store reference for toggling
        self.node_buttons[category_name] = {
            "expand_btn": expand_btn,
            "content_frame": content_frame,
            "node_types": node_types,
            "category_frame": category_frame
        }
        
        # Expand first category by default
        if not self.expanded_categories and category_name == "Input":
            self._toggle_category(category_name, expand_btn, content_frame)
    
    def _populate_category_nodes(self, parent_frame: ctk.CTkFrame, node_types: List[str]):
        """Populate a category with node buttons."""
        for node_type in node_types:
            node_info = self.node_factory.get_node_info(node_type)
            self._create_node_button(parent_frame, node_type, node_info)
    
    def _create_node_button(self, parent: ctk.CTkFrame, node_type: str, node_info: Dict):
        """Create a draggable node button."""
        button_frame = ctk.CTkFrame(parent, height=60)
        button_frame.pack(fill="x", padx=5, pady=2)
        button_frame.pack_propagate(False)
        
        # Node icon and info
        info_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Icon (emoji or symbol)
        icon_label = ctk.CTkLabel(
            info_frame,
            text=node_info.get("icon", "📦"),
            font=("Arial", 16)
        )
        icon_label.pack(side="left", padx=5)
        
        # Node details
        details_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        name_label = ctk.CTkLabel(
            details_frame,
            text=node_info.get("title", node_type),
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            details_frame,
            text=node_info.get("description", ""),
            font=("Arial", 8),
            anchor="w"
        )
        desc_label.pack(anchor="w")
        
        # Add button
        add_btn = ctk.CTkButton(
            info_frame,
            text="Add",
            width=50,
            height=40,
            command=lambda: self.on_node_drag_start(node_type)
        )
        add_btn.pack(side="right", padx=5)
        
        # Add hover effects
        self._setup_node_button_hover(button_frame, add_btn)
        
        # Store button reference
        if "buttons" not in self.node_buttons:
            self.node_buttons["buttons"] = {}
        self.node_buttons["buttons"][node_type] = {
            "frame": button_frame,
            "button": add_btn,
            "node_info": node_info
        }
    
    def _setup_node_button_hover(self, frame: ctk.CTkFrame, button: ctk.CTkButton):
        """Setup hover effects for node buttons."""
        def on_enter(event):
            colors = self.theme_manager.get_current_theme()["colors"]
            frame.configure(fg_color=colors["node_hover"])
            button.configure(fg_color=colors["accent_hover"])
        
        def on_leave(event):
            colors = self.theme_manager.get_current_theme()["colors"]
            frame.configure(fg_color=colors["bg_secondary"])
            button.configure(fg_color=colors["accent_primary"])
        
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        # Bind to all child widgets
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            
            # Bind to nested children
            for nested_child in child.winfo_children():
                nested_child.bind("<Enter>", on_enter)
                nested_child.bind("<Leave>", on_leave)
    
    def _toggle_category(self, category_name: str, expand_btn: ctk.CTkButton, 
                        content_frame: ctk.CTkFrame):
        """Toggle category expansion."""
        if category_name in self.expanded_categories:
            # Collapse
            self.expanded_categories.remove(category_name)
            expand_btn.configure(text="▶")
            content_frame.pack_forget()
        else:
            # Expand
            self.expanded_categories.add(category_name)
            expand_btn.configure(text="▼")
            content_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            # Populate if not already done
            if not content_frame.winfo_children():
                node_types = self.node_buttons[category_name]["node_types"]
                self._populate_category_nodes(content_frame, node_types)
    
    def _on_search_changed(self, event):
        """Handle search text changes."""
        search_text = self.search_entry.get().lower()
        
        if not search_text:
            # Show all categories
            self._show_all_categories()
        else:
            # Filter nodes based on search
            self._filter_nodes(search_text)
    
    def _show_all_categories(self):
        """Show all categories and nodes."""
        for category_name, category_data in self.node_buttons.items():
            if category_name == "buttons":
                continue
            
            category_frame = category_data["category_frame"]
            category_frame.pack(fill="x", pady=2)
    
    def _filter_nodes(self, search_text: str):
        """Filter nodes based on search text."""
        # Hide all categories first
        for category_name, category_data in self.node_buttons.items():
            if category_name == "buttons":
                continue
            
            category_frame = category_data["category_frame"]
            category_frame.pack_forget()
        
        # Show matching nodes
        matching_categories = set()
        
        if "buttons" in self.node_buttons:
            for node_type, button_data in self.node_buttons["buttons"].items():
                node_info = button_data["node_info"]
                
                # Check if node matches search
                if (search_text in node_type.lower() or
                    search_text in node_info.get("title", "").lower() or
                    search_text in node_info.get("description", "").lower()):
                    
                    # Find which category this node belongs to
                    for category_name, category_data in self.node_buttons.items():
                        if category_name == "buttons":
                            continue
                        
                        if node_type in category_data["node_types"]:
                            matching_categories.add(category_name)
                            break
        
        # Show matching categories
        for category_name in matching_categories:
            category_data = self.node_buttons[category_name]
            category_frame = category_data["category_frame"]
            category_frame.pack(fill="x", pady=2)
            
            # Auto-expand matching categories
            if category_name not in self.expanded_categories:
                expand_btn = category_data["expand_btn"]
                content_frame = category_data["content_frame"]
                self._toggle_category(category_name, expand_btn, content_frame)
    
    def apply_theme(self):
        """Apply the current theme to the palette."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Update main frame
        self.configure(fg_color=colors["panel_bg"])
        
        # Update header
        self.header_frame.configure(fg_color=colors["panel_bg"])
        self.title_label.configure(text_color=colors["text_primary"])
        
        # Update search
        self.search_frame.configure(fg_color=colors["panel_bg"])
        self.search_entry.configure(
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text_primary"]
        )
        
        # Update scrollable frame
        self.scrollable_frame.configure(fg_color=colors["bg_primary"])
        
        # Update all category frames and buttons
        self._update_category_colors()
    
    def _update_category_colors(self):
        """Update colors for all category elements."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        for category_name, category_data in self.node_buttons.items():
            if category_name == "buttons":
                continue
            
            # Update category frame colors recursively
            self._update_widget_colors_recursive(
                category_data["category_frame"], colors
            )
    
    def _update_widget_colors_recursive(self, widget, colors: Dict[str, str]):
        """Recursively update widget colors."""
        try:
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=colors["bg_secondary"])
            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=colors["text_primary"])
            elif isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=colors["accent_primary"],
                    hover_color=colors["accent_hover"]
                )
            
            # Update children
            for child in widget.winfo_children():
                self._update_widget_colors_recursive(child, colors)
                
        except Exception:
            # Skip widgets that don't support color configuration
            pass
    
    def highlight_node_type(self, node_type: str):
        """Highlight a specific node type in the palette."""
        if "buttons" in self.node_buttons and node_type in self.node_buttons["buttons"]:
            button_data = self.node_buttons["buttons"][node_type]
            frame = button_data["frame"]
            
            colors = self.theme_manager.get_current_theme()["colors"]
            frame.configure(fg_color=colors["accent_primary"])
            
            # Remove highlight after delay
            self.after(2000, lambda: frame.configure(fg_color=colors["bg_secondary"]))
    
    def get_node_count(self) -> int:
        """Get the total number of available nodes."""
        total = 0
        for category_name, category_data in self.node_buttons.items():
            if category_name == "buttons":
                continue
            total += len(category_data["node_types"])
        return total
    
    def expand_all_categories(self):
        """Expand all categories."""
        for category_name, category_data in self.node_buttons.items():
            if category_name == "buttons":
                continue
            
            if category_name not in self.expanded_categories:
                expand_btn = category_data["expand_btn"]
                content_frame = category_data["content_frame"]
                self._toggle_category(category_name, expand_btn, content_frame)
    
    def collapse_all_categories(self):
        """Collapse all categories."""
        categories_to_collapse = list(self.expanded_categories)
        
        for category_name in categories_to_collapse:
            if category_name in self.node_buttons:
                category_data = self.node_buttons[category_name]
                expand_btn = category_data["expand_btn"]
                content_frame = category_data["content_frame"]
                self._toggle_category(category_name, expand_btn, content_frame)
