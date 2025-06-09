"""
Properties panel for editing node configurations.
Provides dynamic property editors with validation and modern styling.
"""

import customtkinter as ctk
import tkinter as tk
from typing import Dict, Any, Callable, Optional, List
from app.themes import ThemeManager

class PropertiesPanel(ctk.CTkFrame):
    """Modern properties panel with dynamic property editors."""
    
    def __init__(self, parent, theme_manager: ThemeManager,
                 on_property_changed: Callable[[str, Any], None]):
        """Initialize the properties panel."""
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.on_property_changed = on_property_changed
        
        # Panel state
        self.current_node_data: Optional[Dict] = None
        self.property_widgets: Dict[str, Any] = {}
        
        self._create_header()
        self._create_scrollable_content()
        self._show_welcome_message()
    
    def _create_header(self):
        """Create the properties panel header."""
        self.header_frame = ctk.CTkFrame(self, height=50)
        self.header_frame.pack(fill="x", padx=5, pady=5)
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Properties",
            font=("Arial", 14, "bold")
        )
        self.title_label.pack(pady=15)
    
    def _create_scrollable_content(self):
        """Create scrollable content area."""
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            label_text=""
        )
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _show_welcome_message(self):
        """Show welcome message when no node is selected."""
        self.welcome_frame = ctk.CTkFrame(self.content_frame)
        self.welcome_frame.pack(fill="both", expand=True, padx=10, pady=20)
        
        welcome_icon = ctk.CTkLabel(
            self.welcome_frame,
            text="⚙️",
            font=("Arial", 32)
        )
        welcome_icon.pack(pady=10)
        
        welcome_text = ctk.CTkLabel(
            self.welcome_frame,
            text="Select a node to\nedit its properties",
            font=("Arial", 12),
            justify="center"
        )
        welcome_text.pack(pady=5)
    
    def load_properties(self, node_data: Dict):
        """Load properties for a node."""
        self.current_node_data = node_data
        self._clear_content()
        
        if not node_data:
            self._show_welcome_message()
            return
        
        # Create node info section
        self._create_node_info_section(node_data)
        
        # Create properties sections
        self._create_basic_properties_section(node_data)
        self._create_advanced_properties_section(node_data)
        self._create_connections_section(node_data)
    
    def _clear_content(self):
        """Clear all content from the properties panel."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.property_widgets.clear()
    
    def _create_node_info_section(self, node_data: Dict):
        """Create node information section."""
        info_frame = ctk.CTkFrame(self.content_frame)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        # Section header
        header_label = ctk.CTkLabel(
            info_frame,
            text="Node Information",
            font=("Arial", 12, "bold")
        )
        header_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Node type
        type_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(type_frame, text="Type:", width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(
            type_frame, 
            text=node_data.get("type", "Unknown"),
            anchor="w"
        ).pack(side="left", padx=(10, 0))
        
        # Node ID
        id_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        id_frame.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(id_frame, text="ID:", width=80, anchor="w").pack(side="left")
        id_label = ctk.CTkLabel(
            id_frame,
            text=node_data.get("id", "Unknown")[:12] + "...",
            anchor="w",
            font=("Courier", 9)
        )
        id_label.pack(side="left", padx=(10, 0))
        
        # Node title (editable)
        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(2, 10))
        
        ctk.CTkLabel(title_frame, text="Title:", width=80, anchor="w").pack(side="left")
        
        title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Node title..."
        )
        title_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        title_entry.insert(0, node_data.get("title", node_data.get("type", "")))
        title_entry.bind("<KeyRelease>", 
                        lambda e: self.on_property_changed("title", title_entry.get()))
        
        self.property_widgets["title"] = title_entry
    
    def _create_basic_properties_section(self, node_data: Dict):
        """Create basic properties section."""
        properties = node_data.get("properties", {})
        
        if not properties:
            return
        
        basic_frame = ctk.CTkFrame(self.content_frame)
        basic_frame.pack(fill="x", padx=5, pady=5)
        
        # Section header
        header_label = ctk.CTkLabel(
            basic_frame,
            text="Basic Properties",
            font=("Arial", 12, "bold")
        )
        header_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Create property editors
        for prop_name, prop_value in properties.items():
            if not prop_name.startswith("_"):  # Skip internal properties
                self._create_property_editor(basic_frame, prop_name, prop_value)
    
    def _create_advanced_properties_section(self, node_data: Dict):
        """Create advanced properties section."""
        # Get node schema for advanced properties
        schema = node_data.get("schema", {})
        advanced_props = schema.get("advanced_properties", {})
        
        if not advanced_props:
            return
        
        advanced_frame = ctk.CTkFrame(self.content_frame)
        advanced_frame.pack(fill="x", padx=5, pady=5)
        
        # Collapsible header
        header_frame = ctk.CTkFrame(advanced_frame, height=40)
        header_frame.pack(fill="x", padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        self.advanced_expanded = getattr(self, 'advanced_expanded', False)
        
        expand_btn = ctk.CTkButton(
            header_frame,
            text="▼" if self.advanced_expanded else "▶",
            width=30,
            height=25,
            command=lambda: self._toggle_advanced_section(expand_btn, content_frame)
        )
        expand_btn.pack(side="left", padx=5, pady=7)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="Advanced Properties",
            font=("Arial", 12, "bold")
        )
        header_label.pack(side="left", padx=10, pady=7)
        
        # Content frame
        content_frame = ctk.CTkFrame(advanced_frame)
        if self.advanced_expanded:
            content_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            for prop_name, prop_config in advanced_props.items():
                self._create_advanced_property_editor(
                    content_frame, prop_name, prop_config
                )
    
    def _create_connections_section(self, node_data: Dict):
        """Create connections information section."""
        connections_frame = ctk.CTkFrame(self.content_frame)
        connections_frame.pack(fill="x", padx=5, pady=5)
        
        # Section header
        header_label = ctk.CTkLabel(
            connections_frame,
            text="Connections",
            font=("Arial", 12, "bold")
        )
        header_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Input pins
        inputs = node_data.get("inputs", [])
        if inputs:
            inputs_label = ctk.CTkLabel(
                connections_frame,
                text="Inputs:",
                font=("Arial", 10, "bold")
            )
            inputs_label.pack(anchor="w", padx=20, pady=(5, 2))
            
            for input_pin in inputs:
                pin_frame = ctk.CTkFrame(connections_frame, fg_color="transparent")
                pin_frame.pack(fill="x", padx=30, pady=1)
                
                pin_icon = ctk.CTkLabel(pin_frame, text="🔌", width=20)
                pin_icon.pack(side="left")
                
                pin_label = ctk.CTkLabel(
                    pin_frame,
                    text=f"{input_pin['name']} ({input_pin.get('type', 'any')})",
                    anchor="w"
                )
                pin_label.pack(side="left", padx=5)
        
        # Output pins
        outputs = node_data.get("outputs", [])
        if outputs:
            outputs_label = ctk.CTkLabel(
                connections_frame,
                text="Outputs:",
                font=("Arial", 10, "bold")
            )
            outputs_label.pack(anchor="w", padx=20, pady=(10, 2))
            
            for output_pin in outputs:
                pin_frame = ctk.CTkFrame(connections_frame, fg_color="transparent")
                pin_frame.pack(fill="x", padx=30, pady=(1, 10))
                
                pin_icon = ctk.CTkLabel(pin_frame, text="🔌", width=20)
                pin_icon.pack(side="left")
                
                pin_label = ctk.CTkLabel(
                    pin_frame,
                    text=f"{output_pin['name']} ({output_pin.get('type', 'any')})",
                    anchor="w"
                )
                pin_label.pack(side="left", padx=5)
    
    def _create_property_editor(self, parent: ctk.CTkFrame, prop_name: str, prop_value: Any):
        """Create an appropriate editor for a property."""
        prop_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prop_frame.pack(fill="x", padx=10, pady=2)
        
        # Property label
        label = ctk.CTkLabel(
            prop_frame,
            text=f"{prop_name.replace('_', ' ').title()}:",
            width=100,
            anchor="w"
        )
        label.pack(side="left")
        
        # Create appropriate editor based on type
        if isinstance(prop_value, bool):
            editor = self._create_boolean_editor(prop_frame, prop_name, prop_value)
        elif isinstance(prop_value, (int, float)):
            editor = self._create_number_editor(prop_frame, prop_name, prop_value)
        elif isinstance(prop_value, str):
            if len(prop_value) > 50:
                editor = self._create_text_editor(prop_frame, prop_name, prop_value)
            else:
                editor = self._create_string_editor(prop_frame, prop_name, prop_value)
        elif isinstance(prop_value, list):
            editor = self._create_list_editor(prop_frame, prop_name, prop_value)
        else:
            editor = self._create_string_editor(prop_frame, prop_name, str(prop_value))
        
        self.property_widgets[prop_name] = editor
    
    def _create_string_editor(self, parent: ctk.CTkFrame, prop_name: str, value: str):
        """Create a string property editor."""
        entry = ctk.CTkEntry(parent, placeholder_text="Enter value...")
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        entry.insert(0, str(value))
        entry.bind("<KeyRelease>", 
                  lambda e: self.on_property_changed(prop_name, entry.get()))
        return entry
    
    def _create_number_editor(self, parent: ctk.CTkFrame, prop_name: str, value: float):
        """Create a number property editor."""
        entry = ctk.CTkEntry(parent, placeholder_text="Enter number...")
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        entry.insert(0, str(value))
        
        def on_change(event):
            try:
                new_value = float(entry.get()) if '.' in entry.get() else int(entry.get())
                self.on_property_changed(prop_name, new_value)
            except ValueError:
                pass  # Invalid number, ignore
        
        entry.bind("<KeyRelease>", on_change)
        return entry
    
    def _create_boolean_editor(self, parent: ctk.CTkFrame, prop_name: str, value: bool):
        """Create a boolean property editor."""
        switch = ctk.CTkSwitch(
            parent,
            text="",
            command=lambda: self.on_property_changed(prop_name, switch.get())
        )
        switch.pack(side="left", padx=(10, 0))
        
        if value:
            switch.select()
        
        return switch
    
    def _create_text_editor(self, parent: ctk.CTkFrame, prop_name: str, value: str):
        """Create a multi-line text property editor."""
        # Create a frame for the text editor
        text_frame = ctk.CTkFrame(parent)
        text_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        text_widget = ctk.CTkTextbox(text_frame, height=80)
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        text_widget.insert("1.0", value)
        
        def on_text_change(event):
            content = text_widget.get("1.0", "end-1c")
            self.on_property_changed(prop_name, content)
        
        text_widget.bind("<KeyRelease>", on_text_change)
        return text_widget
    
    def _create_list_editor(self, parent: ctk.CTkFrame, prop_name: str, value: List):
        """Create a list property editor."""
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # Simple comma-separated editor for now
        entry = ctk.CTkEntry(list_frame, placeholder_text="Comma-separated values...")
        entry.pack(fill="x", padx=5, pady=5)
        entry.insert(0, ", ".join(str(item) for item in value))
        
        def on_change(event):
            try:
                text = entry.get()
                if text.strip():
                    new_list = [item.strip() for item in text.split(",")]
                else:
                    new_list = []
                self.on_property_changed(prop_name, new_list)
            except Exception:
                pass
        
        entry.bind("<KeyRelease>", on_change)
        return entry
    
    def _create_advanced_property_editor(self, parent: ctk.CTkFrame, prop_name: str,
                                       prop_config: Dict):
        """Create an advanced property editor with validation."""
        prop_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prop_frame.pack(fill="x", padx=10, pady=5)
        
        # Property label with description
        label_frame = ctk.CTkFrame(prop_frame, fg_color="transparent")
        label_frame.pack(fill="x")
        
        label = ctk.CTkLabel(
            label_frame,
            text=prop_config.get("title", prop_name),
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        label.pack(anchor="w")
        
        if "description" in prop_config:
            desc_label = ctk.CTkLabel(
                label_frame,
                text=prop_config["description"],
                font=("Arial", 8),
                anchor="w"
            )
            desc_label.pack(anchor="w", pady=(0, 5))
        
        # Create editor based on type
        prop_type = prop_config.get("type", "string")
        default_value = prop_config.get("default", "")
        
        if prop_type == "select":
            editor = self._create_select_editor(prop_frame, prop_name, prop_config)
        elif prop_type == "file":
            editor = self._create_file_editor(prop_frame, prop_name, prop_config)
        elif prop_type == "color":
            editor = self._create_color_editor(prop_frame, prop_name, default_value)
        else:
            editor = self._create_string_editor(prop_frame, prop_name, str(default_value))
        
        self.property_widgets[prop_name] = editor
    
    def _create_select_editor(self, parent: ctk.CTkFrame, prop_name: str, config: Dict):
        """Create a dropdown select editor."""
        options = config.get("options", [])
        default = config.get("default", options[0] if options else "")
        
        dropdown = ctk.CTkComboBox(
            parent,
            values=options,
            command=lambda value: self.on_property_changed(prop_name, value)
        )
        dropdown.pack(fill="x", pady=2)
        dropdown.set(default)
        
        return dropdown
    
    def _create_file_editor(self, parent: ctk.CTkFrame, prop_name: str, config: Dict):
        """Create a file selection editor."""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", pady=2)
        
        entry = ctk.CTkEntry(file_frame, placeholder_text="Select file...")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_file():
            from tkinter import filedialog
            file_types = config.get("file_types", [("All files", "*.*")])
            filename = filedialog.askopenfilename(filetypes=file_types)
            if filename:
                entry.delete(0, "end")
                entry.insert(0, filename)
                self.on_property_changed(prop_name, filename)
        
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse",
            width=70,
            command=browse_file
        )
        browse_btn.pack(side="right")
        
        return entry
    
    def _create_color_editor(self, parent: ctk.CTkFrame, prop_name: str, default_color: str):
        """Create a color selection editor."""
        color_frame = ctk.CTkFrame(parent)
        color_frame.pack(fill="x", pady=2)
        
        entry = ctk.CTkEntry(color_frame, placeholder_text="#ffffff")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        entry.insert(0, default_color)
        
        def pick_color():
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=entry.get())
            if color[1]:  # If user didn't cancel
                entry.delete(0, "end")
                entry.insert(0, color[1])
                self.on_property_changed(prop_name, color[1])
        
        color_btn = ctk.CTkButton(
            color_frame,
            text="🎨",
            width=40,
            command=pick_color
        )
        color_btn.pack(side="right")
        
        entry.bind("<KeyRelease>", 
                  lambda e: self.on_property_changed(prop_name, entry.get()))
        
        return entry
    
    def _toggle_advanced_section(self, expand_btn: ctk.CTkButton, content_frame: ctk.CTkFrame):
        """Toggle the advanced properties section."""
        self.advanced_expanded = not getattr(self, 'advanced_expanded', False)
        
        if self.advanced_expanded:
            expand_btn.configure(text="▼")
            content_frame.pack(fill="x", padx=5, pady=(0, 5))
        else:
            expand_btn.configure(text="▶")
            content_frame.pack_forget()
    
    def clear_properties(self):
        """Clear all properties and show welcome message."""
        self.current_node_data = None
        self._clear_content()
        self._show_welcome_message()
    
    def apply_theme(self):
        """Apply the current theme to the properties panel."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Update main frame
        self.configure(fg_color=colors["panel_bg"])
        
        # Update header
        self.header_frame.configure(fg_color=colors["panel_bg"])
        self.title_label.configure(text_color=colors["text_primary"])
        
        # Update content frame
        self.content_frame.configure(fg_color=colors["bg_primary"])
        
        # Update all property widgets
        self._update_widget_colors_recursive(self.content_frame, colors)
    
    def _update_widget_colors_recursive(self, widget, colors: Dict[str, str]):
        """Recursively update widget colors."""
        try:
            if isinstance(widget, ctk.CTkFrame):
                if str(widget.cget("fg_color")) != "transparent":
                    widget.configure(fg_color=colors["bg_secondary"])
            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(text_color=colors["text_primary"])
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=colors["input_bg"],
                    border_color=colors["input_border"],
                    text_color=colors["text_primary"]
                )
            elif isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=colors["accent_primary"],
                    hover_color=colors["accent_hover"]
                )
            elif isinstance(widget, ctk.CTkComboBox):
                widget.configure(
                    fg_color=colors["input_bg"],
                    border_color=colors["input_border"],
                    text_color=colors["text_primary"]
                )
            elif isinstance(widget, ctk.CTkTextbox):
                widget.configure(
                    fg_color=colors["input_bg"],
                    border_color=colors["input_border"],
                    text_color=colors["text_primary"]
                )
            
            # Update children
            for child in widget.winfo_children():
                self._update_widget_colors_recursive(child, colors)
                
        except Exception:
            # Skip widgets that don't support color configuration
            pass
    
    def get_current_properties(self) -> Optional[Dict]:
        """Get the current property values."""
        if not self.current_node_data:
            return None
        
        properties = {}
        for prop_name, widget in self.property_widgets.items():
            try:
                if isinstance(widget, ctk.CTkEntry):
                    properties[prop_name] = widget.get()
                elif isinstance(widget, ctk.CTkSwitch):
                    properties[prop_name] = widget.get()
                elif isinstance(widget, ctk.CTkComboBox):
                    properties[prop_name] = widget.get()
                elif isinstance(widget, ctk.CTkTextbox):
                    properties[prop_name] = widget.get("1.0", "end-1c")
            except Exception:
                pass
        
        return properties
    
    def validate_properties(self) -> List[str]:
        """Validate current properties and return list of errors."""
        errors = []
        
        if not self.current_node_data:
            return errors
        
        # TODO: Implement property validation based on node schema
        # For now, return empty list (no errors)
        
        return errors
