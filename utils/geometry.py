"""
Geometric utilities for canvas operations and spatial calculations.
Provides classes and functions for working with points, rectangles, and shapes.
"""

import math
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass

@dataclass
class Point:
    """Represents a 2D point with x and y coordinates."""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        """Add two points."""
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract two points."""
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        """Multiply point by scalar."""
        return Point(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Point':
        """Divide point by scalar."""
        return Point(self.x / scalar, self.y / scalar)
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def magnitude(self) -> float:
        """Calculate magnitude (distance from origin)."""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self) -> 'Point':
        """Normalize the point to unit length."""
        mag = self.magnitude()
        if mag == 0:
            return Point(0, 0)
        return Point(self.x / mag, self.y / mag)
    
    def dot(self, other: 'Point') -> float:
        """Calculate dot product with another point."""
        return self.x * other.x + self.y * other.y
    
    def angle_to(self, other: 'Point') -> float:
        """Calculate angle to another point in radians."""
        return math.atan2(other.y - self.y, other.x - self.x)
    
    def rotate(self, angle: float, origin: Optional['Point'] = None) -> 'Point':
        """Rotate point around origin by angle (in radians)."""
        if origin is None:
            origin = Point(0, 0)
        
        # Translate to origin
        translated = self - origin
        
        # Rotate
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        rotated_x = translated.x * cos_a - translated.y * sin_a
        rotated_y = translated.x * sin_a + translated.y * cos_a
        
        # Translate back
        return Point(rotated_x, rotated_y) + origin
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)
    
    def to_int_tuple(self) -> Tuple[int, int]:
        """Convert to integer tuple."""
        return (int(self.x), int(self.y))
    
    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> 'Point':
        """Create point from tuple."""
        return cls(coords[0], coords[1])

@dataclass
class Rectangle:
    """Represents a rectangle with position and dimensions."""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def left(self) -> float:
        """Left edge x-coordinate."""
        return self.x
    
    @property
    def right(self) -> float:
        """Right edge x-coordinate."""
        return self.x + self.width
    
    @property
    def top(self) -> float:
        """Top edge y-coordinate."""
        return self.y
    
    @property
    def bottom(self) -> float:
        """Bottom edge y-coordinate."""
        return self.y + self.height
    
    @property
    def center(self) -> Point:
        """Center point of rectangle."""
        return Point(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def top_left(self) -> Point:
        """Top-left corner."""
        return Point(self.x, self.y)
    
    @property
    def top_right(self) -> Point:
        """Top-right corner."""
        return Point(self.right, self.y)
    
    @property
    def bottom_left(self) -> Point:
        """Bottom-left corner."""
        return Point(self.x, self.bottom)
    
    @property
    def bottom_right(self) -> Point:
        """Bottom-right corner."""
        return Point(self.right, self.bottom)
    
    def contains_point(self, point: Point) -> bool:
        """Check if rectangle contains a point."""
        return (self.left <= point.x <= self.right and
                self.top <= point.y <= self.bottom)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """Check if this rectangle intersects with another."""
        return (self.left < other.right and
                self.right > other.left and
                self.top < other.bottom and
                self.bottom > other.top)
    
    def intersection(self, other: 'Rectangle') -> Optional['Rectangle']:
        """Get intersection rectangle with another rectangle."""
        if not self.intersects(other):
            return None
        
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        
        return Rectangle(left, top, right - left, bottom - top)
    
    def union(self, other: 'Rectangle') -> 'Rectangle':
        """Get union rectangle with another rectangle."""
        left = min(self.left, other.left)
        top = min(self.top, other.top)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        
        return Rectangle(left, top, right - left, bottom - top)
    
    def expand(self, amount: float) -> 'Rectangle':
        """Expand rectangle by amount in all directions."""
        return Rectangle(
            self.x - amount,
            self.y - amount,
            self.width + 2 * amount,
            self.height + 2 * amount
        )
    
    def scale(self, factor: float, origin: Optional[Point] = None) -> 'Rectangle':
        """Scale rectangle by factor around origin."""
        if origin is None:
            origin = self.center
        
        new_width = self.width * factor
        new_height = self.height * factor
        
        # Calculate new position to maintain origin
        new_x = origin.x - (origin.x - self.x) * factor
        new_y = origin.y - (origin.y - self.y) * factor
        
        return Rectangle(new_x, new_y, new_width, new_height)
    
    def area(self) -> float:
        """Calculate area of rectangle."""
        return self.width * self.height
    
    def perimeter(self) -> float:
        """Calculate perimeter of rectangle."""
        return 2 * (self.width + self.height)
    
    @classmethod
    def from_points(cls, p1: Point, p2: Point) -> 'Rectangle':
        """Create rectangle from two corner points."""
        x = min(p1.x, p2.x)
        y = min(p1.y, p2.y)
        width = abs(p2.x - p1.x)
        height = abs(p2.y - p1.y)
        return cls(x, y, width, height)
    
    @classmethod
    def from_center(cls, center: Point, width: float, height: float) -> 'Rectangle':
        """Create rectangle from center point and dimensions."""
        x = center.x - width / 2
        y = center.y - height / 2
        return cls(x, y, width, height)

class Transform:
    """2D transformation matrix for scaling, rotation, and translation."""
    
    def __init__(self, matrix: Optional[List[List[float]]] = None):
        """Initialize transform with optional matrix."""
        if matrix is None:
            # Identity matrix
            self.matrix = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
        else:
            self.matrix = matrix
    
    def translate(self, dx: float, dy: float) -> 'Transform':
        """Apply translation."""
        translation = Transform([
            [1.0, 0.0, dx],
            [0.0, 1.0, dy],
            [0.0, 0.0, 1.0]
        ])
        return self.multiply(translation)
    
    def scale(self, sx: float, sy: Optional[float] = None) -> 'Transform':
        """Apply scaling."""
        if sy is None:
            sy = sx
        
        scaling = Transform([
            [sx, 0.0, 0.0],
            [0.0, sy, 0.0],
            [0.0, 0.0, 1.0]
        ])
        return self.multiply(scaling)
    
    def rotate(self, angle: float) -> 'Transform':
        """Apply rotation (angle in radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        rotation = Transform([
            [cos_a, -sin_a, 0.0],
            [sin_a, cos_a, 0.0],
            [0.0, 0.0, 1.0]
        ])
        return self.multiply(rotation)
    
    def multiply(self, other: 'Transform') -> 'Transform':
        """Multiply with another transform."""
        result = [[0.0] * 3 for _ in range(3)]
        
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    result[i][j] += self.matrix[i][k] * other.matrix[k][j]
        
        return Transform(result)
    
    def transform_point(self, point: Point) -> Point:
        """Transform a point using this transformation."""
        x = self.matrix[0][0] * point.x + self.matrix[0][1] * point.y + self.matrix[0][2]
        y = self.matrix[1][0] * point.x + self.matrix[1][1] * point.y + self.matrix[1][2]
        return Point(x, y)
    
    def inverse(self) -> 'Transform':
        """Calculate inverse transformation."""
        # Calculate determinant
        det = (self.matrix[0][0] * (self.matrix[1][1] * self.matrix[2][2] - 
                                   self.matrix[1][2] * self.matrix[2][1]) -
               self.matrix[0][1] * (self.matrix[1][0] * self.matrix[2][2] - 
                                   self.matrix[1][2] * self.matrix[2][0]) +
               self.matrix[0][2] * (self.matrix[1][0] * self.matrix[2][1] - 
                                   self.matrix[1][1] * self.matrix[2][0]))
        
        if abs(det) < 1e-10:
            raise ValueError("Transform is not invertible")
        
        # Calculate inverse matrix
        inv = [[0.0] * 3 for _ in range(3)]
        
        inv[0][0] = (self.matrix[1][1] * self.matrix[2][2] - 
                     self.matrix[1][2] * self.matrix[2][1]) / det
        inv[0][1] = (self.matrix[0][2] * self.matrix[2][1] - 
                     self.matrix[0][1] * self.matrix[2][2]) / det
        inv[0][2] = (self.matrix[0][1] * self.matrix[1][2] - 
                     self.matrix[0][2] * self.matrix[1][1]) / det
        
        inv[1][0] = (self.matrix[1][2] * self.matrix[2][0] - 
                     self.matrix[1][0] * self.matrix[2][2]) / det
        inv[1][1] = (self.matrix[0][0] * self.matrix[2][2] - 
                     self.matrix[0][2] * self.matrix[2][0]) / det
        inv[1][2] = (self.matrix[0][2] * self.matrix[1][0] - 
                     self.matrix[0][0] * self.matrix[1][2]) / det
        
        inv[2][0] = (self.matrix[1][0] * self.matrix[2][1] - 
                     self.matrix[1][1] * self.matrix[2][0]) / det
        inv[2][1] = (self.matrix[0][1] * self.matrix[2][0] - 
                     self.matrix[0][0] * self.matrix[2][1]) / det
        inv[2][2] = (self.matrix[0][0] * self.matrix[1][1] - 
                     self.matrix[0][1] * self.matrix[1][0]) / det
        
        return Transform(inv)

# Utility functions

def distance_between_points(p1: Point, p2: Point) -> float:
    """Calculate distance between two points."""
    return p1.distance_to(p2)

def midpoint(p1: Point, p2: Point) -> Point:
    """Calculate midpoint between two points."""
    return Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)

