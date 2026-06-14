# Charge Referencing

Insulating samples become positively (+) charged at the surface due to photoelectron emission, so **the entire spectrum is shifted toward higher BE.** Any comparison of binding energies is meaningful only after correction.

## Standard Method: C 1s = 284.8 eV

Set the C-C/C-H peak of adventitious carbon — present on the surface of almost every sample — to **284.8 eV**, and translate the entire range by that difference.

In this program: **Tools → Charge Correction** — entering the measured C 1s value shifts all regions at once (equivalent to XPSPEAK's Region Shift).

## Limitations and Cautions

- The reference differs from one publication to another (use cases of 284.5–285.0 eV exist). **The reference value must be stated explicitly in the paper.**
- Because the composition of adventitious carbon varies from sample to sample, there is an inherent uncertainty on the order of ±0.2 eV.
- **Caution for Ru-containing samples**: Ru 3d3/2 overlaps the C 1s region (~284.3 eV), which can lead to misjudging the C-C position.
- Differential charging: if the amount of charging varies across regions within the sample, the peaks broaden asymmetrically — this cannot be resolved by translation, and re-measurement with modified flood gun conditions is required.

## Alternative References

- Samples with exposed metallic components: the metal peak itself (e.g., Au 4f7/2 = 84.0 eV)
- Oxide lattice oxygen O 1s ≈ 530.0 eV (when the literature value for the relevant oxide is reliable)
- If two or more internal references are available, cross-check them.

#### References
- T.L. Barr, S. Seal, *J. Vac. Sci. Technol. A* 13 (1995) 1239
- G. Greczynski, L. Hultman, *Prog. Mater. Sci.* 107 (2020) 100591 — C 1s 보정의 한계 비판적 검토
