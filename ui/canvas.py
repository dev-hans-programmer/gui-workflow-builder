"""
Workflow canvas for visual drag-and-drop node editing.
Provides smooth animations, beautiful node designs, and connection handling.
"""

import tkinter as tk
from tkinter import Canvas
import customtkinter as ctk
from typing import Dict, List, Optional, Tuple, Callable, Any
import json
import math
import uuid

from nodes.node_factory import NodeFactory
from utils.geometry import Point, Rectangle, distance_between_points
from utils.animations import AnimationManager
from app.themes import ThemeManager

class WorkflowCanvas(ctk.CTkFrame):
    """Modern canvas for visual workflow editing with animations."""
    
    def __init__(self, parent, theme_manager: ThemeManager, workflow_engine,
                 on_node_selected: Callable[[Optional[str]], None],
                 on_canvas_changed: Callable[[], None]):
        """Initialize the workflow canvas."""
        super().__init__(parent)
        
        self.theme_manager = theme_manager
        self.workflow_engine = workflow_engine
        self.on_node_selected = on_node_selected
        self.on_canvas_changed = on_canvas_changed
        
        # Canvas state
        self.nodes: Dict[str, Dict] = {}
        self.connections: Dict[str, Dict] = {}
        self.selected_node: Optional[str] = None
        self.hovered_node: Optional[str] = None
        self.dragging_node: Optional[str] = None
        self.connecting_from: Optional[Tuple[str, str]] = None  # (node_id, pin_type)
        self.creating_node_type: Optional[str] = None
        self.hint_text_id: Optional[int] = None
        
        # Canvas properties
        self.zoom_level = 1.0
        self.pan_offset = Point(0, 0)
        self.unsaved_changes = False
        
        # Node factory for creating nodes
        self.node_factory = NodeFactory()
        
        # Animation manager
        self.animation_manager = AnimationManager(self)
        
        self._create_canvas()
        self._setup_bindings()
    
    def _create_canvas(self):
        """Create the main canvas widget."""
        self.canvas = Canvas(
            self,
            highlightthickness=0,
            bd=0
        )
        
        # Add scrollbars
        self.v_scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
            scrollregion=(-2000, -2000, 2000, 2000)
        )
        
        # Layout canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _setup_bindings(self):
        """Setup canvas event bindings."""
        # Mouse events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        
        # Keyboard events
        self.canvas.bind("<Delete>", self._on_delete)
        self.canvas.bind("<Control-a>", self._on_select_all)
        self.canvas.bind("<Control-c>", self._on_copy)
        self.canvas.bind("<Control-v>", self._on_paste)
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)
        
        # Focus for keyboard events
        self.canvas.focus_set()
    
    def apply_theme(self):
        """Apply the current theme to the canvas."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        self.canvas.configure(bg=colors["bg_canvas"])
        self.configure(fg_color=colors["bg_secondary"])
        
        # Redraw all nodes and connections with new colors
        self._redraw_all()
    
    def _redraw_all(self):
        """Redraw all canvas elements with current theme."""
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw grid
        self._draw_grid()
        
        # Redraw all connections
        for connection_id, connection in self.connections.items():
            self._draw_connection(connection_id)
        
        # Redraw all nodes
        for node_id, node in self.nodes.items():
            self._draw_node(node_id)
    
    def _draw_grid(self):
        """Draw a subtle grid background."""
        colors = self.theme_manager.get_current_theme()["colors"]
        grid_color = colors["panel_border"]
        
        # Calculate visible area
        x1 = self.canvas.canvasx(0)
        y1 = self.canvas.canvasy(0)
        x2 = self.canvas.canvasx(self.canvas.winfo_width())
        y2 = self.canvas.canvasy(self.canvas.winfo_height())
        
        # Grid spacing
        grid_size = 20 * self.zoom_level
        
        # Draw vertical lines
        x = int(x1 / grid_size) * grid_size
        while x < x2:
            self.canvas.create_line(x, y1, x, y2, fill=grid_color, width=1, tags="grid")
            x += grid_size
        
        # Draw horizontal lines
        y = int(y1 / grid_size) * grid_size
        while y < y2:
            self.canvas.create_line(x1, y, x2, y, fill=grid_color, width=1, tags="grid")
            y += grid_size
    
    def start_node_creation(self, node_type: str):
        """Start creating a new node of the specified type."""
        self.creating_node_type = node_type
        self.canvas.configure(cursor="crosshair")
        
        # Add visual feedback on canvas
        self._show_creation_hint(node_type)
    
    def _on_click(self, event):
        """Handle mouse click events."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        clicked_item = self.canvas.find_closest(x, y)[0]
        
        # Check if creating a new node
        if self.creating_node_type:
            self._create_node_at_position(self.creating_node_type, x, y)
            self.creating_node_type = None
            self.canvas.configure(cursor="")
            self._hide_creation_hint()
            return
        
        # Check what was clicked
        tags = self.canvas.gettags(clicked_item)
        
        if "node" in tags:
            # Get node ID from tags
            node_id = next((tag for tag in tags if tag.startswith("node_")), None)
            if node_id:
                node_id = node_id[5:]  # Remove "node_" prefix
                self._select_node(node_id)
                self.dragging_node = node_id
        
        elif "pin" in tags:
            # Handle pin clicks for connections
            self._handle_pin_click(tags, x, y)
        
        else:
            # Clicked on empty canvas
            self._select_node(None)
    
    def _on_drag(self, event):
        """Handle mouse drag events."""
        if self.dragging_node:
            x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            self._move_node(self.dragging_node, x, y)
    
    def _on_release(self, event):
        """Handle mouse release events."""
        self.dragging_node = None
    
    def _on_mouse_move(self, event):
        """Handle mouse movement for hover effects."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)[0]
        tags = self.canvas.gettags(item)
        
        # Update hover state
        new_hovered = None
        if "node" in tags:
            node_id = next((tag for tag in tags if tag.startswith("node_")), None)
            if node_id:
                new_hovered = node_id[5:]
        
        if new_hovered != self.hovered_node:
            if self.hovered_node:
                self._update_node_visual_state(self.hovered_node)
            self.hovered_node = new_hovered
            if self.hovered_node:
                self._update_node_visual_state(self.hovered_node)
    
    def _on_double_click(self, event):
        """Handle double-click events."""
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        item = self.canvas.find_closest(x, y)[0]
        tags = self.canvas.gettags(item)
        
        if "node" in tags:
            node_id = next((tag for tag in tags if tag.startswith("node_")), None)
            if node_id:
                node_id = node_id[5:]
                self._edit_node(node_id)
    
    def _on_right_click(self, event):
        """Handle right-click context menu."""
        # TODO: Implement context menu
        pass
    
    def _on_delete(self, event):
        """Handle delete key press."""
        if self.selected_node:
            self._delete_node(self.selected_node)
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        # Determine zoom direction
        if event.delta > 0 or event.num == 4:
            zoom_factor = 1.1
        else:
            zoom_factor = 0.9
        
        # Update zoom level
        new_zoom = self.zoom_level * zoom_factor
        if 0.1 <= new_zoom <= 5.0:
            self.zoom_level = new_zoom
            self._apply_zoom()
    
    def _create_node_at_position(self, node_type: str, x: float, y: float):
        """Create a new node at the specified position."""
        node_id = str(uuid.uuid4())
        
        # Create node data using factory
        node_data = self.node_factory.create_node(node_type, node_id)
        node_data["position"] = {"x": x, "y": y}
        
        # Add to nodes collection
        self.nodes[node_id] = node_data
        
        # Draw the node
        self._draw_node(node_id)
        
        # Select the new node
        self._select_node(node_id)
        
        # Mark as changed
        self._mark_changed()
    
    def _draw_node(self, node_id: str):
        """Draw a node on the canvas with modern styling."""
        node = self.nodes[node_id]
        pos = node["position"]
        x, y = pos["x"], pos["y"]
        
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Node dimensions
        width, height = 120, 80
        corner_radius = 8
        
        # Determine node state colors
        state = "normal"
        if node_id == self.selected_node:
            state = "selected"
        elif node_id == self.hovered_node:
            state = "hover"
        
        # Draw node background with rounded corners
        self._draw_rounded_rectangle(
            x - width//2, y - height//2,
            x + width//2, y + height//2,
            corner_radius, node_id, state
        )
        
        # Draw node title
        title = node.get("title", node["type"])
        self.canvas.create_text(
            x, y - 20,
            text=title,
            fill=colors["text_primary"],
            font=("Arial", 10, "bold"),
            tags=(f"node_{node_id}", "node", "text")
        )
        
        # Draw node type
        self.canvas.create_text(
            x, y,
            text=node["type"],
            fill=colors["text_secondary"],
            font=("Arial", 8),
            tags=(f"node_{node_id}", "node", "text")
        )
        
        # Draw input pins
        inputs = node.get("inputs", [])
        for i, input_pin in enumerate(inputs):
            pin_x = x - width//2 - 5
            pin_y = y - 20 + (i * 15)
            self._draw_pin(pin_x, pin_y, "input", node_id, input_pin["name"])
        
        # Draw output pins
        outputs = node.get("outputs", [])
        for i, output_pin in enumerate(outputs):
            pin_x = x + width//2 + 5
            pin_y = y - 20 + (i * 15)
            self._draw_pin(pin_x, pin_y, "output", node_id, output_pin["name"])
        
        # Draw status indicator if node has status
        status = node.get("status")
        if status:
            self._draw_status_indicator(x + width//2 - 10, y - height//2 + 10, status)
    
    def _draw_rounded_rectangle(self, x1: float, y1: float, x2: float, y2: float,
                              radius: float, node_id: str, state: str):
        """Draw a rounded rectangle for the node background."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Determine colors based on state
        if state == "selected":
            fill_color = colors["node_bg"]
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
        
        # Create rounded rectangle using polygons
        points = self._get_rounded_rect_points(x1, y1, x2, y2, radius)
        
        self.canvas.create_polygon(
            points,
            fill=fill_color,
            outline=outline_color,
            width=width,
            smooth=True,
            tags=(f"node_{node_id}", "node", "background")
        )
    
    def _get_rounded_rect_points(self, x1: float, y1: float, x2: float, y2: float,
                               radius: float) -> List[float]:
        """Generate points for a rounded rectangle."""
        points = []
        
        # Top side
        points.extend([x1 + radius, y1])
        points.extend([x2 - radius, y1])
        
        # Top-right corner
        for i in range(10):
            angle = i * math.pi / 20
            points.extend([x2 - radius + radius * math.cos(angle),
                          y1 + radius - radius * math.sin(angle)])
        
        # Right side
        points.extend([x2, y1 + radius])
        points.extend([x2, y2 - radius])
        
        # Bottom-right corner
        for i in range(10):
            angle = i * math.pi / 20
            points.extend([x2 - radius + radius * math.sin(angle),
                          y2 - radius + radius * math.cos(angle)])
        
        # Bottom side
        points.extend([x2 - radius, y2])
        points.extend([x1 + radius, y2])
        
        # Bottom-left corner
        for i in range(10):
            angle = i * math.pi / 20
            points.extend([x1 + radius - radius * math.cos(angle),
                          y2 - radius + radius * math.sin(angle)])
        
        # Left side
        points.extend([x1, y2 - radius])
        points.extend([x1, y1 + radius])
        
        # Top-left corner
        for i in range(10):
            angle = i * math.pi / 20
            points.extend([x1 + radius - radius * math.sin(angle),
                          y1 + radius - radius * math.cos(angle)])
        
        return points
    
    def _draw_pin(self, x: float, y: float, pin_type: str, node_id: str, pin_name: str):
        """Draw an input or output pin."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        radius = 4
        fill_color = colors["accent_primary"] if pin_type == "output" else colors["input_bg"]
        outline_color = colors["accent_primary"]
        
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline=outline_color,
            width=2,
            tags=(f"pin_{node_id}_{pin_type}_{pin_name}", "pin", pin_type)
        )
    
    def _draw_status_indicator(self, x: float, y: float, status: str):
        """Draw a status indicator on the node."""
        colors = self.theme_manager.get_current_theme()["colors"]
        
        status_colors = {
            "running": colors["info"],
            "success": colors["success"],
            "error": colors["error"],
            "warning": colors["warning"]
        }
        
        color = status_colors.get(status, colors["text_secondary"])
        
        self.canvas.create_oval(
            x - 4, y - 4, x + 4, y + 4,
            fill=color,
            outline=color,
            tags=("status",)
        )
    
    def _draw_connection(self, connection_id: str):
        """Draw a connection between two pins."""
        connection = self.connections[connection_id]
        colors = self.theme_manager.get_current_theme()["colors"]
        
        # Get pin positions
        from_pos = self._get_pin_position(connection["from_node"], connection["from_pin"])
        to_pos = self._get_pin_position(connection["to_node"], connection["to_pin"])
        
        if from_pos and to_pos:
            # Create curved connection line
            control_points = self._calculate_bezier_control_points(from_pos, to_pos)
            
            # Draw bezier curve
            self._draw_bezier_curve(
                from_pos, control_points[0], control_points[1], to_pos,
                colors["connection_line"], 2, f"connection_{connection_id}"
            )
    
    def _get_pin_position(self, node_id: str, pin_name: str) -> Optional[Point]:
        """Get the canvas position of a pin."""
        if node_id not in self.nodes:
            return None
        
        # Find pin canvas item
        pin_tags = self.canvas.find_withtag(f"pin_{node_id}_output_{pin_name}") or \
                   self.canvas.find_withtag(f"pin_{node_id}_input_{pin_name}")
        
        if pin_tags:
            coords = self.canvas.coords(pin_tags[0])
            if len(coords) >= 4:
                x = (coords[0] + coords[2]) / 2
                y = (coords[1] + coords[3]) / 2
                return Point(x, y)
        
        return None
    
    def _calculate_bezier_control_points(self, start: Point, end: Point) -> Tuple[Point, Point]:
        """Calculate control points for a smooth bezier curve."""
        offset = 50
        control1 = Point(start.x + offset, start.y)
        control2 = Point(end.x - offset, end.y)
        return (control1, control2)
    
    def _draw_bezier_curve(self, start: Point, control1: Point, control2: Point, end: Point,
                          color: str, width: int, tags: str):
        """Draw a smooth bezier curve."""
        # Generate points along the curve
        points = []
        steps = 20
        
        for i in range(steps + 1):
            t = i / steps
            x, y = self._bezier_point(start, control1, control2, end, t)
            points.extend([x, y])
        
        self.canvas.create_line(
            points,
            fill=color,
            width=width,
            smooth=True,
            tags=(tags, "connection")
        )
    
    def _bezier_point(self, p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Tuple[float, float]:
        """Calculate a point on a cubic bezier curve."""
        x = (1-t)**3 * p0.x + 3*(1-t)**2*t * p1.x + 3*(1-t)*t**2 * p2.x + t**3 * p3.x
        y = (1-t)**3 * p0.y + 3*(1-t)**2*t * p1.y + 3*(1-t)*t**2 * p2.y + t**3 * p3.y
        return (x, y)
    
    def _select_node(self, node_id: Optional[str]):
        """Select a node and update visual state."""
        if self.selected_node:
            self._update_node_visual_state(self.selected_node)
        
        self.selected_node = node_id
        
        if self.selected_node:
            self._update_node_visual_state(self.selected_node)
        
        # Notify selection change
        self.on_node_selected(node_id)
    
    def _update_node_visual_state(self, node_id: str):
        """Update the visual state of a node."""
        if node_id in self.nodes:
            # Redraw the node with current state
            self.canvas.delete(f"node_{node_id}")
            self._draw_node(node_id)
    
    def _move_node(self, node_id: str, x: float, y: float):
        """Move a node to a new position."""
        if node_id in self.nodes:
            self.nodes[node_id]["position"]["x"] = x
            self.nodes[node_id]["position"]["y"] = y
            
            # Redraw node and its connections
            self.canvas.delete(f"node_{node_id}")
            self._draw_node(node_id)
            self._redraw_node_connections(node_id)
            
            self._mark_changed()
    
    def _redraw_node_connections(self, node_id: str):
        """Redraw all connections for a node."""
        for connection_id, connection in self.connections.items():
            if connection["from_node"] == node_id or connection["to_node"] == node_id:
                self.canvas.delete(f"connection_{connection_id}")
                self._draw_connection(connection_id)
    
    def _handle_pin_click(self, tags: List[str], x: float, y: float):
        """Handle clicks on pins for creating connections."""
        # Extract pin information from tags
        pin_tag = next((tag for tag in tags if tag.startswith("pin_")), None)
        if not pin_tag:
            return
        
        parts = pin_tag.split("_")
        if len(parts) >= 4:
            node_id = parts[1]
            pin_type = parts[2]  # "input" or "output"
            pin_name = "_".join(parts[3:])
            
            if self.connecting_from is None:
                # Start connection from output pin
                if pin_type == "output":
                    self.connecting_from = (node_id, pin_name)
            else:
                # Complete connection to input pin
                if pin_type == "input":
                    from_node, from_pin = self.connecting_from
                    self._create_connection(from_node, from_pin, node_id, pin_name)
                
                self.connecting_from = None
    
    def _create_connection(self, from_node: str, from_pin: str, to_node: str, to_pin: str):
        """Create a connection between two pins."""
        connection_id = str(uuid.uuid4())
        
        connection_data = {
            "from_node": from_node,
            "from_pin": from_pin,
            "to_node": to_node,
            "to_pin": to_pin
        }
        
        self.connections[connection_id] = connection_data
        self._draw_connection(connection_id)
        self._mark_changed()
    
    def _delete_node(self, node_id: str):
        """Delete a node and its connections."""
        if node_id not in self.nodes:
            return
        
        # Remove all connections involving this node
        connections_to_remove = []
        for connection_id, connection in self.connections.items():
            if connection["from_node"] == node_id or connection["to_node"] == node_id:
                connections_to_remove.append(connection_id)
        
        for connection_id in connections_to_remove:
            self.canvas.delete(f"connection_{connection_id}")
            del self.connections[connection_id]
        
        # Remove the node
        self.canvas.delete(f"node_{node_id}")
        del self.nodes[node_id]
        
        # Clear selection if this node was selected
        if self.selected_node == node_id:
            self._select_node(None)
        
        self._mark_changed()
    
    def _mark_changed(self):
        """Mark the canvas as having unsaved changes."""
        self.unsaved_changes = True
        self.on_canvas_changed()
    
    def _apply_zoom(self):
        """Apply the current zoom level to the canvas."""
        # TODO: Implement proper zooming
        pass
    
    def clear_canvas(self):
        """Clear all nodes and connections."""
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.selected_node = None
        self.hovered_node = None
        self.unsaved_changes = False
        self._draw_grid()
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.unsaved_changes
    
    def mark_saved(self):
        """Mark the canvas as saved."""
        self.unsaved_changes = False
    
    def has_nodes(self) -> bool:
        """Check if the canvas has any nodes."""
        return len(self.nodes) > 0
    
    def get_workflow_data(self) -> Dict:
        """Get the complete workflow data for serialization."""
        return {
            "nodes": self.nodes,
            "connections": self.connections,
            "canvas_state": {
                "zoom_level": self.zoom_level,
                "pan_offset": {"x": self.pan_offset.x, "y": self.pan_offset.y}
            }
        }
    
    def load_workflow(self, workflow_data: Dict):
        """Load workflow data into the canvas."""
        self.clear_canvas()
        
        # Load nodes
        self.nodes = workflow_data.get("nodes", {})
        
        # Load connections
        self.connections = workflow_data.get("connections", {})
        
        # Load canvas state
        canvas_state = workflow_data.get("canvas_state", {})
        self.zoom_level = canvas_state.get("zoom_level", 1.0)
        pan_offset = canvas_state.get("pan_offset", {"x": 0, "y": 0})
        self.pan_offset = Point(pan_offset["x"], pan_offset["y"])
        
        # Redraw everything
        self._redraw_all()
        
        self.unsaved_changes = False
    
    def get_node_data(self, node_id: str) -> Optional[Dict]:
        """Get data for a specific node."""
        return self.nodes.get(node_id)
    
    def get_selected_node(self) -> Optional[str]:
        """Get the currently selected node ID."""
        return self.selected_node
    
    def update_node_property(self, node_id: str, property_name: str, value: Any):
        """Update a property of a node."""
        if node_id in self.nodes:
            if "properties" not in self.nodes[node_id]:
                self.nodes[node_id]["properties"] = {}
            
            self.nodes[node_id]["properties"][property_name] = value
            self._mark_changed()
    
    def update_node_status(self, node_id: str, status: str):
        """Update the execution status of a node."""
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
            self._update_node_visual_state(node_id)
    
    def clear_node_statuses(self):
        """Clear execution status from all nodes."""
        for node in self.nodes.values():
            node.pop("status", None)
        self._redraw_all()
    
    # Stub methods for missing event handlers
    def _on_select_all(self, event):
        """Handle select all."""
        pass
    
    def _on_copy(self, event):
        """Handle copy."""
        pass
    
    def _on_paste(self, event):
        """Handle paste."""
        pass
    
    def _edit_node(self, node_id: str):
        """Edit node properties."""
        pass