def angle_between_points(p1: Point, p2: Point) -> float:
    """Calculate angle from p1 to p2 in radians."""
    return math.atan2(p2.y - p1.y, p2.x - p1.x)

def point_on_circle(center: Point, radius: float, angle: float) -> Point:
    """Get point on circle at given angle."""
    x = center.x + radius * math.cos(angle)
    y = center.y + radius * math.sin(angle)
    return Point(x, y)

def point_on_line(start: Point, end: Point, t: float) -> Point:
    """Get point on line segment at parameter t (0 to 1)."""
    return Point(
        start.x + t * (end.x - start.x),
        start.y + t * (end.y - start.y)
    )

def closest_point_on_line(point: Point, line_start: Point, line_end: Point) -> Point:
    """Find closest point on line segment to given point."""
    line_vec = line_end - line_start
    point_vec = point - line_start
    
    line_length_sq = line_vec.dot(line_vec)
    if line_length_sq == 0:
        return line_start
    
    t = max(0, min(1, point_vec.dot(line_vec) / line_length_sq))
    return point_on_line(line_start, line_end, t)

def point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    """Check if point is inside polygon using ray casting algorithm."""
    if len(polygon) < 3:
        return False
    
    x, y = point.x, point.y
    inside = False
    
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i].x, polygon[i].y
        xj, yj = polygon[j].x, polygon[j].y
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside

