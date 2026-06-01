"""
Genetics module for the Digital Organism Simulator.
Handles genomes, inheritance, and mutations.

Генетика цифровых организмов — наследование, мутации, геном.
"""

import numpy as np
from typing import List, Tuple, Optional
from config import (
    GENOME_SIZE, BASE_MUTATION_RATE, MUTATION_MAGNITUDE,
    GENE_SIGHT_RADIUS, GENE_SPEED, GENE_INTELLIGENCE,
    GENE_MEMORY_CAPACITY, GENE_MAX_RESOURCES, GENE_MAX_HEALTH,
    GENE_MAX_HUNGER, GENE_MAX_THIRST, GENE_MAX_ENERGY,
    GENE_AGGRESSION, GENE_EXPLORATION, GENE_SOCIALITY,
    GENE_BUILD_TENDENCY, GENE_FOOD_PREFERENCE, GENE_WATER_EFFICIENCY,
    GENE_METABOLISM, GENE_STORAGE_TENDENCY, GENE_REPRODUCTION_RATE,
    GENE_MUTATION_RATE, GENE_LONGEVITY,
    MAX_SIGHT_RADIUS, MEMORY_CAPACITY_DEFAULT,
)

# Each gene is a float between 0.0 and 1.0
# The actual trait value is derived by mapping this to a meaningful range


