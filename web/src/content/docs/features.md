---
title: Features
description: Backgrounds, lineshapes, doublets, satellites, the fit auditor, a citation-backed reference database, quantification, batch fitting and flexible import — everything in PikaXPS.
---

## Backgrounds
Shirley (iterative), Shirley + Linear, Tougaard (U2), and Linear — plus an **active Shirley** that
is derived from the peak model and co-fit with the peaks. Endpoints are draggable; **Fit BG**
settles the background before you add peaks.

## Lineshapes
Gaussian–Lorentzian (sum and product forms), Voigt, exponential-tail asymmetric, and
**Doniach–Šunjić** for metallic states.

## Peak types: single / doublet / satellite
Set each peak's role from the table:
- **Doublet** — auto-constrains spin-orbit splitting, area ratio (2:1 / 3:2 / 4:3) and FWHM.
- **Satellite** — ties the position to a parent peak; its area is folded into the parent species
  for quantification (shake-up/plasmon intensity belongs to the same chemical state).
- **Pin** a peak to freeze it while the rest optimise; or lock just its position.

## 🔍 The fit auditor
One click produces a report that checks what a careful reviewer would:
FWHM sanity, binding energies vs. the reference DB, doublet integrity, metallic-lineshape
asymmetry, expected satellites, over-fit signals, charge referencing, the residual
(band-passed z-score), and a **leave-one-out peak-necessity test** (BIC) that flags peaks the
data doesn't actually require. [Learn how it works →](/guides/fit-audit/)

## Reference database
24 elements with binding energies, spin-orbit parameters and RSFs — **every value carries its
literature citation** (Biesinger, Moulder, NIST SRD 20). One-click fitting recipes (Ni 2p, Co 2p,
Fe 2p, C 1s, O 1s, S 2p, Pt 4f, Mo 3d, …). Add your own references; they're saved locally and kept
across updates, and you can [submit them to the shared database](/contribute/).

## Quantification & charge correction
Scofield-RSF atomic % (doublet and satellite areas summed automatically). Charge-correct every
region to C 1s = 284.8 eV in one click from the fitted C–C peak.

## Import & export
Import `.dat / .txt / .csv / .xlsx / .xls`, Thermo Avantage multi-sheet exports, VAMAS `.vms`, or
paste two columns from Excel/Origin (KE→BE conversion built in). Export parameters and component
curves to CSV/Excel, and publication figures to PNG/SVG/PDF.

## Built-in Korean help
백그라운드 · 라인섀입 · constraint · 대전 보정 · 권장 절차 · 정량 가이드 — 출처 포함.
