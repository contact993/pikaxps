---
title: Download Corepeak
description: Download the free Corepeak XPS peak-fitting app for macOS and Windows.
---

Corepeak is free and open source (GPLv3). No account, no install of Python required.

## Latest release

Get the installers from the **[GitHub Releases page →](https://github.com/contact993/corepeak/releases)**.

### macOS (Apple Silicon)
1. Download **`Corepeak-macOS.dmg`**, open it, and drag **Corepeak** to Applications.
2. First launch: **right-click → Open → Open** (one-time, because the app isn't from the App Store).
3. If you ever see "damaged, can't be opened": run `xattr -cr "/Applications/Corepeak.app"` in Terminal, then right-click → Open.

### Windows (10 / 11, x64)
1. Download the `.zip`, extract it, and run **Corepeak.exe** from the extracted folder.
2. On the first SmartScreen prompt: **More info → Run anyway** (the reputation prompt clears as more people download).

:::note
Need an Intel-Mac or Linux build? [Open an issue](https://github.com/contact993/corepeak/issues/new/choose) and let me know.
:::

## Run from source

```bash
git clone https://github.com/contact993/corepeak && cd corepeak
python -m venv .venv && . .venv/bin/activate
pip install -e .
python -m xpsfit.app
```

## ⭐ After you install

Corepeak is **100% free, with no ads**. If it helps your work, two things keep it alive:

- **[Star it on GitHub →](https://github.com/contact993/corepeak)** — the clearest signal that the tool is used.
- **[Cite it in your paper →](/corepeak/cite/)** — citations are what justify a free academic tool's continued development.
