"""
Professional game UI system with menus, panels, and animations.
Профессиональный интерфейс как в настоящей игре.
"""

import pygame
import numpy as np
from typing import Tuple, Optional, Callable, List
from enum import Enum


class UITheme:
    """Beautiful color theme for the game."""
    
    # Color palette
    PRIMARY = (41, 128, 185)      # Blue
    SECONDARY = (52, 73, 94)      # Dark blue
    ACCENT = (46, 204, 113)       # Green
    DANGER = (231, 76, 60)        # Red
    WARNING = (241, 196, 15)      # Yellow
    
    # Backgrounds
    BG_DARK = (22, 34, 63)
    BG_LIGHT = (236, 240, 241)
    BG_PANEL = (52, 73, 94)
    
    # Text
    TEXT_PRIMARY = (236, 240, 241)
    TEXT_SECONDARY = (149, 165, 166)
    TEXT_ACCENT = (52, 152, 219)


class ButtonState(Enum):
    """Button state enum."""
    NORMAL = 0
    HOVERED = 1
    PRESSED = 2
    DISABLED = 3


class AnimatedButton:
    """Professional animated button."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, callback: Optional[Callable] = None,
                 color: Tuple[int, int, int] = UITheme.PRIMARY):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.state = ButtonState.NORMAL
        self.hover_progress = 0.0
        self.click_progress = 0.0
        self.enabled = True
    
    def update(self) -> None:
        """Update button animation."""
        if self.state == ButtonState.HOVERED:
            self.hover_progress = min(1.0, self.hover_progress + 0.1)
        else:
            self.hover_progress = max(0.0, self.hover_progress - 0.1)
        
        if self.state == ButtonState.PRESSED:
            self.click_progress = min(1.0, self.click_progress + 0.2)
        else:
            self.click_progress = max(0.0, self.click_progress - 0.15)
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button with animations."""
        if not self.enabled:
            color = UITheme.TEXT_SECONDARY
        else:
            # Interpolate color based on hover
            hover_mult = 1.0 + self.hover_progress * 0.3
            color = tuple(min(255, int(c * hover_mult)) for c in self.color)
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        # Draw border
        border_width = 2 + int(self.hover_progress * 2)
        pygame.draw.rect(surface, UITheme.TEXT_PRIMARY, self.rect, 
                        border_width, border_radius=8)
        
        # Draw click effect (scale down)
        if self.click_progress > 0:
            scale = 1.0 - self.click_progress * 0.05
            inner_rect = pygame.Rect(
                self.rect.x + self.rect.width * (1 - scale) / 2,
                self.rect.y + self.rect.height * (1 - scale) / 2,
                self.rect.width * scale,
                self.rect.height * scale
            )
            pygame.draw.rect(surface, color, inner_rect, border_radius=6)
        
        # Draw text
        text_surf = font.render(self.text, True, UITheme.TEXT_PRIMARY)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events."""
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.state = ButtonState.HOVERED
            else:
                self.state = ButtonState.NORMAL
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = ButtonState.PRESSED
                if self.callback:
                    self.callback()
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            self.state = ButtonState.NORMAL
        
        return False


class StatPanel:
    """Beautiful stats panel."""
    
    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.stats = {}
        self.fade_in = 0.0
    
    def add_stat(self, name: str, value: str, color: Tuple[int, int, int] = UITheme.TEXT_PRIMARY):
        """Add a stat to display."""
        self.stats[name] = (value, color)
    
    def update(self) -> None:
        """Update panel animation."""
        self.fade_in = min(1.0, self.fade_in + 0.05)
    
    def draw(self, surface: pygame.Surface, font_small: pygame.font.Font, 
             font_medium: pygame.font.Font) -> None:
        """Draw the stats panel."""
        alpha = int(200 * self.fade_in)
        
        # Background with transparency
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill((*UITheme.BG_PANEL, alpha))
        pygame.draw.rect(panel_surf, (*UITheme.PRIMARY, int(255 * self.fade_in)), 
                        panel_surf.get_rect(), 2, border_radius=8)
        
        surface.blit(panel_surf, self.rect)
        
        # Title
        title_surf = font_medium.render(self.title, True, UITheme.ACCENT)
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        
        # Stats
        y_offset = self.rect.y + 40
        for name, (value, color) in self.stats.items():
            name_surf = font_small.render(name, True, UITheme.TEXT_SECONDARY)
            value_surf = font_small.render(str(value), True, color)
            
            surface.blit(name_surf, (self.rect.x + 15, y_offset))
            surface.blit(value_surf, (self.rect.x + 150, y_offset))
            
            y_offset += 25


class ProgressBar:
    """Animated progress bar."""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 label: str, color: Tuple[int, int, int] = UITheme.ACCENT):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.color = color
        self.value = 0.0
        self.target_value = 0.0
    
    def set_value(self, value: float) -> None:
        """Set target value (0.0 to 1.0)."""
        self.target_value = max(0.0, min(1.0, value))
    
    def update(self) -> None:
        """Smooth interpolation."""
        self.value += (self.target_value - self.value) * 0.1
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the progress bar."""
        # Background
        pygame.draw.rect(surface, UITheme.BG_PANEL, self.rect, border_radius=4)
        
        # Progress
        progress_rect = pygame.Rect(self.rect.x, self.rect.y,
                                   self.rect.width * self.value, self.rect.height)
        pygame.draw.rect(surface, self.color, progress_rect, border_radius=4)
        
        # Border
        pygame.draw.rect(surface, UITheme.PRIMARY, self.rect, 1, border_radius=4)
        
        # Label
        label_surf = font.render(self.label, True, UITheme.TEXT_PRIMARY)
        text_x = self.rect.x + 5
        text_y = self.rect.y + (self.rect.height - label_surf.get_height()) // 2
        surface.blit(label_surf, (text_x, text_y))
        
        # Percentage text
        pct_text = f"{int(self.value * 100)}%"
        pct_surf = font.render(pct_text, True, UITheme.TEXT_PRIMARY)
        text_x = self.rect.x + self.rect.width - pct_surf.get_width() - 5
        surface.blit(pct_surf, (text_x, text_y))


