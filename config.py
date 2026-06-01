"""
Configuration module for the Digital Organism Simulator.
Contains all tunable parameters for the simulation world, organisms, and rendering.

Цифровой организм — симулятор эволюции
"""

# ========================= WORLD PARAMETERS =========================
WORLD_WIDTH = 100
WORLD_HEIGHT = 100
WORLD_SIZE = (WORLD_WIDTH, WORLD_HEIGHT)

# Cell types (represented as integers for performance)
CELL_EMPTY = 0
CELL_GRASS = 1
CELL_TREE = 2
CELL_BERRY_BUSH = 3
CELL_WATER = 4
CELL_STONE = 5
CELL_SHELTER = 6
CELL_RESOURCE = 7  # generic resource deposit

# Initial terrain generation probabilities (must sum to 1.0 for each terrain type)
TERRAIN_PROB_GRASS = 0.35
TERRAIN_PROB_TREE = 0.12
TERRAIN_PROB_BERRY = 0.08
TERRAIN_PROB_WATER = 0.10
TERRAIN_PROB_STONE = 0.10
TERRAIN_PROB_EMPTY = 0.25

# Resource values
GRASS_FOOD_VALUE = 10
BERRY_FOOD_VALUE = 25
TREE_WOOD_VALUE = 30
WATER_THIRST_VALUE = 20
STONE_RESOURCE_VALUE = 15

# Regrowth and change rates
TREE_GROWTH_CHANCE = 0.001        # per tick, new tree may sprout
BERRY_REGROWTH_CHANCE = 0.003     # berry regrowth chance per tick
RESOURCE_REGROWTH_CHANCE = 0.002
MAX_TREES = 200
MAX_BERRIES = 150

# ========================= DAY/NIGHT CYCLE =========================
DAY_LENGTH = 300       # ticks
NIGHT_LENGTH = 100
CYCLE_LENGTH = DAY_LENGTH + NIGHT_LENGTH  # total ticks per full cycle

# Season constants
SEASON_SPRING = 0
SEASON_SUMMER = 1
SEASON_AUTUMN = 2
SEASON_WINTER = 3
SEASON_NAMES = ["Весна", "Лето", "Осень", "Зима"]
SEASON_LENGTH = 800    # ticks per season
FULL_YEAR = SEASON_LENGTH * 4

# Season effects on growth multipliers
SEASON_GROWTH_MULT = {
    SEASON_SPRING: 1.5,
    SEASON_SUMMER: 1.8,
    SEASON_AUTUMN: 1.0,
    SEASON_WINTER: 0.2,
}

# ========================= ORGANISM DEFAULTS =========================
MAX_HEALTH = 100.0
MAX_HUNGER = 100.0
MAX_THIRST = 100.0
MAX_ENERGY = 100.0
MAX_RESOURCES = 200.0

# Consumption rates per tick (balanced for survival)
HUNGER_DECAY = 0.04           # Slower hunger decay
THIRST_DECAY = 0.05           # Slower thirst decay
ENERGY_DECAY_MOVE = 0.3       # Lower energy cost for movement
ENERGY_DECAY_WORK = 0.6       # Lower energy cost for work
ENERGY_REST_RECOVERY = 0.5    # Higher rest recovery
HEALTH_DECAY_HUNGER = 0.02    # Lower health loss when starving
HEALTH_DECAY_THIRST = 0.03    # Lower health loss when dehydrated

# Perception radius (how far the organism can "see")
DEFAULT_SIGHT_RADIUS = 5
MAX_SIGHT_RADIUS = 12

# Age limits
MAX_AGE = 3000            # maximum age in ticks (longer lives)
AGE_MATURE = 80           # age at which organism can reproduce (earlier breeding)

# ========================= GENETICS =========================
GENOME_SIZE = 20  # number of genes

# Gene indices for different traits
GENE_SIGHT_RADIUS = 0
GENE_SPEED = 1
GENE_INTELLIGENCE = 2        # learning rate multiplier
GENE_MEMORY_CAPACITY = 3
GENE_MAX_RESOURCES = 4
GENE_MAX_HEALTH = 5
GENE_MAX_HUNGER = 6
GENE_MAX_THIRST = 7
GENE_MAX_ENERGY = 8
GENE_AGGRESSION = 9         # 0=peaceful, 1=aggressive
GENE_EXPLORATION = 10        # tendency to explore vs stay near resources
GENE_SOCIALITY = 11          # tendency to stay near others
GENE_BUILD_TENDENCY = 12     # tendency to build structures
GENE_FOOD_PREFERENCE = 13    # plant vs meat preference (herbivore/omnivore)
GENE_WATER_EFFICIENCY = 14   # how efficiently water is used
GENE_METABOLISM = 15         # energy efficiency
GENE_STORAGE_TENDENCY = 16   # tendency to hoard resources
GENE_REPRODUCTION_RATE = 17  # how often they reproduce
GENE_MUTATION_RATE = 18      # mutation probability for offspring
GENE_LONGEVITY = 19          # lifespan modifier

