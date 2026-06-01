"""
Renderer module for the Digital Organism Simulator.
Beautiful visualization with terrain shading, animations, and particle effects.

Рендеринг — красивая визуализация с рельефом, анимациями и частицами.
"""

import pygame
import numpy as np
import math
from typing import List, Optional, Tuple
from organism_visuals import OrganismRenderer, TerrainRenderer
from advanced_3d import Advanced3DRenderer, EnhancedParticleSystem
from professional_ui import ProfessionalGameUI, NotificationSystem, UITheme
from config import (
    WORLD_WIDTH, WORLD_HEIGHT, CELL_PIXEL_SIZE,
    DISPLAY_WIDTH, DISPLAY_HEIGHT, UI_PANEL_WIDTH, UI_SIDEBAR_X,
    CELL_EMPTY, CELL_GRASS, CELL_TREE, CELL_BERRY_BUSH,
    CELL_WATER, CELL_STONE, CELL_SHELTER, CELL_RESOURCE,
    COLOR_GRASS, COLOR_TREE, COLOR_BERRY, COLOR_WATER,
    COLOR_STONE, COLOR_EMPTY, COLOR_SHELTER, COLOR_RESOURCE,
    COLOR_DAY_SKY, COLOR_NIGHT_SKY, COLOR_UI_BG, COLOR_UI_TEXT,
    COLOR_UI_HIGHLIGHT, COLOR_UI_ACCENT,
    COLOR_ORGANISM_HEALTHY, COLOR_ORGANISM_HUNGRY,
    COLOR_ORGANISM_THIRSTY, COLOR_ORGANISM_DYING, COLOR_ORGANISM_OLD,
    SEASON_SPRING, SEASON_SUMMER, SEASON_AUTUMN, SEASON_WINTER,
    GRASS_FOOD_VALUE,
)


