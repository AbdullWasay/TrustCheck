"""Lightweight Supabase REST helper (avoids heavy supabase-py on Vercel)."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx


class SupabaseRestError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class SupabaseRest:
    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: Optional[dict[str, str]] = None,
        json_body: Any = None,
    ) -> list[dict[str, Any]]:
        endpoint = f"{self.url}/rest/v1/{table}"
        try:
            response = httpx.request(
                method,
                endpoint,
                headers=self.headers,
                params=params,
                json=json_body,
                timeout=20.0,
            )
        except httpx.HTTPError as exc:
            raise SupabaseRestError(f"Supabase request failed: {exc}") from exc

        if response.status_code >= 400:
            raise SupabaseRestError(
                f"Supabase error ({response.status_code}): {response.text}",
                status_code=response.status_code,
            )

        if not response.content:
            return []

        data = response.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def select(
        self,
        table: str,
        *,
        columns: str = "*",
        filters: Optional[dict[str, str]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"select": columns}
        if filters:
            params.update(filters)
        if order:
            params["order"] = order
        if limit is not None:
            params["limit"] = str(limit)
        return self._request("GET", table, params=params)

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        return self._request("POST", table, json_body=row)

    def update(
        self,
        table: str,
        row: dict[str, Any],
        *,
        filters: dict[str, str],
    ) -> list[dict[str, Any]]:
        return self._request("PATCH", table, params=filters, json_body=row)


def get_rest_client() -> SupabaseRest:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = (
        os.getenv("SUPABASE_SECRET_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or ""
    ).strip()

    if not supabase_url or not supabase_key:
        raise SupabaseRestError(
            "Missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY in environment variables."
        )

    return SupabaseRest(supabase_url, supabase_key)
