"""
Enhanced organism visuals - realistic fly/insect rendering.
Draws beautiful animated organisms with anatomically correct features.

Красивая визуализация организмов — реалистичные мухи с анимациями.
"""

import pygame
import numpy as np
from typing import Tuple
from config import CELL_PIXEL_SIZE


class OrganismRenderer:
    """Renders beautiful fly organisms with animation."""
    
    def __init__(self):
        self.wing_angle = 0.0
        
    def draw_fly(self, surface: pygame.Surface, x: float, y: float,
                 color: Tuple[int, int, int], wing_offset: float = 0.0,
                 health_percent: float = 1.0, emotion_state: str = "normal") -> None:
        """
        Draw a fly organism at the given position.
        
        Args:
            surface: Pygame surface to draw on
            x, y: Screen coordinates
            color: Base body color
            wing_offset: Animation offset for wings (-1 to 1)
            health_percent: 0.0 to 1.0
            emotion_state: "fear", "happy", "searching", "normal"
        """
        cx, cy = int(x), int(y)
        
        # Draw based on emotion/state
        if emotion_state == "fear":
            self._draw_scared_fly(surface, cx, cy, color, wing_offset, health_percent)
        elif emotion_state == "searching":
            self._draw_searching_fly(surface, cx, cy, color, wing_offset, health_percent)
        elif emotion_state == "happy":
            self._draw_happy_fly(surface, cx, cy, color, wing_offset, health_percent)
        else:
            self._draw_normal_fly(surface, cx, cy, color, wing_offset, health_percent)
    
    def _draw_normal_fly(self, surf: pygame.Surface, cx: int, cy: int,
                        color: Tuple[int, int, int], wing_angle: float,
                        health: float) -> None:
        """Draw a normal, neutral fly."""
        # Body size based on health
        body_radius = int(CELL_PIXEL_SIZE * 0.35 * health)
        
        # Draw wings (semi-transparent)
        wing_color = (200, 220, 240, 100)
        wing_width = body_radius * 3
        wing_height = body_radius * 2
        
        # Left wing
        angle_left = wing_angle * 30
        self._draw_wing(surf, cx - body_radius, cy, wing_width, wing_height,
                       angle_left, wing_color)
        # Right wing
        self._draw_wing(surf, cx + body_radius, cy, wing_width, wing_height,
                       -angle_left, wing_color)
        
        # Body segments
        self._draw_body_segments(surf, cx, cy, body_radius, color, health)
        
        # Head with eyes
        head_color = tuple(min(255, c + 20) for c in color)
        pygame.draw.circle(surf, head_color, (cx, cy - body_radius), body_radius // 2)
        
        # Eyes
        eye_color = (255, 255, 255)
        pygame.draw.circle(surf, eye_color, (cx - 2, cy - body_radius - 1), 1)
        pygame.draw.circle(surf, eye_color, (cx + 2, cy - body_radius - 1), 1)
        
        # Antennae
        self._draw_antennae(surf, cx, cy - body_radius, color)
    
    def _draw_scared_fly(self, surf: pygame.Surface, cx: int, cy: int,
                        color: Tuple[int, int, int], wing_angle: float,
                        health: float) -> None:
        """Draw a fly showing fear - erratic wings, tense body."""
        body_radius = int(CELL_PIXEL_SIZE * 0.35 * health)
        
        # Erratic wing movement
        wing_color = (200, 220, 240, 150)
        wing_width = body_radius * 3.5
        wing_height = body_radius * 2.5
        
        for i in range(2):
            angle_variation = wing_angle * (40 + np.random.uniform(-20, 20))
            self._draw_wing(surf, cx - body_radius - i * 2, cy, wing_width,
                           wing_height, angle_variation, wing_color)
        
        # Tense body - darker color
        fear_color = tuple(int(c * 0.7) for c in color)
        self._draw_body_segments(surf, cx, cy, body_radius, fear_color, health)
        
        # Eyes wide open
        head_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.circle(surf, head_color, (cx, cy - body_radius), body_radius // 2)
        
        eye_color = (255, 100, 100)  # Red tinted eyes
        pygame.draw.circle(surf, eye_color, (cx - 2, cy - body_radius - 1), 2)
        pygame.draw.circle(surf, eye_color, (cx + 2, cy - body_radius - 1), 2)
    
    def _draw_searching_fly(self, surf: pygame.Surface, cx: int, cy: int,
                           color: Tuple[int, int, int], wing_angle: float,
                           health: float) -> None:
        """Draw a fly actively searching - hovering pattern."""
        body_radius = int(CELL_PIXEL_SIZE * 0.35 * health)
        
        # Hovering wings (slower, more controlled)
        wing_color = (200, 220, 240, 120)
        wing_width = body_radius * 3
        wing_height = body_radius * 2
        
        # Slight hover position shift
        hover_offset = np.sin(wing_angle * 2) * 2
        hover_cy = cy + hover_offset
        
        self._draw_wing(surf, cx - body_radius, hover_cy, wing_width, wing_height,
                       wing_angle * 20, wing_color)
        self._draw_wing(surf, cx + body_radius, hover_cy, wing_width, wing_height,
                       -wing_angle * 20, wing_color)
        
        # Normal body
        self._draw_body_segments(surf, cx, hover_cy, body_radius, color, health)
        
        head_color = tuple(min(255, c + 20) for c in color)
        pygame.draw.circle(surf, head_color, (cx, hover_cy - body_radius), body_radius // 2)
        
        # Eyes looking around
        eye_offset = int(2 * np.sin(wing_angle * 3))
        eye_color = (255, 255, 255)
        pygame.draw.circle(surf, eye_color, (cx - 2 + eye_offset, hover_cy - body_radius - 1), 1)
        pygame.draw.circle(surf, eye_color, (cx + 2 + eye_offset, hover_cy - body_radius - 1), 1)
    
    def _draw_happy_fly(self, surf: pygame.Surface, cx: int, cy: int,
                       color: Tuple[int, int, int], wing_angle: float,
                       health: float) -> None:
        """Draw a happy, content fly."""
        body_radius = int(CELL_PIXEL_SIZE * 0.35 * health)
        
        # Lazy, slow wings
        wing_color = (200, 220, 240, 80)
        wing_width = body_radius * 2.5
        wing_height = body_radius * 1.5
        
        self._draw_wing(surf, cx - body_radius, cy, wing_width, wing_height,
                       wing_angle * 15, wing_color)
        self._draw_wing(surf, cx + body_radius, cy, wing_width, wing_height,
                       -wing_angle * 15, wing_color)
        
        # Brighter body color for happiness
        happy_color = tuple(min(255, int(c * 1.2)) for c in color)
        self._draw_body_segments(surf, cx, cy, body_radius, happy_color, health)
        
        head_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.circle(surf, head_color, (cx, cy - body_radius), body_radius // 2)
        
        # Happy eyes - closed/squinting
        eye_color = (255, 255, 200)
        pygame.draw.line(surf, eye_color, (cx - 3, cy - body_radius), 
                        (cx - 1, cy - body_radius), 1)
        pygame.draw.line(surf, eye_color, (cx + 1, cy - body_radius),
                        (cx + 3, cy - body_radius), 1)
    
    def _draw_wing(self, surf: pygame.Surface, cx: int, cy: int,
                   width: int, height: int, angle: float,
                   color: Tuple[int, int, int, int]) -> None:
        """Draw a translucent wing."""
        wing_surf = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
        
        # Wing is an ellipse (leaf shape)
        points = []
        for i in range(20):
            t = i / 20.0
            x = width * np.sin(t * np.pi) * np.cos(angle * np.pi / 180)
            y = height * t
            points.append((width + x, y))
        
        if len(points) > 2:
            pygame.draw.polygon(wing_surf, color, points)
            pygame.draw.polygon(wing_surf, (*color[:3], 200), points, 1)
        
        rotated = pygame.transform.rotate(wing_surf, angle)
        rect = rotated.get_rect(center=(cx, cy))
        surf.blit(rotated, rect, special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_body_segments(self, surf: pygame.Surface, cx: int, cy: int,
                           radius: int, color: Tuple[int, int, int],
                           health: float) -> None:
        """Draw segmented insect body."""
        # Thorax (middle) - largest
        pygame.draw.circle(surf, color, (cx, cy), radius)
        
        # Abdomen (rear)
        abd_color = tuple(int(c * 0.8) for c in color)
        pygame.draw.circle(surf, abd_color, (cx, cy + radius), radius // 2)
        
        # Segment lines
        line_color = tuple(int(c * 0.6) for c in color)
        pygame.draw.line(surf, line_color, (cx - radius, cy), (cx + radius, cy), 1)
        pygame.draw.line(surf, line_color, (cx, cy - radius), (cx, cy + radius), 1)
        
        # Health indicator - color tint
        if health < 0.5:
            damage_color = (255, 100, 100, 100)
            damage_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(damage_surf, damage_color, (radius, radius), radius)
            surf.blit(damage_surf, (cx - radius, cy - radius), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_antennae(self, surf: pygame.Surface, cx: int, cy: int,
                      color: Tuple[int, int, int]) -> None:
        """Draw antennae."""
        ant_color = tuple(int(c * 0.7) for c in color)
        ant_len = 10
        # Left antenna
        pygame.draw.line(surf, ant_color, (cx - 1, cy),
                        (cx - int(ant_len * 0.5), cy - ant_len), 2)
        # Right antenna
        pygame.draw.line(surf, ant_color, (cx + 1, cy),
                        (cx + int(ant_len * 0.5), cy - ant_len), 2)


class TerrainRenderer:
    """Enhanced terrain rendering with grass and height visualization."""
    
    @staticmethod
    def draw_enhanced_grass(surf: pygame.Surface, size: int,
                           height: float = 0.0, moisture: float = 0.5) -> pygame.Surface:
        """Draw grass with natural variation based on height and moisture."""
        grass_surf = pygame.Surface((size, size))
        
        # Base green - varies with moisture and height
        base_g = int(150 + moisture * 50 + (1 - height) * 30)
        base_r = int(50 + (1 - height) * 20)
        base_b = int(50 + moisture * 20)
        
        base_color = (base_r, base_g, base_b)
        grass_surf.fill(base_color)
        
        # Grass blade details
        for _ in range(8):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            blade_color = (
                base_r + np.random.randint(-15, 25),
                base_g + np.random.randint(-20, 30),
                base_b + np.random.randint(-10, 15)
            )
            blade_color = tuple(max(0, min(255, c)) for c in blade_color)
            pygame.draw.line(grass_surf, blade_color, (x, y), 
                           (x + np.random.randint(-1, 2), y - np.random.randint(1, 3)), 1)
        
        return grass_surf
    
    @staticmethod
    def draw_height_shaded_cell(surf: pygame.Surface, size: int,
                               base_color: Tuple[int, int, int],
                               height: float) -> pygame.Surface:
        """Draw a cell with shading based on height."""
        shaded_surf = pygame.Surface((size, size))
        
        # Shade darkens with height (higher = darker = shadow effect)
        shade_factor = 0.7 + height * 0.3  # 0.7 to 1.0
        shaded_color = tuple(int(c * shade_factor) for c in base_color)
        
        shaded_surf.fill(shaded_color)
        
        # Add highlight on low areas (water reflection effect)
        if height < -0.2:
            highlight = (255, 255, 255, 30)
            h_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.line(h_surf, highlight, (0, size // 3), (size, size // 3), 2)
            shaded_surf.blit(h_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        return shaded_surf
