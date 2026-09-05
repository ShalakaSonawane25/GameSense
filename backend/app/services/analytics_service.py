"""Analytics service computing game statistics and heatmap clusters."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.session import GameSession
from app.models.telemetry import GameplayEvent, PositionSample
from app.schemas.analytics import (
    OverviewStatsResponse,
    HeatmapPointResponse,
    PersonaMetricResponse,
    PersonaComparisonResponse,
)

class AnalyticsService:
    @staticmethod
    def get_overview_stats(db: Session, level_name: Optional[str] = None) -> OverviewStatsResponse:
        """Calculate overall playtesting metrics across sessions."""
        query = db.query(GameSession)
        if level_name:
            query = query.filter(GameSession.level_name == level_name)
        
        sessions = query.all()
        total_sessions = len(sessions)
        
        if total_sessions == 0:
            return OverviewStatsResponse(
                total_sessions=0,
                completed_sessions=0,
                failed_sessions=0,
                win_rate_percentage=0.0,
                avg_duration_seconds=0.0,
                total_deaths_recorded=0,
                total_items_collected=0,
                total_enemies_defeated=0,
                active_personas_count=0
            )

        completed = sum(1 for s in sessions if s.status == "COMPLETED")
        failed = sum(1 for s in sessions if s.status == "FAILED")
        win_rate = round((completed / total_sessions) * 100.0, 2)
        
        valid_durations = [s.duration_seconds for s in sessions if s.duration_seconds > 0]
        avg_duration = round(sum(valid_durations) / len(valid_durations), 2) if valid_durations else 0.0
        
        total_deaths = sum(s.total_deaths for s in sessions)
        total_items = sum(s.items_collected for s in sessions)
        total_enemies = sum(s.enemies_defeated for s in sessions)
        unique_personas = len(set(s.persona_type for s in sessions))

        return OverviewStatsResponse(
            total_sessions=total_sessions,
            completed_sessions=completed,
            failed_sessions=failed,
            win_rate_percentage=win_rate,
            avg_duration_seconds=avg_duration,
            total_deaths_recorded=total_deaths,
            total_items_collected=total_items,
            total_enemies_defeated=total_enemies,
            active_personas_count=unique_personas
        )

    @staticmethod
    def get_heatmap_points(
        db: Session,
        heatmap_type: str = "DEATH",
        level_name: Optional[str] = "Level_1",
        persona_type: Optional[str] = None,
        grid_precision: float = 1.0
    ) -> list[HeatmapPointResponse]:
        """
        Aggregate coordinates into discrete spatial grid clusters.
        - heatmap_type 'DEATH': Clusters death events from gameplay_events.
        - heatmap_type 'MOVEMENT': Clusters position samples from position_samples.
        """
        points: list[HeatmapPointResponse] = []

        if heatmap_type.upper() == "DEATH":
            query = db.query(GameplayEvent).join(GameSession, GameplayEvent.session_id == GameSession.session_id)
            query = query.filter(GameplayEvent.event_type == "DEATH")
            if level_name:
                query = query.filter(GameplayEvent.level_name == level_name)
            if persona_type and persona_type.upper() != "ALL":
                query = query.filter(GameSession.persona_type == persona_type)

            death_events = query.all()
            
            # Spatial clustering using dictionary (rounding coordinates to grid precision)
            cluster_map: dict[tuple[float, float], dict] = {}
            for ev in death_events:
                grid_x = round(ev.x / grid_precision) * grid_precision
                grid_y = round(ev.y / grid_precision) * grid_precision
                key = (grid_x, grid_y)
                if key not in cluster_map:
                    cluster_map[key] = {"weight": 0, "causes": {}}
                cluster_map[key]["weight"] += 1
                cause = ev.cause_or_source or "Unknown"
                cluster_map[key]["causes"][cause] = cluster_map[key]["causes"].get(cause, 0) + 1

            for (gx, gy), data in cluster_map.items():
                top_cause = max(data["causes"], key=data["causes"].get) if data["causes"] else "Unknown"
                points.append(HeatmapPointResponse(
                    x=gx,
                    y=gy,
                    weight=data["weight"],
                    cause=top_cause
                ))

        elif heatmap_type.upper() == "MOVEMENT":
            query = db.query(PositionSample).join(GameSession, PositionSample.session_id == GameSession.session_id)
            if level_name:
                query = query.filter(PositionSample.level_name == level_name)
            if persona_type and persona_type.upper() != "ALL":
                query = query.filter(GameSession.persona_type == persona_type)

            positions = query.all()
            cluster_map: dict[tuple[float, float], int] = {}
            for pos in positions:
                grid_x = round(pos.x / (grid_precision * 2)) * (grid_precision * 2)
                grid_y = round(pos.y / (grid_precision * 2)) * (grid_precision * 2)
                key = (grid_x, grid_y)
                cluster_map[key] = cluster_map.get(key, 0) + 1

            for (gx, gy), count in cluster_map.items():
                points.append(HeatmapPointResponse(
                    x=gx,
                    y=gy,
                    weight=count,
                    cause=None
                ))

        return points

    @staticmethod
    def get_persona_comparison(db: Session, level_name: Optional[str] = None) -> PersonaComparisonResponse:
        """Compare performance and playstyle metrics across AI personas and human players."""
        query = db.query(GameSession)
        if level_name:
            query = query.filter(GameSession.level_name == level_name)

        sessions = query.all()
        by_persona: dict[str, list[GameSession]] = {}
        for s in sessions:
            by_persona.setdefault(s.persona_type, []).append(s)

        results: list[PersonaMetricResponse] = []
        for persona, p_sessions in by_persona.items():
            count = len(p_sessions)
            completed = sum(1 for s in p_sessions if s.status == "COMPLETED")
            win_rate = round((completed / count) * 100.0, 2)
            
            durations = [s.duration_seconds for s in p_sessions if s.duration_seconds > 0]
            avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
            
            avg_deaths = round(sum(s.total_deaths for s in p_sessions) / count, 2)
            avg_score = round(sum(s.total_score for s in p_sessions) / count, 2)
            avg_items = round(sum(s.items_collected for s in p_sessions) / count, 2)

            results.append(PersonaMetricResponse(
                persona_type=persona,
                session_count=count,
                win_rate_percentage=win_rate,
                avg_duration_seconds=avg_duration,
                avg_deaths=avg_deaths,
                avg_score=avg_score,
                avg_items_collected=avg_items
            ))

        return PersonaComparisonResponse(personas=results)
