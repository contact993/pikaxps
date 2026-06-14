# Quantitative Analysis (Atomic %)

Atomic fraction of element i: **nᵢ ∝ Aᵢ / RSFᵢ** — peak areas are divided by the sensitivity factor (RSF) for comparison.

```
atomic % = (Aᵢ/RSFᵢ) / Σⱼ(Aⱼ/RSFⱼ) × 100
```

## RSF (Relative Sensitivity Factor)

The default RSF in this program is the **Scofield photoionization cross section** (Al Kα, referenced to C 1s = 1.0).
Important limitations:

- Scofield values are **pure cross sections**. The actual sensitivity depends on the instrument's transmission function,
  IMFP (inelastic mean free path), and analyzer angle.
- **If a manufacturer's instrument RSF is available, use it preferentially** (it can be edited directly in the Quantify table).
- **Relative comparison** between samples measured on the same instrument under the same conditions is the most reliable.

## Rules of Use

1. Process all regions with the **same background method**.
2. For doublets, calculate using the **sum of the two component areas** (this program sums them automatically).
3. Only compare areas between regions measured at the same pass energy.
4. Surface sensitivity: XPS sees only the top ~5–10 nm. This is the **surface composition**, not the "bulk composition."

## Uncertainty

The realistic accuracy of XPS quantification is on the order of **±10% (relative)**. The second decimal place of atomic % is
meaningless.

#### References
- J.H. Scofield, *J. Electron Spectrosc. Relat. Phenom.* 8 (1976) 129
- C.J. Powell, A. Jablonski, *J. Electron Spectrosc.* 178-179 (2010) 331 (IMFP)
- M.P. Seah, *Surf. Interface Anal.* 31 (2001) 721
