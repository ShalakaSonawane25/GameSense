"""Automated AI Persona Simulation Runner.

Simulates automated playtesting sessions across the four AI personas (Beginner, Explorer,
Speedrunner, Aggressive) and transmits telemetry into GameSense.
"""
import time
import uuid
import random
import argparse
import requests
from app.ai_agent.personas import PERSONA_PROFILES

# Common level landmark points (X, Y) for a 2D/3D platformer level
LEVEL_WAYPOINTS = [
    {"x": 0.0, "y": 0.0, "name": "Spawn_Point"},
    {"x": 15.0, "y": 1.5, "name": "Platform_A"},
    {"x": 32.0, "y": -2.0, "name": "Spike_Chasm_Trap"},  # Known hazard point
    {"x": 48.0, "y": 3.0, "name": "Checkpoint_1"},
    {"x": 65.0, "y": 2.0, "name": "Goblin_Patrol_Zone"},
    {"x": 82.0, "y": 4.5, "name": "Floating_Islands"},
    {"x": 100.0, "y": 0.0, "name": "Level_Goal"}
]

def simulate_session(
    base_url: str,
    persona_type: str,
    level_name: str = "Level_1"
) -> dict:
    """Simulates a single playtest run for an AI persona."""
    profile = PERSONA_PROFILES.get(persona_type.upper(), PERSONA_PROFILES["BEGINNER"])
    session_id = f"sim_{persona_type.lower()}_{uuid.uuid4().hex[:8]}"

    # 1. Start Session
    start_payload = {
        "session_id": session_id,
        "persona_type": persona_type.upper(),
        "level_name": level_name,
        "game_version": "1.0.0-sim"
    }
    res = requests.post(f"{base_url}/api/telemetry/session/start", json=start_payload)
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to start session: {res.text}")

    # 2. Simulate Movement & Events along waypoints
    curr_time = 0.0
    curr_x = 0.0
    curr_y = 0.0
    positions = []
    deaths_count = 0
    items_count = 0
    enemies_count = 0
    score = 0
    player_health = 100
    failed = False

    for wp in LEVEL_WAYPOINTS:
        target_x = wp["x"]
        target_y = wp["y"]
        wp_name = wp["name"]

        # Step towards waypoint
        steps = max(2, int(abs(target_x - curr_x) / (profile.speed_factor * 2.5)))
        for s in range(steps):
            curr_time += random.uniform(0.8, 1.4) / profile.speed_factor
            curr_x += (target_x - curr_x) / (steps - s)
            curr_y += (target_y - curr_y) / (steps - s) + random.uniform(-0.2, 0.2)

            positions.append({
                "timestamp": round(curr_time, 2),
                "x": round(curr_x, 2),
                "y": round(curr_y, 2),
                "z": 0.0,
                "health": player_health
            })

        # Check for hazard encounter at spike trap
        if "Spike_Chasm" in wp_name:
            if random.random() < profile.hazard_death_chance:
                deaths_count += 1
                player_health = 0
                failed = True
                
                # Send death event
                death_payload = {
                    "session_id": session_id,
                    "event_type": "DEATH",
                    "level_name": level_name,
                    "timestamp": round(curr_time, 2),
                    "x": round(curr_x, 2),
                    "y": round(curr_y, 2),
                    "z": 0.0,
                    "cause_or_source": "Spike_Chasm_Trap",
                    "additional_data": {"hazard_zone": "Chasm_1"}
                }
                requests.post(f"{base_url}/api/telemetry/events", json=death_payload)
                break  # Session ends on death

        # Check for optional collectibles (Explorers pick up more)
        if random.random() < profile.exploration_rate:
            items_count += 1
            score += 100
            item_payload = {
                "session_id": session_id,
                "event_type": "ITEM_PICKUP",
                "level_name": level_name,
                "timestamp": round(curr_time, 2),
                "x": round(curr_x, 2),
                "y": round(curr_y, 2),
                "z": 0.0,
                "cause_or_source": "Gold_Coin"
            }
            requests.post(f"{base_url}/api/telemetry/events", json=item_payload)

        # Check for enemy engagement (Aggressive attacks more)
        if "Patrol" in wp_name:
            if random.random() < profile.enemy_engagement_rate:
                enemies_count += 1
                score += 250
                kill_payload = {
                    "session_id": session_id,
                    "event_type": "ENEMY_KILLED",
                    "level_name": level_name,
                    "timestamp": round(curr_time, 2),
                    "x": round(curr_x, 2),
                    "y": round(curr_y, 2),
                    "z": 0.0,
                    "cause_or_source": "Goblin_Scout"
                }
                requests.post(f"{base_url}/api/telemetry/events", json=kill_payload)

    # 3. Flush Position Batch
    if positions:
        pos_payload = {
            "session_id": session_id,
            "level_name": level_name,
            "positions": positions
        }
        requests.post(f"{base_url}/api/telemetry/positions/batch", json=pos_payload)

    # 4. End Session
    status = "FAILED" if failed else "COMPLETED"
    end_payload = {
        "session_id": session_id,
        "status": status,
        "duration_seconds": round(curr_time, 2),
        "total_score": score,
        "total_deaths": deaths_count,
        "items_collected": items_count,
        "enemies_defeated": enemies_count
    }
    requests.post(f"{base_url}/api/telemetry/session/end", json=end_payload)

    return {
        "session_id": session_id,
        "persona": persona_type,
        "status": status,
        "duration": round(curr_time, 2),
        "deaths": deaths_count,
        "items": items_count,
        "enemies": enemies_count
    }

def run_simulation_suite(base_url: str = "http://127.0.0.1:8000", runs_per_persona: int = 3):
    """Runs a batch of simulations across all 4 personas."""
    personas = ["BEGINNER", "EXPLORER", "SPEEDRUNNER", "AGGRESSIVE"]
    print(f"--- Starting GameSense AI Simulation Suite ({runs_per_persona} runs per persona) ---")
    
    results = []
    for p in personas:
        print(f"\n[AI Persona: {p}]")
        for i in range(runs_per_persona):
            summary = simulate_session(base_url, p)
            results.append(summary)
            print(f"  Run {i+1}: Status={summary['status']}, Duration={summary['duration']}s, Deaths={summary['deaths']}, Items={summary['items']}")

    print("\n--- Simulation Complete ---")
    print(f"Total sessions generated: {len(results)}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GameSense AI Agent Playtest Runner")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="FastAPI Base URL")
    parser.add_argument("--runs", type=int, default=2, help="Number of runs per persona")
    args = parser.parse_args()

    run_simulation_suite(base_url=args.url, runs_per_persona=args.runs)
