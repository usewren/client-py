from __future__ import annotations

from typing import Any, Optional

from wren._http import _AsyncHttpClient, _HttpClient
from wren._types import Permission, _parse_permission


class PermissionsResource:
    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def list(self) -> list[Permission]:
        data = self._http.request("GET", "/api/permissions")
        return [_parse_permission(p) for p in data.get("permissions", [])]

    def create(
        self,
        principal: str,
        resource: str,
        access: str,
        *,
        label_filter: Optional[str] = None,
        filter_lang: Optional[str] = None,
        filter_expr: Optional[str] = None,
        audit_reads: bool = False,
        audit_writes: bool = False,
    ) -> Permission:
        body: dict[str, Any] = {
            "principal": principal,
            "resource": resource,
            "access": access,
            "labelFilter": label_filter,
            "filterLang": filter_lang,
            "filterExpr": filter_expr,
            "auditReads": audit_reads,
            "auditWrites": audit_writes,
        }
        data = self._http.request("POST", "/api/permissions", body=body)
        return _parse_permission(data)

    def update(
        self,
        id: str,
        *,
        access: Optional[str] = None,
        label_filter: Optional[str] = None,
        filter_lang: Optional[str] = None,
        filter_expr: Optional[str] = None,
        audit_reads: Optional[bool] = None,
        audit_writes: Optional[bool] = None,
    ) -> Permission:
        body: dict[str, Any] = {
            "access": access,
            "labelFilter": label_filter,
            "filterLang": filter_lang,
            "filterExpr": filter_expr,
            "auditReads": audit_reads,
            "auditWrites": audit_writes,
        }
        data = self._http.request("PATCH", f"/api/permissions/{id}", body=body)
        return _parse_permission(data)

    def delete(self, id: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"/api/permissions/{id}")  # type: ignore[return-value]


class AsyncPermissionsResource:
    def __init__(self, http: _AsyncHttpClient) -> None:
        self._http = http

    async def list(self) -> list[Permission]:
        data = await self._http.request("GET", "/api/permissions")
        return [_parse_permission(p) for p in data.get("permissions", [])]

    async def create(
        self,
        principal: str,
        resource: str,
        access: str,
        *,
        label_filter: Optional[str] = None,
        filter_lang: Optional[str] = None,
        filter_expr: Optional[str] = None,
        audit_reads: bool = False,
        audit_writes: bool = False,
    ) -> Permission:
        body: dict[str, Any] = {
            "principal": principal,
            "resource": resource,
            "access": access,
            "labelFilter": label_filter,
            "filterLang": filter_lang,
            "filterExpr": filter_expr,
            "auditReads": audit_reads,
            "auditWrites": audit_writes,
        }
        data = await self._http.request("POST", "/api/permissions", body=body)
        return _parse_permission(data)

    async def update(
        self,
        id: str,
        *,
        access: Optional[str] = None,
        label_filter: Optional[str] = None,
        filter_lang: Optional[str] = None,
        filter_expr: Optional[str] = None,
        audit_reads: Optional[bool] = None,
        audit_writes: Optional[bool] = None,
    ) -> Permission:
        body: dict[str, Any] = {
            "access": access,
            "labelFilter": label_filter,
            "filterLang": filter_lang,
            "filterExpr": filter_expr,
            "auditReads": audit_reads,
            "auditWrites": audit_writes,
        }
        data = await self._http.request("PATCH", f"/api/permissions/{id}", body=body)
        return _parse_permission(data)

    async def delete(self, id: str) -> dict[str, Any]:
        return await self._http.request("DELETE", f"/api/permissions/{id}")  # type: ignore[return-value]
