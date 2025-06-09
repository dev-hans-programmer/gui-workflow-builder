"""
Animation utilities for smooth UI interactions and transitions.
Provides easing functions, animation controllers, and visual effects.
"""

import math
import time
import threading
from typing import Callable, Optional, Any, Dict, List
from dataclasses import dataclass
from enum import Enum

class EasingType(Enum):
    """Easing function types for animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    ELASTIC = "elastic"
    BOUNCE = "bounce"
    SPRING = "spring"

@dataclass
class AnimationFrame:
    """Represents a single frame in an animation."""
    time: float
    value: Any
    progress: float

class EasingFunctions:
    """Collection of easing functions for smooth animations."""
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation."""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in."""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out."""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in."""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out."""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out."""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def elastic_out(t: float) -> float:
        """Elastic ease-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        
        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @staticmethod
    def bounce_out(t: float) -> float:
        """Bounce ease-out."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t - 1.5 / d1) * t + 0.75
        elif t < 2.5 / d1:
            return n1 * (t - 2.25 / d1) * t + 0.9375
        else:
            return n1 * (t - 2.625 / d1) * t + 0.984375
    
    @staticmethod
    def spring(t: float, tension: float = 100, friction: float = 10) -> float:
        """Spring animation with configurable tension and friction."""
        # Simplified spring physics
        omega = math.sqrt(tension)
        zeta = friction / (2 * math.sqrt(tension))
        
        if zeta < 1:  # Underdamped
            omega_d = omega * math.sqrt(1 - zeta * zeta)
            return 1 - math.exp(-zeta * omega * t) * math.cos(omega_d * t)
        else:  # Overdamped
            return 1 - math.exp(-omega * t)
    
    @classmethod
    def get_easing_function(cls, easing_type: EasingType) -> Callable[[float], float]:
        """Get easing function by type."""
        mapping = {
            EasingType.LINEAR: cls.linear,
            EasingType.EASE_IN: cls.ease_in_cubic,
            EasingType.EASE_OUT: cls.ease_out_cubic,
            EasingType.EASE_IN_OUT: cls.ease_in_out_cubic,
            EasingType.ELASTIC: cls.elastic_out,
            EasingType.BOUNCE: cls.bounce_out,
            EasingType.SPRING: cls.spring
        }
        return mapping.get(easing_type, cls.linear)

class Animation:
    """Represents a single animation with timing and easing."""
    
    def __init__(self, start_value: Any, end_value: Any, duration: float,
                 easing: EasingType = EasingType.EASE_OUT,
                 on_update: Optional[Callable[[Any], None]] = None,
                 on_complete: Optional[Callable[[], None]] = None):
        """Initialize animation."""
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.easing = easing
        self.on_update = on_update
        self.on_complete = on_complete
        
        self.start_time: Optional[float] = None
        self.is_running = False
        self.is_completed = False
        self.current_value = start_value
        
        self.easing_function = EasingFunctions.get_easing_function(easing)
    
    def start(self):
        """Start the animation."""
        self.start_time = time.time()
        self.is_running = True
        self.is_completed = False
    
    def update(self) -> bool:
        """Update animation and return True if still running."""
        if not self.is_running or self.is_completed:
            return False
        
        if self.start_time is None:
            self.start()
        
        elapsed = time.time() - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Apply easing
        eased_progress = self.easing_function(progress)
        
        # Interpolate value
        self.current_value = self._interpolate(self.start_value, self.end_value, eased_progress)
        
        # Call update callback
        if self.on_update:
            self.on_update(self.current_value)
        
        # Check if completed
        if progress >= 1.0:
            self.is_completed = True
            self.is_running = False
            if self.on_complete:
                self.on_complete()
            return False
        
        return True
    
    def stop(self):
        """Stop the animation."""
        self.is_running = False
    
    def reset(self):
        """Reset animation to initial state."""
        self.start_time = None
        self.is_running = False
        self.is_completed = False
        self.current_value = self.start_value
    
    def _interpolate(self, start: Any, end: Any, progress: float) -> Any:
        """Interpolate between start and end values."""
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            return start + (end - start) * progress
        elif isinstance(start, tuple) and isinstance(end, tuple) and len(start) == len(end):
            # Tuple interpolation (e.g., colors, coordinates)
            return tuple(s + (e - s) * progress for s, e in zip(start, end))
        elif isinstance(start, dict) and isinstance(end, dict):
            # Dictionary interpolation
            result = {}
            for key in start.keys():
                if key in end:
                    result[key] = self._interpolate(start[key], end[key], progress)
                else:
                    result[key] = start[key]
            return result
        else:
            # For non-numeric types, return end value when progress > 0.5
            return end if progress > 0.5 else start

class AnimationManager:
    """Manages multiple animations with threading support."""
    
    def __init__(self, parent_widget=None):
        """Initialize animation manager."""
        self.parent_widget = parent_widget
        self.animations: Dict[str, Animation] = {}
        self.animation_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.frame_rate = 60  # FPS
        self.frame_time = 1.0 / self.frame_rate
    
    def add_animation(self, name: str, animation: Animation) -> str:
        """Add animation to manager."""
        self.animations[name] = animation
        self._ensure_animation_loop()
        return name
    
    def create_animation(self, name: str, start_value: Any, end_value: Any,
                        duration: float, easing: EasingType = EasingType.EASE_OUT,
                        on_update: Optional[Callable[[Any], None]] = None,
                        on_complete: Optional[Callable[[], None]] = None) -> str:
        """Create and add new animation."""
        animation = Animation(start_value, end_value, duration, easing, on_update, on_complete)
        return self.add_animation(name, animation)
    
    def start_animation(self, name: str):
        """Start specific animation."""
        if name in self.animations:
            self.animations[name].start()
            self._ensure_animation_loop()
    
    def stop_animation(self, name: str):
        """Stop specific animation."""
        if name in self.animations:
            self.animations[name].stop()
    
    def remove_animation(self, name: str):
        """Remove animation from manager."""
        if name in self.animations:
            self.animations[name].stop()
            del self.animations[name]
    
    def stop_all(self):
        """Stop all animations."""
        for animation in self.animations.values():
            animation.stop()
        self.is_running = False
    
    def clear_all(self):
        """Clear all animations."""
        self.stop_all()
        self.animations.clear()
    
    def _ensure_animation_loop(self):
        """Ensure animation loop is running."""
        if not self.is_running and self.animations:
            self.is_running = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()
    
    def _animation_loop(self):
        """Main animation loop."""
        while self.is_running and self.animations:
            start_time = time.time()
            
            # Update all animations
            completed_animations = []
            for name, animation in self.animations.items():
                if animation.is_running and not animation.update():
                    completed_animations.append(name)
            
            # Remove completed animations
            for name in completed_animations:
                if name in self.animations:
                    del self.animations[name]
            
            # Check if any animations are still running
            if not any(anim.is_running for anim in self.animations.values()):
                self.is_running = False
                break
            
            # Sleep for frame timing
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def animate_property(self, widget, property_name: str, target_value: Any,
                        duration: float = 0.3, easing: EasingType = EasingType.EASE_OUT,
                        on_complete: Optional[Callable[[], None]] = None) -> str:
        """Animate a widget property."""
        # Get current value
        try:
            current_value = getattr(widget, property_name)
        except AttributeError:
            current_value = 0
        
        # Create update function
        def update_property(value):
            try:
                if self.parent_widget:
                    self.parent_widget.after(0, lambda: setattr(widget, property_name, value))
                else:
                    setattr(widget, property_name, value)
            except Exception:
                pass  # Widget might be destroyed
        
        # Create animation
        animation_name = f"{id(widget)}_{property_name}"
        return self.create_animation(
            animation_name, current_value, target_value, duration, easing,
            update_property, on_complete
        )
    
    def fade_in(self, widget, duration: float = 0.3) -> str:
        """Fade in animation."""
        return self.animate_property(widget, 'alpha', 1.0, duration)
    
    def fade_out(self, widget, duration: float = 0.3) -> str:
        """Fade out animation."""
        return self.animate_property(widget, 'alpha', 0.0, duration)
    
    def slide_in(self, widget, direction: str = "left", distance: int = 100,
                duration: float = 0.3) -> str:
        """Slide in animation."""
        current_x = getattr(widget, 'x', 0)
        current_y = getattr(widget, 'y', 0)
        
        if direction == "left":
            start_x = current_x - distance
            target_x = current_x
            target_y = current_y
        elif direction == "right":
            start_x = current_x + distance
            target_x = current_x
            target_y = current_y
        elif direction == "up":
            start_x = current_x
            start_y = current_y - distance
            target_x = current_x
            target_y = current_y
        else:  # down
            start_x = current_x
            start_y = current_y + distance
            target_x = current_x
            target_y = current_y
        
        # Set initial position
        if hasattr(widget, 'place'):
            widget.place(x=start_x, y=getattr(widget, 'y', 0))
        
        return self.animate_property(widget, 'x', target_x, duration, EasingType.EASE_OUT)
    
    def scale_animation(self, widget, target_scale: float = 1.0, duration: float = 0.3) -> str:
        """Scale animation."""
        return self.animate_property(widget, 'scale', target_scale, duration, EasingType.SPRING)
    
    def pulse_animation(self, widget, intensity: float = 1.2, duration: float = 0.5) -> str:
        """Pulse animation that scales up and down."""
        def on_scale_up_complete():
            self.animate_property(widget, 'scale', 1.0, duration / 2, EasingType.EASE_OUT)
        
        return self.animate_property(widget, 'scale', intensity, duration / 2, 
                                   EasingType.EASE_IN, on_scale_up_complete)
    
    def shake_animation(self, widget, intensity: int = 5, duration: float = 0.5) -> str:
        """Shake animation for error feedback."""
        original_x = getattr(widget, 'x', 0)
        shake_count = int(duration * 10)  # 10 shakes per second
        
        def shake_step(step: int):
            if step >= shake_count:
                # Return to original position
                if hasattr(widget, 'place'):
                    widget.place(x=original_x)
                return
            
            # Calculate shake offset
            progress = step / shake_count
            decay = 1 - progress  # Decay over time
            offset = intensity * decay * (1 if step % 2 == 0 else -1)
            
            # Apply shake
            if hasattr(widget, 'place'):
                widget.place(x=original_x + offset)
            
            # Schedule next shake
            if self.parent_widget:
                self.parent_widget.after(int(1000 / 10), lambda: shake_step(step + 1))
        
        shake_step(0)
        return f"shake_{id(widget)}"
    
    def color_transition(self, widget, target_color: str, duration: float = 0.3,
                        property_name: str = "fg_color") -> str:
        """Animate color transition."""
        # This would need to be implemented with color interpolation
        # For now, just set the target color
        animation_name = f"{id(widget)}_color"
        
        def set_color():
            try:
                if hasattr(widget, 'configure'):
                    widget.configure(**{property_name: target_color})
            except Exception:
                pass
        
        # Use a simple delay for color transition
        if self.parent_widget:
            self.parent_widget.after(int(duration * 1000), set_color)
        
        return animation_name
    
    def chain_animations(self, animations: List[tuple]) -> str:
        """Chain multiple animations to run in sequence."""
        chain_id = f"chain_{int(time.time())}"
        
        def run_next_animation(index: int = 0):
            if index >= len(animations):
                return
            
            name, start_val, end_val, duration, easing = animations[index]
            
            def on_complete():
                run_next_animation(index + 1)
            
            self.create_animation(f"{chain_id}_{index}", start_val, end_val, 
                                duration, easing, None, on_complete)
            self.start_animation(f"{chain_id}_{index}")
        
        run_next_animation()
        return chain_id
    
    def get_animation_count(self) -> int:
        """Get number of active animations."""
        return len([anim for anim in self.animations.values() if anim.is_running])
    
    def is_animating(self, name: str) -> bool:
        """Check if specific animation is running."""
        return name in self.animations and self.animations[name].is_running

# Utility functions for common animation patterns

def create_hover_animation(widget, animation_manager: AnimationManager,
                          hover_scale: float = 1.05, duration: float = 0.2):
    """Create hover animation bindings for a widget."""
    def on_enter(event):
        animation_manager.scale_animation(widget, hover_scale, duration)
    
    def on_leave(event):
        animation_manager.scale_animation(widget, 1.0, duration)
    
    if hasattr(widget, 'bind'):
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

def create_click_animation(widget, animation_manager: AnimationManager,
                          click_scale: float = 0.95, duration: float = 0.1):
    """Create click animation bindings for a widget."""
    def on_button_press(event):
        animation_manager.scale_animation(widget, click_scale, duration)
    
    def on_button_release(event):
        animation_manager.scale_animation(widget, 1.0, duration)
    
    if hasattr(widget, 'bind'):
        widget.bind('<Button-1>', on_button_press)
        widget.bind('<ButtonRelease-1>', on_button_release)

def interpolate_color(start_color: str, end_color: str, progress: float) -> str:
    """Interpolate between two hex colors."""
    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb: tuple) -> str:
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"
    
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    
    interpolated_rgb = tuple(
        start + (end - start) * progress
        for start, end in zip(start_rgb, end_rgb)
    )
    
    return rgb_to_hex(interpolated_rgb)
