"""
Evolution module for the Digital Organism Simulator.
Manages population dynamics, natural selection, and evolutionary tracking.

Эволюция — управление популяцией, отбор, статистика поколений.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from config import (
    INITIAL_POPULATION, MAX_POPULATION,
    REWARD_PENALTY_DEATH,
)


class EvolutionTracker:
    """
    Tracks evolutionary metrics across generations.
    Records births, deaths, genetic diversity, and population trends.
    """

    def __init__(self):
        # Population tracking
        self.total_births: int = 0
        self.total_deaths: int = 0
        self.current_population: int = 0
        self.max_population_reached: int = 0

        # Generation tracking
        self.current_generation: int = 1
        self.generation_stats: List[Dict] = []  # stats per generation

        # Age tracking
        self.oldest_organism_age: int = 0
        self.oldest_organism_gen: int = 1

        # Intelligence tracking
        self.total_intelligence: float = 0.0
        self.average_intelligence: float = 0.0

        # Fitness tracking
        self.fitness_history: List[float] = []

        # Species/genetic diversity tracking
        self.genetic_diversity_history: List[float] = []

        # Strategy tracking across population
        self.strategy_prevalence: Dict[str, int] = defaultdict(int)

        # Event log
        self.events: List[str] = []

    def register_birth(self, organism) -> None:
        """Register a new birth."""
        self.total_births += 1
        self.current_population += 1
        if self.current_population > self.max_population_reached:
            self.max_population_reached = self.current_population

        if organism.generation > self.current_generation:
            self.current_generation = organism.generation

        self.total_intelligence += organism.intelligence

    def register_death(self, organism, tick: int, reason: str = "unknown") -> None:
        """Register a death."""
        self.total_deaths += 1
        self.current_population -= 1

        # Update oldest age
        if organism.age > self.oldest_organism_age:
            self.oldest_organism_age = organism.age
            self.oldest_organism_gen = organism.generation

        # Log event
        event = f"[Тик {tick}] Смерть #{organism.uid}: поколение {organism.generation}, возраст {organism.age}, причина: {reason}"
        self.events.append(event)

    def register_building(self, organism, tick: int) -> None:
        """Register a building event."""
        event = f"[Тик {tick}] Постройка: организм #{organism.uid} построил убежище"
        self.events.append(event)

    def register_reproduction(self, parent, child, tick: int, method: str = "половое") -> None:
        """Register a reproduction event."""
        event = (f"[Тик {tick}] Размножение: #{parent.uid} (поколение {parent.generation}) "
                 f"-> #{child.uid} (поколение {child.generation}), метод: {method}")
        self.events.append(event)

    def register_mutation(self, organism, gene_index: int, old_val: float, new_val: float, tick: int) -> None:
        """Register a mutation event."""
        event = (f"[Тик {tick}] Мутация: организм #{organism.uid}, "
                 f"ген {gene_index}: {old_val:.2f} -> {new_val:.2f}")
        self.events.append(event)

    def register_strategy(self, organism, strategy: str, tick: int) -> None:
        """Register a strategy discovery."""
        self.strategy_prevalence[strategy] += 1
        event = f"[Тик {tick}] Новая стратегия: организм #{organism.uid} открыл '{strategy}'"
        self.events.append(event)

    def update(self, organisms: List['Organism']) -> Dict:
        """
        Update statistics based on current population.
        Returns a summary dict of current stats.
        """
        alive = [o for o in organisms if o.is_alive]
        self.current_population = len(alive)

        if alive:
            # Average intelligence
            self.total_intelligence = sum(o.intelligence for o in alive)
            self.average_intelligence = self.total_intelligence / len(alive)

            # Average generation
            avg_generation = sum(o.generation for o in alive) / len(alive)

            # Count shelters built
            total_buildings = sum(o.buildings_made for o in alive)

            # Count children
            total_children = sum(o.children_count for o in alive)

            # Age stats
            ages = [o.age for o in alive]
            avg_age = sum(ages) / len(ages)

            # Genetic diversity (average pairwise difference)
            if len(alive) > 1:
                sample = alive[:min(20, len(alive))]  # limit sample size
                diffs = []
                for i in range(len(sample)):
                    for j in range(i + 1, len(sample)):
                        diffs.append(sample[i].genome.similarity(sample[j].genome))
                avg_similarity = sum(diffs) / len(diffs) if diffs else 1.0
            else:
                avg_similarity = 1.0

            # Collect generation stats
            gen_stats = {
                "generation": self.current_generation,
                "population": self.current_population,
                "average_intelligence": round(self.average_intelligence, 2),
                "average_age": round(avg_age, 1),
                "oldest_age": self.oldest_organism_age,
                "total_births": self.total_births,
                "total_deaths": self.total_deaths,
                "buildings": total_buildings,
                "children": total_children,
                "genetic_similarity": round(avg_similarity, 3),
                "total_buildings": total_buildings,
            }

        else:
            avg_similarity = 1.0
            gen_stats = {
                "generation": self.current_generation,
                "population": 0,
                "average_intelligence": 0,
                "average_age": 0,
                "oldest_age": self.oldest_organism_age,
                "total_births": self.total_births,
                "total_deaths": self.total_deaths,
                "buildings": 0,
                "children": 0,
                "genetic_similarity": 1.0,
                "total_buildings": 0,
            }

        self.generation_stats.append(gen_stats)
        self.genetic_diversity_history.append(avg_similarity)

        return gen_stats

    def get_summary_stats(self) -> Dict:
        """Get a comprehensive summary of current evolutionary state."""
        return {
            "Поколение": self.current_generation,
            "Население": self.current_population,
            "Рождений всего": self.total_births,
            "Смертей всего": self.total_deaths,
            "Макс. популяция": self.max_population_reached,
            "Старейший возраст": f"{self.oldest_organism_age} тиков",
            "Средний интеллект": round(self.average_intelligence, 2),
            "Убежищ построено": sum(s.get("total_buildings", 0) for s in self.generation_stats[-5:]),
            "Всего событий": len(self.events),
        }

    def get_recent_events(self, count: int = 20) -> List[str]:
        """Get the most recent log events."""
        return self.events[-count:]

    def natural_selection(self, organisms: List['Organism']) -> List['Organism']:
        """
        Apply natural selection pressure.
        Returns the list of surviving organisms.
        Organisms with low fitness are more likely to die.
        """
        survivors = []
        for org in organisms:
            if not org.is_alive:
                continue

            # Calculate fitness based on multiple factors
            fitness = self._calculate_fitness(org)

            # Death probability inversely related to fitness
            death_prob = 1.0 / (1.0 + fitness * 5.0)

            # Additional death factors
            if org.hunger <= 0 or org.thirst <= 0:
                death_prob += 0.1
            if org.health < org.max_health * 0.2:
                death_prob += 0.2
            if org.age > org.max_age_ticks * 0.8:
                death_prob += 0.15

            death_prob = min(0.95, death_prob)

            if np.random.random() > death_prob:
                survivors.append(org)
            else:
                org.is_alive = False

        return survivors

    def _calculate_fitness(self, organism) -> float:
        """
        Calculate the fitness of an organism based on its life achievements.
        Higher fitness = more successful organism.
        """
        fitness = 1.0

        # Positive factors
        fitness += organism.total_food_eaten * 0.01
        fitness += organism.total_water_drunk * 0.01
        fitness += organism.total_resources_collected * 0.02
        fitness += organism.buildings_made * 5.0
        fitness += organism.children_count * 10.0
        fitness += len(organism.cells_visited) * 0.01

        # Age bonus (living longer is good)
        fitness += organism.age * 0.01

        # Genetic factors
        fitness += organism.intelligence * 1.0
        fitness += organism.speed * 0.5
        fitness += organism.metabolism * 0.5

        # Negative factors
        if organism.health < organism.max_health * 0.5:
            fitness -= 2.0

        return max(0.1, fitness)

    def select_parents(self, organisms: List['Organism']) -> List['Organism']:
        """
        Select organisms most likely to reproduce based on fitness.
        Returns a list of candidate parents.
        """
        alive = [o for o in organisms if o.is_alive and o.is_mature]

        if len(alive) < 2:
            return alive

        # Calculate fitness for each organism
        fitness_scores = [self._calculate_fitness(o) for o in alive]

        # Normalize to probabilities
        total_fitness = sum(fitness_scores)
        if total_fitness <= 0:
            return alive

        probabilities = [f / total_fitness for f in fitness_scores]

        # Select parents using fitness-proportional selection
        num_parents = min(len(alive), max(2, len(alive) // 2))
        selected_indices = np.random.choice(
            len(alive),
            size=num_parents,
            replace=False,
            p=probabilities
        )

        return [alive[i] for i in selected_indices]

    def cull_population(self, organisms: List['Organism']) -> List['Organism']:
        """
        If population exceeds MAX_POPULATION, remove the least fit organisms.
        """
        alive = [o for o in organisms if o.is_alive]

        if len(alive) <= MAX_POPULATION:
            return organisms

        # Calculate fitness and sort
        fitness_scores = [(o, self._calculate_fitness(o)) for o in alive]
        fitness_scores.sort(key=lambda x: x[1])

        # Remove excess (kill the least fit)
        excess = len(alive) - MAX_POPULATION
        for i in range(excess):
            if i < len(fitness_scores):
                fitness_scores[i][0].is_alive = False

        return organisms