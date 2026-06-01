"""
Simulation module for the Digital Organism Simulator.
Main game loop that ties together world, organisms, AI, evolution, and rendering.

Симуляция — главный игровой цикл, связывающий все модули.
"""

import time
import logging
from typing import List, Optional, Tuple
import numpy as np

from config import (
    INITIAL_POPULATION, MAX_POPULATION,
    ACTION_NAMES, ACTION_COUNT,
    ACTION_MOVE_UP, ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT,
    ACTION_EAT, ACTION_DRINK, ACTION_REST, ACTION_COLLECT,
    ACTION_BUILD, ACTION_REPRODUCE, ACTION_EXPLORE, ACTION_GUARD,
    MEMORY_EVENT_FOOD, MEMORY_EVENT_WATER, MEMORY_EVENT_BUILD,
    MEMORY_EVENT_BIRTH, MEMORY_EVENT_DANGER, MEMORY_EVENT_RESOURCE,
    LOG_FILE, WORLD_WIDTH, WORLD_HEIGHT,
)

from world import World, WorldCell
from genetics import Genome
from organism import Organism
from ai import QLearningBrain, compute_reward
from evolution import EvolutionTracker


class Simulation:
    """
    Main simulation controller.
    Manages the update loop, organism interactions, and coordinates all modules.
    """

    def __init__(self):
        # Initialize core components
        self.world = World()
        self.organisms: List[Organism] = []
        self.evolution_tracker = EvolutionTracker()
        self.tick_count: int = 0
        self.is_running: bool = True
        self.is_paused: bool = False
        self.tick_rate: int = 10  # ticks per second

        # Setup logging
        self._setup_logging()

        # Create initial population
        self._initialize_population()

        # Pending offspring (created during tick, added at end)
        self.pending_offspring: List[Organism] = []

        # Track which cells have organisms (collision avoidance)
        self.occupied_cells: set = set()

        # Performance tracking
        self.last_update_time: float = time.time()
        self.accumulated_time: float = 0.0

    def _setup_logging(self) -> None:
        """Configure logging to both file and console."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler() if __debug__ else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_population(self) -> None:
        """Create the initial population of organisms."""
        self.logger.info("Создание начальной популяции...")
        for i in range(INITIAL_POPULATION):
            # Get random position
            x, y = self.world.get_random_walkable_cell()

            # Create genome
            genome = Genome()

            # Create organism
            organism = Organism(
                x=x, y=y,
                genome=genome,
                generation=1,
                parent_ids=None
            )

            # Create AI brain
            organism.brain = QLearningBrain(
                intelligence=organism.intelligence,
                organism_id=organism.uid
            )

            self.organisms.append(organism)
            self.evolution_tracker.register_birth(organism)

        self.logger.info(f"Создано {INITIAL_POPULATION} организмов")

    def update(self) -> None:
        """
        Perform one simulation tick.
        Updates world, all organisms, AI, and evolution.
        """
        if self.is_paused or not self.is_running:
            return

        self.tick_count += 1

        # 1. Update world (resources, time, seasons)
        self.world.update()

        # 2. Update organism internal states
        for org in self.organisms:
            if not org.is_alive:
                continue

            state_update = org.update_state(self.tick_count, {})
            if "died" in state_update:
                self._handle_death(org, state_update.get("reason", "unknown"))
                continue

            # Update animation
            org.update_animation()
            
            # Update perception
            org.update_perception(self.world)

        # 3. Process AI decisions and actions
        self._process_ai_decisions()

        # 4. Natural selection pressure
        self.evolution_tracker.natural_selection(self.organisms)

        # 5. Cull population if too large
        self.evolution_tracker.cull_population(self.organisms)

        # 6. Add pending offspring
        for child in self.pending_offspring:
            self.organisms.append(child)
        self.pending_offspring.clear()

        # 7. Remove dead organisms (keep them for stats, but mark as dead)
        # Dead organisms stay in the list for statistics but are ignored by logic

        # 8. Update evolution stats
        if self.tick_count % 50 == 0:  # Update stats every 50 ticks
            self.evolution_tracker.update(self.organisms)

        # 9. Log periodic summary
        if self.tick_count % 200 == 0:
            alive = sum(1 for o in self.organisms if o.is_alive)
            self.logger.info(
                f"Тик {self.tick_count}: {alive} живых, "
                f"поколение {self.evolution_tracker.current_generation}, "
                f"сезон {self.world.get_season_name()}"
            )

    def _process_ai_decisions(self) -> None:
        """Process AI decision-making for all alive organisms."""
        for org in self.organisms:
            if not org.is_alive:
                continue

            # Refresh survival goals before choosing actions
            self._refresh_target_goals(org)

            # Get current state
            state = org.get_state_for_ai(self.world)

            # If organism has an active target, prefer moving toward it
            action = self._action_for_active_target(org)
            if action is None:
                if org.brain:
                    action = org.brain.choose_action(state)
                else:
                    # Fallback: random action if no brain
                    action = np.random.randint(0, ACTION_COUNT)

            org.last_action = action

            # Execute action and get result
            result = self._execute_action(org, action)

            # Calculate reward
            reward = compute_reward(state, action, result)

            # Learn from the action
            if org.brain:
                next_state = org.get_state_for_ai(self.world)
                org.brain.learn(reward, next_state)

            # Store result for display
            org.last_action_result = result

    def _refresh_target_goals(self, organism: Organism) -> None:
        """Set or refresh target goals for hunger, thirst, and resource needs."""
        if organism.current_target is not None and organism.current_goal is not None:
            return

        if organism.hunger < organism.max_hunger * 0.7:
            food_pos = self.world.find_nearest_food(organism.x, organism.y, max_dist=25)
            if food_pos is not None:
                organism.current_target = food_pos
                organism.current_goal = "eat"
                return

        if organism.thirst < organism.max_thirst * 0.7:
            water_pos = self.world.find_nearest_water(organism.x, organism.y, max_dist=25)
            if water_pos is not None:
                organism.current_target = water_pos
                organism.current_goal = "drink"
                return

        if organism.resource_nearby and organism.current_goal is None:
            resource_pos = self.world.find_nearest_of_type(organism.x, organism.y, 7, max_dist=20)
            if resource_pos is not None:
                organism.current_target = resource_pos
                organism.current_goal = "collect"
                return

    def _action_for_active_target(self, organism: Organism) -> int | None:
        """Translate an active target goal into a movement action."""
        if organism.current_target is None or organism.current_goal is None:
            return None

        tx, ty = organism.current_target
        if organism.x == tx and organism.y == ty:
            organism.current_target = None
            organism.current_goal = None
            return None

        dx = tx - organism.x
        dy = ty - organism.y
        if abs(dx) >= abs(dy):
            return ACTION_MOVE_RIGHT if dx > 0 else ACTION_MOVE_LEFT
        return ACTION_MOVE_DOWN if dy > 0 else ACTION_MOVE_UP

    def _execute_action(self, organism: Organism, action: int) -> dict:
        """
        Execute an action for an organism.
        Returns a dict describing the result of the action.
        """
        result = {
            "ate": False,
            "drank": False,
            "rested": False,
            "collected": False,
            "built": False,
            "reproduced": False,
            "found_food": False,
            "found_water": False,
            "explored_new": False,
            "was_inactive": False,
        }

        if action == ACTION_MOVE_UP:
            moved = organism._move_relative(0, -1, self.world)
            if not moved:
                result["was_inactive"] = True

        elif action == ACTION_MOVE_DOWN:
            moved = organism._move_relative(0, 1, self.world)
            if not moved:
                result["was_inactive"] = True

        elif action == ACTION_MOVE_LEFT:
            moved = organism._move_relative(-1, 0, self.world)
            if not moved:
                result["was_inactive"] = True

        elif action == ACTION_MOVE_RIGHT:
            moved = organism._move_relative(1, 0, self.world)
            if not moved:
                result["was_inactive"] = True

        elif action == ACTION_EAT:
            organism.wake_up()
            ate = organism.eat(self.world)
            result["ate"] = ate
            if ate:
                organism.current_target = None
                organism.current_goal = None
            else:
                # Try to find food if none nearby
                food_pos = self.world.find_nearest_food(
                    organism.x, organism.y, max_dist=15
                )
                if food_pos:
                    organism.current_target = food_pos
                    organism.current_goal = "eat"
                    result["found_food"] = True
                else:
                    result["was_inactive"] = True

        elif action == ACTION_DRINK:
            organism.wake_up()
            drank = organism.drink(self.world)
            result["drank"] = drank
            if drank:
                organism.current_target = None
                organism.current_goal = None
            else:
                water_pos = self.world.find_nearest_water(
                    organism.x, organism.y, max_dist=15
                )
                if water_pos:
                    organism.current_target = water_pos
                    organism.current_goal = "drink"
                    result["found_water"] = True
                else:
                    result["was_inactive"] = True

        elif action == ACTION_REST:
            rested = organism.rest()
            result["rested"] = rested

        elif action == ACTION_COLLECT:
            organism.wake_up()
            collected = organism.collect_resources(self.world)
            result["collected"] = collected
            if collected:
                organism.current_target = None
                organism.current_goal = None
            else:
                # Try to find resources
                resource_pos = None
                for terrain_type in [2, 5, 7]:  # TREE, STONE, RESOURCE
                    resource_pos = self.world.find_nearest_of_type(
                        organism.x, organism.y, terrain_type, max_dist=15
                    )
                    if resource_pos:
                        break
                if resource_pos:
                    organism.current_target = resource_pos
                    organism.current_goal = "collect"
                else:
                    result["was_inactive"] = True

        elif action == ACTION_BUILD:
            organism.wake_up()
            built = organism.build_shelter(self.world)
            result["built"] = built
            if built:
                self.evolution_tracker.register_building(
                    organism, self.tick_count
                )
                self.logger.info(
                    f"Организм #{organism.uid} построил убежище "
                    f"в ({organism.x}, {organism.y})"
                )

        elif action == ACTION_REPRODUCE:
            organism.wake_up()

            # Try to find a mate nearby
            mate = self._find_mate(organism)

            # Attempt reproduction
            child = organism.reproduce(self.world, partner=mate)
            if child:
                # Create AI brain for child
                child.brain = QLearningBrain(
                    intelligence=child.intelligence,
                    organism_id=child.uid
                )

                self.pending_offspring.append(child)
                self.evolution_tracker.register_birth(child)

                method = "половое" if mate else "бесполое"
                self.evolution_tracker.register_reproduction(
                    organism, child, self.tick_count, method
                )

                # Check for new strategies
                if organism.brain:
                    organism.brain.strategies_discovered.add("Размножение")

                result["reproduced"] = True

                self.logger.info(
                    f"Рождение #{child.uid} (поколение {child.generation}), "
                    f"родитель #{organism.uid}, метод: {method}"
                )
            else:
                result["was_inactive"] = True

        elif action == ACTION_EXPLORE:
            organism.wake_up()
            explored = organism.explore(self.world)
            # Check if exploring revealed new cells
            if organism.explored_cells > 0:
                result["explored_new"] = True
            if not explored:
                result["was_inactive"] = True

        elif action == ACTION_GUARD:
            organism.wake_up()
            guarded = organism.guard(self.world)
            result["rested"] = guarded

        else:
            result["was_inactive"] = True

        return result

    def _find_mate(self, organism: Organism) -> Optional[Organism]:
        """Find a nearby mate for reproduction."""
        if not organism.is_mature:
            return None

        for other in self.organisms:
            if other is organism or not other.is_alive:
                continue
            if not other.is_mature:
                continue
            if other.reproduction_cooldown > 0:
                continue
            if other.energy < 30:
                continue

            # Check distance
            dist = abs(other.x - organism.x) + abs(other.y - organism.y)
            if dist <= organism.sight_radius:
                return other

        return None

    def _handle_death(self, organism: Organism, reason: str) -> None:
        """Handle the death of an organism."""
        if not organism.is_alive:
            return

        organism.die(self.tick_count, reason)
        self.evolution_tracker.register_death(
            organism, self.tick_count, reason
        )

        # Penalty for the AI
        if organism.brain:
            state = {
                "hunger": 0, "max_hunger": 100,
                "thirst": 0, "max_thirst": 100,
                "energy": 0, "max_energy": 100,
                "health": 0, "max_health": 100,
                "food_nearby": False, "water_nearby": False,
                "resource_nearby": False, "shelter_nearby": False,
                "mate_nearby": False,
                "is_daytime": True, "age": 0, "is_mature": False,
                "can_reproduce": False, "is_near_shelter": False,
                "resources": 0, "max_resources": 100, "season": 0,
            }
            organism.brain.learn(-50.0, state)

    def get_alive_organisms(self) -> List[Organism]:
        """Get list of alive organisms."""
        return [o for o in self.organisms if o.is_alive]

    def get_stats(self) -> dict:
        """Get comprehensive simulation statistics."""
        alive = self.get_alive_organisms()
        world_stats = self.world.get_stats()
        evo_stats = self.evolution_tracker.get_summary_stats()

        return {
            **world_stats,
            **evo_stats,
            "alive_count": len(alive),
            "total_organisms": len(self.organisms),
            "tick_rate": self.tick_rate,
        }

    def set_paused(self, paused: bool) -> None:
        """Set the pause state."""
        self.is_paused = paused

    def set_tick_rate(self, rate: int) -> None:
        """Set the simulation tick rate."""
        self.tick_rate = max(1, min(100, rate))

    def select_organism(self, organism: Optional[Organism]) -> None:
        """Select an organism for detailed inspection."""
        if organism and organism.is_alive:
            # Center camera on selected organism
            pass  # Camera centering handled by renderer

    def cleanup(self) -> None:
        """Cleanup simulation resources."""
        self.logger.info("Симуляция завершена")
        logging.shutdown()