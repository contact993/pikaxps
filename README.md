# Corepeak

**Free, cross-platform XPS peak-fitting for macOS & Windows — with a built-in fit auditor and a
citation-backed reference database. The modern replacement for XPSPEAK 4.1.**

Corepeak reproduces the familiar XPSPEAK workflow with a modern interface, then goes further:
it doesn't just let you fit X-ray photoelectron spectroscopy data — it **checks whether your fit
is physically and statistically defensible**, and it knows the literature binding energies so you
don't have to look them up.

![screenshot](docs/screenshot.png)

> Free and open source (GPLv3). Academic use is free forever. No account, no limits, no ads on the
> download — and no 5,000-point / 51-peak ceiling like XPSPEAK.

## Why Corepeak

| | Corepeak | XPSPEAK 4.1 | CasaXPS | KherveFitting / LG4X |
|---|---|---|---|---|
| Price | **Free (OSS)** | Free | €830+ (academic) | Free (OSS) |
| macOS native | **✅** | ❌ (Windows only) | ❌ (emulation) | ✅ |
| Built-in **fit auditor** | **✅** | ❌ | ❌ | ❌ |
| Citation-backed **reference DB** | **✅** | ❌ | partial | ❌ |
| One-click fitting **recipes** | **✅** | ❌ | ✅ | ❌ |
| Doublet + satellite peak types | **✅** | limited | ✅ | partial |
| Actively maintained | **✅** | ❌ (1999) | ✅ | ✅ |

## Features

- **Backgrounds** — Shirley (iterative), Shirley+Linear, Tougaard (U2), Linear, plus an *active
  Shirley* that co-fits with the peaks. Draggable endpoints; "Fit BG" settles the background first.
- **Lineshapes** — Gaussian-Lorentzian (sum & product), Voigt, exponential-tail asymmetric,
  Doniach-Šunjić for metals.
- **Peak types** — set each peak as **single / doublet / satellite** from the table. Doublets
  auto-constrain spin-orbit splitting, area ratio and FWHM; satellite areas are folded into the
  parent species for quantification.
- **🔍 Fit audit** — a one-click report that checks FWHM sanity, binding energies against the
  reference DB, doublet integrity, metallic-lineshape asymmetry, expected satellites, over-fit
  signals, charge referencing, the residual (band-passed z-score), and a **leave-one-out
  peak-necessity test** (BIC) that flags peaks the data doesn't actually require.
- **Reference database** — 24 elements with binding energies, spin-orbit parameters and RSFs,
  **every value carrying its literature citation** (Biesinger, Moulder, NIST SRD 20). One-click
  recipes (Ni 2p, Co 2p, Fe 2p, C 1s, O 1s, S 2p, Pt 4f, Mo 3d, …). Add your own references —
  saved to `~/.xpsfit/user_refdb.json`, kept across updates.
- **Import** — `.dat/.txt/.csv/.xlsx/.xls`, Thermo Avantage multi-sheet exports, VAMAS `.vms`, or
  paste two columns straight from Excel/Origin. KE→BE conversion built in.
- **Quantification** — Scofield-RSF atomic % (doublet/satellite areas summed automatically).
- **Charge correction** — pick the fitted C–C peak, shift every region to 284.8 eV in one click.
- **Batch fitting**, **publication figures** (PNG/SVG/PDF) and **CSV/Excel export**.
- **Korean help** built in (백그라운드/라인섀입/constraint/대전보정/정량 가이드, 출처 포함).

## Install

Download the latest signed build from the [Releases](https://github.com/contact993/corepeak/releases)
page:
- **macOS** — unzip, move `Corepeak.app` to Applications, first launch via right-click → Open.
- **Windows** — unzip, run `Corepeak.exe` from the extracted folder ("More info → Run anyway" on
  the first SmartScreen prompt).

No Python install required.

### Run from source

```bash
git clone https://github.com/contact993/corepeak && cd xpsfit
python -m venv .venv && . .venv/bin/activate
pip install -e .
python -m xpsfit.app
```

## Feedback, feature requests & contributing references

This tool grows from its users:
- **Bug / feature** — open an [issue](https://github.com/contact993/corepeak/issues/new/choose).
- **Questions & feature voting** — the [Discussions](https://github.com/contact993/corepeak/discussions) board.
- **📚 Contribute a reference value** — use the *Submit a reference value* issue template (a
  literature source is required). Accepted submissions ship in the next release with credit, so the
  database keeps getting richer.

## How to cite

If Corepeak helped your work, please cite it (see [CITATION.cff](CITATION.cff)). A software paper
with a DOI is in preparation; until then, cite the repository and release version.

## License

GPLv3 (see [LICENSE](LICENSE)). **Academic and non-commercial use is free, forever.** Commercial use
is currently also free under the GPLv3 until a commercial license is established — see
[COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md). Third-party components and reference-data sources are
listed in [THIRD-PARTY-LICENSES.txt](THIRD-PARTY-LICENSES.txt).

## Maintenance

Maintained part-time by a single developer. Released as stable open source: if updates slow, the
tool remains usable and the source stays available. Reference-data values are literature starting
points — always verify assignments against the cited sources before publication.

#### Reference-data sources
M. C. Biesinger et al. (*Appl. Surf. Sci.* 2010/2011; *Surf. Interface Anal.* 2009) · J. F. Moulder
et al., *Handbook of XPS* (1992) · NIST XPS Database SRD 20 · J. H. Scofield (1976) RSFs.
