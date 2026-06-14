# Recommended Fitting Procedure

## 1. Preparation — Start with Charge Correction

1. **Peak-fit the C 1s region first**: fit the adventitious C-C component (around ~284.8)
2. **BE Shift in the Regions panel**: pressing the "C-C→284.8" button automatically calculates the required shift
   (or enter the ± value directly) → pressing "Apply Shift" moves **all regions (O 1s, metal peaks, etc.)
   by the same value**. To move only some of them, turn off "Apply to all," select from the list, and apply
3. Identify the elements present from the survey scan — detect unexpected elements (contamination) before fitting
4. Region selection: wide enough that a **flat segment is visible on both sides** of the peak. If a neighboring peak
   intrudes into the window, drag the BG vertical lines to trim the range (data outside the window is shown faded and
   excluded from fitting; cancel with "↔ Range reset")

## 2. Background

1. Select the type (default: Shirley — see "Background" in Help)
2. Place the endpoints far enough from the peak tails
3. Check area sensitivity by moving the endpoints ±1 eV — if it fluctuates strongly, consider widening the region and re-measuring

## 3. Building the Peak Model

1. **Start from the reference DB**: search for the element → bring up the guideline for the expected chemical state and compare against the data
2. Add only components that have a chemical basis (using a recipe is recommended)
3. Always fix the splitting/ratio for doublets (Insert Doublet function)
4. Link the FWHM among components of the same kind
5. Use an asymmetric line shape for metallic components (GL+Tail or Doniach-Šunjić)

## 4. Fitting

1. Place the peaks at approximate positions (drag) and **Optimise Region**
2. After convergence, check the residual: a remaining structural pattern means the model is insufficient/excessive
3. Re-fit with different initial values — the same answer should emerge for the result to be trustworthy

## 5. Validation Checklist (Before Manuscript Submission)

- [ ] Are all FWHMs within the physical range (0.7–2.5 eV, excluding the envelope)?
- [ ] Are the doublet ratios/spacings fixed?
- [ ] Are the centers within the literature range (compared against the DB)?
- [ ] Is the residual flat?
- [ ] Have you **reported all of** the background type/range, line shape, constraints, and correction reference?
- [ ] Did you avoid treating a transition-metal multiplet (Ni 2p, Co 2p, Fe 2p, Cr 2p, Mn 2p) as a single simple peak?

## How to Read the Residual — "Do I Need One More Peak?"

The residual below the plot = **measured data − model (peaks + background)**.

- If the residual is scattered only as **random noise** around 0 → the model is sufficient. Adding more components
  always lowers χ² but carries no chemical meaning (overfitting)
- If a **wave/hump on the scale of a peak width** remains in the residual → this is a sign that something the model
  failed to capture exists at that position (one of: a missing component, satellite, asymmetry, or a background problem)

**🔍 The Diagnose button** comprehensively audits the items a reviewer looks at and organizes them into a ✖/⚠/✓ report:

| Item | What is checked |
|---|---|
| FWHM | < 0.35 eV (fitting noise) / > 3 eV (without a satellite label) / pinned to a boundary value |
| Reference | Compares each peak's BE against the known chemical-species ranges in the DB; if it doesn't match, suggests the closest state |
| Doublet | When the partner should be inside the window but is missing / for an unlinked partner, the actual spacing/area ratio vs. the theoretical value |
| Line shape | Fitting a metallic state (DB hint) with a symmetric GL → warns of oxide overestimation |
| Satellite | When the state is satellite-accompanied (Cu(II)/Co(II)/Ni(II), etc.) but the satellite peak is missing |
| Overfitting | Peak pairs with spacing < 0.4 eV, components contributing < 1%, components with area 0 |
| **Necessity** | **Removes peaks one at a time and re-fits (leave-one-out)** — if the result stays the same after removal (ΔBIC ≤ 0), flags it as a "peak the data does not require." Quantitatively catches peaks that are "the same before and after addition" |
| Charge correction | If it is the C 1s region, whether C-C is within 284.8 ± 0.25 |
| Residual statistics | Bandpass z-score + ΔBIC for adding the peak under test (< −10 = strong evidence for addition) |

> Look at the statistical and the physical/literature checks together — a fitting is trustworthy only when it passes both.

## Top 5 Common Errors

1. **Metal as a symmetric peak** → oxide overestimation
2. **Free doublet ratio** → unphysical solution
3. **Excessive number of components** → good χ² but no chemical meaning
4. **Shirley endpoints on top of the peak** → area distortion
5. **Ignoring the multiplet of transition-metal 2p** → use the Biesinger-recommended envelope (see the ref in the DB)

#### References
- M.C. Biesinger 외, *Appl. Surf. Sci.* 257 (2011) 2717
- D.R. Baer 외, "XPS 분석 보고 가이드라인", *J. Vac. Sci. Technol. A* 37 (2019) 031401
- G.H. Major 외, "흔한 XPS fitting 오류", *J. Vac. Sci. Technol. A* 38 (2020) 061203
