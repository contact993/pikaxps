---
title: Download PikaXPS
description: Download the free PikaXPS XPS peak-fitting app for macOS and Windows.
---

PikaXPS is free and open source (GPLv3). No account, no Python install required.

## Download (latest version)

- **⬇ macOS (Apple Silicon) — [PikaXPS-macOS.dmg](https://github.com/contact993/pikaxps/releases/latest/download/PikaXPS-macOS.dmg)**
- **⬇ Windows 10 / 11 (x64) — [PikaXPS-Windows-x64.zip](https://github.com/contact993/pikaxps/releases/latest/download/PikaXPS-Windows-x64.zip)**

These links download the file directly. (To browse every version, see the
[Releases page](https://github.com/contact993/pikaxps/releases) — there, pick the `.dmg` / `.zip`
under **Assets**, *not* the auto-generated "Source code".)

The app is **unsigned** (no paid Apple/Microsoft certificate), so on first launch your OS will warn
you. That's expected — here's the one-time step to allow it:

### Opening it on macOS (Apple Silicon)

1. Open the `.dmg` and drag **PikaXPS** into **Applications**.
2. Allow the unsigned app (pick whichever works on your macOS):
   - **Recommended:** open **Terminal** and run `xattr -cr "/Applications/PikaXPS.app"`, then open PikaXPS normally. (This just clears the download‑quarantine flag — it's why "damaged, can't be opened" appears.)
   - **Or via Settings:** double‑click PikaXPS once (it gets blocked) → open **System Settings → Privacy & Security** → scroll down → **Open Anyway** → **Open**.
   - **Older macOS:** **right‑click the app → Open → Open**.

:::caution[Apple Silicon only]
This build runs on **Apple Silicon (M1–M4)** Macs. It will **not** run on an Intel Mac.
Need an Intel or Linux build? [Open an issue](https://github.com/contact993/pikaxps/issues/new/choose).
:::

### Opening it on Windows (10 / 11, x64)

1. **Right‑click the `.zip` → Extract All.** Don't run it from inside the zip — the app needs the whole extracted folder.
2. Open the extracted **PikaXPS** folder and run **PikaXPS.exe**.
3. If a blue **SmartScreen** box appears: **More info → Run anyway** (it's unsigned; the warning fades as more people download).

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
