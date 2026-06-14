# Satellite peaks — shake-up, plasmon, multiplet

These are the broad, weak structures that appear next to the main peak (almost always on the **higher-BE side**).
They are not a new chemical species but rather **photoemission from the same chemical species that has lost additional energy**.

## Types

**Shake-up** — as the photoelectron leaves, it excites a valence electron into an unoccupied level
(π→π*, charge transfer in transition metals). It loses that much kinetic energy, so the apparent BE increases.
- Classic fingerprint: a strong satellite at +~8.5 eV from the **Cu(II)** main peak (absent for Cu(I)/Cu(0) → oxidation-state discrimination!)
- **Ni(II)** +~6.1 eV, **Co(II)** +~6.3 eV (a strong satellite = high-spin divalent fingerprint)
- **π-π\*** of sp² carbon: C 1s main peak +~6.6 eV (290.5–291.5 eV)

**Plasmon loss** — a loss peak that arises from exciting the collective oscillation of conduction electrons in a metal.
**Several can appear in succession** spaced by the plasmon energy (pronounced in Al, Mg, Si, etc.).

**Shake-off / multiplet** — the valence electron is completely ejected (into the continuum),
or the structure splits through coupling between the unpaired electron and the core hole (broad envelopes of Cr³⁺, Mn²⁺, Fe³⁺, etc.).

## Why it matters

1. **Do not mistake it for a different chemical species** — interpreting a satellite as a new oxidation state is the most common misreading
2. **Include it in quantification** — satellite intensity is part of that species' emission. Quantifying without it
   underestimates that species (Biesinger's Cu(0):Cu(II) quantification protocol is a representative example)
3. **Oxidation-state fingerprint** — the presence/absence, intensity, and spacing of the satellite are themselves information (e.g., CuO vs Cu₂O)

## How to use it in this program

In the peak table, **select "Satellite" in the Type column at the far left** → specify the main peak and Δ (the spacing), and then:

- The position is tied to **main peak + Δ** (it follows the main peak when it moves; edit/release Δ from 🔗)
- The FWHM starts broad (satellites are inherently broad)
- **In Quantify, its area is automatically added to the main peak's chemical species**
- 🔍 diagnostics recognize it as a satellite and do not raise false warnings such as "unknown state"

> If the state description in the Reference DB contains a hint like "satellite ~786," use that spacing as Δ.

#### References
- M.C. Biesinger, XPS Reference Pages (xpsfitting.com) — Shake-up Structure / Cu(0):Cu(II) Calculations
- HarwellXPS Guru — Shake-up Peaks (harwellxps.guru)
- M.C. Biesinger 외, *Appl. Surf. Sci.* 257 (2011) 2717