# Mutation parameters
BASE_MUTATION_RATE = 0.05
MUTATION_MAGNITUDE = 0.15    # how much a gene can change in one mutation

# ========================= AI / REINFORCEMENT LEARNING =========================
# Q-learning parameters
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EXPLORATION_RATE_INITIAL = 0.8
EXPLORATION_RATE_MIN = 0.05
EXPLORATION_DECAY = 0.9995

# Actions
ACTION_COUNT = 12
ACTION_MOVE_UP = 0
ACTION_MOVE_DOWN = 1
ACTION_MOVE_LEFT = 2
ACTION_MOVE_RIGHT = 3
ACTION_EAT = 4
ACTION_DRINK = 5
ACTION_REST = 6
ACTION_COLLECT = 7
ACTION_BUILD = 8
ACTION_REPRODUCE = 9
ACTION_EXPLORE = 10
ACTION_GUARD = 11

ACTION_NAMES = [
    "Движение ↑",
    "Движение ↓",
    "Движение ←",
    "Движение →",
    "Поесть",
    "Попить",
    "Отдых",
    "Сбор ресурсов",
    "Строительство",
    "Размножение",
    "Исследование",
    "Охрана",
]

# Rewards (higher rewards to reinforce learning)
REWARD_EAT = 20.0
REWARD_DRINK = 20.0
REWARD_REST = 5.0
REWARD_COLLECT_RESOURCE = 15.0
REWARD_BUILD = 30.0
REWARD_REPRODUCE = 50.0
REWARD_EXPLORE_NEW = 8.0
REWARD_SURVIVE_TICK = 0.5
REWARD_FIND_FOOD = 12.0
REWARD_FIND_WATER = 12.0
REWARD_GROW_RESOURCES = 5.0

REWARD_PENALTY_HUNGER = -5.0
REWARD_PENALTY_THIRST = -5.0
REWARD_PENALTY_INACTIVITY = -2.0
REWARD_PENALTY_DEATH = -80.0
REWARD_PENALTY_DAMAGE = -15.0

# ========================= MEMORY =========================
MEMORY_CAPACITY_DEFAULT = 20
MEMORY_EVENT_FOOD = "еда"
MEMORY_EVENT_WATER = "вода"
MEMORY_EVENT_TREE = "дерево"
MEMORY_EVENT_DANGER = "опасность"
MEMORY_EVENT_BUILD = "строительство"
MEMORY_EVENT_BIRTH = "рождение"
MEMORY_EVENT_RESOURCE = "ресурс"
MEMORY_EVENT_DEATH = "смерть"

# ========================= POPULATION =========================
INITIAL_POPULATION = 35
MAX_POPULATION = 100
REPRODUCTION_ENERGY_COST = 20.0    # Lower cost for easier reproduction
REPRODUCTION_HEALTH_COST = 10.0    # Lower health cost
REPRODUCTION_COOLDOWN = 50         # Faster reproduction cooldown

# ========================= RENDERING =========================
# Display dimensions
DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
CELL_PIXEL_SIZE = 6  # size of each world cell in pixels

# Colors (R, G, B)
COLOR_GRASS = (50, 160, 50)
COLOR_TREE = (30, 100, 30)
COLOR_BERRY = (200, 50, 100)
COLOR_WATER = (40, 80, 180)
COLOR_STONE = (120, 120, 120)
COLOR_EMPTY = (60, 60, 40)
COLOR_SHELTER = (160, 120, 80)
COLOR_RESOURCE = (200, 200, 50)

COLOR_ORGANISM_HEALTHY = (50, 200, 50)
COLOR_ORGANISM_HUNGRY = (200, 200, 50)
COLOR_ORGANISM_THIRSTY = (200, 100, 50)
COLOR_ORGANISM_DYING = (200, 50, 50)
COLOR_ORGANISM_OLD = (150, 150, 200)

COLOR_DAY_SKY = (135, 206, 235)
COLOR_NIGHT_SKY = (10, 10, 30)
COLOR_UI_BG = (30, 30, 40)
COLOR_UI_TEXT = (220, 220, 220)
COLOR_UI_HIGHLIGHT = (255, 200, 50)
COLOR_UI_ACCENT = (80, 120, 200)

# UI panel dimensions
UI_PANEL_WIDTH = 300
UI_SIDEBAR_X = DISPLAY_WIDTH - UI_PANEL_WIDTH

# ========================= SIMULATION SPEED =========================
TICK_RATE_NORMAL = 10       # ticks per second
TICK_RATE_FAST = 50
TICK_RATE_FASTER = 100
TICK_RATE_SLOW = 3
TICK_RATES = {
    "slow": TICK_RATE_SLOW,
    "normal": TICK_RATE_NORMAL,
    "fast": TICK_RATE_FAST,
    "faster": TICK_RATE_FASTER,
}

# ========================= LOGGING =========================
LOG_FILE = "simulation_log.txt"

# ========================= MISC =========================
MAX_ENTITIES_PER_CELL = 3