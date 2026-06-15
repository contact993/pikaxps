---
title: The fit audit — is your XPS fit defensible?
description: How PikaXPS's automated fit auditor uses FWHM checks, reference binding energies, BIC and a leave-one-out test to catch over-fitted and unphysical XPS peak fits.
---

A flat residual is **necessary but not sufficient**: an XPS fit can match the data perfectly and
still be chemically wrong, or use peaks the data doesn't justify. PikaXPS's **fit auditor** runs
the checks an experienced reviewer would, in one click, and returns a ✖ / ⚠ / ✓ report.

## What it checks
- **FWHM sanity** — flags widths that are unphysically narrow (noise-fitting) or too broad for a
  single species, and parameters stuck at their bounds.
- **Reference binding energies** — compares each peak's position against the citation-backed
  database; if it matches no known state, it says so and names the nearest one.
- **Doublet integrity** — is the spin-orbit partner present, with the right splitting and area
  ratio? [More on doublets →](/guides/doublet-fitting/)
- **Lineshape** — warns when a metallic state is fit with a symmetric Gaussian–Lorentzian (which
  inflates the oxide component).
- **Expected satellites** — flags missing shake-up satellites for states that always have them
  (Cu(II), Co(II), Ni(II)…).
- **Over-fit signals** — near-coincident peaks, <1% components, zero-area peaks.
- **Charge referencing** — is C 1s C–C on 284.8 eV?

## The two statistical tests
- **Residual z-score** — band-pass filters the residual to peak-width features and reports the
  largest unexplained structure in units of the noise. Below 3σ, there's nothing to add.
- **Leave-one-out necessity (BIC)** — refits the model *without each peak* and compares the Bayesian
  Information Criterion. **If the fit is just as good without a peak, the data doesn't require it.**
  This is the test that catches the "I added a peak and nothing changed" situation — a strong sign
  the peak should go.

## The rule
Statistics are necessary, not sufficient. Before adding a component, confirm a known chemical state
can sit at that binding energy (the auditor checks the reference DB for you). Both the statistics
and the chemistry have to agree.

[Download PikaXPS →](/download/) and run the audit on your next fit.
