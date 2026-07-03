"""Draw a clean 5-stage CBR cycle diagram (Gambar 1)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BLUE = "#2783DE"; DARK = "#2C2C2B"; SOFT = "#E5F2FC"; BORDER = "#9cc6ee"
import os
RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RES, exist_ok=True)

stages = [
    ("1. Representasi\nKasus", "Kodekan rekam pasien\nsebagai kasus"),
    ("2. Retrieve", "Ambil k kasus paling\nmirip (HEOM)"),
    ("3. Reuse", "Voting berbobot\nsimilaritas"),
    ("4. Revise", "Uji keyakinan\n& koreksi"),
    ("5. Retain", "Simpan kasus baru\nke basis kasus"),
]

fig, ax = plt.subplots(figsize=(7.2, 5.4))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

# central case base
cx, cy = 5, 5
cb = FancyBboxPatch((cx-1.35, cy-0.75), 2.7, 1.5, boxstyle="round,pad=0.08,rounding_size=0.18",
                    linewidth=2, edgecolor=BLUE, facecolor=SOFT)
ax.add_patch(cb)
ax.text(cx, cy, "Basis Kasus\n(Case Base)", ha="center", va="center",
        fontsize=11, fontweight="bold", color=DARK)

# stage nodes around a circle
R = 3.7
angles = np.linspace(90, 90-360, len(stages), endpoint=False)
pos = []
for ang in angles:
    a = np.deg2rad(ang)
    pos.append((cx + R*np.cos(a), cy + R*np.sin(a)*0.92))

for (title, desc), (x, y) in zip(stages, pos):
    box = FancyBboxPatch((x-1.15, y-0.6), 2.3, 1.2,
                         boxstyle="round,pad=0.06,rounding_size=0.15",
                         linewidth=1.6, edgecolor=BLUE, facecolor="white")
    ax.add_patch(box)
    ax.text(x, y+0.18, title, ha="center", va="center", fontsize=10,
            fontweight="bold", color=BLUE)
    ax.text(x, y-0.34, desc, ha="center", va="center", fontsize=7.4, color=DARK)

# cyclic arrows between consecutive stages
for i in range(len(pos)):
    x1, y1 = pos[i]; x2, y2 = pos[(i+1) % len(pos)]
    arr = FancyArrowPatch((x1, y1), (x2, y2),
                          connectionstyle="arc3,rad=0.22",
                          arrowstyle="-|>", mutation_scale=18,
                          linewidth=1.8, color="#7D7A75",
                          shrinkA=26, shrinkB=26)
    ax.add_patch(arr)

# thin links to the central case base (retrieve reads, retain writes)
for i in [0, 1, 4]:
    x, y = pos[i]
    ax.add_patch(FancyArrowPatch((x, y), (cx, cy), connectionstyle="arc3,rad=0.0",
                 arrowstyle="-", linewidth=0.9, color=BORDER,
                 shrinkA=24, shrinkB=34, linestyle="--"))

ax.set_title("Siklus Case-Based Reasoning (5 Tahap)", fontsize=13,
             fontweight="bold", color=DARK, pad=6)
fig.tight_layout()
fig.savefig(f"{RES}/fig_cbr_cycle.png", dpi=170, bbox_inches="tight")
print("saved fig_cbr_cycle.png")
