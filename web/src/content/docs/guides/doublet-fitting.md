---
title: Spin-orbit doublet fitting in XPS
description: How to fit XPS spin-orbit doublets correctly — fixing the splitting, area ratio and FWHM so the optimizer doesn't place ghost peaks.
---

p, d and f core levels split into two peaks by spin-orbit coupling, and the **splitting and area
ratio are physical constants** — not free parameters. Fitting them as independent free peaks is one
of the most common XPS mistakes: the optimizer, blind to the doublet structure, parks broad "ghost"
peaks wherever they reduce χ².

## The constants to fix
| Orbital | Components | Area ratio |
|---|---|---|
| p | p3/2 : p1/2 | 2 : 1 |
| d | d5/2 : d3/2 | 3 : 2 |
| f | f7/2 : f5/2 | 4 : 3 |

The splitting (eV) is element- and orbital-specific (e.g. S 2p 1.18, Mo 3d 3.15, Pt 4f 3.33).

## How to do it in PikaXPS
In the peak table, set the peak's **Type** to **Doublet**. PikaXPS then creates the partner with:
- partner centre = main + splitting (fixed),
- partner area = main × ratio (fixed),
- partner FWHM = main FWHM (linked).

If PikaXPS recognises the region (name it like "Ir 4f"), the splitting and ratio fill
automatically; otherwise you enter them once. The same-species FWHMs stay linked, so the optimizer
only fits what physics leaves free.

## When the ratio looks off
Some metals (e.g. Ti) show ratios slightly off the theoretical value because of Coster–Kronig
effects — start from the theoretical value anyway, and only release a constraint with a clear
physical reason. The **fit auditor** will tell you if a freed ratio has drifted too far.

[Download PikaXPS →](/download/)
