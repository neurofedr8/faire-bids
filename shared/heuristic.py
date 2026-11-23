"""Indexing heuristic of this stream; `faire index` loads it from the stream's history.

Each top-level entry of the received directory is one item (a session folder or file).
Settings come from `heuristic.yml` next to this file, rendered from the template answers:

- `item_pattern`: regex the item name must fully match; its named groups are the sample
  entities of the ma-DMP, plus optional `instrument` and `pilot` groups;
- `instrument_from`: `dicom` (DICOM headers, formatted with `dicom_instrument_format`),
  `name` (the `instrument` group) or `single` (always `single_instrument`);
- `place_format`: path of the item in the stream instance, formatted with its entities.
"""

import re
from pathlib import Path

import yaml

CONFIG = yaml.safe_load(Path(__file__).with_name("heuristic.yml").read_text())
ITEM_PATTERN = re.compile(CONFIG["item_pattern"])
NOT_ENTITIES = ("instrument", "pilot")


def _match(item: Path) -> re.Match:
    match = ITEM_PATTERN.fullmatch(item.name)
    if match is None:
        raise ValueError(f"{item.name!r} does not match {ITEM_PATTERN.pattern!r}")
    return match


def _clean(value: str) -> str:
    """Identifier-safe value: letters, digits and '-' only."""
    return re.sub(r"[^A-Za-z0-9-]", "", str(value))


def _dicom_instrument(item: Path) -> str:
    try:
        import pydicom
    except ImportError as exc:
        raise RuntimeError("instrument_from=dicom needs pydicom where `faire index` runs") from exc
    template = CONFIG["dicom_instrument_format"]
    files = [item] if item.is_file() else sorted(p for p in item.rglob("*") if p.is_file())
    for path in files:
        try:
            header = pydicom.dcmread(path, stop_before_pixels=True)
        except Exception:  # not a DICOM file
            continue
        fields = {name: _clean(getattr(header, name, ""))
                  for name in re.findall(r"{(\w+)}", template)}
        return template.format(**fields)
    raise ValueError(f"{item.name!r} holds no readable DICOM file")


def instrument(item: Path) -> str:
    """Identifier of the instrument that produced the item, as declared in the ma-DMP."""
    source = CONFIG["instrument_from"]
    if source == "dicom":
        return _dicom_instrument(item)
    if source == "name":
        return _clean(_match(item).group("instrument"))
    return CONFIG["single_instrument"]


def entities(item: Path) -> dict[str, str]:
    """Sample entities of the item, from the named groups of the item pattern."""
    groups = _match(item).groupdict()
    return {k: v for k, v in groups.items() if k not in NOT_ENTITIES and v is not None}


def place(item: Path, entities: dict[str, str]) -> str:
    """Path of the item inside the stream instance."""
    return CONFIG["place_format"].format(**entities)


def pilot(item: Path, entities: dict[str, str]) -> bool:
    """True when the `pilot` group of the item pattern matched."""
    return "pilot" in ITEM_PATTERN.groupindex and _match(item).group("pilot") is not None
