"""
Organism module for the Digital Organism Simulator.
Defines the Organism class with all its properties, needs, memory and actions.

Цифровое существо — организм со всеми параметрами, потребностями и действиями.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from enum import Enum
from animation import AnimationState
from config import (
    MAX_HEALTH, MAX_HUNGER, MAX_THIRST, MAX_ENERGY, MAX_RESOURCES,
    HUNGER_DECAY, THIRST_DECAY, ENERGY_DECAY_MOVE, ENERGY_DECAY_WORK,
    ENERGY_REST_RECOVERY, HEALTH_DECAY_HUNGER, HEALTH_DECAY_THIRST,
    DEFAULT_SIGHT_RADIUS, MAX_AGE, AGE_MATURE,
    ACTION_COUNT, ACTION_MOVE_UP, ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT,
    ACTION_EAT, ACTION_DRINK, ACTION_REST, ACTION_COLLECT,
    ACTION_BUILD, ACTION_REPRODUCE, ACTION_EXPLORE, ACTION_GUARD,
    MEMORY_CAPACITY_DEFAULT, MEMORY_EVENT_FOOD, MEMORY_EVENT_WATER,
    MEMORY_EVENT_TREE, MEMORY_EVENT_DANGER, MEMORY_EVENT_BUILD,
    MEMORY_EVENT_BIRTH, MEMORY_EVENT_RESOURCE, MEMORY_EVENT_DEATH,
    REPRODUCTION_ENERGY_COST, REPRODUCTION_HEALTH_COST, REPRODUCTION_COOLDOWN,
    GRASS_FOOD_VALUE, BERRY_FOOD_VALUE, TREE_WOOD_VALUE,
    WATER_THIRST_VALUE, STONE_RESOURCE_VALUE,
    CELL_GRASS, CELL_BERRY_BUSH, CELL_TREE, CELL_WATER, CELL_STONE,
    CELL_SHELTER, CELL_RESOURCE, CELL_EMPTY,
    WORLD_WIDTH, WORLD_HEIGHT,
)


class OrganismMemory:
    """Stores recent events and learned information about the world."""

    __slots__ = ("capacity", "events")

    def __init__(self, capacity: int = MEMORY_CAPACITY_DEFAULT):
        self.capacity: int = capacity
        self.events: List[Dict] = []  # list of event dicts with 'type', 'tick', 'details'

    def add_event(self, event_type: str, tick: int, details: str = "") -> None:
        """Add an event to memory, keeping within capacity."""
        self.events.append({
            "type": event_type,
            "tick": tick,
            "details": details,
        })
        if len(self.events) > self.capacity:
            self.events.pop(0)

    def get_recent_events(self, count: int = 5) -> List[Dict]:
        """Get the most recent events."""
        return self.events[-count:]

    def has_event_type(self, event_type: str) -> bool:
        """Check if a certain type of event exists in memory."""
        return any(e["type"] == event_type for e in self.events)

    def count_event_type(self, event_type: str) -> int:
        """Count occurrences of a specific event type."""
        return sum(1 for e in self.events if e["type"] == event_type)

    def get_all_events(self) -> List[Dict]:
        """Get all events in memory."""
        return self.events.copy()


class Organism:
    """
    Represents a single digital organism in the simulation.
    Has physical attributes, needs, memory, and can perform actions.
    """

    # Class-level counter for unique IDs
    _next_id: int = 1

    def __init__(
        self,
        x: int,
        y: int,
        genome: 'Genome',  # Forward reference
        generation: int = 1,
        parent_ids: Optional[Tuple[int, int]] = None,
    ):
        # Unique identifier
        self.uid: int = Organism._next_id
        Organism._next_id += 1

        # Position in the world
        self.x: int = x
        self.y: int = y
        self.prev_x: int = x
        self.prev_y: int = y

        # Genetics
        self.genome = genome
        self.generation: int = generation
        self.parent_ids: Optional[Tuple[int, int]] = parent_ids

        # Derived traits from genetics
        self.max_health: float = genome.get_trait_max_health()
        self.max_hunger: float = genome.get_trait_max_hunger()
        self.max_thirst: float = genome.get_trait_max_thirst()
        self.max_energy: float = genome.get_trait_max_energy()
        self.max_resources: float = genome.get_trait_max_resources()
        self.sight_radius: int = genome.get_trait_sight_radius()
        self.speed: float = genome.get_trait_speed()
        self.intelligence: float = genome.get_trait_intelligence()
        self.memory_capacity: int = genome.get_trait_memory_capacity()
        self.longevity_modifier: float = genome.get_trait_longevity()
        self.aggression: float = genome.get_trait_aggression()
        self.exploration_tendency: float = genome.get_trait_exploration()
        self.sociality: float = genome.get_trait_sociality()
        self.build_tendency: float = genome.get_trait_build_tendency()
        self.food_preference: float = genome.get_trait_food_preference()
        self.water_efficiency: float = genome.get_trait_water_efficiency()
        self.metabolism: float = genome.get_trait_metabolism()
        self.storage_tendency: float = genome.get_trait_storage_tendency()

        # Current state
        self.health: float = self.max_health
        self.hunger: float = self.max_hunger * 0.7  # start a bit hungry
        self.thirst: float = self.max_thirst * 0.7  # start a bit thirsty
        self.energy: float = self.max_energy * 0.9
        self.resources: float = 10.0  # starting resources

        # Age tracking
        self.age: int = 0  # in ticks
        self.max_age_ticks: int = int(MAX_AGE * self.longevity_modifier)
        self.is_mature: bool = False
        self.is_alive: bool = True
        self.is_sleeping: bool = False

        # Reproduction
        self.reproduction_cooldown: int = 0
        self.children_count: int = 0

        # Memory
        self.memory = OrganismMemory(capacity=self.memory_capacity)

        # Action tracking
        self.last_action: int = -1
        self.last_action_result: dict = {}
        self.stuck_counter: int = 0  # counts ticks without moving
        self.last_positions: List[Tuple[int, int]] = []
        self.total_distance_traveled: float = 0.0

        # Perception data (updated each tick by the simulation)
        self.seen_cells: List[Tuple[int, int, 'WorldCell']] = []
        self.nearby_organisms: List['Organism'] = []
        self.food_nearby: bool = False
        self.water_nearby: bool = False
        self.resource_nearby: bool = False
        self.shelter_nearby: bool = False
        self.mate_nearby: bool = False

        # Goals and planning
        self.current_target: Optional[Tuple[int, int]] = None  # target (x,y)
        self.current_goal: Optional[str] = None  # e.g., "eat", "drink", "explore"
        self.direction_facing: Tuple[int, int] = (0, 1)  # direction vector

        # Statistics
        self.total_food_eaten: float = 0.0
        self.total_water_drunk: float = 0.0
        self.total_resources_collected: float = 0.0
        self.buildings_made: int = 0
        self.explored_cells: int = 0
        self.cells_visited: set = set()
        self.cells_visited.add((x, y))

        # AI brain (set externally by simulation)
        self.brain = None  # QLearningBrain instance
        
        # Animation system
        self.animation = AnimationState()
        self.animation.current_x = x * 20  # CELL_PIXEL_SIZE = 20
        self.animation.current_y = y * 20

    def update_state(self, tick: int, world_state: dict) -> dict:
        """
        Update the organism's internal state for one tick.
        Applies decay to hunger, thirst, energy, and health.
        Returns a dict describing the state changes.
        """
        if not self.is_alive:
            return {}

        self.age += 1

        # Check death conditions
        if self.age >= self.max_age_ticks:
            self.is_alive = False
            return {"died": True, "reason": "old_age"}

        if self.health <= 0:
            self.is_alive = False
            return {"died": True, "reason": "health_depleted"}

        # Maturity check
        if not self.is_mature and self.age >= AGE_MATURE:
            self.is_mature = True

        # Apply metabolism to decay rates
        metabolic_rate = 1.0 / self.metabolism  # Higher metabolism = slower decay

        # Hunger decay
        hunger_decay = HUNGER_DECAY * metabolic_rate
        self.hunger = max(0, self.hunger - hunger_decay)

        # Thirst decay
        thirst_decay = THIRST_DECAY * metabolic_rate / self.water_efficiency
        self.thirst = max(0, self.thirst - thirst_decay)

        # Energy recovery when sleeping/resting
        if self.is_sleeping:
            self.energy = min(self.max_energy, self.energy + ENERGY_REST_RECOVERY * 2)
        else:
            # Natural energy recovery (slow)
            self.energy = min(self.max_energy, self.energy + ENERGY_REST_RECOVERY * 0.3)

        # Health effects from starvation/thirst
        if self.hunger <= 0:
            self.health -= HEALTH_DECAY_HUNGER
        if self.thirst <= 0:
            self.health -= HEALTH_DECAY_THIRST

        # Slowly regenerate health if not starving and not thirsty
        if self.hunger > 30 and self.thirst > 30 and self.health < self.max_health:
            self.health = min(self.max_health, self.health + 0.05)

        # Cooldown decrement
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1

        state_update = {}
        if self.hunger <= 0:
            state_update["starving"] = True
        if self.thirst <= 0:
            state_update["dehydrated"] = True
        if self.health < self.max_health * 0.3:
            state_update["dying"] = True
        if self.is_mature and self.reproduction_cooldown == 0 and self.energy >= REPRODUCTION_ENERGY_COST:
            state_update["can_reproduce"] = True

        return state_update

    def get_state_for_ai(self, world) -> dict:
        """
        Build the state dictionary for the AI decision-making system.
        Includes internal needs, perceptions, and environmental context.
        """
        danger_nearby = False
        if world and self.brain and hasattr(self.brain, 'fear_memory'):
            danger = self.brain.fear_memory.get_position_danger(self.x, self.y)
            danger_nearby = danger > 0.3

        return {
            "hunger": self.hunger,
            "max_hunger": self.max_hunger,
            "thirst": self.thirst,
            "max_thirst": self.max_thirst,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "health": self.health,
            "max_health": self.max_health,
            "food_nearby": self.food_nearby,
            "water_nearby": self.water_nearby,
            "resource_nearby": self.resource_nearby,
            "shelter_nearby": self.shelter_nearby,
            "mate_nearby": self.mate_nearby,
            "danger_nearby": danger_nearby,
            "is_daytime": world.is_daytime if world else True,
            "age": self.age,
            "is_mature": self.is_mature,
            "can_reproduce": self.is_mature and self.reproduction_cooldown == 0
                             and self.energy >= REPRODUCTION_ENERGY_COST,
            "is_near_shelter": self._check_near_shelter(world),
            "resources": self.resources,
            "max_resources": self.max_resources,
            "season": world.current_season if world else 0,
            "can_explore": True,
        }

    def _check_near_shelter(self, world) -> bool:
        """Check if the organism is near a shelter."""
        if world is None:
            return False
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                cx, cy = self.x + dx, self.y + dy
                cell = world.get_cell(cx, cy)
                if cell and cell.has_shelter:
                    return True
        return False

    def update_perception(self, world) -> None:
        """
        Update the organism's perception of the world around it.
        This is called by the simulation each tick before the AI acts.
        """
        if not self.is_alive or world is None:
            return

        # Get visible cells
        vis_mod = world.get_visibility_modifier()
        effective_radius = max(1, int(self.sight_radius * vis_mod))
        self.seen_cells = world.get_cells_in_radius(self.x, self.y, effective_radius)

        # Reset flags
        self.food_nearby = False
        self.water_nearby = False
        self.resource_nearby = False
        self.shelter_nearby = False

        # Scan seen cells
        for (cx, cy, cell) in self.seen_cells:
            if cell.is_food_source():
                self.food_nearby = True
            if cell.is_water():
                self.water_nearby = True
            if cell.is_resource_source():
                self.resource_nearby = True
            if cell.has_shelter:
                self.shelter_nearby = True

    def move_towards(self, target_x: int, target_y: int, world) -> bool:
        """
        Move the organism one step towards a target position.
        Returns True if movement occurred.
        """
        if not self.is_alive:
            return False

        dx = target_x - self.x
        dy = target_y - self.y
        dist = (dx * dx + dy * dy) ** 0.5

        if dist == 0:
            return False

        # Normalize direction
        step_x = int(round(dx / dist))
        step_y = int(round(dy / dist))

        # Apply speed: faster organisms can move more steps per tick
        # (speed is handled in simulation loop by calling move multiple times)
        return self._move_relative(step_x, step_y, world)

    def _move_relative(self, dx: int, dy: int, world) -> bool:
        """Move by a relative offset if the destination is walkable."""
        new_x = self.x + dx
        new_y = self.y + dy

        # Check bounds
        if not world.is_in_bounds(new_x, new_y):
            return False

        # Check if walkable
        cell = world.get_cell(new_x, new_y)
        if cell is None or not cell.is_walkable():
            return False

        # Check for other organisms (simple collision: no stacking)
        # (this check is done by simulation)

        # Execute movement
        self.prev_x = self.x
        self.prev_y = self.y
        self.x = new_x
        self.y = new_y
        
        # Start animation
        self.animation.start_move(self.prev_x, self.prev_y, self.x, self.y)

        # Update direction
        if dx != 0 or dy != 0:
            self.direction_facing = (dx, dy)

        # Track movement
        self.cells_visited.add((new_x, new_y))
        self.total_distance_traveled += 1

        # Energy cost
        self.energy -= ENERGY_DECAY_MOVE * (1.0 / self.metabolism)

        # Track last positions for stuck detection
        self.last_positions.append((new_x, new_y))
        if len(self.last_positions) > 10:
            self.last_positions.pop(0)

        return True

    def is_stuck(self) -> bool:
        """Check if the organism has been stuck in the same area."""
        if len(self.last_positions) < 10:
            return False
        unique_positions = set(self.last_positions)
        return len(unique_positions) <= 2

    def eat(self, world) -> bool:
        """
        Eat food from the current or nearby cell.
        Returns True if food was consumed.
        """
        if not self.is_alive or self.hunger >= self.max_hunger:
            return False

        # Try to eat from current cell first, then nearby cells
        for (cx, cy, cell) in self.seen_cells:
            if cell.is_food_source():
                amount = min(
                    15.0,  # how much can eat at once
                    self.max_hunger - self.hunger,  # how much needed
                )
                consumed = world.consume_food(cx, cy, amount)
                if consumed > 0:
                    self.hunger = min(self.max_hunger, self.hunger + consumed)
                    self.total_food_eaten += consumed
                    self.energy = min(self.max_energy, self.energy + consumed * 0.3)
                    self.memory.add_event(MEMORY_EVENT_FOOD, world.tick,
                                          f"Съел {consumed:.1f} еды")
                    return True
        return False

    def drink(self, world) -> bool:
        """
        Drink water from a nearby water source.
        Returns True if water was consumed.
        """
        if not self.is_alive or self.thirst >= self.max_thirst:
            return False

        for (cx, cy, cell) in self.seen_cells:
            if cell.is_water():
                amount = min(15.0, self.max_thirst - self.thirst)
                consumed = world.consume_water(cx, cy, amount)
                if consumed > 0:
                    self.thirst = min(self.max_thirst, self.thirst + consumed * self.water_efficiency)
                    self.total_water_drunk += consumed
                    self.memory.add_event(MEMORY_EVENT_WATER, world.tick,
                                          f"Выпил {consumed:.1f} воды")
                    return True
        return False

    def rest(self) -> bool:
        """
        Rest to recover energy.
        Returns True if rest was beneficial.
        """
        if not self.is_alive:
            return False

        self.is_sleeping = True
        recovery = ENERGY_REST_RECOVERY * 2
        self.energy = min(self.max_energy, self.energy + recovery)
        return True

    def wake_up(self) -> None:
        """Wake the organism from rest."""
        self.is_sleeping = False

    def collect_resources(self, world) -> bool:
        """
        Collect building resources (wood, stone) from a nearby source.
        Returns True if resources were collected.
        """
        if not self.is_alive or self.resources >= self.max_resources:
            return False

        for (cx, cy, cell) in self.seen_cells:
            if cell.is_resource_source():
                amount = min(10.0, self.max_resources - self.resources)
                harvested = world.harvest_resource(cx, cy, amount)
                if harvested > 0:
                    self.resources += harvested
                    self.total_resources_collected += harvested
                    self.energy -= ENERGY_DECAY_WORK * (1.0 / self.metabolism)
                    self.memory.add_event(MEMORY_EVENT_RESOURCE, world.tick,
                                          f"Собрал {harvested:.1f} ресурсов")
                    return True
        return False

    def build_shelter(self, world) -> bool:
        """
        Build a shelter at the current position using resources.
        Returns True if shelter was built.
        """
        if not self.is_alive:
            return False

        if self.resources < 20:
            return False  # Not enough resources

        # Check if we can build here
        cell = world.get_cell(self.x, self.y)
        if cell is None or cell.has_shelter or not cell.is_walkable():
            return False

        # Build the shelter
        success = world.add_shelter(self.x, self.y)
        if success:
            self.resources -= 20
            self.energy -= ENERGY_DECAY_WORK * 2
            self.buildings_made += 1
            self.memory.add_event(MEMORY_EVENT_BUILD, world.tick,
                                  "Построил убежище")
            return True
        return False

    def reproduce(self, world, partner: Optional['Organism'] = None) -> Optional['Organism']:
        """
        Reproduce, creating a new organism.
        If partner is provided, sexual reproduction; otherwise asexual.
        Returns the offspring Organism if successful, None otherwise.
        """
        if not self.is_alive or not self.is_mature:
            return None
        if self.reproduction_cooldown > 0:
            return None
        if self.energy < REPRODUCTION_ENERGY_COST:
            return None

        from genetics import Genome

        # Create offspring genome
        if partner and partner.is_alive and partner.is_mature:
            # Sexual reproduction
            child_genome = Genome.combine(self.genome, partner.genome)
            parent_ids = (self.uid, partner.uid)
        else:
            # Asexual reproduction (clone with mutations)
            child_genome = self.genome.mutate()
            parent_ids = (self.uid, None)

        # Find a nearby position for the offspring
        child_x, child_y = self.x, self.y
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = self.x + dx, self.y + dy
                if world.is_in_bounds(nx, ny):
                    cell = world.get_cell(nx, ny)
                    if cell and cell.is_walkable() and not cell.has_shelter:
                        child_x, child_y = nx, ny
                        break

        # Create offspring
        child = Organism(
            x=child_x,
            y=child_y,
            genome=child_genome,
            generation=self.generation + 1,
            parent_ids=parent_ids,
        )

        # Apply costs
        self.energy -= REPRODUCTION_ENERGY_COST
        self.health -= REPRODUCTION_HEALTH_COST
        self.reproduction_cooldown = REPRODUCTION_COOLDOWN
        self.children_count += 1

        self.memory.add_event(MEMORY_EVENT_BIRTH, world.tick,
                              f"Родил потомка (поколение {self.generation + 1})")

        return child

    def explore(self, world) -> bool:
        """
        Move in a random direction to explore new territory.
        If there is an active target, move toward that target instead.
        Returns True if movement occurred.
        """
        if not self.is_alive:
            return False

        if self.current_target is not None and self.current_goal in {"eat", "drink", "collect"}:
            tx, ty = self.current_target
            dx = tx - self.x
            dy = ty - self.y
            if dx == 0 and dy == 0:
                self.current_target = None
                self.current_goal = None
                return False
            if abs(dx) >= abs(dy):
                step_x = int(np.sign(dx))
                step_y = 0
            else:
                step_x = 0
                step_y = int(np.sign(dy))
            return self._move_relative(step_x, step_y, world)

        # Bias movement towards unexplored directions
        dx = np.random.randint(-1, 2)
        dy = np.random.randint(-1, 2)
        if dx == 0 and dy == 0:
            dx = 1

        return self._move_relative(dx, dy, world)

    def guard(self, world) -> bool:
        """
        Guard current position/shelter. Just stands still and watches.
        Provides a small energy recovery bonus.
        """
        if not self.is_alive:
            return False

        self.energy = min(self.max_energy, self.energy + ENERGY_REST_RECOVERY * 0.5)
        return True
    
    def update_animation(self) -> None:
        """Update animation state each tick."""
        self.animation.update()
    
    def get_emotion_state(self) -> str:
        """Get current emotion state for rendering."""
        fear_level = 0.0
        if self.brain and hasattr(self.brain, 'fear_memory'):
            fear_level = self.brain.fear_memory.fear_level
        
        if fear_level > 0.6:
            return "fear"
        elif self.hunger > self.max_hunger * 0.7 or self.thirst > self.max_thirst * 0.7:
            return "searching"
        elif self.energy > self.max_energy * 0.8 and self.hunger < self.max_hunger * 0.3:
            return "happy"
        else:
            return "normal"
    
    def record_danger_experience(self, danger_type: str = "unknown") -> None:
        """Record a dangerous event for fear conditioning."""
        if self.brain and hasattr(self.brain, 'fear_memory'):
            tick = getattr(self, '_current_tick', 0)
            self.brain.fear_memory.register_danger(self.x, self.y, tick)

    def get_organism_state_color(self) -> Tuple[int, int, int]:
        """
        Get the display color based on the organism's current state.
        """
        from config import (
            COLOR_ORGANISM_HEALTHY, COLOR_ORGANISM_HUNGRY,
            COLOR_ORGANISM_THIRSTY, COLOR_ORGANISM_DYING, COLOR_ORGANISM_OLD,
        )

        if self.health < self.max_health * 0.3:
            return COLOR_ORGANISM_DYING
        if self.hunger < self.max_hunger * 0.3:
            return COLOR_ORGANISM_HUNGRY
        if self.thirst < self.max_thirst * 0.3:
            return COLOR_ORGANISM_THIRSTY
        if self.age > self.max_age_ticks * 0.7:
            return COLOR_ORGANISM_OLD
        return COLOR_ORGANISM_HEALTHY

    def get_status_string(self) -> str:
        """Get a short status description of the organism."""
        if not self.is_alive:
            return "Мёртв"
        parts = []
        if self.hunger < self.max_hunger * 0.3:
            parts.append("Голоден")
        if self.thirst < self.max_thirst * 0.3:
            parts.append("Хочет пить")
        if self.energy < self.max_energy * 0.2:
            parts.append("Устал")
        if self.health < self.max_health * 0.3:
            parts.append("При смерти")
        if not parts:
            parts.append("Здоров")
        return ", ".join(parts)

    def get_life_stats(self) -> dict:
        """Get comprehensive life statistics for display."""
        return {
            "Возраст": f"{self.age} тиков",
            "Здоровье": f"{self.health:.1f}/{self.max_health:.0f}",
            "Сытость": f"{self.hunger:.1f}/{self.max_hunger:.0f}",
            "Жажда": f"{self.thirst:.1f}/{self.max_thirst:.0f}",
            "Энергия": f"{self.energy:.1f}/{self.max_energy:.0f}",
            "Ресурсы": f"{self.resources:.1f}/{self.max_resources:.0f}",
            "Поколение": str(self.generation),
            "Дети": str(self.children_count),
            "Пройдено": f"{self.total_distance_traveled:.0f} клеток",
            "Исследовано": str(len(self.cells_visited)),
            "Построек": str(self.buildings_made),
            "Всего еды": f"{self.total_food_eaten:.0f}",
            "Всего воды": f"{self.total_water_drunk:.0f}",
            "Скорость": f"{self.speed:.2f}",
            "Зрение": str(self.sight_radius),
        }

    def get_last_actions_str(self, count: int = 5) -> List[str]:
        """Get string representation of last actions."""
        from config import ACTION_NAMES
        events = self.memory.get_recent_events(count)
        result = []
        for e in events:
            result.append(f"[{e['tick']}] {e['type']}: {e['details']}")
        # If no events, show last action
        if not result and self.last_action >= 0:
            result.append(ACTION_NAMES[self.last_action])
        return result

    def die(self, tick: int, reason: str = "unknown") -> None:
        """Mark the organism as dead."""
        self.is_alive = False
        self.memory.add_event(MEMORY_EVENT_DEATH, tick, f"Смерть: {reason}")