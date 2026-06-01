"""
World module for the Digital Organism Simulator.
Realistic 2D world with terrain height, biomes, day/night, seasons.

Мир симуляции — рельеф, биомы, смена дня и ночи, сезоны.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Set
from config import (
    WORLD_WIDTH, WORLD_HEIGHT, WORLD_SIZE,
    CELL_EMPTY, CELL_GRASS, CELL_TREE, CELL_BERRY_BUSH,
    CELL_WATER, CELL_STONE, CELL_SHELTER, CELL_RESOURCE,
    TERRAIN_PROB_GRASS, TERRAIN_PROB_TREE, TERRAIN_PROB_BERRY,
    TERRAIN_PROB_WATER, TERRAIN_PROB_STONE, TERRAIN_PROB_EMPTY,
    TREE_GROWTH_CHANCE, BERRY_REGROWTH_CHANCE, RESOURCE_REGROWTH_CHANCE,
    MAX_TREES, MAX_BERRIES,
    GRASS_FOOD_VALUE, BERRY_FOOD_VALUE, TREE_WOOD_VALUE,
    WATER_THIRST_VALUE, STONE_RESOURCE_VALUE,
    DAY_LENGTH, NIGHT_LENGTH, CYCLE_LENGTH,
    SEASON_SPRING, SEASON_SUMMER, SEASON_AUTUMN, SEASON_WINTER,
    SEASON_NAMES, SEASON_LENGTH, FULL_YEAR, SEASON_GROWTH_MULT,
)


class WorldCell:
    """
    Represents a single cell in the world grid.
    Each cell has terrain type, height, resources, and flora.
    """

    __slots__ = ("terrain", "resources", "has_shelter", "is_burning",
                 "height", "moisture", "foliage_amount", "shimmer")

    def __init__(self, terrain: int = CELL_EMPTY):
        self.terrain: int = terrain
        self.resources: float = 0.0
        self.has_shelter: bool = False
        self.is_burning: bool = False
        self.height: float = 0.0       # terrain height (-1.0 to 1.0)
        self.moisture: float = 0.5     # moisture level (0-1) affects growth
        self.foliage_amount: float = 0.0  # visual density of foliage
        self.shimmer: float = 0.0      # for water animation

    def is_walkable(self) -> bool:
        return self.terrain != CELL_WATER and self.terrain != CELL_STONE

    def is_water(self) -> bool:
        return self.terrain == CELL_WATER

    def is_food_source(self) -> bool:
        return (self.terrain == CELL_GRASS or self.terrain == CELL_BERRY_BUSH) and self.resources > 0

    def is_resource_source(self) -> bool:
        return (self.terrain == CELL_TREE and self.resources > 0) or \
               (self.terrain == CELL_STONE and self.resources > 0) or \
               (self.terrain == CELL_RESOURCE and self.resources > 0)

    def get_foliage_color_mult(self) -> float:
        """Get color multiplier based on moisture and height for natural look."""
        base = 0.6 + self.moisture * 0.4
        if self.height > 0.3:
            base *= 0.85  # higher = less green
        return max(0.3, min(1.0, base))


class World:
    """
    The 2D grid world with realistic terrain, biomes, and resources.
    Uses Perlin-like noise for natural terrain generation.
    """

    def __init__(self) -> None:
        self.grid: List[List[WorldCell]] = [
            [WorldCell() for _ in range(WORLD_WIDTH)]
            for _ in range(WORLD_HEIGHT)
        ]

        # Time tracking
        self.tick: int = 0
        self.time_of_day: float = 0.0
        self.is_daytime: bool = True
        self.current_season: int = SEASON_SPRING
        self.season_tick: int = 0

        # Counters
        self.tree_count: int = 0
        self.berry_count: int = 0
        self.shelter_positions: Set[Tuple[int, int]] = set()

        # Generate realistic terrain
        self._generate_height_map()
        self._generate_biomes()
        self._initialize_resources()

    def _generate_height_map(self) -> None:
        """
        Generate terrain height using layered noise for realistic hills/valleys.
        """
        size = max(WORLD_WIDTH, WORLD_HEIGHT)
        # Use numpy for efficient generation
        x_coords = np.arange(WORLD_WIDTH)
        y_coords = np.arange(WORLD_HEIGHT)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Multiple octaves of Perlin-like noise
        noise = np.zeros((WORLD_HEIGHT, WORLD_WIDTH))
        amplitude = 1.0
        frequency = 0.05
        for _ in range(4):
            noise += amplitude * np.sin(xx * frequency) * np.cos(yy * frequency)
            noise += amplitude * np.sin((xx + yy) * frequency * 0.7)
            amplitude *= 0.5
            frequency *= 2.0

        # Normalize to [-1, 1]
        noise = noise / noise.max() * 2 - 1

        # Generate moisture map (for biomes)
        moisture = np.random.random((WORLD_HEIGHT, WORLD_WIDTH)) * 0.5 + 0.5
        moisture += np.sin(yy * 0.02) * 0.2  # latitudinal moisture band

        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                self.grid[y][x].height = float(noise[y][x])
                self.grid[y][x].moisture = float(np.clip(moisture[y][x], 0.0, 1.0))

    def _generate_biomes(self) -> None:
        """
        Assign terrain types based on height and moisture.
        Low areas become water, mid areas become grass/forest,
        high areas become stone/mountains.
        """
        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                cell = self.grid[y][x]
                h = cell.height
                m = cell.moisture

                # Biome assignment
                if h < -0.4:
                    # Low areas - water
                    cell.terrain = CELL_WATER
                    cell.resources = float(WATER_THIRST_VALUE)
                elif h < -0.2:
                    # Wetlands / shore - grass with high moisture
                    cell.terrain = CELL_GRASS
                    cell.resources = float(np.random.randint(3, GRASS_FOOD_VALUE))
                    cell.foliage_amount = 0.7 + m * 0.3
                elif h < 0.2:
                    # Plains - grass and bushes
                    if m > 0.6 and np.random.random() < 0.15:
                        cell.terrain = CELL_BERRY_BUSH
                        self.berry_count += 1
                        cell.resources = float(np.random.randint(5, BERRY_FOOD_VALUE))
                    elif np.random.random() < 0.15:
                        cell.terrain = CELL_TREE
                        self.tree_count += 1
                        cell.resources = float(np.random.randint(5, TREE_WOOD_VALUE))
                    else:
                        cell.terrain = CELL_GRASS
                        cell.resources = float(np.random.randint(2, GRASS_FOOD_VALUE))
                    cell.foliage_amount = 0.5 + m * 0.5
                elif h < 0.5:
                    # Forest hills
                    if np.random.random() < 0.25:
                        cell.terrain = CELL_TREE
                        self.tree_count += 1
                        cell.resources = float(np.random.randint(8, TREE_WOOD_VALUE + 5))
                    elif np.random.random() < 0.10:
                        cell.terrain = CELL_BERRY_BUSH
                        self.berry_count += 1
                        cell.resources = float(np.random.randint(5, BERRY_FOOD_VALUE))
                    else:
                        cell.terrain = CELL_GRASS
                        cell.resources = float(np.random.randint(1, GRASS_FOOD_VALUE - 2))
                    cell.foliage_amount = 0.4 + m * 0.4
                else:
                    # Mountains - stone
                    cell.terrain = CELL_STONE
                    cell.resources = float(np.random.randint(3, STONE_RESOURCE_VALUE + 5))
                    cell.foliage_amount = 0.1

                # Random resource deposits in grassland
                if cell.terrain == CELL_GRASS and np.random.random() < 0.03:
                    cell.terrain = CELL_RESOURCE
                    cell.resources = float(np.random.randint(10, 30))
                    cell.foliage_amount = 0.2

    def _initialize_resources(self) -> None:
        """Fine-tune initial resource distribution."""
        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                cell = self.grid[y][x]
                if cell.resources <= 0:
                    if cell.terrain == CELL_GRASS:
                        cell.resources = float(np.random.randint(2, GRASS_FOOD_VALUE))
                        cell.foliage_amount = 0.5 + cell.moisture * 0.5
                    elif cell.terrain == CELL_EMPTY:
                        cell.resources = 0.0
                        cell.foliage_amount = 0.1
                    elif cell.terrain == CELL_WATER:
                        cell.resources = float(WATER_THIRST_VALUE)
                    elif cell.terrain == CELL_RESOURCE:
                        cell.resources = float(np.random.randint(10, 30))

    def update(self) -> None:
        """Update world state each tick."""
        self.tick += 1
        self._update_time()
        self._update_season()
        self._regrow_resources()
        self._spread_vegetation()

    def _update_time(self) -> None:
        """Update day/night cycle with smooth transitions."""
        cycle_progress = self.tick % CYCLE_LENGTH
        if cycle_progress < DAY_LENGTH:
            self.is_daytime = True
            self.time_of_day = cycle_progress / DAY_LENGTH
        else:
            self.is_daytime = False
            self.time_of_day = (cycle_progress - DAY_LENGTH) / NIGHT_LENGTH

        # Update water shimmer for animation
        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                if self.grid[y][x].terrain == CELL_WATER:
                    self.grid[y][x].shimmer = (
                        np.sin(self.tick * 0.05 + x * 0.5 + y * 0.3) * 0.5 + 0.5
                    )

    def _update_season(self) -> None:
        """Update current season."""
        self.season_tick = self.tick % FULL_YEAR
        if self.season_tick < SEASON_LENGTH:
            self.current_season = SEASON_SPRING
        elif self.season_tick < SEASON_LENGTH * 2:
            self.current_season = SEASON_SUMMER
        elif self.season_tick < SEASON_LENGTH * 3:
            self.current_season = SEASON_AUTUMN
        else:
            self.current_season = SEASON_WINTER

    def get_season_name(self) -> str:
        return SEASON_NAMES[self.current_season]

    def get_growth_multiplier(self) -> float:
        return SEASON_GROWTH_MULT[self.current_season]

    def _regrow_resources(self) -> None:
        """Regrow resources based on season, moisture, and daylight."""
        growth_mult = self.get_growth_multiplier()
        day_mult = 1.5 if self.is_daytime else 0.5

        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                cell = self.grid[y][x]

                if cell.is_burning:
                    if np.random.random() < 0.05:
                        cell.is_burning = False
                        cell.terrain = CELL_EMPTY
                        cell.resources = 0.0
                        cell.foliage_amount = 0.0
                    continue

                moisture_bonus = cell.moisture * 0.5
                regrowth_rate = 0.03 * growth_mult * day_mult * (1.0 + moisture_bonus)

                if cell.terrain == CELL_GRASS:
                    if cell.resources < GRASS_FOOD_VALUE:
                        if np.random.random() < regrowth_rate:
                            cell.resources = min(GRASS_FOOD_VALUE, cell.resources + 1)
                            cell.foliage_amount = min(1.0, cell.foliage_amount + 0.01)

                elif cell.terrain == CELL_BERRY_BUSH:
                    if cell.resources < BERRY_FOOD_VALUE:
                        if np.random.random() < regrowth_rate * 0.6:
                            cell.resources = min(BERRY_FOOD_VALUE, cell.resources + 1)

                elif cell.terrain == CELL_WATER:
                    cell.resources = float(WATER_THIRST_VALUE)

                elif cell.terrain == CELL_RESOURCE:
                    if cell.resources < 30:
                        if np.random.random() < RESOURCE_REGROWTH_CHANCE * growth_mult:
                            cell.resources = min(30, cell.resources + 1)

    def _spread_vegetation(self) -> None:
        """Spread vegetation to nearby cells naturally."""
        growth_mult = self.get_growth_multiplier()

        if self.tree_count < MAX_TREES:
            for _ in range(3):  # Multiple attempts
                x = np.random.randint(0, WORLD_WIDTH)
                y = np.random.randint(0, WORLD_HEIGHT)
                if self.grid[y][x].terrain == CELL_TREE:
                    if np.random.random() < TREE_GROWTH_CHANCE * growth_mult:
                        dx, dy = np.random.randint(-2, 3), np.random.randint(-2, 3)
                        nx, ny = np.clip(x + dx, 0, WORLD_WIDTH - 1), np.clip(y + dy, 0, WORLD_HEIGHT - 1)
                        neighbor = self.grid[ny][nx]
                        if neighbor.terrain == CELL_EMPTY or neighbor.terrain == CELL_GRASS:
                            if neighbor.moisture > 0.3 and neighbor.height > -0.1:
                                neighbor.terrain = CELL_TREE
                                neighbor.resources = float(np.random.randint(5, 15))
                                neighbor.foliage_amount = 0.8
                                self.tree_count += 1
                                break

        if self.berry_count < MAX_BERRIES:
            x = np.random.randint(0, WORLD_WIDTH)
            y = np.random.randint(0, WORLD_HEIGHT)
            if self.grid[y][x].terrain == CELL_BERRY_BUSH:
                if np.random.random() < BERRY_REGROWTH_CHANCE * growth_mult:
                    dx, dy = np.random.randint(-2, 3), np.random.randint(-2, 3)
                    nx, ny = np.clip(x + dx, 0, WORLD_WIDTH - 1), np.clip(y + dy, 0, WORLD_HEIGHT - 1)
                    neighbor = self.grid[ny][nx]
                    if neighbor.terrain == CELL_EMPTY or neighbor.terrain == CELL_GRASS:
                        neighbor.terrain = CELL_BERRY_BUSH
                        neighbor.resources = float(np.random.randint(5, 15))
                        self.berry_count += 1

    def get_cell(self, x: int, y: int) -> Optional[WorldCell]:
        if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT:
            return self.grid[y][x]
        return None

    def is_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT

    def add_shelter(self, x: int, y: int) -> bool:
        cell = self.get_cell(x, y)
        if cell is not None and not cell.has_shelter:
            cell.has_shelter = True
            cell.terrain = CELL_SHELTER
            self.shelter_positions.add((x, y))
            return True
        return False

    def consume_food(self, x: int, y: int, amount: float) -> float:
        cell = self.get_cell(x, y)
        if cell is None or not cell.is_food_source():
            return 0.0
        consumed = min(amount, cell.resources)
        cell.resources -= consumed
        if cell.resources <= 0:
            cell.foliage_amount = max(0.1, cell.foliage_amount - 0.3)
        return consumed

    def consume_water(self, x: int, y: int, amount: float) -> float:
        cell = self.get_cell(x, y)
        if cell is None or not cell.is_water():
            return 0.0
        consumed = min(amount, cell.resources)
        cell.resources -= consumed
        return consumed

    def harvest_resource(self, x: int, y: int, amount: float) -> float:
        cell = self.get_cell(x, y)
        if cell is None or not cell.is_resource_source():
            return 0.0
        harvested = min(amount, cell.resources)
        cell.resources -= harvested
        if cell.resources <= 0:
            if cell.terrain == CELL_TREE:
                self.tree_count -= 1
                cell.terrain = CELL_GRASS
                cell.foliage_amount = 0.2
            elif cell.terrain == CELL_RESOURCE:
                cell.terrain = CELL_EMPTY
                cell.foliage_amount = 0.1
        return harvested

    def get_visibility_modifier(self) -> float:
        if self.is_daytime:
            return 1.0
        else:
            moon_phase = np.sin(self.tick * 0.01)
            return 0.25 + (moon_phase * 0.15)

    def get_cells_in_radius(self, cx: int, cy: int, radius: int) -> List[Tuple[int, int, WorldCell]]:
        cells = []
        for y in range(max(0, cy - radius), min(WORLD_HEIGHT, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(WORLD_WIDTH, cx + radius + 1)):
                dx, dy = x - cx, y - cy
                dist = (dx * dx + dy * dy) ** 0.5
                if dist <= radius:
                    cells.append((x, y, self.grid[y][x]))
        return cells

    def find_nearest_of_type(self, cx: int, cy: int, terrain_type: int,
                              max_dist: int = 20) -> Optional[Tuple[int, int]]:
        best_dist = max_dist * max_dist
        best_pos = None
        for y in range(max(0, cy - max_dist), min(WORLD_HEIGHT, cy + max_dist + 1)):
            for x in range(max(0, cx - max_dist), min(WORLD_WIDTH, cx + max_dist + 1)):
                if self.grid[y][x].terrain == terrain_type:
                    d = (x - cx) ** 2 + (y - cy) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_pos = (x, y)
        return best_pos

    def find_nearest_food(self, cx: int, cy: int, max_dist: int = 20) -> Optional[Tuple[int, int]]:
        best_dist = max_dist * max_dist
        best_pos = None
        for y in range(max(0, cy - max_dist), min(WORLD_HEIGHT, cy + max_dist + 1)):
            for x in range(max(0, cx - max_dist), min(WORLD_WIDTH, cx + max_dist + 1)):
                cell = self.grid[y][x]
                if cell.is_food_source():
                    d = (x - cx) ** 2 + (y - cy) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_pos = (x, y)
        return best_pos

    def find_nearest_water(self, cx: int, cy: int, max_dist: int = 20) -> Optional[Tuple[int, int]]:
        return self.find_nearest_of_type(cx, cy, CELL_WATER, max_dist)

    def find_nearest_shelter(self, cx: int, cy: int, max_dist: int = 20) -> Optional[Tuple[int, int]]:
        best_dist = max_dist * max_dist
        best_pos = None
        for (sx, sy) in self.shelter_positions:
            d = (sx - cx) ** 2 + (sy - cy) ** 2
            if d < best_dist:
                best_dist = d
                best_pos = (sx, sy)
        return best_pos

    def get_random_walkable_cell(self) -> Tuple[int, int]:
        while True:
            x = np.random.randint(0, WORLD_WIDTH)
            y = np.random.randint(0, WORLD_HEIGHT)
            cell = self.grid[y][x]
            if cell.is_walkable() and not cell.has_shelter:
                return (x, y)

    def get_stats(self) -> dict:
        """Get world statistics."""
        stats = {
            "food_cells": 0, "water_cells": 0, "tree_cells": 0,
            "total_food": 0.0, "shelters": len(self.shelter_positions),
            "tick": self.tick, "season": self.get_season_name(),
            "is_daytime": self.is_daytime, "time_of_day": round(self.time_of_day, 2),
        }
        for y in range(WORLD_HEIGHT):
            for x in range(WORLD_WIDTH):
                cell = self.grid[y][x]
                if cell.is_food_source():
                    stats["food_cells"] += 1
                    stats["total_food"] += cell.resources
                if cell.terrain == CELL_WATER:
                    stats["water_cells"] += 1
                if cell.terrain == CELL_TREE:
                    stats["tree_cells"] += 1
        stats["total_food"] = round(stats["total_food"], 0)
        return stats