"""Frozen declarative profiles for the Attack Overlay trace family."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttackOverlayTraceProfile:
    profile_name: str
    blocked_path: str


ATTACK_OVERLAY_TRACE_PROFILES = (
    AttackOverlayTraceProfile(
        profile_name="ATTACK_OVERLAY_T07_V2",
        blocked_path="request.amount",
    ),
    AttackOverlayTraceProfile(
        profile_name="ATTACK_OVERLAY_T08_V2",
        blocked_path="request.payee",
    ),
)


__all__ = [
    "ATTACK_OVERLAY_TRACE_PROFILES",
    "AttackOverlayTraceProfile",
]
