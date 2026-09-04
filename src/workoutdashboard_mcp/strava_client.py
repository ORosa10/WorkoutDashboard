from __future__ import annotations

import os
import time
from typing import Any

import httpx


class StravaAPIError(RuntimeError):
    """Raised when the Strava API returns an error."""


class StravaClient:
    BASE_URL = "https://www.strava.com/api/v3"
    TOKEN_URL = "https://www.strava.com/oauth/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("STRAVA_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET", "").strip()
        self.access_token = os.getenv("STRAVA_ACCESS_TOKEN", "").strip()
        self.refresh_token = os.getenv("STRAVA_REFRESH_TOKEN", "").strip()
        expires_raw = os.getenv("STRAVA_TOKEN_EXPIRES_AT", "0").strip()
        try:
            self.expires_at = int(expires_raw or "0")
        except ValueError:
            self.expires_at = 0

    def configured(self) -> bool:
        return bool(self.access_token)

    def _refresh_if_needed(self) -> None:
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return
        if self.expires_at and time.time() < self.expires_at - 60:
            return

        response = httpx.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=20,
        )
        if response.is_error:
            raise StravaAPIError(
                f"Strava token refresh failed ({response.status_code}): {response.text[:500]}"
            )

        payload = response.json()
        self.access_token = payload["access_token"]
        self.refresh_token = payload.get("refresh_token", self.refresh_token)
        self.expires_at = int(payload.get("expires_at", 0))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self.access_token:
            raise StravaAPIError(
                "Strava is not configured. Set STRAVA_ACCESS_TOKEN, or configure "
                "STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN."
            )

        self._refresh_if_needed()
        response = httpx.request(
            method,
            f"{self.BASE_URL}{path}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
            timeout=30,
        )
        if response.is_error:
            raise StravaAPIError(
                f"Strava API request failed ({response.status_code}): {response.text[:500]}"
            )
        return response.json()

    def list_activities(
        self,
        *,
        after: int | None = None,
        before: int | None = None,
        page: int = 1,
        per_page: int = 30,
    ) -> Any:
        params: dict[str, Any] = {
            "page": max(1, page),
            "per_page": min(max(1, per_page), 200),
        }
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        return self.request("GET", "/athlete/activities", params=params)

    def get_activity(self, activity_id: int) -> Any:
        return self.request("GET", f"/activities/{activity_id}")

    def get_streams(self, activity_id: int, keys: str) -> Any:
        return self.request(
            "GET",
            f"/activities/{activity_id}/streams",
            params={"keys": keys, "key_by_type": "true"},
        )

    def get_athlete_stats(self) -> Any:
        athlete = self.request("GET", "/athlete")
        return self.request("GET", f"/athletes/{athlete['id']}/stats")

    def get_zones(self, activity_id: int) -> Any:
        return self.request("GET", f"/activities/{activity_id}/zones")
