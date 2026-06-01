"""
Enhanced AI behaviors - better learning, emotional responses, and decision making.
Organisms learn realistic behaviors from experience.

Улучшенный ИИ — лучшее обучение, эмоции, реалистичное поведение.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from config import (
    ACTION_MOVE_UP, ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT,
    ACTION_EAT, ACTION_DRINK, ACTION_REST, ACTION_BUILD, ACTION_REPRODUCE,
    WORLD_WIDTH, WORLD_HEIGHT,
)


class EmotionalState:
    """Tracks emotional state of organism - affects decision making."""
    
    def __init__(self):
        self.fear_level: float = 0.0
        self.hunger_stress: float = 0.0
        self.thirst_stress: float = 0.0
        self.curiosity: float = 0.5
        self.contentment: float = 0.5
        
    def update(self, hunger: float, thirst: float, health: float,
               max_hunger: float, max_thirst: float, max_health: float) -> None:
        """Update emotional state based on physical needs."""
        # Hunger and thirst stress
        self.hunger_stress = max(0.0, min(1.0, hunger / max_hunger))
        self.thirst_stress = max(0.0, min(1.0, thirst / max_thirst))
        
        # Contentment depends on being fed and healthy
        fed_level = 1.0 - self.hunger_stress
        hydrated_level = 1.0 - self.thirst_stress
        health_level = health / max_health
        
        self.contentment = (fed_level + hydrated_level + health_level) / 3.0
        
        # Curiosity increases when content, decreases when stressed
        stress = (self.hunger_stress + self.thirst_stress) / 2.0
        self.curiosity = 0.3 + self.contentment * 0.7 - stress * 0.5
        self.curiosity = max(0.0, min(1.0, self.curiosity))
    
    def get_emotion_name(self) -> str:
        """Get a name for current emotional state."""
        if self.fear_level > 0.6:
            return "fear"
        elif self.hunger_stress > 0.7 or self.thirst_stress > 0.7:
            return "searching"
        elif self.contentment > 0.7:
            return "happy"
        else:
            return "normal"


class MemoryBank:
    """Stores learned information about the world."""
    
    def __init__(self, max_memories: int = 100):
        self.good_locations: Dict[Tuple[int, int], float] = {}  # pos -> value
        self.bad_locations: Dict[Tuple[int, int], float] = {}   # pos -> danger
        self.predator_sightings: List[Tuple[int, int, int]] = []  # (x, y, tick)
        self.shelter_locations: List[Tuple[int, int]] = []
        self.food_sources: List[Tuple[int, int, str]] = []  # (x, y, type)
        self.water_sources: List[Tuple[int, int]] = []
        self.max_memories = max_memories
        
    def add_good_location(self, x: int, y: int, value: float) -> None:
        """Remember a good location."""
        key = (x, y)
        self.good_locations[key] = max(self.good_locations.get(key, 0), value)
        if len(self.good_locations) > self.max_memories:
            # Remove least valuable
            min_key = min(self.good_locations.keys(),
                         key=lambda k: self.good_locations[k])
            del self.good_locations[min_key]
    
    def add_bad_location(self, x: int, y: int, danger: float) -> None:
        """Remember a dangerous location."""
        key = (x, y)
        self.bad_locations[key] = max(self.bad_locations.get(key, 0), danger)
        if len(self.bad_locations) > self.max_memories:
            # Remove oldest (least recent)
            min_key = list(self.bad_locations.keys())[0]
            del self.bad_locations[min_key]
    
    def is_location_familiar(self, x: int, y: int, radius: int = 5) -> bool:
        """Check if organism knows about this area."""
        for (lx, ly) in list(self.good_locations.keys()) + list(self.bad_locations.keys()):
            if abs(x - lx) <= radius and abs(y - ly) <= radius:
                return True
        return False
    
    def get_best_nearby_location(self, x: int, y: int, radius: int = 10) -> Optional[Tuple[int, int]]:
        """Find the best known location nearby."""
        best_loc = None
        best_value = -1
        
        for (lx, ly), value in self.good_locations.items():
            dist = abs(x - lx) + abs(y - ly)
            if dist <= radius:
                if value / (1 + dist * 0.1) > best_value:
                    best_value = value / (1 + dist * 0.1)
                    best_loc = (lx, ly)
        
        return best_loc


class SmartDecisionMaker:
    """Makes intelligent decisions based on state, emotion, and memory."""
    
    def __init__(self, intelligence: float = 0.5):
        self.intelligence = intelligence
        self.emotional_state = EmotionalState()
        self.memory = MemoryBank()
    
    def choose_action(self, org_state: Dict, visible_cells: List[Tuple[int, int, int]],
                      available_actions: List[int]) -> int:
        """
        Choose an action intelligently.
        
        Args:
            org_state: Dictionary with hunger, thirst, health, etc.
            visible_cells: List of (x, y, cell_type) visible to organism
            available_actions: List of action IDs that are available
        
        Returns:
            Chosen action ID
        """
        # Update emotional state
        self.emotional_state.update(
            org_state.get('hunger', 0),
            org_state.get('thirst', 0),
            org_state.get('health', 0),
            org_state.get('max_hunger', 100),
            org_state.get('max_thirst', 100),
            org_state.get('max_health', 100)
        )
        
        emotion = self.emotional_state.get_emotion_name()
        
        # Decision tree based on emotional state
        if emotion == "fear":
            return self._choose_fear_action(available_actions)
        elif emotion == "searching":
            return self._choose_search_action(org_state, visible_cells, available_actions)
        elif emotion == "happy":
            return self._choose_exploration_action(available_actions)
        else:
            return self._choose_normal_action(org_state, visible_cells, available_actions)
    
    def _choose_fear_action(self, available_actions: List[int]) -> int:
        """When afraid, seek shelter or hide."""
        movement_actions = [ACTION_MOVE_UP, ACTION_MOVE_DOWN, 
                           ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT]
        rest_actions = [ACTION_REST, ACTION_BUILD]
        
        # Prefer hiding in shelter
        if ACTION_REST in available_actions:
            return ACTION_REST
        
        # Otherwise move randomly
        move_opts = [a for a in available_actions if a in movement_actions]
        if move_opts:
            return np.random.choice(move_opts)
        
        return available_actions[0] if available_actions else 0
    
    def _choose_search_action(self, org_state: Dict, visible_cells: List,
                             available_actions: List[int]) -> int:
        """When hungry/thirsty, search actively for food/water."""
        from config import CELL_GRASS, CELL_BERRY_BUSH, CELL_WATER
        
        hunger = org_state.get('hunger', 0)
        thirst = org_state.get('thirst', 0)
        
        # Look for food in visible cells
        food_cells = [c for c in visible_cells 
                     if c[2] in (CELL_GRASS, CELL_BERRY_BUSH)]
        water_cells = [c for c in visible_cells if c[2] == CELL_WATER]
        
        # If hungry and food visible, go to food
        if hunger > thirst and food_cells:
            target = min(food_cells, 
                        key=lambda c: abs(c[0]) + abs(c[1]))
            return self._move_towards(target, available_actions)
        
        # If thirsty and water visible, go to water
        if thirst > hunger and water_cells:
            target = min(water_cells,
                        key=lambda c: abs(c[0]) + abs(c[1]))
            return self._move_towards(target, available_actions)
        
        # Otherwise move randomly (explore)
        movement_actions = [ACTION_MOVE_UP, ACTION_MOVE_DOWN,
                           ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT]
        move_opts = [a for a in available_actions if a in movement_actions]
        
        if move_opts:
            return np.random.choice(move_opts)
        
        return available_actions[0] if available_actions else 0
    
    def _choose_exploration_action(self, available_actions: List[int]) -> int:
        """When content and curious, explore new areas."""
        from config import ACTION_EXPLORE, ACTION_COLLECT, ACTION_BUILD, ACTION_REPRODUCE
        
        # Prefer exploring and building
        if ACTION_EXPLORE in available_actions:
            return ACTION_EXPLORE
        
        if ACTION_BUILD in available_actions and np.random.random() < 0.3:
            return ACTION_BUILD
        
        # Otherwise random movement
        movement_actions = [ACTION_MOVE_UP, ACTION_MOVE_DOWN,
                           ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT]
        move_opts = [a for a in available_actions if a in movement_actions]
        
        if move_opts:
            return np.random.choice(move_opts)
        
        return available_actions[0] if available_actions else 0
    
    def _choose_normal_action(self, org_state: Dict, visible_cells: List,
                             available_actions: List[int]) -> int:
        """Normal, balanced decision making."""
        from config import CELL_GRASS, CELL_BERRY_BUSH, CELL_WATER
        
        # Mix of searching and exploring
        if np.random.random() < 0.4:
            # Search for resources
            return self._choose_search_action(org_state, visible_cells, available_actions)
        else:
            # Explore
            return self._choose_exploration_action(available_actions)
    
    def _move_towards(self, target: Tuple[int, int, int],
                      available_actions: List[int]) -> int:
        """Move towards a target."""
        tx, ty, _ = target
        
        movement_map = {
            ACTION_MOVE_UP: (0, -1),
            ACTION_MOVE_DOWN: (0, 1),
            ACTION_MOVE_LEFT: (-1, 0),
            ACTION_MOVE_RIGHT: (1, 0),
        }
        
        best_action = None
        best_dist = float('inf')
        
        for action, (dx, dy) in movement_map.items():
            if action in available_actions:
                new_dist = abs(tx - dx) + abs(ty - dy)
                if new_dist < best_dist:
                    best_dist = new_dist
                    best_action = action
        
        if best_action is not None:
            return best_action
        
        return available_actions[0] if available_actions else 0


class FearLearningSystem:
    """Enhanced fear learning based on experiences."""
    
    def __init__(self):
        self.fear_associations: Dict[Tuple[int, int], float] = {}
        self.danger_events: List[Tuple[int, int, int, str]] = []  # (x, y, tick, danger_type)
        self.fear_decay_rate: float = 0.98
        
    def record_danger(self, x: int, y: int, tick: int,
                      danger_type: str = "unknown") -> None:
        """Record a dangerous event for fear conditioning."""
        key = (x, y)
        current_fear = self.fear_associations.get(key, 0.0)
        
        # Strengthen fear of this location
        self.fear_associations[key] = min(1.0, current_fear + 0.25)
        
        # Also fear nearby locations
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nearby_key = (x + dx, y + dy)
                if nearby_key != key:
                    nearby_fear = self.fear_associations.get(nearby_key, 0.0)
                    self.fear_associations[nearby_key] = min(1.0, nearby_fear + 0.1)
        
        self.danger_events.append((x, y, tick, danger_type))
    
    def update_fears(self) -> None:
        """Decay fears over time."""
        for key in self.fear_associations:
            self.fear_associations[key] *= self.fear_decay_rate
    
    def get_fear_level(self, x: int, y: int) -> float:
        """Get fear level for a location."""
        fear = 0.0
        
        # Direct fear
        if (x, y) in self.fear_associations:
            fear = max(fear, self.fear_associations[(x, y)])
        
        # Nearby fear
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nearby_key = (x + dx, y + dy)
                if nearby_key in self.fear_associations:
                    nearby_fear = self.fear_associations[nearby_key]
                    fear = max(fear, nearby_fear * 0.6)
        
        return min(1.0, fear)
