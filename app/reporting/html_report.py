"""HTML reporting helpers."""

from __future__ import annotations

from ..core.models import PipelineSnapshot
from ..core.utils import format_field_path


def build_html_report(snapshot: PipelineSnapshot) -> str:
    """Build a simple HTML report for audits."""
    rows = "\n".join(
        f"<tr><td>{item.entity_type.value}</td><td>{format_field_path(item.location.field_path)}</td><td>{item.location.record_index}</td></tr>"
        for item in snapshot.detections
    )

    return f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <title>DataShield Report</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; }}
      th {{ background-color: #f4f4f4; text-align: left; }}
    </style>
  </head>
  <body>
    <h1>DataShield Report</h1>
    <p><strong>Input file:</strong> {snapshot.source.input_path.name}</p>
    <p><strong>Sanitization mode:</strong> {snapshot.request.sanitization_mode.value}</p>
    <p><strong>Total detections:</strong> {len(snapshot.detections)}</p>

    <h2>Detections</h2>
    <table>
      <thead>
        <tr><th>Type</th><th>Field</th><th>Record</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </body>
</html>
"""
