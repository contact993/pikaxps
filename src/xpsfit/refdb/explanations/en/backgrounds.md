# Background

Beneath every XPS peak lies a background produced by inelastically scattered electrons.
Since the peak area is "whatever remains after subtracting the background," **the choice of background directly governs the quantitative result.**

## Linear

Connects the two endpoints with a straight line.

- **When**: weak peaks where the background change is small (C 1s, N 1s, O 1s and other light elements), narrow energy windows
- **Caution**: unsuitable for regions with a large step across the peak, such as transition-metal 2p — the area becomes distorted

## Shirley

A background that "rises in a staircase fashion in proportion to the cumulative area under the peak." Because inelastically scattered electrons appear on the **higher binding-energy side** of the original peak, the background also rises toward the high-BE side.
It is converged self-consistently through an iterative calculation.

- **When**: the default for most metal/transition-metal regions. The de facto standard for XPS fitting
- **Caution**: **sensitive to endpoint position** — if you place an endpoint on the tail of the peak, the area can shift by several percent.
  Place the endpoints on a flat region sufficiently far from the peak, and check the sensitivity of the result by moving the endpoint position by ±1 eV.
- This program sets each endpoint as the average of several neighboring points to reduce sensitivity to noise (the same as XPSPEAK)

### Simultaneous BG fit (Active Shirley)

Standard Shirley builds the background from the cumulative area of the **measured data**, so it is sensitive to noise and to other peak structures within the window. When you enable "Simultaneous BG fit," the background is derived from the **peak model** (the Sherwood approach) and optimized together with the peaks — as the fitting iterates, the peaks and the background adjust to each other and converge. Try enabling it when ordinary Shirley produces an odd-looking background.

## Shirley + Linear

A form that adds a linear slope to Shirley (XPSPEAK's "Shirley+Linear"). Use it when a tilted background (e.g., the tail of another peak) underlies the entire spectrum. With slope = 0 it is identical to pure Shirley.

## Tougaard

The most physically rigorous method, explicitly integrating the physics of inelastic scattering (the universal loss function, F(T) = B·T/(C+T²)²).

- **When**: when absolute quantification matters and a wide energy range (30 eV or more past the peak) has been measured
- **Caution**: inaccurate in narrow windows. For routine chemical-state analysis, Shirley is sufficient in most cases
- Parameters: C = 1643 eV² (universal); B is auto-scaled to the data endpoint (manual adjustment possible)

## Practical summary

| Situation | Recommendation |
|---|---|
| Transition-metal 2p (Ni, Co, Fe, ...) | Shirley |
| C 1s, N 1s, O 1s | Shirley or Linear |
| Absolute quantification, wide measurement range | Tougaard |
| Peak on a tilted baseline | Shirley+Linear |

> Changing the background type changes the area. **Always state in your paper which background was used.**

#### References
- D.A. Shirley, *Phys. Rev. B* 5 (1972) 4709
- S. Tougaard, *Surf. Interface Anal.* 25 (1997) 137
- M.C. Biesinger, et al. — Recommendations for XPS analysis: *Appl. Surf. Sci.* 257 (2011) 2717
