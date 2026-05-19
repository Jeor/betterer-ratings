from __future__ import annotations

from typing import Any, cast

from betterer_ratings.core.retry import parse_retry_after
from betterer_ratings.domain.models import PMDBDeleteResult, PMDBSubmitResult


async def delete_mapping_by_id(client: Any, mapping_id: str) -> PMDBDeleteResult:
    response = await client._delete_with_gates(
        url=f"{client.base_url}/api/external/mappings/{mapping_id}",
        contribution_gate=client.mapping_gate,
    )
    return cast(PMDBDeleteResult, client._to_delete_result(
        response,
        endpoint=f"/api/external/mappings/{mapping_id}",
    ))


async def resolve_mapping_duplicate_or_conflict(
    client: Any,
    *,
    tmdb_id: int,
    media_type: str,
    id_type: str,
    id_value: str,
) -> PMDBSubmitResult:
    lookup = await client._fetch_existing_mappings(tmdb_id, media_type)
    if lookup.status in (429, 500, 502, 503, 504, 0):
        return PMDBSubmitResult(
            success=False,
            retryable=True,
            retry_after_seconds=parse_retry_after(lookup.headers.get("retry-after"), 30),
            duplicate_or_exists=False,
            error_text=lookup.text or "PMDB mapping lookup failed",
            item_id=None,
            status_code=lookup.status,
            error_code=client._extract_error_code(lookup.data, lookup.text),
            endpoint="/api/external/mappings",
        )
    if lookup.status == 401:
        return PMDBSubmitResult(
            success=False,
            retryable=True,
            retry_after_seconds=300,
            duplicate_or_exists=False,
            error_text=lookup.text or "PMDB unauthorized while listing mappings",
            item_id=None,
            status_code=lookup.status,
            error_code=client._extract_error_code(lookup.data, lookup.text),
            endpoint="/api/external/mappings",
        )
    if lookup.status == 403:
        return PMDBSubmitResult(
            success=False,
            retryable=False,
            retry_after_seconds=0,
            duplicate_or_exists=False,
            error_text=lookup.text or "PMDB forbidden while listing mappings",
            item_id=None,
            status_code=lookup.status,
            error_code=client._extract_error_code(lookup.data, lookup.text),
            endpoint="/api/external/mappings",
        )

    entries = client._extract_mappings_for_type(lookup.data, id_type)
    # If the exact mapping exists remotely, treat conflict/duplicate as success.
    for entry in entries:
        if client._mapping_entry_matches_value(entry, id_value):
            return PMDBSubmitResult(
                success=True,
                retryable=False,
                retry_after_seconds=0,
                duplicate_or_exists=True,
                error_text="",
                item_id=client._extract_entry_id(entry),
                status_code=200,
                error_code="exists",
                endpoint="/api/external/mappings",
            )

    return PMDBSubmitResult(
        success=False,
        retryable=False,
        retry_after_seconds=0,
        duplicate_or_exists=False,
        error_text=(
            "PMDB reported duplicate/conflict for mapping create, but exact mapping "
            "was not found during confirmation."
        ),
        item_id=None,
        status_code=409,
        error_code="duplicate_unresolved",
        endpoint="/api/external/mappings",
    )


async def submit_mapping(
    client: Any,
    *,
    tmdb_id: int,
    media_type: str,
    id_type: str,
    id_value: str,
) -> PMDBSubmitResult:
    response = await client._post_with_gates(
        url=f"{client.base_url}/api/external/mappings",
        payload={
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "id_type": id_type,
            "id_value": id_value,
        },
        contribution_gate=client.mapping_gate,
    )
    result = client._to_submit_result(
        response,
        endpoint="/api/external/mappings",
    )
    if not result.success and (
        client._is_create_failed_mapping(result) or client._is_duplicate_or_exists_result(result)
    ):
        resolved = await client._resolve_mapping_duplicate_or_conflict(
            tmdb_id=tmdb_id,
            media_type=media_type,
            id_type=id_type,
            id_value=id_value,
        )
        return cast(PMDBSubmitResult, resolved)
    return cast(PMDBSubmitResult, result)