class Particle:
    """Simple particle for visual effects."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int],
                 life: int = 20, speed: float = 1.0):
        self.x = x
        self.y = y
        self.vx = np.random.uniform(-1, 1) * speed
        self.vy = np.random.uniform(-2, 0) * speed
        self.color = color
        self.life = life
        self.max_life = life
        self.size = np.random.randint(2, 4)

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # gravity
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int]) -> None:
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color[:3], alpha)
        sx = int(self.x) - camera_offset[0]
        sy = int(self.y) - camera_offset[1]
        if 0 <= sx <= DISPLAY_WIDTH and 0 <= sy <= DISPLAY_HEIGHT:
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            s.fill(color)
            surface.blit(s, (sx, sy))


class Camera:
    """Smooth-scrolling camera."""

    def __init__(self):
        self.x: float = 0.0
        self.y: float = 0.0
        self.target_x: float = 0.0
        self.target_y: float = 0.0
        self.zoom: float = 1.0
        self.view_width: int = UI_SIDEBAR_X
        self.view_height: int = DISPLAY_HEIGHT

    def clamp(self) -> None:
        world_pixel_w = WORLD_WIDTH * CELL_PIXEL_SIZE
        world_pixel_h = WORLD_HEIGHT * CELL_PIXEL_SIZE
        self.x = max(0, min(self.x, world_pixel_w - self.view_width))
        self.y = max(0, min(self.y, world_pixel_h - self.view_height))

    def move(self, dx: int, dy: int) -> None:
        self.target_x += dx
        self.target_y += dy
        self.target_x = max(0, min(self.target_x,
                                   WORLD_WIDTH * CELL_PIXEL_SIZE - self.view_width))
        self.target_y = max(0, min(self.target_y,
                                   WORLD_HEIGHT * CELL_PIXEL_SIZE - self.view_height))

    def update(self) -> None:
        """Smooth camera follow."""
        self.x += (self.target_x - self.x) * 0.1
        self.y += (self.target_y - self.y) * 0.1
        self.clamp()

    def world_to_screen(self, wx: int, wy: int) -> Tuple[int, int]:
        sx = int(wx * CELL_PIXEL_SIZE - self.x)
        sy = int(wy * CELL_PIXEL_SIZE - self.y)
        return (sx, sy)
    
    def world_to_screen_pixel(self, px: float, py: float) -> Tuple[int, int]:
        """Convert pixel-based world coordinates to screen coordinates."""
        sx = int(px - self.x)
        sy = int(py - self.y)
        return (sx, sy)

    def screen_to_world(self, sx: int, sy: int) -> Tuple[int, int]:
        wx = int((sx + self.x) / CELL_PIXEL_SIZE)
        wy = int((sy + self.y) / CELL_PIXEL_SIZE)
        return (wx, wy)


class Renderer:
    """
    Main rendering engine with beautiful visuals, animations, and effects.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption("🌿 Цифровой организм — Симулятор эволюции 🌿")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_small = pygame.font.Font(None, 13)
        self.font_medium = pygame.font.Font(None, 17)
        self.font_large = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 28)

        self.camera = Camera()
        self.world_surface = pygame.Surface((UI_SIDEBAR_X, DISPLAY_HEIGHT))

        # Light overlay for smooth day/night
        self.light_overlay = pygame.Surface((UI_SIDEBAR_X, DISPLAY_HEIGHT), pygame.SRCALPHA)

        # Season color overlay
        self.season_overlay = pygame.Surface((UI_SIDEBAR_X, DISPLAY_HEIGHT))

        # Visual renderers
        self.organism_renderer = OrganismRenderer()
        self.terrain_renderer = TerrainRenderer()
        self.advanced_3d = Advanced3DRenderer()
        self.particle_system = EnhancedParticleSystem()

        # Professional UI
        self.game_ui = ProfessionalGameUI(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.notifications = NotificationSystem()

        # Particle systems
        self.particles: List[Particle] = []

        # Organism animation data
        self.organism_bob: float = 0.0  # bobbing animation offset

        # Pre-render terrain tiles
        self.terrain_cache = {}
        self._build_terrain_cache()

        # Performance
        self.fps: float = 0.0
        self.frame_count: int = 0

    def _build_terrain_cache(self) -> None:
        """Pre-render beautiful terrain tiles."""
        size = CELL_PIXEL_SIZE
        self.terrain_cache = {
            CELL_EMPTY: self._make_empty_tile(size),
            CELL_GRASS: self._make_grass_tile(size),
            CELL_TREE: self._make_tree_tile(size),
            CELL_BERRY_BUSH: self._make_berry_tile(size),
            CELL_WATER: self._make_water_tile(size),
            CELL_STONE: self._make_stone_tile(size),
            CELL_SHELTER: self._make_shelter_tile(size),
            CELL_RESOURCE: self._make_resource_tile(size),
        }

    def _make_empty_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size))
        surf.fill((80, 75, 60))
        # Add small dirt texture
        for _ in range(2):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            surf.set_at((x, y), (100, 90, 70))
        return surf

    def _make_grass_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size))
        # Base green with slight variation
        base = (50 + np.random.randint(-10, 10),
                150 + np.random.randint(-15, 15),
                50 + np.random.randint(-10, 10))
        surf.fill(base)
        # Add grass blade details
        for _ in range(4):
            x = np.random.randint(1, size - 1)
            y = np.random.randint(1, size - 1)
            shade = (
                min(255, base[0] + np.random.randint(-20, 30)),
                min(255, base[1] + np.random.randint(-20, 20)),
                min(255, base[2] + np.random.randint(-20, 30)),
            )
            surf.set_at((x, y), shade)
            if x > 0:
                surf.set_at((x - 1, y), shade)
        return surf

    def _make_tree_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Trunk
        trunk_color = (80 + np.random.randint(-20, 20),
                       50 + np.random.randint(-10, 10),
                       30 + np.random.randint(-10, 10))
        trunk_w = max(1, size // 4)
        trunk_x = (size - trunk_w) // 2
        for i in range(size * 3 // 4, size):
            for j in range(trunk_x, trunk_x + trunk_w):
                if 0 <= j < size:
                    surf.set_at((j, i), trunk_color)
        # Foliage - multiple overlapping circles for natural look
        foliage_colors = [
            (20, np.random.randint(90, 130), 20),
            (30, np.random.randint(100, 140), 30),
            (40, np.random.randint(80, 120), 25),
        ]
        for i, (fr, fg, fb) in enumerate(foliage_colors):
            cx = size // 2 + np.random.randint(-2, 3)
            cy = size // 3 + np.random.randint(-2, 3)
            r = size // 3 + np.random.randint(-1, 2)
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < size and 0 <= py < size:
                            current = surf.get_at((px, py))
                            if current[3] < 200:
                                shade = (
                                    fr + np.random.randint(-10, 10),
                                    fg + np.random.randint(-15, 15),
                                    fb + np.random.randint(-10, 10),
                                    220
                                )
                                surf.set_at((px, py), shade)
        return surf

    def _make_berry_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Base bush
        bush_color = (40, 100 + np.random.randint(-10, 10), 40)
        for dx in range(size):
            for dy in range(size // 2, size):
                x_dist = abs(dx - size // 2) / (size // 2)
                y_dist = abs(dy - size // 2) / (size // 2)
                if x_dist * x_dist + y_dist * y_dist <= 1.0:
                    alpha = int(200 * (1 - x_dist * x_dist - y_dist * y_dist))
                    if alpha > 50:
                        surf.set_at((dx, dy), (*bush_color, alpha))
        # Berries
        berry_colors = [(200, 30, 80), (220, 50, 100), (180, 20, 60)]
        for _ in range(3):
            bx = np.random.randint(2, size - 2)
            by = np.random.randint(size // 2, size - 2)
            bc = berry_colors[np.random.randint(0, len(berry_colors))]
            for r in range(2):
                for dx in range(-r, r + 1):
                    for dy in range(-r, r + 1):
                        if dx * dx + dy * dy <= r * r:
                            px, py = bx + dx, by + dy
                            if 0 <= px < size and 0 <= py < size:
                                surf.set_at((px, py), (*bc, 255))
        return surf

    def _make_water_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        base_blue = (30, 70 + np.random.randint(-10, 10),
                     140 + np.random.randint(-10, 10))
        surf.fill((*base_blue, 200))
        # Add wave highlights
        for x in range(size):
            wave_y = int(size // 2 + np.sin(x * 0.8) * 1.5)
            if 0 <= wave_y < size:
                current = surf.get_at((x, wave_y))
                lighter = (min(255, current[0] + 40),
                           min(255, current[1] + 40),
                           min(255, current[2] + 30), current[3])
                surf.set_at((x, wave_y), lighter)
        return surf

    def _make_stone_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size))
        base = (100 + np.random.randint(-10, 10),
                100 + np.random.randint(-10, 10),
                100 + np.random.randint(-10, 10))
        surf.fill(base)
        # Add rock texture
        for _ in range(5):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            shade = tuple(min(255, max(0, c + np.random.randint(-30, 30))) for c in base)
            surf.set_at((x, y), shade)
        return surf

    def _make_shelter_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Walls
        wall_color = (130, 100, 70)
        for dx in range(1, size - 1):
            for dy in range(size // 2, size - 1):
                surf.set_at((dx, dy), (*wall_color, 200))
        # Roof
        roof_color = (150, 80, 40)
        for dx in range(size):
            for dy in range(size // 4, size // 2):
                x_off = abs(dx - size // 2) / (size // 2)
                y_off = abs(dy - size // 4) / (size // 4)
                if x_off + y_off <= 1.0:
                    alpha = int(255 * (1 - (x_off + y_off) * 0.5))
                    surf.set_at((dx, dy), (*roof_color, alpha))
        # Door
        door_color = (80, 60, 40)
        for dx in range(size // 3, size * 2 // 3):
            for dy in range(size * 3 // 4, size):
                surf.set_at((dx, dy), (*door_color, 220))
        return surf

    def _make_resource_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # Base crystal-like deposit
        base = (180, 180, 50)
        for dx in range(size):
            for dy in range(size):
                dist = abs(dx - size // 2) + abs(dy - size // 2)
                if dist < size // 2:
                    alpha = int(200 * (1 - dist / (size // 2)))
                    sparkle = np.sin(dx * 2 + dy * 3) * 20
                    color = (
                        min(255, base[0] + int(sparkle)),
                        min(255, base[1] + int(sparkle)),
                        min(255, base[2] + int(sparkle * 0.5)),
                        alpha
                    )
                    surf.set_at((dx, dy), color)
        return surf

    def add_particles(self, x: float, y: float, color: Tuple[int, int, int],
                      count: int = 5, speed: float = 2.0) -> None:
        for _ in range(count):
            self.particles.append(Particle(x, y, color, life=np.random.randint(10, 30),
                                           speed=speed))

    def render(self, world, organisms: list, ui_manager) -> None:
        """Main render call."""
        self.frame_count += 1
        self.organism_bob = math.sin(self.frame_count * 0.05) * 1.5

        # Update camera
        self.camera.update()

        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        self.particle_system.update()
        self.notifications.update()

        # Draw
        sky_color = self._get_sky_color(world)
        self.screen.fill(sky_color)
        self._render_world(world, organisms)
        
        # Draw particle effects
        self.particle_system.draw(self.screen, 
                                 (int(self.camera.x), int(self.camera.y)))

        # Draw UI
        self.game_ui.update()
        self.game_ui.draw(self.screen)
        
        # Draw notifications
        self.notifications.draw(self.screen, self.font_medium, 100)
        
        # Draw old UI (backward compatibility)
        ui_manager.draw(self.screen, world, organisms)

        # Debug FPS
        fps_text = self.font_small.render(f"FPS: {self.clock.get_fps():.0f}", True, (200, 200, 200))
        self.screen.blit(fps_text, (5, 5))

        pygame.display.flip()
        self.fps = self.clock.get_fps()
        self.clock.tick(60)
    
    def handle_ui_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events."""
        return self.game_ui.handle_event(event)

    def _get_sky_color(self, world) -> Tuple[int, int, int]:
        """Get interpolated sky color based on time."""
        if world is None:
            return COLOR_DAY_SKY
        if world.is_daytime:
            # Dawn/dusk coloring
            t = world.time_of_day
            if t < 0.2:
                # Sunrise: orange-red dawn
                factor = t / 0.2
                r = int(135 + (255 - 135) * (1 - factor))
                g = int(206 - 80 * (1 - factor))
                b = int(235 - 120 * (1 - factor))
            elif t > 0.8:
                # Sunset
                factor = (t - 0.8) / 0.2
                r = int(135 + (255 - 135) * factor)
                g = int(206 - 80 * factor)
                b = int(235 - 120 * factor)
            else:
                r, g, b = COLOR_DAY_SKY
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        else:
            # Night sky with stars
            t = world.time_of_day
            darkness = 0.3 + t * 0.4
            r = int(10 * darkness)
            g = int(10 * darkness)
            b = int(30 * darkness)
            return (r, g, b)

    def _get_season_color_mult(self, world) -> Tuple[float, float, float]:
        """Get RGB multiplier for seasonal coloring."""
        if world is None:
            return (1.0, 1.0, 1.0)
        if world.current_season == SEASON_SPRING:
            return (0.9, 1.1, 0.9)  # fresh green
        elif world.current_season == SEASON_SUMMER:
            return (1.0, 1.0, 1.0)  # normal
        elif world.current_season == SEASON_AUTUMN:
            return (1.2, 0.8, 0.5)  # orange/brown tint
        else:  # WINTER
            return (0.7, 0.7, 0.8)  # blueish grey

    def _render_world(self, world, organisms: list) -> None:
        """Render the world with all visual layers."""
        self.world_surface.fill((40, 35, 30))

        if world is None:
            self.screen.blit(self.world_surface, (0, 0))
            return

        cam = self.camera
        season_mult = self._get_season_color_mult(world)

        # Calculate visible range
        start_x = max(0, int(cam.x // CELL_PIXEL_SIZE) - 1)
        start_y = max(0, int(cam.y // CELL_PIXEL_SIZE) - 1)
        end_x = min(WORLD_WIDTH, start_x + cam.view_width // CELL_PIXEL_SIZE + 3)
        end_y = min(WORLD_HEIGHT, start_y + cam.view_height // CELL_PIXEL_SIZE + 3)

        # Draw terrain
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                cell = world.grid[y][x]
                screen_x, screen_y = cam.world_to_screen(x, y)

                # Get base tile
                if cell.terrain in self.terrain_cache:
                    tile = self.terrain_cache[cell.terrain]
                    self.world_surface.blit(tile, (screen_x, screen_y))

                # Apply season tint to green areas
                if cell.terrain in (CELL_GRASS, CELL_TREE, CELL_BERRY_BUSH):
                    overlay = pygame.Surface((CELL_PIXEL_SIZE, CELL_PIXEL_SIZE), pygame.SRCALPHA)
                    r, g, b = season_mult
                    overlay.fill((0, 0, 0, 0))
                    for dx in range(CELL_PIXEL_SIZE):
                        for dy in range(CELL_PIXEL_SIZE):
                            orig = tile.get_at((dx, dy))
                            new_color = (
                                min(255, int(orig[0] * r)),
                                min(255, int(orig[1] * g)),
                                min(255, int(orig[2] * b)),
                                orig[3] if len(orig) > 3 else 255
                            )
                            if len(orig) > 3:
                                overlay.set_at((dx, dy), new_color)
                            else:
                                self.world_surface.set_at((screen_x + dx, screen_y + dy), new_color[:3])
                    if cell.terrain == CELL_GRASS and len(tile.get_at((0, 0))) > 3:
                        self.world_surface.blit(overlay, (screen_x, screen_y),
                                                special_flags=pygame.BLEND_ALPHA_SDL2)

                # Draw water shimmer animation
                if cell.terrain == CELL_WATER and cell.shimmer > 0:
                    shimmer_alpha = int(cell.shimmer * 40)
                    shimmer_overlay = pygame.Surface((CELL_PIXEL_SIZE, CELL_PIXEL_SIZE),
                                                      pygame.SRCALPHA)
                    shimmer_overlay.fill((255, 255, 255, shimmer_alpha))
                    self.world_surface.blit(shimmer_overlay, (screen_x, screen_y))

                # Draw foliage density for grass
                if cell.terrain == CELL_GRASS and cell.resources > 0:
                    density = min(1.0, cell.resources / GRASS_FOOD_VALUE + cell.foliage_amount * 0.3)
                    if density > 0.5:
                        extra_green = pygame.Surface((CELL_PIXEL_SIZE, CELL_PIXEL_SIZE),
                                                      pygame.SRCALPHA)
                        extra_green.fill((0, 60, 0, int((density - 0.5) * 80)))
                        self.world_surface.blit(extra_green, (screen_x, screen_y))

        # Draw organisms
        for org in organisms:
            if not org.is_alive:
                continue
            self._draw_organism(org, world)

        # Draw particles
        for p in self.particles:
            p.draw(self.world_surface, (cam.x, cam.y))

        # Night overlay
        if world and not world.is_daytime:
            darkness = 1.0 - world.time_of_day
            night_alpha = int(min(150, darkness * 120))
            overlay = pygame.Surface((UI_SIDEBAR_X, DISPLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 20, night_alpha))
            self.world_surface.blit(overlay, (0, 0))

        # Blit world
        self.screen.blit(self.world_surface, (0, 0))

    def _draw_organism(self, organism, world) -> None:
        """Draw an organism with beautiful animated visuals."""
        cam = self.camera
        
        # Get animated screen position
        anim_x = organism.animation.current_x
        anim_y = organism.animation.current_y
        sx, sy = cam.world_to_screen_pixel(anim_x, anim_y)
        
        # Off-screen check
        if sx < -40 or sx > UI_SIDEBAR_X + 40 or sy < -40 or sy > DISPLAY_HEIGHT + 40:
            return
        
        # Get animation data
        wing_beat = organism.animation.wing_beat
        health_percent = organism.health / max(1, organism.max_health)
        emotion = organism.get_emotion_state()
        
        # Draw the fly using the enhanced renderer
        self.organism_renderer.draw_fly(
            self.world_surface,
            sx + CELL_PIXEL_SIZE // 2,
            sy + CELL_PIXEL_SIZE // 2,
            organism.get_organism_state_color(),
            wing_offset=wing_beat / (2 * np.pi),  # normalize to 0-1
            health_percent=health_percent,
            emotion_state=emotion
        )
        
        # Draw vision radius (subtle glow)
        if organism.sight_radius > 0:
            vis_pixels = min(80, int(organism.sight_radius * CELL_PIXEL_SIZE * 0.8))
            vis_surf = pygame.Surface((vis_pixels * 2, vis_pixels * 2), pygame.SRCALPHA)
            
            color = organism.get_organism_state_color()
            alpha = 10 if world and world.is_daytime else 5
            
            for r in range(vis_pixels, 0, -1):
                a = int(alpha * (1 - r / vis_pixels))
                pygame.draw.circle(vis_surf, (*color[:3], a),
                                 (vis_pixels, vis_pixels), r)
            
            self.world_surface.blit(vis_surf,
                                  (sx + CELL_PIXEL_SIZE // 2 - vis_pixels,
                                   sy + CELL_PIXEL_SIZE // 2 - vis_pixels),
                                  special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Health bar
        if organism.health < organism.max_health:
            bar_w = CELL_PIXEL_SIZE + 2
            bar_h = 2
            bar_x = sx - 1
            bar_y = sy - 4
            hp_pct = max(0, organism.health / organism.max_health)
            # Background
            pygame.draw.rect(self.world_surface, (150, 30, 30),
                             (bar_x, bar_y, bar_w, bar_h))
            # Health
            hp_color = (50, 200, 50) if hp_pct > 0.5 else (200, 200, 50) if hp_pct > 0.25 else (200, 30, 30)
            pygame.draw.rect(self.world_surface, hp_color,
                             (bar_x, bar_y, int(bar_w * hp_pct), bar_h))

        # Goal indicator
        if organism.current_goal:
            goal_icons = {"eat": "🍎", "drink": "💧", "explore": "🔍",
                          "collect": "⛏️", "build": "🏠", "reproduce": "❤️"}
            icon = goal_icons.get(organism.current_goal, "?")
            goal_text = self.font_small.render(icon, True, (255, 255, 255))
            self.world_surface.blit(goal_text, (sx, sy - CELL_PIXEL_SIZE - 2))

    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()