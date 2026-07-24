from __future__ import annotations

from pathlib import Path
from typing import Any

from ev4_transition.diagnostics import Diagnostic, diagnostic
from ev4_transition.producer_gate_export import ProducerGateExportValidator


class OperationalProducerGateExportValidator(ProducerGateExportValidator):
    """Validate operational Producer authority against the actual owner checkout.

    Contract schemas remain Project Gate-owned, while referenced artifact bytes are
    resolved relative to the producer checkout that owns those artifacts.
    """

    def __init__(self, project_gate_root: str | Path, artifact_root: str | Path) -> None:
        super().__init__(project_gate_root, operational=True)
        self.artifact_root = Path(artifact_root)

    def _resolve_reference(self, artifact_ref: Any) -> tuple[Path | None, Diagnostic | None]:
        if not isinstance(artifact_ref, str) or not artifact_ref:
            return None, diagnostic(
                "PG_EXPORT_OUTPUT_REF_MISSING",
                "error",
                "Consequential output requires artifact_ref.",
                "$.stage_manifest",
            )
        try:
            root = self.artifact_root.resolve(strict=True)
            candidate = (root / artifact_ref).resolve(strict=True)
            candidate.relative_to(root)
        except FileNotFoundError:
            return None, diagnostic(
                "PG_EXPORT_REFERENCED_ARTIFACT_MISSING",
                "error",
                "Consequential referenced artifact does not exist.",
                "$.stage_manifest",
                artifact_ref=artifact_ref,
            )
        except (OSError, RuntimeError, ValueError):
            return None, diagnostic(
                "PG_EXPORT_REFERENCED_ARTIFACT_PATH_UNSAFE",
                "error",
                "Consequential referenced artifact path is unsafe.",
                "$.stage_manifest",
                artifact_ref=artifact_ref,
            )
        if not candidate.is_file():
            return None, diagnostic(
                "PG_EXPORT_REFERENCED_ARTIFACT_NOT_FILE",
                "error",
                "Consequential referenced artifact must be a regular file.",
                "$.stage_manifest",
                artifact_ref=artifact_ref,
            )
        return candidate, None
