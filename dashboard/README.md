# React Dashboard Integration Guide (For Member 1)

This guide documents the GameSense FastAPI endpoints for the React.js + Tailwind analytics dashboard.

## Server Connection
- **Base URL:** `http://127.0.0.1:8000/api`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **CORS:** Enabled for React development servers on ports `3000`, `5173`, and `8080`.

---

## Key Dashboard Endpoints

### 1. Dashboard Overview KPIs
* **Endpoint:** `GET /api/analytics/overview`
* **Response Sample:**
```json
{
  "total_sessions": 24,
  "completed_sessions": 16,
  "failed_sessions": 8,
  "win_rate_percentage": 66.67,
  "avg_duration_seconds": 42.5,
  "total_deaths_recorded": 19,
  "total_items_collected": 58,
  "total_enemies_defeated": 31,
  "active_personas_count": 4
}
```

### 2. Spatial Heatmap Coordinates
* **Endpoint:** `GET /api/analytics/heatmaps?type=DEATH&level_name=Level_1`
* **Query Params:**
  * `type`: `"DEATH"` or `"MOVEMENT"`
  * `level_name`: `"Level_1"`
  * `persona_type`: optional (e.g. `"BEGINNER"`, `"SPEEDRUNNER"`, or leave empty for all)
* **Response Sample:**
```json
[
  { "x": 32.0, "y": -2.0, "weight": 7, "cause": "Spike_Chasm_Trap" },
  { "x": 65.0, "y": 2.0, "weight": 3, "cause": "Goblin_Scout" }
]
```

### 3. AI Persona Playstyle Comparison
* **Endpoint:** `GET /api/analytics/personas/comparison`
* **Response Sample:**
```json
{
  "personas": [
    {
      "persona_type": "BEGINNER",
      "session_count": 6,
      "win_rate_percentage": 33.33,
      "avg_duration_seconds": 68.2,
      "avg_deaths": 2.1,
      "avg_score": 250.0,
      "avg_items_collected": 1.5
    },
    {
      "persona_type": "SPEEDRUNNER",
      "session_count": 6,
      "win_rate_percentage": 100.0,
      "avg_duration_seconds": 24.8,
      "avg_deaths": 0.0,
      "avg_score": 400.0,
      "avg_items_collected": 0.2
    }
  ]
}
```

### 4. Game Balancing Recommendations
* **Fetch Suggestions:** `GET /api/recommendations`
* **Trigger New Analysis:** `POST /api/recommendations/analyze` with body `{"level_name": "Level_1"}`
* **Response Sample:**
```json
[
  {
    "id": 1,
    "level_name": "Level_1",
    "issue_category": "DIFFICULTY_SPIKE",
    "severity": "HIGH",
    "message": "Severe hazard bottleneck at coordinate (32.0, -2.0). 7 players died to 'Spike_Chasm_Trap'.",
    "suggested_action": "Reduce trigger speed of Spike_Chasm_Trap by 20% or add a visible warning cue and health pickup before this section.",
    "target_coordinates": "{\"x\": 32.0, \"y\": -2.0}",
    "created_at": "2026-09-02T10:30:00"
  }
]
```

### 5. Playtesting Session History
* **Endpoint:** `GET /api/sessions?limit=50`
* Returns paginated session logs with filters for `persona_type` and `status` (`COMPLETED`/`FAILED`).
