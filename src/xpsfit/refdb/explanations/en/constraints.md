# Inter-Peak Constraints (XPSPEAK's "Relation with another peak")

Constraints are the most powerful tool for preventing overfitting. "Adding one more peak always improves the fit"
— which is why **every physically determined relationship should be fixed**, so that the degrees of freedom are reduced and the result becomes chemically meaningful.

## Spin-orbit doublet — must be fixed

The p, d, and f orbitals split into two peaks through spin-orbit coupling, and **the spacing and area ratio are physical constants**:

| Orbital | Components | Area ratio (theoretical) |
|---|---|---|
| p | p3/2 : p1/2 | 2 : 1 |
| d | d5/2 : d3/2 | 3 : 2 |
| f | f7/2 : f5/2 | 4 : 3 |

The splitting (eV) differs for each element and orbital (check it in the reference DB panel — e.g., S 2p 1.18,
Mo 3d 3.15, Pt 4f 3.33 eV). This program's "Insert doublet" automatically applies three constraints:

- partner center = main center + splitting (fixed)
- partner area = main area × ratio (fixed)
- partner FWHM = main FWHM (linked)

> Exception: for some metals (e.g., Ti), the Coster-Kronig effect broadens the 2p1/2 component, so the ratio may
> deviate slightly from the theoretical value. Even so, start from the theoretical value.

## FWHM linking

Different chemical states of the same element (e.g., C-C and C-O) usually have similar widths → start by linking the FWHM,
and release it only when there is a chemical justification (oxides being broader than metals is normal).

## Restricting the center range

Restrict the center of each component to the literature value ±0.2–0.5 eV. When you insert a peak from the reference DB,
this is set automatically. If the fitting drags the center outside the literature range, it is a sign that the model is wrong.

## Expression syntax

This program's constraints are lmfit expressions. The parameters of peak number i are `p{i}_center`,
`p{i}_area`, `p{i}_fwhm`, `p{i}_mix`, `p{i}_asym`:

```
p0_center + 1.18      # +1.18 eV from peak 0
p0_area * 0.5         # half the area of peak 0
p0_fwhm               # same width as peak 0
```

## Overfitting checklist

- **Chemical justification** comes before the number of components (why should this state exist in this sample?)
- If the residual is flat with no structure, that is sufficient — do not add components just to reduce χ² further
- Check that fitting the same data from different initial values gives the same answer (uniqueness of the solution)
- State all constraints when reporting (reproducibility)

#### References
- M.C. Biesinger et al., *Appl. Surf. Sci.* 257 (2011) 2717 — recommended fitting parameters for transition metals
- Recommendations for analytical reporting: D.R. Baer et al., *J. Vac. Sci. Technol. A* 37 (2019) 031401
