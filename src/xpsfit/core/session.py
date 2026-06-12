"""Project save/load: .xfp files (JSON)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .spectrum import Region

FORMAT_VERSION = 1
EXTENSION = ".xfp"


@dataclass
class Session:
    regions: list[Region] = field(default_factory=list)
    notes: str = ""
    path: Path | None = None

    def to_dict(self) -> dict:
        return {
            "format": "xpsfit-project",
            "version": FORMAT_VERSION,
            "notes": self.notes,
            "regions": [r.to_dict() for r in self.regions],
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path).with_suffix(EXTENSION)
        path.write_text(json.dumps(self.to_dict(), indent=1), encoding="utf-8")
        self.path = path
        return path

    @classmethod
    def load(cls, path: str | Path) -> "Session":
        path = Path(path)
        d = json.loads(path.read_text(encoding="utf-8"))
        if d.get("format") != "xpsfit-project":
            raise ValueError(f"{path.name} is not an XPSFit project file")
        s = cls(
            regions=[Region.from_dict(rd) for rd in d.get("regions", [])],
            notes=d.get("notes", ""),
        )
        s.path = path
        return s
