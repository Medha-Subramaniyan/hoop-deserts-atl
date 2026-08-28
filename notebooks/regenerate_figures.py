"""Regenerate figures 01, 02, 04 from the final processed data.

The committed PNGs predate the Chicago city-limits scope decision, so their
Chicago values disagree with all_tracts.csv. Same design system as
notebooks/visualizations.ipynb; data source is the processed CSV instead of
re-executing both city notebooks.
"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("data/processed/viz")
INK, MUTED, GRID, SURF = "#1a1a1a", "#6b6b6b", "#e5e5e3", "#ffffff"
ATL, CHI = "#e8833a", "#2a6fb5"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
})
SRC = "OpenStreetMap · CDC PLACES 2025 · ACS 2023 5-yr"
QL = ["Q1\nlowest", "Q2", "Q3", "Q4\nhighest"]
LAB = {"Atlanta": "Atlanta  (Fulton + DeKalb)", "Chicago": "Chicago  (city limits)"}
def tag(fig): fig.text(0.01, 0.012, SRC, fontsize=7.5, color=MUTED, ha="left")

t = pd.read_csv("data/processed/tableau/all_tracts.csv")
t["q"] = t.income_q.astype(str).str[:2]
t = t[t.q.isin(["Q1", "Q2", "Q3", "Q4"])]
R = {c: g for c, g in t.groupby("city")}

# ---- 01 courts by income quartile ----
fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
for ax, (city, color) in zip(axes, [("Atlanta", ATL), ("Chicago", CHI)]):
    a = R[city]
    q = a.groupby("q").apply(
        lambda d: d.court_count.sum() / (d.total_population.sum() / 1e4),
        include_groups=False).reindex(["Q1", "Q2", "Q3", "Q4"])
    ax.bar(range(4), q.values, color=color, width=0.62, zorder=3)
    for i, v in enumerate(q.values):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=11,
                fontweight="bold", color=INK)
    ax.set_xticks(range(4)); ax.set_xticklabels(QL, fontsize=9.5)
    ax.set_title(LAB[city], fontsize=13, fontweight="bold", loc="left", color=INK, pad=10)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0); ax.set_axisbelow(True)
    ax.set_ylim(0, 2.45)
axes[0].set_ylabel("courts per 10,000 residents", fontsize=10)
fig.suptitle("Chicago built courts where income is lowest. Atlanta built them at both ends.",
             fontsize=15.5, fontweight="bold", x=.01, ha="left", y=.99, color=INK)
fig.text(.01, .905, "Basketball courts per 10,000 residents, by census-tract income quartile",
         fontsize=10.5, color=MUTED, ha="left")
plt.tight_layout(rect=[0, .035, 1, .88]); tag(fig)
plt.savefig(OUT / "01_courts_by_income_quartile.png", dpi=220, bbox_inches="tight")
plt.close()

# ---- 02 inactivity slope ----
fig, ax = plt.subplots(figsize=(7.6, 6))
# Q4 endpoints nearly coincide (13.8 vs 13.4), so nudge those two labels apart
# vertically; Q1 endpoints are far enough apart to sit on the line.
Q4_NUDGE = {"Atlanta": 0.55, "Chicago": -0.55}
for city, color in [("Atlanta", ATL), ("Chicago", CHI)]:
    v = R[city].groupby("q")["LPA"].median().reindex(["Q1", "Q2", "Q3", "Q4"])
    ax.plot(range(4), v.values, "-o", color=color, lw=2.6, ms=9, zorder=3, label=city)
    ax.text(-0.13, v.values[0], f"{v.values[0]:.1f}%", ha="right", va="center",
            fontsize=11, fontweight="bold", color=color)
    ax.text(3.13, v.values[-1] + Q4_NUDGE[city], f"{v.values[-1]:.1f}%", ha="left",
            va="center", fontsize=11, fontweight="bold", color=color)
ax.set_xticks(range(4)); ax.set_xticklabels(QL, fontsize=10)
ax.set_xlim(-0.75, 3.75)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_ylabel("% adults physically inactive (median)", fontsize=10)
ax.legend(frameon=False, fontsize=11, loc="upper right")
fig.suptitle("The gap that is real, in both cities", fontsize=16, fontweight="bold",
             x=.02, ha="left", y=.99, color=INK)
fig.text(.02, .925,
         "Physical inactivity falls steeply with income — regardless of where courts were built",
         fontsize=10.5, color=MUTED, ha="left")
plt.tight_layout(rect=[0, .035, 1, .90]); tag(fig)
plt.savefig(OUT / "02_inactivity_slope.png", dpi=220, bbox_inches="tight")
plt.close()

# ---- 04 race by quartile ----
CW, CB, CH = "#8c8c8c", "#4a3aa7", "#1baf7a"
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, city in zip(axes, ["Atlanta", "Chicago"]):
    g = R[city].groupby("q")[["pct_white", "pct_black", "pct_hispanic"]].median() \
               .reindex(["Q1", "Q2", "Q3", "Q4"])
    x, w = np.arange(4), 0.26
    ax.bar(x - w, g.pct_white, w, color=CW, label="White", zorder=3)
    ax.bar(x, g.pct_black, w, color=CB, label="Black", zorder=3)
    ax.bar(x + w, g.pct_hispanic, w, color=CH, label="Hispanic", zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(QL, fontsize=9.5)
    ax.set_title(LAB[city], fontsize=13, fontweight="bold", loc="left", color=INK, pad=10)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True); ax.set_ylim(0, 95)
axes[0].set_ylabel("median % of tract population", fontsize=10)
axes[0].legend(frameon=False, fontsize=10, ncol=3, loc="upper center")
fig.suptitle('"Low income" is not one population — and the courts followed only one of them',
             fontsize=15, fontweight="bold", x=.01, ha="left", y=.99, color=INK)
fig.text(.01, .905, "Median race/ethnicity share by income quartile. ACS race and Hispanic "
         "origin are separate measures, so shares do not sum to 100%.",
         fontsize=10, color=MUTED, ha="left")
plt.tight_layout(rect=[0, .035, 1, .87]); tag(fig)
plt.savefig(OUT / "04_race_by_quartile.png", dpi=220, bbox_inches="tight")
plt.close()
print("regenerated 01, 02, 04")