class Genome:
    """
    Represents the genetic code of an organism.
    Contains 20 genes, each encoded as a float in [0.0, 1.0].
    """

    __slots__ = ("genes",)

    def __init__(self, genes: Optional[np.ndarray] = None) -> None:
        if genes is not None:
            self.genes: np.ndarray = np.clip(genes, 0.0, 1.0)
        else:
            # Create a random genome
            self.genes = np.random.random(GENOME_SIZE).astype(np.float64)

    def get_gene(self, index: int) -> float:
        """Get the raw value of a specific gene (0.0 to 1.0)."""
        return float(self.genes[index])

    def get_trait_sight_radius(self) -> int:
        """Derive sight radius from gene (1 to MAX_SIGHT_RADIUS)."""
        val = self.get_gene(GENE_SIGHT_RADIUS)
        return max(1, int(val * MAX_SIGHT_RADIUS))

    def get_trait_speed(self) -> float:
        """Derive movement speed modifier (0.5 to 2.0)."""
        val = self.get_gene(GENE_SPEED)
        return 0.5 + val * 1.5

    def get_trait_intelligence(self) -> float:
        """Derive learning rate multiplier (0.1 to 2.0)."""
        val = self.get_gene(GENE_INTELLIGENCE)
        return 0.1 + val * 1.9

    def get_trait_memory_capacity(self) -> int:
        """Derive memory capacity (5 to 50)."""
        val = self.get_gene(GENE_MEMORY_CAPACITY)
        return max(5, int(val * 50))

    def get_trait_max_resources(self) -> float:
        """Derive max resource capacity (50 to 400)."""
        val = self.get_gene(GENE_MAX_RESOURCES)
        return 50.0 + val * 350.0

    def get_trait_max_health(self) -> float:
        """Derive max health (50 to 200)."""
        val = self.get_gene(GENE_MAX_HEALTH)
        return 50.0 + val * 150.0

    def get_trait_max_hunger(self) -> float:
        """Derive max hunger (50 to 200)."""
        val = self.get_gene(GENE_MAX_HUNGER)
        return 50.0 + val * 150.0

    def get_trait_max_thirst(self) -> float:
        """Derive max thirst (50 to 200)."""
        val = self.get_gene(GENE_MAX_THIRST)
        return 50.0 + val * 150.0

    def get_trait_max_energy(self) -> float:
        """Derive max energy (50 to 200)."""
        val = self.get_gene(GENE_MAX_ENERGY)
        return 50.0 + val * 150.0

    def get_trait_aggression(self) -> float:
        """Derive aggression level (0.0 = peaceful, 1.0 = aggressive)."""
        return self.get_gene(GENE_AGGRESSION)

    def get_trait_exploration(self) -> float:
        """Derive exploration tendency (0.0 = stay near home, 1.0 = wander)."""
        return self.get_gene(GENE_EXPLORATION)

    def get_trait_sociality(self) -> float:
        """Derive social tendency (0.0 = solitary, 1.0 = social)."""
        return self.get_gene(GENE_SOCIALITY)

    def get_trait_build_tendency(self) -> float:
        """Derive building tendency (0.0 = never builds, 1.0 = builds often)."""
        return self.get_gene(GENE_BUILD_TENDENCY)

    def get_trait_food_preference(self) -> float:
        """Derive food preference (0.0 = only plants, 1.0 = only meat)."""
        return self.get_gene(GENE_FOOD_PREFERENCE)

    def get_trait_water_efficiency(self) -> float:
        """Derive water efficiency modifier (0.5 to 2.0)."""
        val = self.get_gene(GENE_WATER_EFFICIENCY)
        return 0.5 + val * 1.5

    def get_trait_metabolism(self) -> float:
        """Derive metabolism efficiency (0.5 to 2.0). Higher = slower energy decay."""
        val = self.get_gene(GENE_METABOLISM)
        return 0.5 + val * 1.5

    def get_trait_storage_tendency(self) -> float:
        """Derive tendency to store resources (0.0 to 1.0)."""
        return self.get_gene(GENE_STORAGE_TENDENCY)

    def get_trait_reproduction_rate(self) -> float:
        """Derive reproduction rate modifier (0.5 to 2.0)."""
        val = self.get_gene(GENE_REPRODUCTION_RATE)
        return 0.5 + val * 1.5

    def get_trait_mutation_rate(self) -> float:
        """Derive mutation rate for offspring (0.01 to 0.3)."""
        val = self.get_gene(GENE_MUTATION_RATE)
        return 0.01 + val * 0.29

    def get_trait_longevity(self) -> float:
        """Derive lifespan modifier (0.5 to 2.0)."""
        val = self.get_gene(GENE_LONGEVITY)
        return 0.5 + val * 1.5

    def get_all_traits_dict(self) -> dict:
        """Return all traits as a dictionary for display."""
        return {
            "Зрение (радиус)": self.get_trait_sight_radius(),
            "Скорость": round(self.get_trait_speed(), 2),
            "Интеллект": round(self.get_trait_intelligence(), 2),
            "Память (ёмкость)": self.get_trait_memory_capacity(),
            "Макс. ресурсы": round(self.get_trait_max_resources(), 0),
            "Макс. здоровье": round(self.get_trait_max_health(), 0),
            "Макс. сытость": round(self.get_trait_max_hunger(), 0),
            "Макс. вода": round(self.get_trait_max_thirst(), 0),
            "Макс. энергия": round(self.get_trait_max_energy(), 0),
            "Агрессия": round(self.get_trait_aggression(), 2),
            "Исследование": round(self.get_trait_exploration(), 2),
            "Социальность": round(self.get_trait_sociality(), 2),
            "Строительство": round(self.get_trait_build_tendency(), 2),
            "Предпочтение еды": round(self.get_trait_food_preference(), 2),
            "Эффективность воды": round(self.get_trait_water_efficiency(), 2),
            "Метаболизм": round(self.get_trait_metabolism(), 2),
            "Накопление": round(self.get_trait_storage_tendency(), 2),
            "Размножение": round(self.get_trait_reproduction_rate(), 2),
            "Мутации": round(self.get_trait_mutation_rate(), 3),
            "Долголетие": round(self.get_trait_longevity(), 2),
        }

    def get_raw_genes_str(self) -> str:
        """Return a compact string representation of the genome."""
        return ",".join(f"{g:.2f}" for g in self.genes)

    def crossover(self, other: "Genome") -> Tuple["Genome", "Genome"]:
        """
        Perform single-point crossover between two genomes.
        Returns two offspring genomes.
        """
        point = np.random.randint(1, GENOME_SIZE - 1)
        child1_genes = np.concatenate([self.genes[:point], other.genes[point:]])
        child2_genes = np.concatenate([other.genes[:point], self.genes[point:]])
        return Genome(child1_genes), Genome(child2_genes)

    def mutate(self, mutation_rate: Optional[float] = None) -> "Genome":
        """
        Apply random mutations to the genome.
        Each gene has a chance of being mutated.
        Returns a new mutated Genome.
        """
        if mutation_rate is None:
            mutation_rate = BASE_MUTATION_RATE

        new_genes = self.genes.copy()
        for i in range(GENOME_SIZE):
            if np.random.random() < mutation_rate:
                # Add a random delta, then clip to [0, 1]
                delta = np.random.normal(0, MUTATION_MAGNITUDE)
                new_genes[i] = np.clip(new_genes[i] + delta, 0.0, 1.0)
        return Genome(new_genes)

    @staticmethod
    def combine(parent1: "Genome", parent2: "Genome") -> "Genome":
        """
        Create a child genome from two parents with crossover and mutation.
        """
        # Perform crossover to get two children, pick one randomly
        child1, _ = parent1.crossover(parent2)
        # Determine mutation rate from the more mutable parent
        mut_rate = max(
            parent1.get_trait_mutation_rate(),
            parent2.get_trait_mutation_rate()
        )
        # Apply mutation
        child = child1.mutate(mut_rate)
        return child

    def similarity(self, other: "Genome") -> float:
        """
        Compute genetic similarity (1.0 = identical, 0.0 = completely different).
        """
        diff = np.abs(self.genes - other.genes)
        return float(1.0 - np.mean(diff))
