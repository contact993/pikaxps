---
title: Download PikaXPS
description: Download the free PikaXPS XPS peak-fitting app for macOS and Windows.
---

PikaXPS is free and open source (GPLv3). No account, no install of Python required.

## Latest release

Get the installers from the **[GitHub Releases page →](https://github.com/contact993/pikaxps/releases)**.

### macOS (Apple Silicon)
1. Download **`PikaXPS-macOS.dmg`**, open it, and drag **PikaXPS** to Applications.
2. First launch: **right-click → Open → Open** (one-time, because the app isn't from the App Store).
3. If you ever see "damaged, can't be opened": run `xattr -cr "/Applications/PikaXPS.app"` in Terminal, then right-click → Open.

### Windows (10 / 11, x64)
1. Download the `.zip`, extract it, and run **PikaXPS.exe** from the extracted folder.
2. On the first SmartScreen prompt: **More info → Run anyway** (the reputation prompt clears as more people download).

:::note
Need an Intel-Mac or Linux build? [Open an issue](https://github.com/contact993/pikaxps/issues/new/choose) and let me know.
:::

## Run from source

```bash
git clone https://github.com/contact993/pikaxps && cd pikaxps
python -m venv .venv && . .venv/bin/activate
pip install -e .
python -m xpsfit.app
```

## ⭐ After you install

PikaXPS is **100% free, with no ads**. If it helps your work, two things keep it alive:

- **[Star it on GitHub →](https://github.com/contact993/pikaxps)** — the clearest signal that the tool is used.
- **[Cite it in your paper →](/pikaxps/cite/)** — citations are what justify a free academic tool's continued development.
