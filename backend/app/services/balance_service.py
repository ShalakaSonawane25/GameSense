"""Rule-based Game Balancing Recommendation Engine."""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.session import GameSession
from app.models.telemetry import GameplayEvent, PositionSample
from app.models.recommendation import BalanceRecommendation
from app.schemas.recommendation import RecommendationResponse

class BalanceService:
    @staticmethod
    def analyze_and_generate_recommendations(
        db: Session,
        level_name: Optional[str] = "Level_1"
    ) -> list[BalanceRecommendation]:
        """
        Executes rule-based heuristics on telemetry data to discover game balance issues
        and generate actionable suggestions for game designers.
        """
        created_recommendations: list[BalanceRecommendation] = []

        # 1. Fetch sessions for the specified level
        sessions_query = db.query(GameSession)
        if level_name:
            sessions_query = sessions_query.filter(GameSession.level_name == level_name)
        sessions = sessions_query.all()

        if len(sessions) < 2:
            # Need at least 2 sessions to establish a pattern
            return []

        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.status == "COMPLETED")
        overall_win_rate = (completed_sessions / total_sessions) * 100.0

        # 2. Fetch all death events for the level
        deaths_query = db.query(GameplayEvent).filter(
            GameplayEvent.event_type == "DEATH"
        )
        if level_name:
            deaths_query = deaths_query.filter(GameplayEvent.level_name == level_name)
        deaths = deaths_query.all()
        total_deaths = len(deaths)

        # -------------------------------------------------------------
        # HEURISTIC 1: Severe Death Hotspots (Difficulty Spikes)
        # -------------------------------------------------------------
        if total_deaths > 0:
            # Cluster deaths by spatial proximity (grid size: 3.0 units)
            spatial_death_clusters: dict[tuple[float, float], list[GameplayEvent]] = {}
            for d in deaths:
                gx = round(d.x / 3.0) * 3.0
                gy = round(d.y / 3.0) * 3.0
                spatial_death_clusters.setdefault((gx, gy), []).append(d)

            for (cx, cy), cluster_events in spatial_death_clusters.items():
                death_count = len(cluster_events)
                cluster_ratio = death_count / total_deaths

                # If a single zone causes >= 25% of all deaths or >= 3 deaths
                if death_count >= 3 or cluster_ratio >= 0.25:
                    causes = [e.cause_or_source for e in cluster_events if e.cause_or_source]
                    top_cause = max(set(causes), key=causes.count) if causes else "Unknown Hazard"
                    
                    coords_json = json.dumps({"x": cx, "y": cy})
                    
                    if "trap" in top_cause.lower() or "spike" in top_cause.lower() or "pit" in top_cause.lower():
                        msg = f"Severe hazard bottleneck at coordinate ({cx}, {cy}). {death_count} players died to '{top_cause}'."
                        action = f"Reduce trigger speed of {top_cause} by 20% or add a visible warning cue and health pickup before this section."
                        category = "DIFFICULTY_SPIKE"
                        severity = "HIGH" if cluster_ratio > 0.4 else "MEDIUM"
                    else:
                        msg = f"Excessive player deaths ({death_count} casualties) concentrated near ({cx}, {cy}) caused by '{top_cause}'."
                        action = f"Consider lowering {top_cause} attack damage by 15% or spacing out enemy patrol routes."
                        category = "DIFFICULTY_SPIKE"
                        severity = "HIGH" if cluster_ratio > 0.4 else "MEDIUM"

                    rec = BalanceRecommendation(
                        level_name=level_name or "Level_1",
                        issue_category=category,
                        severity=severity,
                        message=msg,
                        suggested_action=action,
                        target_coordinates=coords_json,
                        created_at=datetime.utcnow()
                    )
                    db.add(rec)
                    created_recommendations.append(rec)

        # -------------------------------------------------------------
        # HEURISTIC 2: Level Too Easy / Under-Challenging
        # -------------------------------------------------------------
        if overall_win_rate >= 90.0 and total_sessions >= 3:
            rec = BalanceRecommendation(
                level_name=level_name or "Level_1",
                issue_category="UNDER_CHALLENGING",
                severity="LOW",
                message=f"Level has an unusually high win rate of {overall_win_rate:.1f}% across all test sessions.",
                suggested_action="Introduce dynamic enemy scaling or additional environmental hazards in the middle section.",
                target_coordinates=None,
                created_at=datetime.utcnow()
            )
            db.add(rec)
            created_recommendations.append(rec)

        # -------------------------------------------------------------
        # HEURISTIC 3: Persona Disparity (Beginner vs Speedrunner)
        # -------------------------------------------------------------
        beginner_sessions = [s for s in sessions if s.persona_type == "BEGINNER"]
        speedrunner_sessions = [s for s in sessions if s.persona_type == "SPEEDRUNNER"]

        if beginner_sessions and speedrunner_sessions:
            beg_wins = sum(1 for s in beginner_sessions if s.status == "COMPLETED")
            beg_winrate = (beg_wins / len(beginner_sessions)) * 100.0
            
            spd_wins = sum(1 for s in speedrunner_sessions if s.status == "COMPLETED")
            spd_winrate = (spd_wins / len(speedrunner_sessions)) * 100.0

            if spd_winrate >= 80.0 and beg_winrate <= 30.0:
                rec = BalanceRecommendation(
                    level_name=level_name or "Level_1",
                    issue_category="PACING",
                    severity="HIGH",
                    message=f"Significant persona disparity: Speedrunners succeed {spd_winrate:.0f}% of the time, while Beginners pass only {beg_winrate:.0f}%.",
                    suggested_action="Add checkpoint indicators or simplify initial jump mechanics to flatten the beginner learning curve.",
                    target_coordinates=None,
                    created_at=datetime.utcnow()
                )
                db.add(rec)
                created_recommendations.append(rec)

        # Commit new recommendations to SQLite
        if created_recommendations:
            db.commit()
            for r in created_recommendations:
                db.refresh(r)

        return created_recommendations

    @staticmethod
    def get_existing_recommendations(
        db: Session,
        level_name: Optional[str] = None
    ) -> list[BalanceRecommendation]:
        """Fetch saved recommendations from the database."""
        query = db.query(BalanceRecommendation)
        if level_name:
            query = query.filter(BalanceRecommendation.level_name == level_name)
        return query.order_by(BalanceRecommendation.created_at.desc()).all()
