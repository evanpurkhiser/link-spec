"""Validation helpers for cold-process Rekordbox health captures."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable


def event_signature(event: dict) -> dict:
    message = event.get("message", "")

    def field(pattern: str) -> str | None:
        match = re.search(pattern, message, re.IGNORECASE)
        return match.group(1).strip() if match else None

    return {
        "provider": event.get("provider"),
        "event_id": event.get("event_id"),
        "level": event.get("level"),
        "application": field(r"Faulting application name:\s*([^,\r\n]+)"),
        "module": field(r"Faulting module name:\s*([^,\r\n]+)"),
        "exception_code": field(r"Exception code:\s*([^\r\n]+)"),
        "fault_offset": field(r"Fault offset:\s*([^\r\n]+)"),
    }


def health_signature(document: dict) -> dict:
    if document.get("schema_version") != 2:
        raise ValueError("Rekordbox health evidence must use schema 2")
    processes = document.get("rekordbox_processes")
    events = document.get("application_events")
    if not isinstance(processes, list) or not isinstance(events, list):
        raise ValueError("Rekordbox health evidence is incomplete")
    if document.get("rekordbox_process_count") != len(processes):
        raise ValueError("Rekordbox process count differs from process list")

    return {
        "process_count": len(processes),
        "responding_count": sum(process.get("responding") is True for process in processes),
        "application_events": [event_signature(event) for event in events],
    }


def validate_health_pair(
    evidence: Path,
    receipt: dict,
    label_prefix: str,
    sha256: Callable[[Path], str],
) -> dict:
    signatures = {}
    for phase in ("record", "repeat"):
        for position in ("before", "after"):
            name = f"{phase}-health-{position}.json"
            path = evidence / name
            receipt_field = f"{phase}_health_{position}_sha256"
            if receipt.get(receipt_field) != sha256(path):
                raise ValueError(f"{label_prefix}: receipt {receipt_field} does not match")
            document = json.loads(path.read_text())
            if document.get("label") != f"{label_prefix}-{phase}-{position}":
                raise ValueError(f"{label_prefix}: {name} label does not match")
            signatures[f"{phase}_{position}"] = health_signature(document)

        before = signatures[f"{phase}_before"]
        if before["process_count"] != 1 or before["responding_count"] != 1:
            raise ValueError(f"{label_prefix}: {phase} did not start with one responsive process")
        if before["application_events"]:
            raise ValueError(f"{label_prefix}: {phase} began with an Application event")

    if signatures["record_after"] != signatures["repeat_after"]:
        raise ValueError(f"{label_prefix}: record/repeat post-request health differs")

    return signatures["record_after"]
