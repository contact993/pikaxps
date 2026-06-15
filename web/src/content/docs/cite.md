---
title: How to cite PikaXPS
description: How to cite the PikaXPS XPS peak-fitting software in your publications.
---

If PikaXPS helped your research, please mention it — it's how a free academic tool justifies its
continued development.

## The simplest way — one line in your Methods

Just name it where you describe the analysis. For example:

> *XPS spectra were analyzed (peak-fitted) using PikaXPS (https://github.com/contact993/pikaxps).*

or

> *Peak fitting and quantification were performed with PikaXPS.*

For most journals, a one-sentence mention in the **Methods / Experimental** section plus the URL is a
complete and valid software citation — nothing more is needed.

:::tip[Two ways to support this free, no-ads tool]
**⭐ [Star PikaXPS on GitHub](https://github.com/contact993/pikaxps)** and name it in your Methods.
Both are free, take seconds, and are what keep a no-ads academic tool funded and maintained.
:::

## Formal reference (optional)

If your journal wants a full entry in the reference list, a peer-reviewed software paper with a DOI
is in preparation; until it appears, cite the repository and the version you used:

```bibtex
@software{pikaxps,
  author  = {Kim, Taehee},
  title   = {PikaXPS: free cross-platform XPS peak fitting with a built-in fit auditor},
  year    = {2026},
  url     = {https://github.com/contact993/pikaxps},
  version = {0.1.4}
}
```

The repository also ships a [`CITATION.cff`](https://github.com/contact993/pikaxps/blob/main/CITATION.cff),
so GitHub's "Cite this repository" button always gives the current version.

#### Reference-data sources
The bundled binding-energy values are literature references; please also cite the original sources
where appropriate: M. C. Biesinger et al. (*Appl. Surf. Sci.* 2010/2011; *Surf. Interface Anal.*
2009); J. F. Moulder et al., *Handbook of XPS* (1992); NIST XPS Database SRD 20; J. H. Scofield
(1976) for RSFs.
