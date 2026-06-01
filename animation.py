"""
Animation system for smooth movement and visual effects.
Organisms move smoothly between grid cells with animations.

Система анимации — плавное движение и визуальные эффекты.
"""

import numpy as np
import pygame
from typing import Tuple, Optional
from config import CELL_PIXEL_SIZE


class AnimationState:
    """Tracks animation state for an organism."""
    
    def __init__(self):
        self.current_x: float = 0.0
        self.current_y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.progress: float = 0.0  # 0.0 to 1.0
        self.is_moving: bool = False
        self.move_duration: int = 10  # ticks to move one cell
        self.wing_beat: float = 0.0  # 0.0 to 1.0 for wing animation
        self.emotion_anim: float = 0.0  # for fear/happiness expression
        self.last_action: Optional[str] = None
        self.action_timer: int = 0
        
    def start_move(self, from_x: int, from_y: int, to_x: int, to_y: int) -> None:
        """Begin moving from one grid position to another."""
        self.current_x = from_x * CELL_PIXEL_SIZE
        self.current_y = from_y * CELL_PIXEL_SIZE
        self.target_x = to_x * CELL_PIXEL_SIZE
        self.target_y = to_y * CELL_PIXEL_SIZE
        self.progress = 0.0
        self.is_moving = True
        
    def update(self) -> None:
        """Update animation frame."""
        if self.is_moving:
            self.progress += 1.0 / self.move_duration
            if self.progress >= 1.0:
                self.progress = 1.0
                self.is_moving = False
                self.current_x = self.target_x
                self.current_y = self.target_y
            else:
                # Smooth easing
                t = self.progress
                eased = t * t * (3 - 2 * t)  # smoothstep
                self.current_x = (self.target_x - self.current_x) * eased + self.current_x
                self.current_y = (self.target_y - self.current_y) * eased + self.current_y
        
        # Wing beat animation
        self.wing_beat = (self.wing_beat + 0.15) % (2 * np.pi)
        
        # Emotion animation
        if self.action_timer > 0:
            self.action_timer -= 1
            self.emotion_anim = abs(np.sin(self.action_timer * 0.2))
        else:
            self.emotion_anim *= 0.95
            
    def get_screen_position(self) -> Tuple[float, float]:
        """Get current screen position for rendering."""
        return (self.current_x, self.current_y)
    
    def get_wing_position(self) -> float:
        """Get wing angle for animation."""
        return np.sin(self.wing_beat) * 20  # ±20 degrees
    
    def trigger_action(self, action: str, duration: int = 20) -> None:
        """Trigger an action animation (eating, building, etc)."""
        self.last_action = action
        self.action_timer = duration


class ParticleEmitter:
    """Emits particles for visual effects."""
    
    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 count: int = 5, speed: float = 1.5):
        self.particles = []
        for _ in range(count):
            angle = np.random.uniform(0, 2 * np.pi)
            s = speed * np.random.uniform(0.5, 1.5)
            vx = np.cos(angle) * s
            vy = np.sin(angle) * s
            life = np.random.randint(10, 30)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'life': life,
                'max_life': life,
                'color': color,
                'size': np.random.randint(2, 5)
            })
    
    def update(self) -> bool:
        """Update particles. Returns True if any alive."""
        alive = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # gravity
            p['life'] -= 1
            if p['life'] > 0:
                alive.append(p)
        self.particles = alive
        return len(self.particles) > 0
    
    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Draw particles."""
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            sx = int(p['x']) - camera_offset[0]
            sy = int(p['y']) - camera_offset[1]
            
            if 0 <= sx < 1280 and 0 <= sy < 720:
                s = pygame.Surface((p['size'], p['size']), pygame.SRCALPHA)
                color = (*p['color'][:3], alpha)
                s.fill(color)
                surface.blit(s, (sx, sy))
