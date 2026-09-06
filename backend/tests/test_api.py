"""Automated test suite for GameSense Backend APIs."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    """Verify server health check endpoints."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    api_res = client.get("/api/health")
    assert api_res.status_code == 200
    assert api_res.json()["status"] == "healthy"

def test_session_lifecycle_and_telemetry():
    """Verify complete flow: Start -> Positions -> Events -> End -> Verify."""
    session_id = "test_sess_001"
    
    # 1. Start Session
    start_payload = {
        "session_id": session_id,
        "persona_type": "BEGINNER",
        "level_name": "Level_1",
        "game_version": "1.0.0"
    }
    res_start = client.post("/api/telemetry/session/start", json=start_payload)
    assert res_start.status_code == 201
    assert res_start.json()["status"] == "success"

    # 2. Ingest Positions Batch
    pos_payload = {
        "session_id": session_id,
        "level_name": "Level_1",
        "positions": [
            {"timestamp": 1.0, "x": 0.0, "y": 0.0, "z": 0.0, "health": 100},
            {"timestamp": 2.5, "x": 10.0, "y": 2.0, "z": 0.0, "health": 90},
            {"timestamp": 5.0, "x": 30.0, "y": -1.0, "z": 0.0, "health": 40}
        ]
    }
    res_pos = client.post("/api/telemetry/positions/batch", json=pos_payload)
    assert res_pos.status_code == 200
    assert res_pos.json()["records_saved"] == 3

    # 3. Log Gameplay Events
    item_payload = {
        "session_id": session_id,
        "event_type": "ITEM_PICKUP",
        "level_name": "Level_1",
        "timestamp": 3.0,
        "x": 12.0,
        "y": 2.0,
        "z": 0.0,
        "cause_or_source": "Health_Potion"
    }
    res_item = client.post("/api/telemetry/events", json=item_payload)
    assert res_item.status_code == 201

    death_payload = {
        "session_id": session_id,
        "event_type": "DEATH",
        "level_name": "Level_1",
        "timestamp": 5.2,
        "x": 30.5,
        "y": -1.2,
        "z": 0.0,
        "cause_or_source": "Spike_Pit_A"
    }
    res_death = client.post("/api/telemetry/events", json=death_payload)
    assert res_death.status_code == 201

    # 4. End Session
    end_payload = {
        "session_id": session_id,
        "status": "FAILED",
        "duration_seconds": 5.5,
        "total_score": 100,
        "total_deaths": 1,
        "items_collected": 1,
        "enemies_defeated": 0
    }
    res_end = client.post("/api/telemetry/session/end", json=end_payload)
    assert res_end.status_code == 200
    assert res_end.json()["final_status"] == "FAILED"

    # 5. Query Session List
    res_sessions = client.get("/api/sessions")
    assert res_sessions.status_code == 200
    sessions_data = res_sessions.json()
    assert len(sessions_data) == 1
    assert sessions_data[0]["session_id"] == session_id
    assert sessions_data[0]["status"] == "FAILED"

def test_analytics_and_recommendations():
    """Seed multiple runs and test overview KPIs, heatmaps, and recommendations."""
    # Seed 3 sessions with deaths concentrated at (30.0, -1.0)
    for i in range(3):
        sid = f"seed_sess_{i}"
        client.post("/api/telemetry/session/start", json={
            "session_id": sid,
            "persona_type": "BEGINNER",
            "level_name": "Level_1"
        })
        client.post("/api/telemetry/events", json={
            "session_id": sid,
            "event_type": "DEATH",
            "level_name": "Level_1",
            "timestamp": 10.0 + i,
            "x": 30.0,
            "y": -1.0,
            "cause_or_source": "Spike_Trap"
        })
        client.post("/api/telemetry/session/end", json={
            "session_id": sid,
            "status": "FAILED",
            "duration_seconds": 12.0,
            "total_deaths": 1
        })

    # Test Overview KPIs
    overview_res = client.get("/api/analytics/overview")
    assert overview_res.status_code == 200
    data = overview_res.json()
    assert data["total_sessions"] == 3
    assert data["failed_sessions"] == 3
    assert data["win_rate_percentage"] == 0.0

    # Test Heatmaps
    heatmap_res = client.get("/api/analytics/heatmaps?type=DEATH&level_name=Level_1")
    assert heatmap_res.status_code == 200
    pts = heatmap_res.json()
    assert len(pts) >= 1
    assert pts[0]["weight"] == 3
    assert pts[0]["cause"] == "Spike_Trap"

    # Test Recommendations Trigger
    rec_res = client.post("/api/recommendations/analyze", json={"level_name": "Level_1"})
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["status"] == "success"
    assert rec_data["recommendations_created"] >= 1
    assert "Spike_Trap" in rec_data["recommendations"][0]["message"]

