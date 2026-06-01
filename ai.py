"""
AI module for the Digital Organism Simulator.
Advanced Q-learning with fear conditioning, danger awareness, and curiosity.

Искусственный интеллект — Q-обучение со страхом, опасностью и любопытством.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from config import (
    ACTION_COUNT, LEARNING_RATE, DISCOUNT_FACTOR,
    EXPLORATION_RATE_INITIAL, EXPLORATION_RATE_MIN, EXPLORATION_DECAY,
    ACTION_MOVE_UP, ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT,
    ACTION_EAT, ACTION_DRINK, ACTION_REST, ACTION_COLLECT,
    ACTION_BUILD, ACTION_REPRODUCE, ACTION_EXPLORE, ACTION_GUARD,
    ACTION_NAMES,
    REWARD_EAT, REWARD_DRINK, REWARD_REST,
    REWARD_COLLECT_RESOURCE, REWARD_BUILD, REWARD_REPRODUCE,
    REWARD_EXPLORE_NEW, REWARD_SURVIVE_TICK, REWARD_FIND_FOOD, REWARD_FIND_WATER,
    REWARD_GROW_RESOURCES,
    REWARD_PENALTY_HUNGER, REWARD_PENALTY_THIRST,
    REWARD_PENALTY_INACTIVITY, REWARD_PENALTY_DEATH, REWARD_PENALTY_DAMAGE,
)

# State space bins
NUM_HUNGER_BINS = 5
NUM_THIRST_BINS = 5
NUM_ENERGY_BINS = 5
NUM_HEALTH_BINS = 5
NUM_BINARY_BINS = 2

# Fear system constants
FEAR_LEARNING_RATE = 0.15  # How fast fear associations form
FEAR_DECAY = 0.995         # Fear decays slowly over time
MAX_FEAR = 1.0
DANGER_MEMORY_SIZE = 30    # Remember last N danger events


class FearMemory:
    """
    Tracks fear associations with positions and situations.
    Organisms learn to avoid dangerous areas and situations.
    """

    def __init__(self):
        self.danger_positions: Dict[Tuple[int, int], float] = {}  # pos -> fear level
        self.danger_times: List[int] = []  # ticks when danger occurred
        self.fear_level: float = 0.0       # current overall fear
        self.last_danger_tick: int = -100  # when last danger was experienced
        self.safe_shelters: Dict[Tuple[int, int], float] = {}  # shelter -> safety level

    def register_danger(self, x: int, y: int, tick: int) -> None:
        """Associate a position with danger."""
        key = (x, y)
        self.danger_positions[key] = self.danger_positions.get(key, 0.0) + FEAR_LEARNING_RATE
        self.danger_positions[key] = min(MAX_FEAR, self.danger_positions[key])
        self.fear_level = min(MAX_FEAR, self.fear_level + FEAR_LEARNING_RATE)
        self.last_danger_tick = tick
        self.danger_times.append(tick)
        if len(self.danger_times) > DANGER_MEMORY_SIZE:
            self.danger_times.pop(0)

    def register_safety(self, x: int, y: int) -> None:
        """Register a safe position (near shelter, etc)."""
        key = (x, y)
        self.safe_shelters[key] = self.safe_shelters.get(key, 0.0) + 0.1
        # Reduce fear near safety
        if key in self.danger_positions:
            self.danger_positions[key] = max(0, self.danger_positions[key] - 0.05)

    def get_position_danger(self, x: int, y: int) -> float:
        """Get danger level of a position (considering nearby positions too)."""
        max_danger = 0.0
        for (dx, dy), fear in self.danger_positions.items():
            dist = abs(x - dx) + abs(y - dy)
            if dist <= 3:  # Within 3 cells
                contribution = fear * (1.0 - dist / 3.0)
                max_danger = max(max_danger, contribution)
        return max_danger

    def update(self) -> None:
        """Decay fear over time."""
        self.fear_level *= FEAR_DECAY
        # Decay specific position fears
        keys_to_decay = list(self.danger_positions.keys())
        for key in keys_to_decay:
            self.danger_positions[key] *= FEAR_DECAY
            if self.danger_positions[key] < 0.01:
                del self.danger_positions[key]


class QLearningBrain:
    """
    Q-learning with fear conditioning and adaptive exploration.
    Organisms learn not just rewards but also fear of danger.
    """

    def __init__(self, intelligence: float = 1.0, organism_id: int = 0):
        self.organism_id: int = organism_id
        self.intelligence: float = intelligence

        # Q-table
        self.q_table: Dict[int, np.ndarray] = {}

        # Learning parameters
        self.learning_rate: float = LEARNING_RATE * intelligence
        self.discount_factor: float = DISCOUNT_FACTOR
        self.exploration_rate: float = EXPLORATION_RATE_INITIAL

        # State tracking
        self.last_state_hash: Optional[int] = None
        self.last_action: Optional[int] = None
        self.last_reward: float = 0.0

        # Statistics
        self.total_reward: float = 0.0
        self.action_counts: np.ndarray = np.zeros(ACTION_COUNT, dtype=int)
        self.decisions_made: int = 0

        # Fear system
        self.fear_memory = FearMemory()
        self.curiosity_bonus: float = 0.1  # reward bonus for exploring new cells

        # Strategy discovery
        self.strategies_discovered: set = set()
        self.strategy_markers: Dict[str, bool] = {
            "food_search": False, "water_search": False, "exploration": False,
            "resource_collection": False, "building": False, "reproduction": False,
            "territory_defense": False, "resting": False, "danger_avoidance": False,
            "shelter_seeking": False,
        }

        # Learning progress tracking
        self.recent_rewards: List[float] = []
        self.learning_progress: float = 0.0

    def _discretize(self, value: float, max_val: float, bins: int) -> int:
        if max_val <= 0:
            return 0
        normalized = min(1.0, max(0.0, value / max_val))
        return min(bins - 1, int(normalized * bins))

    def _get_state_hash(self, organism_state: dict) -> int:
        """Convert state to hash - includes fear state now."""
        hunger_bin = self._discretize(
            organism_state.get("hunger", 0), organism_state.get("max_hunger", 100), NUM_HUNGER_BINS)
        thirst_bin = self._discretize(
            organism_state.get("thirst", 0), organism_state.get("max_thirst", 100), NUM_THIRST_BINS)
        energy_bin = self._discretize(
            organism_state.get("energy", 0), organism_state.get("max_energy", 100), NUM_ENERGY_BINS)
        health_bin = self._discretize(
            organism_state.get("health", 0), organism_state.get("max_health", 100), NUM_HEALTH_BINS)
        food_nearby = 1 if organism_state.get("food_nearby", False) else 0
        water_nearby = 1 if organism_state.get("water_nearby", False) else 0
        resource_nearby = 1 if organism_state.get("resource_nearby", False) else 0
        shelter_nearby = 1 if organism_state.get("shelter_nearby", False) else 0
        is_daytime = 1 if organism_state.get("is_daytime", True) else 0
        danger_nearby = 1 if organism_state.get("danger_nearby", False) else 0

        hash_val = (
            hunger_bin +
            thirst_bin * NUM_HUNGER_BINS +
            energy_bin * NUM_HUNGER_BINS * NUM_THIRST_BINS +
            health_bin * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS +
            food_nearby * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS +
            water_nearby * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS * 2 +
            resource_nearby * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS * 4 +
            shelter_nearby * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS * 8 +
            is_daytime * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS * 16 +
            danger_nearby * NUM_HUNGER_BINS * NUM_THIRST_BINS * NUM_ENERGY_BINS * NUM_HEALTH_BINS * 32
        )
        return hash_val

    def _get_q_values(self, state_hash: int) -> np.ndarray:
        if state_hash not in self.q_table:
            self.q_table[state_hash] = np.random.uniform(0, 0.1, ACTION_COUNT).astype(np.float64)
        return self.q_table[state_hash]

    def choose_action(self, organism_state: dict) -> int:
        """Choose action with fear-modulated exploration and danger avoidance."""
        state_hash = self._get_state_hash(organism_state)
        q_values = self._get_q_values(state_hash)

        # Apply fear penalty to certain actions
        fear = self.fear_memory.fear_level
        danger_nearby = organism_state.get("danger_nearby", False)

        # Reduce value of actions that would lead to danger
        if danger_nearby and fear > 0.3:
            # Penalize staying still (GUARD) when danger is near - encourage fleeing
            q_values[ACTION_GUARD] -= fear * 5.0
            # Boost movement away from danger
            q_values[ACTION_MOVE_UP] += fear * 2.0
            q_values[ACTION_MOVE_DOWN] += fear * 2.0
            q_values[ACTION_MOVE_LEFT] += fear * 2.0
            q_values[ACTION_MOVE_RIGHT] += fear * 2.0

        # When very hungry, boost eat action
        hunger_ratio = organism_state.get("hunger", 100) / max(1, organism_state.get("max_hunger", 100))
        if hunger_ratio < 0.3:
            q_values[ACTION_EAT] += 5.0
            q_values[ACTION_EXPLORE] += 2.0  # explore to find food

        # When very thirsty, boost drink action
        thirst_ratio = organism_state.get("thirst", 100) / max(1, organism_state.get("max_thirst", 100))
        if thirst_ratio < 0.3:
            q_values[ACTION_DRINK] += 5.0

        # When tired, boost rest
        energy_ratio = organism_state.get("energy", 100) / max(1, organism_state.get("max_energy", 100))
        if energy_ratio < 0.2:
            q_values[ACTION_REST] += 5.0

        # Curiosity: explore new areas
        if organism_state.get("can_explore", True):
            q_values[ACTION_EXPLORE] += self.curiosity_bonus

        # Adaptive exploration rate
        if self.decisions_made > 100:
            self.exploration_rate = max(
                EXPLORATION_RATE_MIN,
                self.exploration_rate * EXPLORATION_DECAY
            )

        # Epsilon-greedy
        if np.random.random() < self.exploration_rate:
            # Smart exploration: prefer actions not tried often
            action_probs = 1.0 / (1.0 + self.action_counts.astype(float))
            action_probs = action_probs / action_probs.sum()
            action = int(np.random.choice(ACTION_COUNT, p=action_probs))
        else:
            max_q = np.max(q_values)
            best_actions = np.where(q_values == max_q)[0]
            action = int(np.random.choice(best_actions))

        self.action_counts[action] += 1
        self.decisions_made += 1
        self.last_state_hash = state_hash
        self.last_action = action

        return action

    def learn(self, reward: float, next_organism_state: dict) -> None:
        """Learn from action outcome with fear conditioning."""
        if self.last_state_hash is None or self.last_action is None:
            return

        # Apply fear modulation to reward
        fear = self.fear_memory.fear_level
        if fear > 0.5:
            reward *= (1.0 - fear * 0.3)  # Fear reduces perceived reward

        # Update Q-values
        q_values = self._get_q_values(self.last_state_hash)
        next_state_hash = self._get_state_hash(next_organism_state)
        next_q_values = self._get_q_values(next_state_hash)
        max_next_q = float(np.max(next_q_values))
        current_q = float(q_values[self.last_action])

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[self.last_state_hash][self.last_action] = new_q

        self.total_reward += reward
        self.last_reward = reward

        # Track recent rewards for progress
        self.recent_rewards.append(reward)
        if len(self.recent_rewards) > 50:
            self.recent_rewards.pop(0)
        if len(self.recent_rewards) > 0:
            self.learning_progress = sum(self.recent_rewards) / len(self.recent_rewards)

        # Update fear memory
        self.fear_memory.update()

        # Check strategy discovery
        self._check_strategy_discovery(reward)

    def _check_strategy_discovery(self, reward: float) -> None:
        """Track discovered strategies."""
        if self.last_action is None:
            return
        action = self.last_action
        if self.last_state_hash is None or self.last_state_hash not in self.q_table:
            q_values = np.zeros(ACTION_COUNT)
        else:
            q_values = self.q_table[self.last_state_hash]

        threshold = 3.0
        if action == ACTION_EAT and q_values[ACTION_EAT] > threshold:
            self.strategies_discovered.add("Поиск еды 🍎")
        if action == ACTION_DRINK and q_values[ACTION_DRINK] > threshold:
            self.strategies_discovered.add("Поиск воды 💧")
        if action == ACTION_EXPLORE and q_values[ACTION_EXPLORE] > threshold:
            self.strategies_discovered.add("Исследование 🔍")
        if action == ACTION_COLLECT and q_values[ACTION_COLLECT] > threshold:
            self.strategies_discovered.add("Сбор ресурсов ⛏️")
        if action == ACTION_BUILD and q_values[ACTION_BUILD] > threshold:
            self.strategies_discovered.add("Строительство 🏠")
        if action == ACTION_REPRODUCE and q_values[ACTION_REPRODUCE] > threshold:
            self.strategies_discovered.add("Размножение ❤️")
        if action == ACTION_REST and q_values[ACTION_REST] > threshold:
            self.strategies_discovered.add("Отдых 😴")

        # Danger avoidance discovered when fear is high and fleeing was chosen
        if self.fear_memory.fear_level > 0.5:
            self.strategies_discovered.add("Избегание опасности ⚠️")

        # Shelter seeking
        if action == ACTION_GUARD and q_values[ACTION_GUARD] > threshold:
            self.strategies_discovered.add("Охрана территории 🛡️")

    def get_strategies_discovered(self) -> List[str]:
        return list(self.strategies_discovered)

    def get_avg_q_value(self) -> float:
        if not self.q_table:
            return 0.0
        total = 0.0
        count = 0
        for q_vals in self.q_table.values():
            total += float(np.mean(q_vals))
            count += 1
        return total / count if count > 0 else 0.0

    def get_q_table_size(self) -> int:
        return len(self.q_table)


def compute_reward(
    organism_state: dict,
    action: int,
    action_result: dict
) -> float:
    """
    Compute reward with emotional valence - positive for achievements,
    strongly negative for pain/danger.
    """
    reward = REWARD_SURVIVE_TICK

    # Positive rewards
    if action_result.get("ate", False):
        reward += REWARD_EAT
    if action_result.get("drank", False):
        reward += REWARD_DRINK
    if action_result.get("rested", False):
        reward += REWARD_REST
    if action_result.get("collected", False):
        reward += REWARD_COLLECT_RESOURCE
    if action_result.get("built", False):
        reward += REWARD_BUILD
    if action_result.get("reproduced", False):
        reward += REWARD_REPRODUCE * 2  # Big reward for reproduction!
    if action_result.get("found_food", False):
        reward += REWARD_FIND_FOOD
    if action_result.get("found_water", False):
        reward += REWARD_FIND_WATER
    if action_result.get("explored_new", False):
        reward += REWARD_EXPLORE_NEW

    # Pain/negative rewards
    hunger = organism_state.get("hunger", 100)
    max_hunger = organism_state.get("max_hunger", 100)
    thirst = organism_state.get("thirst", 100)
    max_thirst = organism_state.get("max_thirst", 100)

    if max_hunger > 0:
        hunger_ratio = hunger / max_hunger
        if hunger_ratio < 0.3:
            reward += REWARD_PENALTY_HUNGER * (1.0 - hunger_ratio / 0.3)
        if hunger_ratio < 0.1:
            reward += REWARD_PENALTY_HUNGER * 3  # Extreme hunger pain!

    if max_thirst > 0:
        thirst_ratio = thirst / max_thirst
        if thirst_ratio < 0.3:
            reward += REWARD_PENALTY_THIRST * (1.0 - thirst_ratio / 0.3)
        if thirst_ratio < 0.1:
            reward += REWARD_PENALTY_THIRST * 3  # Extreme thirst pain!

    # Danger penalty
    if action_result.get("was_injured", False):
        reward += REWARD_PENALTY_DAMAGE

    # Inactivity penalty
    if action_result.get("was_inactive", False):
        reward += REWARD_PENALTY_INACTIVITY

    # Night fear (mild discomfort when alone at night)
    if not organism_state.get("is_daytime", True) and not organism_state.get("shelter_nearby", False):
        reward -= 0.5  # Unease at night without shelter

    return reward