class ProfessionalGameUI:
    """Complete professional game UI."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.font_small = pygame.font.Font(None, 16)
        self.font_medium = pygame.font.Font(None, 22)
        self.font_large = pygame.font.Font(None, 32)
        self.font_title = pygame.font.Font(None, 48)
        
        # UI elements
        self.buttons = []
        self.panels = []
        self.progress_bars = []
        
        # State
        self.show_main_menu = False
        self.show_pause_menu = False
        self.show_game_ui = True
        
        # Animation
        self.menu_fade = 0.0
    
    def add_button(self, x: int, y: int, width: int, height: int,
                  text: str, callback: Optional[Callable] = None) -> AnimatedButton:
        """Add a button."""
        btn = AnimatedButton(x, y, width, height, text, callback)
        self.buttons.append(btn)
        return btn
    
    def add_stats_panel(self, x: int, y: int, width: int, height: int,
                       title: str) -> StatPanel:
        """Add a stats panel."""
        panel = StatPanel(x, y, width, height, title)
        self.panels.append(panel)
        return panel
    
    def add_progress_bar(self, x: int, y: int, width: int, height: int,
                        label: str) -> ProgressBar:
        """Add a progress bar."""
        bar = ProgressBar(x, y, width, height, label)
        self.progress_bars.append(bar)
        return bar
    
    def draw_main_menu(self, surface: pygame.Surface) -> None:
        """Draw main menu."""
        # Background with gradient effect
        for y in range(self.screen_height):
            color_factor = y / self.screen_height
            r = int(22 + (41 - 22) * color_factor)
            g = int(34 + (128 - 34) * color_factor)
            b = int(63 + (185 - 63) * color_factor)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.screen_width, y))
        
        # Title
        title_text = "🌿 ЦИФРОВОЙ ОРГАНИЗМ"
        title_surf = self.font_title.render(title_text, True, UITheme.ACCENT)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 100))
        surface.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle = "Симулятор Эволюции v2.0"
        subtitle_surf = self.font_medium.render(subtitle, True, UITheme.TEXT_SECONDARY)
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, 160))
        surface.blit(subtitle_surf, subtitle_rect)
    
    def draw_pause_menu(self, surface: pygame.Surface) -> None:
        """Draw pause overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = "⏸ ПАУЗА"
        pause_surf = self.font_title.render(pause_text, True, UITheme.ACCENT)
        pause_rect = pause_surf.get_rect(center=(self.screen_width // 2, 
                                                 self.screen_height // 2 - 100))
        surface.blit(pause_surf, pause_rect)
    
    def draw_game_ui(self, surface: pygame.Surface) -> None:
        """Draw in-game HUD."""
        # Top info bar
        info_bar_height = 50
        info_bar = pygame.Surface((self.screen_width, info_bar_height), pygame.SRCALPHA)
        info_bar.fill((*UITheme.BG_PANEL, 200))
        surface.blit(info_bar, (0, 0))
        
        # FPS and tick counter
        tick_text = "▶ Симуляция идет..."
        tick_surf = self.font_small.render(tick_text, True, UITheme.ACCENT)
        surface.blit(tick_surf, (10, 10))
    
    def update(self) -> None:
        """Update all UI elements."""
        for btn in self.buttons:
            btn.update()
        for panel in self.panels:
            panel.update()
        for bar in self.progress_bars:
            bar.update()
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw all UI elements."""
        if self.show_game_ui:
            self.draw_game_ui(surface)
        
        if self.show_pause_menu:
            self.draw_pause_menu(surface)
        
        if self.show_main_menu:
            self.draw_main_menu(surface)
        
        # Draw all panels
        for panel in self.panels:
            panel.draw(surface, self.font_small, self.font_medium)
        
        # Draw all progress bars
        for bar in self.progress_bars:
            bar.draw(surface, self.font_small)
        
        # Draw all buttons
        for btn in self.buttons:
            btn.draw(surface, self.font_medium)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle UI events."""
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False
    
    def toggle_pause(self) -> None:
        """Toggle pause menu."""
        self.show_pause_menu = not self.show_pause_menu
    
    def clear_buttons(self) -> None:
        """Clear all buttons."""
        self.buttons.clear()


class NotificationSystem:
    """Display notifications and messages."""
    
    def __init__(self):
        self.notifications = []
    
    def add_notification(self, text: str, duration: int = 60,
                        color: Tuple[int, int, int] = UITheme.ACCENT,
                        icon: str = "ℹ️") -> None:
        """Add a notification."""
        self.notifications.append({
            'text': text,
            'icon': icon,
            'duration': duration,
            'max_duration': duration,
            'color': color,
            'y_offset': 0.0
        })
    
    def update(self) -> None:
        """Update notifications."""
        alive = []
        for notif in self.notifications:
            notif['duration'] -= 1
            notif['y_offset'] = (1.0 - notif['duration'] / notif['max_duration']) * 30
            
            if notif['duration'] > 0:
                alive.append(notif)
        
        self.notifications = alive
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             start_y: int = 100) -> None:
        """Draw notifications."""
        y = start_y
        for notif in self.notifications:
            alpha = int(255 * (notif['duration'] / notif['max_duration']))
            
            text = f"{notif['icon']} {notif['text']}"
            text_surf = font.render(text, True, notif['color'])
            
            # Semi-transparent background
            bg_surf = pygame.Surface((text_surf.get_width() + 20, 
                                     text_surf.get_height() + 10), pygame.SRCALPHA)
            bg_surf.fill((UITheme.BG_PANEL[0], UITheme.BG_PANEL[1],
                         UITheme.BG_PANEL[2], alpha))
            
            surface.blit(bg_surf, (20, y + int(notif['y_offset'])))
            surface.blit(text_surf, (30, y + 5 + int(notif['y_offset'])))
            
            y += text_surf.get_height() + 20