def test_root_telemetry_endpoint():
    """Verify Task 3 root-level POST /telemetry endpoint lifecycle and validation."""
    session_id = "task3_sess_001"

    # 1. Start a session
    res_start = client.post("/api/telemetry/session/start", json={
        "session_id": session_id,
        "persona_type": "EXPLORER",
        "level_name": "Level_1",
        "game_version": "1.0.0"
    })
    assert res_start.status_code == 201

    # 2. Ingest valid telemetry event via POST /telemetry
    valid_payload = {
        "session_id": session_id,
        "event_type": "DEATH",
        "level_name": "Level_1",
        "timestamp": 8.5,
        "x": 42.0,
        "y": -3.5,
        "z": 0.0,
        "cause_or_source": "Spike_Pit_A",
        "additional_data": {"speed": 5.4}
    }
    res_event = client.post("/telemetry", json=valid_payload)
    assert res_event.status_code == 201
    event_data = res_event.json()
    assert event_data["status"] == "success"
    assert "event_id" in event_data
    assert event_data["event_type"] == "DEATH"

    # 3. Verify record is stored and reflected in session metrics / heatmap
    heatmap_res = client.get("/api/analytics/heatmaps?type=DEATH&level_name=Level_1")
    assert heatmap_res.status_code == 200
    points = heatmap_res.json()
    assert any(p["cause"] == "Spike_Pit_A" for p in points)

    # 4. Verify validation: Invalid payload (missing required event_type and numeric timestamp) returns 422
    invalid_payload = {
        "session_id": session_id,
        "timestamp": "INVALID_TIMESTAMP",
        "x": 42.0,
        "y": -3.5
    }
    res_invalid = client.post("/telemetry", json=invalid_payload)
    assert res_invalid.status_code == 422

    # 5. Verify non-existent session returns 404
    res_nonexistent = client.post("/telemetry", json={
        "session_id": "non_existent_session_999",
        "event_type": "DEATH",
        "timestamp": 1.0,
        "x": 0.0,
        "y": 0.0
    })
    assert res_nonexistent.status_code == 404

def test_root_session_endpoints():
    """Verify Task 6 root-level /session/start and /session/end endpoints."""
    session_id = "root_sess_spec_001"

    # 1. Validation: Missing session_id on start -> 422
    res_bad_start = client.post("/session/start", json={})
    assert res_bad_start.status_code == 422

    # 2. Successful start -> 201
    res_start = client.post("/session/start", json={
        "session_id": session_id,
        "persona_type": "SPEEDRUNNER",
        "level_name": "Level_2",
        "game_version": "1.1.0"
    })
    assert res_start.status_code == 201
    start_data = res_start.json()
    assert start_data["status"] == "success"
    assert start_data["session_id"] == session_id

    # 3. Validation: Missing required status on end -> 422
    res_bad_end = client.post("/session/end", json={
        "session_id": session_id
    })
    assert res_bad_end.status_code == 422

    # 4. Non-existent session on end -> 404
    res_notfound_end = client.post("/session/end", json={
        "session_id": "fake_ghost_session_404",
        "status": "COMPLETED"
    })
    assert res_notfound_end.status_code == 404

    # 5. Successful end -> 200
    res_end = client.post("/session/end", json={
        "session_id": session_id,
        "status": "COMPLETED",
        "duration_seconds": 62.5,
        "total_score": 1500,
        "total_deaths": 2,
        "items_collected": 5,
        "enemies_defeated": 10
    })
    assert res_end.status_code == 200
    end_data = res_end.json()
    assert end_data["status"] == "success"
    assert end_data["session_id"] == session_id
    assert end_data["final_status"] == "COMPLETED"
    assert end_data["duration_seconds"] == 62.5

    # 6. Verify stored in SQLite
    res_get = client.get(f"/api/sessions/{session_id}")
    assert res_get.status_code == 200
    session_row = res_get.json()
    assert session_row["persona_type"] == "SPEEDRUNNER"
    assert session_row["status"] == "COMPLETED"
    assert session_row["total_score"] == 1500
    assert session_row["total_deaths"] == 2