def convex_hull(points: List[Point]) -> List[Point]:
    """Calculate convex hull using Graham scan algorithm."""
    if len(points) < 3:
        return points
    
    # Find the bottom-most point (or left most in case of tie)
    start = min(points, key=lambda p: (p.y, p.x))
    
    # Sort points by polar angle with respect to start point
    def polar_angle(p):
        return math.atan2(p.y - start.y, p.x - start.x)
    
    sorted_points = sorted([p for p in points if p != start], key=polar_angle)
    
    # Build convex hull
    hull = [start]
    
    for point in sorted_points:
        # Remove points that create a right turn
        while len(hull) > 1:
            # Calculate cross product to determine turn direction
            v1 = hull[-1] - hull[-2]
            v2 = point - hull[-1]
            cross = v1.x * v2.y - v1.y * v2.x
            
            if cross <= 0:  # Right turn or collinear
                hull.pop()
            else:
                break
        
        hull.append(point)
    
    return hull

def bounding_box(points: List[Point]) -> Rectangle:
    """Calculate bounding box for a list of points."""
    if not points:
        return Rectangle(0, 0, 0, 0)
    
    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)
    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)
    
    return Rectangle(min_x, min_y, max_x - min_x, max_y - min_y)

def bezier_curve(control_points: List[Point], t: float) -> Point:
    """Calculate point on Bezier curve at parameter t."""
    if not control_points:
        return Point(0, 0)
    
    if len(control_points) == 1:
        return control_points[0]
    
    # De Casteljau's algorithm
    points = control_points[:]
    
    while len(points) > 1:
        new_points = []
        for i in range(len(points) - 1):
            x = points[i].x + t * (points[i + 1].x - points[i].x)
            y = points[i].y + t * (points[i + 1].y - points[i].y)
            new_points.append(Point(x, y))
        points = new_points
    
    return points[0]

def line_intersection(line1_start: Point, line1_end: Point,
                     line2_start: Point, line2_end: Point) -> Optional[Point]:
    """Find intersection point of two line segments."""
    x1, y1 = line1_start.x, line1_start.y
    x2, y2 = line1_end.x, line1_end.y
    x3, y3 = line2_start.x, line2_start.y
    x4, y4 = line2_end.x, line2_end.y
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None  # Lines are parallel
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    if 0 <= t <= 1 and 0 <= u <= 1:
        # Intersection within both line segments
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return Point(x, y)
    
    return None

def grid_snap(point: Point, grid_size: float) -> Point:
    """Snap point to grid."""
    x = round(point.x / grid_size) * grid_size
    y = round(point.y / grid_size) * grid_size
    return Point(x, y)

def viewport_transform(point: Point, viewport: Rectangle, 
                      world_bounds: Rectangle) -> Point:
    """Transform world coordinates to viewport coordinates."""
    # Calculate scale factors
    scale_x = viewport.width / world_bounds.width
    scale_y = viewport.height / world_bounds.height
    
    # Transform coordinates
    x = viewport.x + (point.x - world_bounds.x) * scale_x
    y = viewport.y + (point.y - world_bounds.y) * scale_y
    
    return Point(x, y)

def inverse_viewport_transform(point: Point, viewport: Rectangle,
                              world_bounds: Rectangle) -> Point:
    """Transform viewport coordinates to world coordinates."""
    # Calculate scale factors
    scale_x = world_bounds.width / viewport.width
    scale_y = world_bounds.height / viewport.height
    
    # Transform coordinates
    x = world_bounds.x + (point.x - viewport.x) * scale_x
    y = world_bounds.y + (point.y - viewport.y) * scale_y
    
    return Point(x, y)
