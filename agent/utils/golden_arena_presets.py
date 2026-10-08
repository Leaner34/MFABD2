"""GameKee Golden Arena presets (data only; no UI clicks in this module).

Keep draft presets separate from the existing Mirror Wars PVP pipeline.
Until the PC formation, action order, and blessings have been transcribed and
verified from in-game screenshots, the catalog must not drive game actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "golden_arena_presets.json"


class GoldenArenaPresetError(ValueError):
    """Invalid or incomplete Golden Arena preset data."""


def validate_catalog(catalog: Any) -> None:
    """Reject malformed references before any later UI implementation uses them."""
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise GoldenArenaPresetError("Unsupported Golden Arena preset schema")

    costumes = catalog.get("costumes")
    presets = catalog.get("presets")
    if not isinstance(costumes, dict) or not costumes:
        raise GoldenArenaPresetError("Costume catalog must be a non-empty object")
    if not isinstance(presets, list) or not presets:
        raise GoldenArenaPresetError("Presets must be a non-empty list")

    for costume_id, info in costumes.items():
        if not isinstance(costume_id, str) or not costume_id:
            raise GoldenArenaPresetError("Costume IDs must be non-empty strings")
        if not isinstance(info, dict) or not all(
            isinstance(info.get(k), str) and info[k].strip()
            for k in ("character", "costume")
        ):
            raise GoldenArenaPresetError("Invalid costume: " + costume_id)

    seen = set()
    for preset in presets:
        if not isinstance(preset, dict):
            raise GoldenArenaPresetError("Each preset must be an object")
        preset_id = preset.get("id")
        if not isinstance(preset_id, str) or not preset_id:
            raise GoldenArenaPresetError("Missing preset ID")
        if preset_id in seen:
            raise GoldenArenaPresetError("Duplicate preset ID: " + preset_id)
        seen.add(preset_id)

        roster = preset.get("roster")
        if not isinstance(roster, list) or not roster or not all(
            isinstance(item, str) for item in roster
        ):
            raise GoldenArenaPresetError("Invalid roster: " + preset_id)
        if len(roster) != len(set(roster)):
            raise GoldenArenaPresetError("Duplicate costume in: " + preset_id)
        if any(item not in costumes for item in roster):
            raise GoldenArenaPresetError("Unknown costume in: " + preset_id)

        blessings = preset.get("blessings")
        if not isinstance(blessings, dict) or set(blessings) != {"first", "second"}:
            raise GoldenArenaPresetError("Missing first/second blessings: " + preset_id)


def load_catalog(path: Optional[Path] = None) -> Dict[str, Any]:
    with (path or DEFAULT_PATH).open("r", encoding="utf-8") as stream:
        catalog = json.load(stream)
    validate_catalog(catalog)
    return catalog


def get_preset(preset_id: str, path: Optional[Path] = None) -> Dict[str, Any]:
    catalog = load_catalog(path)
    for preset in catalog["presets"]:
        if preset["id"] == preset_id:
            return preset
    raise KeyError("Unknown Golden Arena preset: " + preset_id)


def require_complete_preset(preset: Dict[str, Any]) -> None:
    """Data completeness gate, NOT a claim that the PC GUI is validated.

    The future PC pipeline must additionally verify game state after each
    operation; passing this function alone never authorizes blind clicking.
    """
    preset_id = preset.get("id", "<unknown>")
    roster = preset.get("roster")
    positions = preset.get("formation")
    order = preset.get("action_order")
    blessings = preset.get("blessings")
    if not isinstance(roster, list) or not roster:
        raise GoldenArenaPresetError("Missing roster: " + preset_id)
    if not isinstance(positions, dict) or set(positions) != set(roster):
        raise GoldenArenaPresetError("Formation not transcribed: " + preset_id)
    if any(
        not isinstance(xy, list)
        or len(xy) != 2
        or any(type(v) is not int or v < 0 for v in xy)
        for xy in positions.values()
    ):
        raise GoldenArenaPresetError("Invalid formation grid: " + preset_id)
    if len({tuple(xy) for xy in positions.values()}) != len(roster):
        raise GoldenArenaPresetError("Overlapping formation cells: " + preset_id)
    if not isinstance(order, list) or len(order) != len(roster) or set(order) != set(roster):
        raise GoldenArenaPresetError("Action order not transcribed: " + preset_id)
    if not isinstance(blessings, dict) or any(
        not isinstance(blessings.get(side), list) or not blessings[side]
        for side in ("first", "second")
    ):
        raise GoldenArenaPresetError("First/second blessings not transcribed: " + preset_id)
