"""Draw the app icon (XPS doublet on rounded square) -> build_scripts/icon_1024.png."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "icon_1024.png"

fig = plt.figure(figsize=(10.24, 10.24), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# rounded-square background (macOS style)
box = FancyBboxPatch((0.06, 0.06), 0.88, 0.88,
                     boxstyle="round,pad=0,rounding_size=0.20",
                     facecolor="#16243a", edgecolor="none")
ax.add_patch(box)

x = np.linspace(0, 1, 400)


def peak(c, w, h):
    return h * np.exp(-4 * np.log(2) * (x - c) ** 2 / w**2)


bg = 0.16 + 0.10 / (1 + np.exp(-(x - 0.52) * 14))  # Shirley-like step
p1 = peak(0.40, 0.13, 0.42)
p2 = peak(0.62, 0.13, 0.22)
env = bg + p1 + p2

mask = (x > 0.10) & (x < 0.90)
ax.fill_between(x[mask], bg[mask], (bg + p1)[mask], color="#4da3ff", alpha=0.75, lw=0)
ax.fill_between(x[mask], bg[mask], (bg + p2)[mask], color="#ff6b6b", alpha=0.75, lw=0)
ax.plot(x[mask], bg[mask], color="#9fb3c8", lw=5, ls=(0, (4, 2)))
ax.plot(x[mask], env[mask], color="white", lw=10, solid_capstyle="round")

# scatter "data" dots above envelope
xs = np.linspace(0.13, 0.87, 26)
bgs = 0.16 + 0.10 / (1 + np.exp(-(xs - 0.52) * 14))
ys = bgs + 0.42 * np.exp(-4 * np.log(2) * (xs - 0.40) ** 2 / 0.13**2) \
    + 0.22 * np.exp(-4 * np.log(2) * (xs - 0.62) ** 2 / 0.13**2)
rng = np.random.default_rng(3)
ax.scatter(xs, ys + rng.normal(0, 0.012, xs.size) + 0.035, s=120,
           color="#ffd166", zorder=5, edgecolors="none")

ax.set_ylim(0, 1)
fig.savefig(OUT, transparent=True)
print("icon ->", OUT)
