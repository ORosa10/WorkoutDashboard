from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from .strava_client import StravaAPIError, StravaClient

mcp = FastMCP("WorkoutDashboard – Strava")
strava = StravaClient()


def _error(exc: Exception) -> dict[str, Any]:
    return {"ok": False, "error": str(exc)}


@mcp.tool()
def connection_status() -> dict[str, Any]:
    """Return whether the connector has a Strava token configured."""
    return {
        "ok": True,
        "provider": "Strava",
        "configured": strava.configured(),
        "read_scope_expected": "activity:read or activity:read_all",
    }


@mcp.tool()
def list_activities(
    days: int = 30,
    page: int = 1,
    per_page: int = 30,
) -> dict[str, Any]:
    """List the authenticated athlete's activities from the last N days."""
    try:
        after = int((datetime.now(timezone.utc) - timedelta(days=max(1, days))).timestamp())
        return {
            "ok": True,
            "days": days,
            "activities": strava.list_activities(
                after=after,
                page=page,
                per_page=per_page,
            ),
        }
    except StravaAPIError as exc:
        return _error(exc)


@mcp.tool()
def get_activity(activity_id: int) -> dict[str, Any]:
    """Get detailed data for one Strava activity."""
    try:
        return {"ok": True, "activity": strava.get_activity(activity_id)}
    except StravaAPIError as exc:
        return _error(exc)


@mcp.tool()
def get_activity_streams(
    activity_id: int,
    keys: str = "time,distance,heartrate,watts,cadence,velocity_smooth,altitude",
) -> dict[str, Any]:
    """Get time-series streams for one activity."""
    try:
        return {
            "ok": True,
            "activity_id": activity_id,
            "streams": strava.get_streams(activity_id, keys),
        }
    except StravaAPIError as exc:
        return _error(exc)


@mcp.tool()
def get_activity_zones(activity_id: int) -> dict[str, Any]:
    """Get heart-rate and power-zone distributions for one activity."""
    try:
        return {
            "ok": True,
            "activity_id": activity_id,
            "zones": strava.get_zones(activity_id),
        }
    except StravaAPIError as exc:
        return _error(exc)


@mcp.tool()
def get_athlete_stats() -> dict[str, Any]:
    """Get recent, year-to-date and all-time activity totals."""
    try:
        return {"ok": True, "stats": strava.get_athlete_stats()}
    except StravaAPIError as exc:
        return _error(exc)


@mcp.tool()
def get_training_summary(days: int = 28) -> dict[str, Any]:
    """Summarize recent training volume by sport type."""
    try:
        days = min(max(1, days), 365)
        after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        activities = strava.list_activities(after=after, page=1, per_page=200)

        summary: dict[str, dict[str, float]] = {}
        for activity in activities:
            sport = activity.get("sport_type") or activity.get("type") or "Unknown"
            bucket = summary.setdefault(
                sport,
                {"sessions": 0, "moving_time_seconds": 0, "distance_m": 0, "elevation_m": 0},
            )
            bucket["sessions"] += 1
            bucket["moving_time_seconds"] += float(activity.get("moving_time") or 0)
            bucket["distance_m"] += float(activity.get("distance") or 0)
            bucket["elevation_m"] += float(activity.get("total_elevation_gain") or 0)

        return {
            "ok": True,
            "days": days,
            "from_utc": datetime.fromtimestamp(after, tz=timezone.utc).isoformat(),
            "activity_count": len(activities),
            "by_sport": summary,
        }
    except StravaAPIError as exc:
        return _error(exc)


# ASGI application used by uvicorn and hosted deployments.
app = mcp.streamable_http_app()


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="streamable-http", port=port)
