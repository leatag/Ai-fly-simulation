"""
Professional 3D rendering system with lighting, shadows, and depth effects.
Создает красивый 3D визуал как в настоящей игре.
"""

import pygame
import numpy as np
from typing import Tuple
from config import CELL_PIXEL_SIZE


class Light3D:
    """Represents a 3D light source."""
    def __init__(self, x: float, y: float, z: float = 50, 
                 intensity: float = 1.0, color: Tuple[int, int, int] = (255, 255, 200)):
        self.x = x
        self.y = y
        self.z = z
        self.intensity = intensity
        self.color = color


class Advanced3DRenderer:
    """Professional 3D rendering with lighting, shadows, and depth."""
    
    def __init__(self):
        self.lights = []
        self.ambient_light = 0.3
        self.shadow_offset = (5, 5)
        
    def add_light(self, light: Light3D):
        """Add a light source to the scene."""
        self.lights.append(light)
    
    def calculate_lighting(self, x: float, y: float, z: float = 0,
                          surface_normal: Tuple[float, float, float] = (0, 0, 1)) -> float:
        """Calculate lighting intensity at a position."""
        intensity = self.ambient_light
        
        for light in self.lights:
            # Distance from light
            dx = light.x - x
            dy = light.y - y
            dz = light.z - z
            dist = (dx*dx + dy*dy + dz*dz) ** 0.5
            
            if dist > 0:
                # Attenuation
                attenuation = light.intensity / (1 + dist * 0.01)
                
                # Normal calculation (simplified)
                light_dir = np.array([dx, dy, dz])
                light_dir = light_dir / (np.linalg.norm(light_dir) + 0.001)
                normal = np.array(surface_normal)
                
                # Lambert's cosine law
                brightness = max(0, np.dot(normal, light_dir))
                intensity += brightness * attenuation
        
        return min(1.0, intensity)
    
    def draw_3d_terrain(self, surface: pygame.Surface, x: int, y: int, size: int,
                       base_color: Tuple[int, int, int], height: float = 0.0,
                       is_water: bool = False) -> None:
        """Draw a 3D terrain cell with shading and depth."""
        
        # Calculate lighting
        light_intensity = self.calculate_lighting(x, y, height)
        
        # Apply height-based shading
        if height > 0.3:  # High terrain = darker (shadow)
            shade = 0.6 + height * 0.2
        elif height < -0.2:  # Low terrain = lighter (reflection)
            shade = 0.85
        else:
            shade = 0.75
        
        shaded_color = tuple(int(c * light_intensity * shade) for c in base_color)
        
        # Main surface
        pygame.draw.rect(surface, shaded_color, (x, y, size, size))
        
        # 3D edge effect (top-left highlight)
        if height < 0.2:
            highlight = tuple(min(255, int(c * 1.2)) for c in shaded_color)
            pygame.draw.line(surface, highlight, (x, y), (x + size, y), 2)
            pygame.draw.line(surface, highlight, (x, y), (x, y + size), 2)
        
        # 3D edge effect (bottom-right shadow)
        if height > -0.2:
            shadow = tuple(max(0, int(c * 0.7)) for c in shaded_color)
            pygame.draw.line(surface, shadow, (x + size - 1, y), 
                           (x + size - 1, y + size - 1), 2)
            pygame.draw.line(surface, shadow, (x, y + size - 1),
                           (x + size - 1, y + size - 1), 2)
        
        # Water shimmer effect
        if is_water:
            shimmer = (255, 255, 255, 50)
            shimmer_y = int(y + size * 0.3)
            s = pygame.Surface((size, 2), pygame.SRCALPHA)
            s.fill(shimmer)
            surface.blit(s, (x, shimmer_y), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw_shadow(self, surface: pygame.Surface, x: int, y: int,
                   width: int, height: int, intensity: float = 0.3) -> None:
        """Draw a shadow under an object."""
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, int(100 * intensity))
        shadow_surf.fill(shadow_color)
        
        shadow_x = x + self.shadow_offset[0]
        shadow_y = y + self.shadow_offset[1]
        
        surface.blit(shadow_surf, (shadow_x, shadow_y), 
                    special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw_3d_object(self, surface: pygame.Surface, x: int, y: int,
                      width: int, height: int, color: Tuple[int, int, int],
                      depth: float = 0.0, cast_shadow: bool = True) -> None:
        """Draw a 3D object with depth effect."""
        
        if cast_shadow:
            self.draw_shadow(surface, x, y, width, height, depth * 0.5)
        
        # Main object
        pygame.draw.rect(surface, color, (x, y, width, height))
        
        # Top highlight (3D effect)
        light_color = tuple(min(255, int(c * 1.3)) for c in color)
        pygame.draw.line(surface, light_color, (x, y), (x + width, y), 2)
        pygame.draw.line(surface, light_color, (x, y), (x, y + int(height * 0.5)), 2)
        
        # Bottom/right shadow
        dark_color = tuple(max(0, int(c * 0.6)) for c in color)
        pygame.draw.line(surface, dark_color, (x + width - 1, y),
                        (x + width - 1, y + height - 1), 2)
        pygame.draw.line(surface, dark_color, (x, y + height - 1),
                        (x + width - 1, y + height - 1), 2)
        
        # Depth indicator - offset slightly
        if depth > 0:
            depth_color = tuple(max(0, int(c * 0.8)) for c in color)
            offset = int(depth * 3)
            pygame.draw.rect(surface, depth_color, 
                           (x + offset, y + offset, width - offset, height - offset), 1)


class EnhancedParticleSystem:
    """Advanced particle system with physics and effects."""
    
    def __init__(self):
        self.particles = []
    
    def emit(self, x: float, y: float, count: int = 10,
            velocity_range: Tuple[float, float] = (-2, 2),
            life_range: Tuple[int, int] = (20, 50),
            color: Tuple[int, int, int] = (255, 255, 200),
            particle_type: str = "spark") -> None:
        """Emit particles."""
        
        for _ in range(count):
            vx = np.random.uniform(*velocity_range)
            vy = np.random.uniform(-3, 1)
            life = np.random.randint(*life_range)
            size = np.random.randint(2, 6)
            
            particle = {
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'life': life, 'max_life': life,
                'color': color,
                'size': size,
                'type': particle_type,
                'rotation': np.random.uniform(0, 360)
            }
            self.particles.append(particle)
    
    def update(self) -> None:
        """Update particles."""
        alive = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # gravity
            p['life'] -= 1
            p['rotation'] += np.random.uniform(-10, 10)
            
            if p['life'] > 0:
                alive.append(p)
        
        self.particles = alive
    
    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        """Draw particles."""
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            sx = int(p['x']) - camera_offset[0]
            sy = int(p['y']) - camera_offset[1]
            
            if 0 <= sx < 1280 and 0 <= sy < 720:
                # Create particle surface
                psize = p['size']
                ps = pygame.Surface((psize * 2, psize * 2), pygame.SRCALPHA)
                
                color = (*p['color'][:3], alpha)
                
                if p['type'] == 'spark':
                    pygame.draw.circle(ps, color, (psize, psize), psize)
                elif p['type'] == 'star':
                    # Draw star shape
                    points = []
                    for i in range(5):
                        angle = i * 2 * np.pi / 5
                        r = psize if i % 2 == 0 else psize // 2
                        px = psize + r * np.cos(angle)
                        py = psize + r * np.sin(angle)
                        points.append((px, py))
                    pygame.draw.polygon(ps, color, points)
                elif p['type'] == 'dust':
                    pygame.draw.circle(ps, color, (psize, psize), psize // 2)
                
                surface.blit(ps, (sx - psize, sy - psize), 
                           special_flags=pygame.BLEND_ALPHA_SDL2)
