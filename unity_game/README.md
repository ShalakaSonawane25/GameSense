# Unity GameSense Integration Guide (For Member 4)

This folder contains the integration scripts and assets connecting the Unity Game to the GameSense FastAPI Backend.

## Quick Start for Unity Developer

1. **Copy the Telemetry Script:**
   - Copy `GameSenseTelemetryClient.cs` into your Unity project's `Assets/Scripts/` folder.
2. **Attach to GameManager:**
   - Attach `GameSenseTelemetryClient` to your `GameManager` or `Player` GameObject.
3. **Configure Inspector Settings:**
   - `Backend URL`: `http://127.0.0.1:8000/api`
   - `Current Level Name`: e.g. `Level_1`
   - `Persona Type`: Keep as `HUMAN` for manual testing, or change to `BEGINNER`, `EXPLORER`, `SPEEDRUNNER`, `AGGRESSIVE` when testing automated AI player bots.
4. **Hook Events:**
   - On Player Death: `FindObjectOfType<GameSenseTelemetryClient>().LogEvent("DEATH", "SpikeTrap");`
   - On Level Goal: `FindObjectOfType<GameSenseTelemetryClient>().EndSession(true);`
   - On Game Over: `FindObjectOfType<GameSenseTelemetryClient>().EndSession(false);`
