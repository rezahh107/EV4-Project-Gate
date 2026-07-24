from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from ev4_transition.runners.repo_paths import normalize_repo_relative_ref


@dataclass(frozen=True, slots=True)
class VerifiedArtifactSnapshot:
    """Immutable exact-byte snapshot of one successfully verified artifact.

    ``exact_bytes`` is intentionally excluded from ``repr``. Callers that need
    JSON-safe output must use :meth:`metadata`; raw bytes are never part of
    diagnostics, receipts, service payloads, or UI state.
    """

    artifact_ref: str
    exact_bytes: bytes = field(repr=False)
    sha256: str
    byte_length: int

    def __post_init__(self) -> None:
        normalized = normalize_repo_relative_ref(self.artifact_ref)
        payload = bytes(self.exact_bytes)
        object.__setattr__(self, "artifact_ref", normalized)
        object.__setattr__(self, "exact_bytes", payload)
        self.validate_integrity()

    @classmethod
    def from_verified_bytes(
        cls,
        *,
        artifact_ref: str,
        exact_bytes: bytes,
    ) -> "VerifiedArtifactSnapshot":
        payload = bytes(exact_bytes)
        return cls(
            artifact_ref=artifact_ref,
            exact_bytes=payload,
            sha256=hashlib.sha256(payload).hexdigest(),
            byte_length=len(payload),
        )

    def validate_integrity(self) -> None:
        if self.byte_length != len(self.exact_bytes):
            raise ValueError("Verified artifact byte length mismatch.")
        actual = hashlib.sha256(self.exact_bytes).hexdigest()
        if self.sha256 != actual:
            raise ValueError("Verified artifact SHA-256 mismatch.")

    def metadata(self) -> dict[str, Any]:
        self.validate_integrity()
        return {
            "artifact_ref": self.artifact_ref,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
        }
