"""Shared domain models for the processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | dict[str, "JsonValue"] | list["JsonValue"]
StructuredData: TypeAlias = JsonValue
FieldPathPart: TypeAlias = str | int
FieldPath: TypeAlias = tuple[FieldPathPart, ...]


class EntityType(StrEnum):
    """Supported PII entity categories."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    TAX_CODE = "TAX_CODE"
    IBAN = "IBAN"
    BIRTH_DATE = "BIRTH_DATE"
    ADDRESS = "ADDRESS"
    IP_ADDRESS = "IP_ADDRESS"
    PERSON_NAME = "PERSON_NAME"


class SanitizationMode(StrEnum):
    """Supported protection strategies."""

    MASK = "mask"
    REDACT = "redact"
    PSEUDONYMIZE = "pseudonymize"


class ReportFormat(StrEnum):
    """Supported audit report formats."""

    JSON = "json"
    HTML = "html"


@dataclass(slots=True, frozen=True)
class EntityLocation:
    """Describe where a detection was found inside a structured document."""

    field_path: FieldPath = field(default_factory=tuple)
    record_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(slots=True, frozen=True)
class DetectedEntity:
    """Represent a single detected PII occurrence."""

    entity_type: EntityType
    value: str
    location: EntityLocation = field(default_factory=EntityLocation)
    confidence: float = 1.0
    detector_name: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class SourceDocument:
    """Canonical representation of an ingested input file."""

    input_path: Path
    input_format: str
    content: StructuredData

    @property
    def record_count(self) -> int:
        """Return a best-effort record count for structured inputs."""
        if isinstance(self.content, list):
            return len(self.content)
        if isinstance(self.content, dict):
            return len(self.content)
        return 1


@dataclass(slots=True, frozen=True)
class PipelineRequest:
    """Describe a processing request from input file to report outputs."""

    input_path: Path
    sanitization_mode: SanitizationMode = SanitizationMode.MASK
    output_dir: Path | None = None
    report_format: ReportFormat = ReportFormat.JSON
    source_format: str | None = None


@dataclass(slots=True, frozen=True)
class AppliedTransformation:
    """Capture how a detected entity was protected."""

    entity: DetectedEntity
    mode: SanitizationMode
    sanitized_value: str


@dataclass(slots=True)
class TransformResult:
    """Contain the transformed content and the applied changes."""

    content: StructuredData
    applied_transformations: list[AppliedTransformation] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class PipelineSnapshot:
    """Immutable snapshot handed to reporting components."""

    request: PipelineRequest
    source: SourceDocument
    detections: tuple[DetectedEntity, ...]
    transform_result: TransformResult
    sanitized_output_path: Path
    report_output_path: Path


@dataclass(slots=True, frozen=True)
class PipelineResult:
    """Final result returned by the central orchestrator."""

    request: PipelineRequest
    source: SourceDocument
    detections: tuple[DetectedEntity, ...]
    transform_result: TransformResult
    report: dict[str, Any] | str
    sanitized_output_path: Path
    report_output_path: Path

    @property
    def entity_counts(self) -> dict[str, int]:
        """Aggregate detections by entity type."""
        counts: dict[str, int] = {}
        for entity in self.detections:
            key = entity.entity_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def total_transformations(self) -> int:
        """Return the number of protected values applied by the transformer."""
        return len(self.transform_result.applied_transformations)
