"""Data model: Region (one acquisition window) holding data, background spec, peaks.

Conventions:
- x is binding energy (eV), stored ascending internally; plots reverse the axis.
- Peak areas are the integral of the component within the region window, so they
  feed directly into RSF quantification.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

PEAK_SHAPES = ("GL_SUM", "GL_PRODUCT", "VOIGT", "GL_TAIL", "DONIACH")
BACKGROUND_TYPES = ("NONE", "LINEAR", "SHIRLEY", "SHIRLEY_LINEAR", "TOUGAARD")


@dataclass
class ParamSpec:
    """One fittable parameter, mirroring lmfit semantics.

    expr links this parameter to another peak's, e.g. "p0_center + 17.3"
    (XPSPEAK's "Relation with another peak"). When expr is set, value/vary
    are ignored by the fit.
    """

    value: float = 0.0
    vary: bool = True
    min: float = -math.inf
    max: float = math.inf
    expr: str | None = None

    def to_dict(self) -> dict:
        d = {"value": self.value, "vary": self.vary}
        if math.isfinite(self.min):
            d["min"] = self.min
        if math.isfinite(self.max):
            d["max"] = self.max
        if self.expr:
            d["expr"] = self.expr
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ParamSpec":
        return cls(
            value=d.get("value", 0.0),
            vary=d.get("vary", True),
            min=d.get("min", -math.inf),
            max=d.get("max", math.inf),
            expr=d.get("expr"),
        )


def _spec(value: float, lo: float = -math.inf, hi: float = math.inf) -> ParamSpec:
    return ParamSpec(value=value, min=lo, max=hi)


@dataclass
class Peak:
    """One fit component.

    mix is %Lorentzian (0=pure Gaussian, 100=pure Lorentzian), XPSPEAK convention.
    asym: GL_TAIL -> exponential tail decay length toward high BE (eV, 0=symmetric);
          DONIACH -> alpha asymmetry parameter.
    """

    label: str = ""
    shape: str = "GL_SUM"
    # peak role: "single" | "doublet_main" | "doublet_partner" | "satellite"
    kind: str = "single"
    # pinned: the whole peak is frozen during fits (others keep optimizing)
    pinned: bool = False
    center: ParamSpec = field(default_factory=ParamSpec)
    area: ParamSpec = field(default_factory=ParamSpec)
    fwhm: ParamSpec = field(default_factory=ParamSpec)
    mix: ParamSpec = field(default_factory=lambda: ParamSpec(value=30.0, min=0.0, max=100.0))
    asym: ParamSpec = field(default_factory=lambda: ParamSpec(value=0.0, vary=False, min=0.0, max=5.0))

    @classmethod
    def create(
        cls,
        center: float,
        area: float = 1000.0,
        fwhm: float = 1.5,
        mix: float = 30.0,
        shape: str = "GL_SUM",
        label: str = "",
        asym: float = 0.0,
    ) -> "Peak":
        p = cls(
            label=label,
            shape=shape,
            center=_spec(center, center - 2.0, center + 2.0),
            area=_spec(area, 0.0),
            fwhm=_spec(fwhm, 0.2, 6.0),
            mix=ParamSpec(value=mix, min=0.0, max=100.0),
            asym=ParamSpec(value=asym, vary=asym > 0, min=0.0, max=5.0),
        )
        return p

    PARAM_NAMES = ("center", "area", "fwhm", "mix", "asym")

    def params(self) -> dict[str, ParamSpec]:
        return {n: getattr(self, n) for n in self.PARAM_NAMES}

    def to_dict(self) -> dict:
        d = {
            "label": self.label,
            "shape": self.shape,
            **{n: getattr(self, n).to_dict() for n in self.PARAM_NAMES},
        }
        if self.kind != "single":
            d["kind"] = self.kind
        if self.pinned:
            d["pinned"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Peak":
        p = cls(label=d.get("label", ""), shape=d.get("shape", "GL_SUM"),
                kind=d.get("kind", "single"), pinned=d.get("pinned", False))
        for n in cls.PARAM_NAMES:
            if n in d:
                setattr(p, n, ParamSpec.from_dict(d[n]))
        return p


@dataclass
class BackgroundSpec:
    """Background definition for a region.

    lo/hi are binding-energy endpoints (eV). avg_points: endpoints are averaged
    over this many data points to reduce noise sensitivity (XPSPEAK does the same).
    slope: extra linear component for SHIRLEY_LINEAR (counts/eV).
    tougaard_b/c: U2 universal cross-section parameters; b<=0 means auto-scale
    so the background meets the data at the high-BE endpoint.
    """

    kind: str = "SHIRLEY"
    lo: float | None = None
    hi: float | None = None
    avg_points: int = 3
    slope: float = 0.0
    tougaard_b: float = 0.0
    tougaard_c: float = 1643.0
    active: bool = False  # Shirley derived from the peak model, co-fit with peaks

    def to_dict(self) -> dict:
        return {
            "kind": self.kind, "lo": self.lo, "hi": self.hi,
            "avg_points": self.avg_points, "slope": self.slope,
            "tougaard_b": self.tougaard_b, "tougaard_c": self.tougaard_c,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BackgroundSpec":
        return cls(**{k: d[k] for k in cls().to_dict() if k in d})


@dataclass
class Region:
    """One spectral window: data + background + peaks."""

    name: str = "Region"
    x: np.ndarray = field(default_factory=lambda: np.array([]))
    y: np.ndarray = field(default_factory=lambda: np.array([]))
    background: BackgroundSpec = field(default_factory=BackgroundSpec)
    peaks: list[Peak] = field(default_factory=list)
    source_file: str = ""
    be_shift: float = 0.0  # charge-correction shift already applied to x (eV)

    def __post_init__(self) -> None:
        self.x = np.asarray(self.x, dtype=float)
        self.y = np.asarray(self.y, dtype=float)
        if self.x.size > 1 and self.x[0] > self.x[-1]:
            self.x = self.x[::-1].copy()
            self.y = self.y[::-1].copy()

    def crop_indices(self) -> tuple[int, int]:
        """Indices of the background window endpoints (defaults to full range)."""
        lo = self.background.lo if self.background.lo is not None else self.x[0]
        hi = self.background.hi if self.background.hi is not None else self.x[-1]
        i1 = int(np.searchsorted(self.x, min(lo, hi), side="left"))
        i2 = int(np.searchsorted(self.x, max(lo, hi), side="right") - 1)
        i1 = max(0, min(i1, self.x.size - 2))
        i2 = max(i1 + 1, min(i2, self.x.size - 1))
        return i1, i2

    def shift_be(self, delta: float) -> None:
        """Charge correction: shift the BE axis and everything tied to it."""
        self.x = self.x + delta
        self.be_shift += delta
        if self.background.lo is not None:
            self.background.lo += delta
        if self.background.hi is not None:
            self.background.hi += delta
        for p in self.peaks:
            p.center.value += delta
            if math.isfinite(p.center.min):
                p.center.min += delta
            if math.isfinite(p.center.max):
                p.center.max += delta

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "background": self.background.to_dict(),
            "peaks": [p.to_dict() for p in self.peaks],
            "source_file": self.source_file,
            "be_shift": self.be_shift,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Region":
        return cls(
            name=d.get("name", "Region"),
            x=np.array(d.get("x", []), dtype=float),
            y=np.array(d.get("y", []), dtype=float),
            background=BackgroundSpec.from_dict(d.get("background", {})),
            peaks=[Peak.from_dict(pd) for pd in d.get("peaks", [])],
            source_file=d.get("source_file", ""),
            be_shift=d.get("be_shift", 0.0),
        )
