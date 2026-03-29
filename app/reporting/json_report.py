"""JSON reporting helpers for audit-friendly pipeline output."""

from __future__ import annotations

from collections import Counter

from ..core.models import AppliedTransformation, DetectedEntity, PipelineSnapshot
from ..core.utils import build_safe_preview, format_field_path


def build_json_report(snapshot: PipelineSnapshot) -> dict[str, object]:
    """Build a privacy-aware JSON-compatible report from a pipeline snapshot."""
    entity_counts = Counter(entity.entity_type.value for entity in snapshot.detections)
    confidence_summary = _build_confidence_summary(snapshot.detections)

    return {
        "input_file": snapshot.source.input_path.name,
        "input_format": snapshot.source.input_format,
        "record_count": snapshot.source.record_count,
        "sanitization_mode": snapshot.request.sanitization_mode.value,
        "entities_found": len(snapshot.detections),
        "entity_counts": dict(sorted(entity_counts.items())),
        "confidence": confidence_summary,
        "output_file": str(snapshot.sanitized_output_path),
        "report_file": str(snapshot.report_output_path),
        "planned_outputs": {
            "sanitized_file": str(snapshot.sanitized_output_path),
            "report_file": str(snapshot.report_output_path),
        },
        "detections": [
            _serialize_detection(entity) for entity in snapshot.detections
        ],
        "transformations": [
            _serialize_transformation(item)
            for item in snapshot.transform_result.applied_transformations
        ],
    }


def _build_confidence_summary(
    detections: list[DetectedEntity] | tuple[DetectedEntity, ...],
) -> dict[str, float] | None:
    """Build an optional confidence summary for the report."""
    if not detections:
        return None

    scores = [entity.confidence for entity in detections]
    return {
        "average": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
    }


def _serialize_detection(entity: DetectedEntity) -> dict[str, object]:
    """Serialize a detection without leaking the raw source value."""
    return {
        "entity_type": entity.entity_type.value,
        "field_path": format_field_path(entity.location.field_path),
        "record_index": entity.location.record_index,
        "char_start": entity.location.char_start,
        "char_end": entity.location.char_end,
        "confidence": entity.confidence,
        "detector_name": entity.detector_name,
        "value_preview": build_safe_preview(entity.value),
    }


def _serialize_transformation(
    transformation: AppliedTransformation,
) -> dict[str, object]:
    """Serialize a transformation summary for audit purposes."""
    return {
        "entity_type": transformation.entity.entity_type.value,
        "mode": transformation.mode.value,
        "field_path": format_field_path(transformation.entity.location.field_path),
        "record_index": transformation.entity.location.record_index,
        "sanitized_preview": build_safe_preview(transformation.sanitized_value),
    }
