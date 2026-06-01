"""
UI module for the Digital Organism Simulator.
Manages the sidebar statistics, buttons, and information panels.

Пользовательский интерфейс — панель статистики, кнопки управления, информация.
"""

import pygame
from typing import List, Optional, Tuple, Dict
from config import (
    DISPLAY_WIDTH, DISPLAY_HEIGHT, UI_PANEL_WIDTH, UI_SIDEBAR_X,
    COLOR_UI_BG, COLOR_UI_TEXT, COLOR_UI_HIGHLIGHT, COLOR_UI_ACCENT,
    COLOR_ORGANISM_HEALTHY, COLOR_ORGANISM_DYING,
    TICK_RATES,
)


class Button:
    """A clickable UI button."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, color: Tuple[int, int, int] = COLOR_UI_ACCENT,
                 toggle: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.toggle = toggle
        self.is_toggled = False
        self.is_hovered = False
        self.is_visible = True
        self.on_click = None  # callback function

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button."""
        if not self.is_visible:
            return

        # Choose color based on state
        if self.toggle and self.is_toggled:
            color = (255, 200, 50)  # highlighted when toggled
        elif self.is_hovered:
            color = tuple(min(255, c + 40) for c in self.color)
        else:
            color = self.color

        # Draw button background
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255, 60), self.rect, 1, border_radius=3)

        # Draw text
        text_surf = font.render(self.text, True, COLOR_UI_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle a pygame event. Returns True if clicked."""
        if not self.is_visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.toggle:
                    self.is_toggled = not self.is_toggled
                if self.on_click:
                    self.on_click()
                return True
        return False


class UIManager:
    """
    Manages the entire user interface including sidebar, buttons, info panels.
    """

    def __init__(self):
        # Fonts
        self.font_small = pygame.font.Font(None, 14)
        self.font_medium = pygame.font.Font(None, 18)
        self.font_large = pygame.font.Font(None, 24)
        self.font_title = pygame.font.Font(None, 28)

        # Sidebar surface
        self.sidebar = pygame.Surface((UI_PANEL_WIDTH, DISPLAY_HEIGHT))
        self.sidebar_rect = pygame.Rect(UI_SIDEBAR_X, 0, UI_PANEL_WIDTH, DISPLAY_HEIGHT)

        # Scroll position for info panels
        self.scroll_y = 0
        self.max_scroll = 0

        # Selected organism
        self.selected_organism = None

        # Simulation speed control
        self.current_speed = "normal"
        self.speed_index = 1
        self.speed_options = ["slow", "normal", "fast", "faster"]
        self.speed_labels = ["Медленно", "Нормально", "Быстро", "Очень быстро"]

        # Pause state
        self.is_paused = False

        # Tab system for info panels
        self.current_tab = 0  # 0=stats, 1=organism, 2=genome, 3=log
        self.tab_names = ["Статистика", "Организм", "Геном", "Лог"]

        # Create buttons
        self.buttons: List[Button] = []
        self._create_buttons()

        # Log lines cache
        self.log_lines: List[str] = []
        self.log_scroll = 0

    def _create_buttons(self) -> None:
        """Create all UI buttons."""
        button_x = UI_SIDEBAR_X + 10
        button_w = (UI_PANEL_WIDTH - 30) // 2

        # Speed buttons
        self.btn_slower = Button(button_x, 5, button_w, 25, "<<")
        self.btn_slower.color = (100, 100, 120)
        self.btn_faster = Button(button_x + button_w + 10, 5, button_w, 25, ">>")
        self.btn_faster.color = (100, 100, 120)

        # Pause button
        self.btn_pause = Button(button_x, 35, UI_PANEL_WIDTH - 20, 25, "Пауза")
        self.btn_pause.toggle = True
        self.btn_pause.color = (120, 80, 80)

        # Tab buttons
        tab_y = 70
        tab_w = (UI_PANEL_WIDTH - 30) // 4
        self.tab_buttons = []
        for i, name in enumerate(self.tab_names):
            btn = Button(
                UI_SIDEBAR_X + 10 + i * (tab_w + 3),
                tab_y, tab_w, 22, name
            )
            btn.color = (60, 60, 80)
            btn.toggle = True
            btn._tab_index = i
            self.tab_buttons.append(btn)

        self.buttons.extend([self.btn_slower, self.btn_faster, self.btn_pause])
        self.buttons.extend(self.tab_buttons)

    def draw(self, surface: pygame.Surface, world, organisms: list) -> None:
        """
        Draw the complete UI overlay.
        """
        # Draw sidebar background
        self.sidebar.fill(COLOR_UI_BG)

        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.sidebar, self.font_small)

        # Draw current speed label
        speed_text = self.font_small.render(
            f"Скорость: {self.speed_labels[self.speed_index]}",
            True, COLOR_UI_TEXT)
        self.sidebar.blit(speed_text, (UI_SIDEBAR_X + 15, 33))

        # Draw tab content
        tab_content_y = 100
        if self.current_tab == 0:
            self._draw_stats_tab(self.sidebar, world, organisms, tab_content_y)
        elif self.current_tab == 1:
            self._draw_organism_tab(self.sidebar, tab_content_y)
        elif self.current_tab == 2:
            self._draw_genome_tab(self.sidebar, tab_content_y)
        elif self.current_tab == 3:
            self._draw_log_tab(self.sidebar, tab_content_y)

        # Draw pause overlay if paused
        if self.is_paused:
            overlay = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            surface.blit(overlay, (0, 0))
            pause_text = self.font_title.render("ПАУЗА", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(UI_SIDEBAR_X // 2, DISPLAY_HEIGHT // 2))
            surface.blit(pause_text, text_rect)

        # Blit sidebar
        surface.blit(self.sidebar, (UI_SIDEBAR_X, 0))

        # Draw border between world and sidebar
        pygame.draw.line(surface, (100, 100, 100),
                         (UI_SIDEBAR_X, 0), (UI_SIDEBAR_X, DISPLAY_HEIGHT), 1)

    def _draw_stats_tab(self, surface: pygame.Surface, world,
                         organisms: list, start_y: int) -> None:
        """Draw the main statistics tab."""
        y = start_y

        # Title
        title = self.font_medium.render("Статистика мира", True, COLOR_UI_HIGHLIGHT)
        surface.blit(title, (UI_SIDEBAR_X + 10, y))
        y += 25

        if world:
            world_stats = world.get_stats()
            lines = [
                f"Тик: {world_stats['tick']}",
                f"Сезон: {world_stats['season']}",
                f"{'День' if world_stats['is_daytime'] else 'Ночь'}",
                f"Клеток с едой: {world_stats['food_cells']}",
                f"Водных клеток: {world_stats['water_cells']}",
                f"Деревьев: {world_stats['tree_cells']}",
                f"Убежищ: {world_stats['shelters']}",
            ]
        else:
            lines = ["Мир не инициализирован"]

        for line in lines:
            text = self.font_small.render(line, True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 12, y))
            y += 16

        y += 10

        # Population stats
        alive = [o for o in organisms if o.is_alive]
        pop_title = self.font_medium.render("Популяция", True, COLOR_UI_HIGHLIGHT)
        surface.blit(pop_title, (UI_SIDEBAR_X + 10, y))
        y += 22

        if alive:
            avg_age = sum(o.age for o in alive) / len(alive)
            avg_gen = sum(o.generation for o in alive) / len(alive)
            avg_intel = sum(o.intelligence for o in alive) / len(alive)
            oldest = max(o.age for o in alive)
            total_children = sum(o.children_count for o in alive)
            total_buildings = sum(o.buildings_made for o in alive)

            pop_lines = [
                f"Живых: {len(alive)}",
                f"Средний возраст: {avg_age:.1f} тиков",
                f"Старейший: {oldest} тиков",
                f"Среднее поколение: {avg_gen:.1f}",
                f"Средний интеллект: {avg_intel:.2f}",
                f"Всего рождений: {sum(o.children_count for o in organisms)}",
                f"Построек: {total_buildings}",
            ]
        else:
            pop_lines = ["Все организмы мертвы"]

        for line in pop_lines:
            text = self.font_small.render(line, True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 12, y))
            y += 16

        y += 10

        # FPS
        fps_text = self.font_small.render(
            f"FPS: {int(pygame.display.get_surface().get_abs_offset()[0])}",
            True, COLOR_UI_TEXT)
        # Alternative: just show a placeholder for performance
        perf_text = self.font_small.render("Симуляция активна", True, COLOR_UI_ACCENT)
        surface.blit(perf_text, (UI_SIDEBAR_X + 10, y))

    def _draw_organism_tab(self, surface: pygame.Surface, start_y: int) -> None:
        """Draw the selected organism info tab."""
        if self.selected_organism is None:
            text = self.font_medium.render(
                "Кликните на существо", True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 10, start_y))
            return

        org = self.selected_organism
        y = start_y

        # Organism header
        header = self.font_medium.render(
            f"Существо #{org.uid}", True, COLOR_UI_HIGHLIGHT)
        surface.blit(header, (UI_SIDEBAR_X + 10, y))
        y += 22

        # Status
        status = org.get_status_string()
        status_color = COLOR_ORGANISM_HEALTHY if "Здоров" in status else COLOR_ORGANISM_DYING
        status_text = self.font_small.render(f"Статус: {status}", True, status_color)
        surface.blit(status_text, (UI_SIDEBAR_X + 12, y))
        y += 18

        # Basic info
        info_lines = [
            f"Поколение: {org.generation}",
            f"Возраст: {org.age}/{org.max_age_ticks}",
            f"Здоровье: {org.health:.1f}/{org.max_health:.0f}",
            f"Сытость: {org.hunger:.1f}/{org.max_hunger:.0f}",
            f"Жажда: {org.thirst:.1f}/{org.max_thirst:.0f}",
            f"Энергия: {org.energy:.1f}/{org.max_energy:.0f}",
            f"Ресурсы: {org.resources:.1f}/{org.max_resources:.0f}",
            f"Дети: {org.children_count}",
            f"Построек: {org.buildings_made}",
            f"Позиция: ({org.x}, {org.y})",
        ]

        for line in info_lines:
            text = self.font_small.render(line, True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 12, y))
            y += 15
            if y > DISPLAY_HEIGHT - 30:
                break

        y += 10

        # Discovered strategies
        if org.brain:
            strategies = org.brain.get_strategies_discovered()
            if strategies:
                strat_title = self.font_small.render(
                    "Стратегии:", True, COLOR_UI_ACCENT)
                surface.blit(strat_title, (UI_SIDEBAR_X + 10, y))
                y += 16
                for strat in strategies:
                    s_text = self.font_small.render(f" - {strat}", True, COLOR_UI_TEXT)
                    surface.blit(s_text, (UI_SIDEBAR_X + 15, y))
                    y += 14
                    if y > DISPLAY_HEIGHT - 20:
                        break

    def _draw_genome_tab(self, surface: pygame.Surface, start_y: int) -> None:
        """Draw the genome/traits information tab."""
        if self.selected_organism is None:
            text = self.font_medium.render(
                "Кликните на существо", True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 10, start_y))
            return

        genome = self.selected_organism.genome
        y = start_y

        title = self.font_medium.render("Геном", True, COLOR_UI_HIGHLIGHT)
        surface.blit(title, (UI_SIDEBAR_X + 10, y))
        y += 22

        traits = genome.get_all_traits_dict()
        for trait_name, trait_value in traits.items():
            text = self.font_small.render(
                f"{trait_name}: {trait_value}", True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 12, y))
            y += 14
            if y > DISPLAY_HEIGHT - 30:
                break

        y += 10
        raw_genes = genome.get_raw_genes_str()
        genes_text = self.font_small.render(
            f"Гены: {raw_genes[:50]}...", True, COLOR_UI_TEXT)
        surface.blit(genes_text, (UI_SIDEBAR_X + 10, y))

    def _draw_log_tab(self, surface: pygame.Surface, start_y: int) -> None:
        """Draw the event log tab."""
        y = start_y
        title = self.font_medium.render("Лог событий", True, COLOR_UI_HIGHLIGHT)
        surface.blit(title, (UI_SIDEBAR_X + 10, y))
        y += 22

        log_start = max(0, len(self.log_lines) - 30 - self.log_scroll)
        log_end = max(0, len(self.log_lines) - self.log_scroll)

        for i in range(log_start, log_end):
            if i >= len(self.log_lines):
                break
            line = self.log_lines[i]
            text = self.font_small.render(line[:55], True, COLOR_UI_TEXT)
            surface.blit(text, (UI_SIDEBAR_X + 10, y))
            y += 13
            if y > DISPLAY_HEIGHT - 20:
                break

        if not self.log_lines:
            no_log = self.font_small.render("Нет событий", True, COLOR_UI_TEXT)
            surface.blit(no_log, (UI_SIDEBAR_X + 10, y))

    def add_log_line(self, line: str) -> None:
        """Add a line to the event log."""
        self.log_lines.append(line)
        if len(self.log_lines) > 200:
            self.log_lines.pop(0)

    def handle_events(self, events: List[pygame.event.Event], world,
                      organisms: list, renderer) -> Dict:
        """
        Handle all UI events from pygame.
        Returns a dict with actions to be performed by the simulation.
        """
        result = {
            "pause_toggle": False,
            "speed_up": False,
            "speed_down": False,
            "select_organism": None,
            "camera_move": (0, 0),
        }

        for event in events:
            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_slower.rect.collidepoint(event.pos):
                    self._speed_down()
                    result["speed_down"] = True
                elif self.btn_faster.rect.collidepoint(event.pos):
                    self._speed_up()
                    result["speed_up"] = True
                elif self.btn_pause.rect.collidepoint(event.pos):
                    self.is_paused = not self.is_paused
                    result["pause_toggle"] = True

                # Tab buttons
                for i, btn in enumerate(self.tab_buttons):
                    if btn.rect.collidepoint(event.pos):
                        self.current_tab = i
                        for other in self.tab_buttons:
                            other.is_toggled = False
                        btn.is_toggled = True

                # Click on world -> select organism
                if event.pos[0] < UI_SIDEBAR_X:
                    wx, wy = renderer.camera.screen_to_world(event.pos[0], event.pos[1])
                    clicked_org = self._find_organism_at(wx, wy, organisms)
                    self.selected_organism = clicked_org
                    result["select_organism"] = clicked_org

            # Keyboard shortcuts
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.is_paused = not self.is_paused
                    result["pause_toggle"] = True
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self._speed_up()
                    result["speed_up"] = True
                elif event.key == pygame.K_MINUS:
                    self._speed_down()
                    result["speed_down"] = True
                elif event.key == pygame.K_UP:
                    result["camera_move"] = (0, -20)
                elif event.key == pygame.K_DOWN:
                    result["camera_move"] = (0, 20)
                elif event.key == pygame.K_LEFT:
                    result["camera_move"] = (-20, 0)
                elif event.key == pygame.K_RIGHT:
                    result["camera_move"] = (20, 0)
                elif event.key == pygame.K_ESCAPE:
                    self.selected_organism = None
                    result["select_organism"] = None

            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.log_scroll = max(0, self.log_scroll - 3)
                else:
                    self.log_scroll += 3

        return result

    def _speed_up(self) -> None:
        """Increase simulation speed."""
        self.speed_index = min(len(self.speed_options) - 1, self.speed_index + 1)
        self.current_speed = self.speed_options[self.speed_index]

    def _speed_down(self) -> None:
        """Decrease simulation speed."""
        self.speed_index = max(0, self.speed_index - 1)
        self.current_speed = self.speed_options[self.speed_index]

    def _find_organism_at(self, wx: int, wy: int,
                           organisms: list) -> Optional[object]:
        """Find an organism at the given world coordinates."""
        for org in organisms:
            if org.is_alive and abs(org.x - wx) <= 1 and abs(org.y - wy) <= 1:
                return org
        return None

    def get_tick_rate(self) -> int:
        """Get the current tick rate based on speed setting."""
        return TICK_RATES.get(self.current_speed, 10)