"""Pipeline orchestration and component wiring."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from .models import (
    DetectedEntity,
    PipelineRequest,
    PipelineResult,
    PipelineSnapshot,
    SanitizationMode,
    SourceDocument,
    StructuredData,
    TransformResult,
)
from .utils import (
    build_report_output_path,
    build_sanitized_output_path,
    infer_input_format,
    resolve_input_path,
)


class Ingestor(Protocol):
    """Load a structured document from disk."""

    def __call__(self, source_path: Path) -> StructuredData:
        """Read and return structured content from the source path."""


class Detector(Protocol):
    """Detect PII entities inside a source document."""

    def __call__(self, source: SourceDocument) -> list[DetectedEntity] | tuple[DetectedEntity, ...]:
        """Return the detected entities for a source document."""


class Transformer(Protocol):
    """Apply the chosen sanitization mode to detected entities."""

    def __call__(
        self,
        source: SourceDocument,
        detections: tuple[DetectedEntity, ...],
        sanitization_mode: SanitizationMode,
    ) -> TransformResult:
        """Return the transformed content and its applied changes."""


class Reporter(Protocol):
    """Build an audit report from a pipeline snapshot."""

    def __call__(self, snapshot: PipelineSnapshot) -> dict[str, Any]:
        """Return a JSON-compatible audit payload."""


class PipelineConfigurationError(RuntimeError):
    """Raised when the orchestrator is missing required components."""


class UnsupportedFormatError(ValueError):
    """Raised when no ingestor is available for the requested format."""


class PipelineOrchestrator:
    """Coordinate the read, detect, transform, and report flow."""

    def __init__(
        self,
        *,
        ingestors: Mapping[str, Ingestor] | None = None,
        detector: Detector | None = None,
        transformer: Transformer | None = None,
        reporter: Reporter | None = None,
    ) -> None:
        self._ingestors: dict[str, Ingestor] = {}
        self._detector = detector
        self._transformer = transformer
        self._reporter = reporter

        for input_format, ingestor in (ingestors or {}).items():
            self.register_ingestor(input_format, ingestor)

    def register_ingestor(self, input_format: str, ingestor: Ingestor) -> None:
        """Register or replace an ingestor for an input format."""
        self._ingestors[self._normalize_input_format(input_format)] = ingestor

    def set_detector(self, detector: Detector) -> None:
        """Register the detector component."""
        self._detector = detector

    def set_transformer(self, transformer: Transformer) -> None:
        """Register the transformer component."""
        self._transformer = transformer

    def set_reporter(self, reporter: Reporter) -> None:
        """Register the reporter component."""
        self._reporter = reporter

    @property
    def supported_input_formats(self) -> tuple[str, ...]:
        """Return the currently registered input formats."""
        return tuple(sorted(self._ingestors))

    def run(self, request: PipelineRequest) -> PipelineResult:
        """Execute the pipeline from input read to report generation."""
        source_path = self._resolve_source_path(request)
        source_format = self._resolve_source_format(request, source_path)

        ingestor = self._get_ingestor(source_format)
        detector = self._require_component(self._detector, "detector")
        transformer = self._require_component(self._transformer, "transformer")
        reporter = self._require_component(self._reporter, "reporter")

        source = SourceDocument(
            input_path=source_path,
            input_format=source_format,
            content=ingestor(source_path),
        )
        detections = tuple(detector(source))
        transform_result = transformer(source, detections, request.sanitization_mode)

        sanitized_output_path = build_sanitized_output_path(
            source_path,
            request.sanitization_mode.value,
            request.output_dir,
        )
        report_output_path = build_report_output_path(
            source_path,
            request.sanitization_mode.value,
            request.report_format.value,
            request.output_dir,
        )

        snapshot = PipelineSnapshot(
            request=request,
            source=source,
            detections=detections,
            transform_result=transform_result,
            sanitized_output_path=sanitized_output_path,
            report_output_path=report_output_path,
        )
        report = reporter(snapshot)

        return PipelineResult(
            request=request,
            source=source,
            detections=detections,
            transform_result=transform_result,
            report=report,
            sanitized_output_path=sanitized_output_path,
            report_output_path=report_output_path,
        )

    def _resolve_source_path(self, request: PipelineRequest) -> Path:
        """Resolve the request path, allowing virtual sources such as database scans."""
        if request.source_format and self._normalize_input_format(request.source_format) == "db":
            return Path(request.input_path).expanduser()
        return resolve_input_path(request.input_path)

    def _resolve_source_format(self, request: PipelineRequest, source_path: Path) -> str:
        """Resolve the source format from the request or file extension."""
        if request.source_format:
            return self._normalize_input_format(request.source_format)

        supported_formats = self.supported_input_formats
        if not supported_formats:
            raise PipelineConfigurationError(
                "No ingestors have been registered with the pipeline orchestrator."
            )
        return infer_input_format(source_path, supported_formats)

    def _get_ingestor(self, input_format: str) -> Ingestor:
        """Return the ingestor for a given format or raise a clear error."""
        normalized_format = self._normalize_input_format(input_format)
        ingestor = self._ingestors.get(normalized_format)
        if ingestor is None:
            supported_list = ", ".join(self.supported_input_formats) or "none"
            raise UnsupportedFormatError(
                f"No ingestor registered for '{normalized_format}'. Registered formats: {supported_list}"
            )
        return ingestor

    @staticmethod
    def _normalize_input_format(input_format: str) -> str:
        """Normalize input format strings such as '.CSV' into 'csv'."""
        return input_format.lower().lstrip(".")

    @staticmethod
    def _require_component(component: Any, component_name: str) -> Any:
        """Ensure a required pipeline component has been configured."""
        if component is None:
            raise PipelineConfigurationError(
                f"The pipeline requires a configured {component_name} component."
            )
        return component


def run_pipeline(
    request: PipelineRequest,
    *,
    ingestors: Mapping[str, Ingestor],
    detector: Detector,
    transformer: Transformer,
    reporter: Reporter,
) -> PipelineResult:
    """Convenience helper for one-off pipeline executions."""
    orchestrator = PipelineOrchestrator(
        ingestors=ingestors,
        detector=detector,
        transformer=transformer,
        reporter=reporter,
    )
    return orchestrator.run(request)

