"""AI Persona definitions and behavior parameters."""
from dataclasses import dataclass

@dataclass
class PersonaConfig:
    name: str
    description: str
    speed_factor: float          # Movement speed multiplier (1.0 = normal)
    hazard_death_chance: float   # Probability of dying to a trap/hazard
    enemy_engagement_rate: float # Willingness to attack enemies
    exploration_rate: float      # Tendency to detour for optional items
    avg_duration_base: float     # Estimated baseline duration in seconds

PERSONA_PROFILES: dict[str, PersonaConfig] = {
    "BEGINNER": PersonaConfig(
        name="BEGINNER",
        description="Hesitant movement, slow reaction time, struggles with traps and hazards.",
        speed_factor=0.7,
        hazard_death_chance=0.45,
        enemy_engagement_rate=0.3,
        exploration_rate=0.2,
        avg_duration_base=65.0
    ),
    "EXPLORER": PersonaConfig(
        name="EXPLORER",
        description="Searches all corners and side paths, collects most items, cautious playstyle.",
        speed_factor=0.9,
        hazard_death_chance=0.10,
        enemy_engagement_rate=0.4,
        exploration_rate=0.9,
        avg_duration_base=85.0
    ),
    "SPEEDRUNNER": PersonaConfig(
        name="SPEEDRUNNER",
        description="Takes optimal direct paths, avoids side routes and enemies, maximizes speed.",
        speed_factor=1.6,
        hazard_death_chance=0.05,
        enemy_engagement_rate=0.1,
        exploration_rate=0.05,
        avg_duration_base=25.0
    ),
    "AGGRESSIVE": PersonaConfig(
        name="AGGRESSIVE",
        description="Seeks out and destroys all enemies, takes risky combat encounters.",
        speed_factor=1.1,
        hazard_death_chance=0.20,
        enemy_engagement_rate=0.95,
        exploration_rate=0.4,
        avg_duration_base=45.0
    )
}
