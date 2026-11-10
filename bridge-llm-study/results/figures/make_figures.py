"""
Figures and LaTeX tables for the paper, from the adjudicated labels.

  detection/.venv/bin/python results/figures/make_figures.py

Writes results/figures/*.pdf and results/tables/*.tex.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "detection"))
from metrics import ATTACK_NAMES, ATTACKS, MODELS, NAMES, RESULTS, add, counts, scores  # noqa: E402

TABLES = HERE.parent / "tables"
TRACKS = {"source": "Source code", "trace": "Transaction information"}
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
RAMP = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#86b6ef", "#2a78d6", "#0d366b"])

plt.rcParams.update({
    "pdf.fonttype": 42,
    "font.family": "sans-serif",
    "font.size": 8,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
})


def load():
    graded = RESULTS / "graded" / "adjudicated"
    return {
        (attack, track, model): json.loads((graded / f"{attack}-{track}-{model}.json").read_text())
        for attack in ATTACKS for track in TRACKS for model in MODELS
    }


def pooled(data, track, model, level):
    total = [0] * 5
    for attack in ATTACKS:
        total = add(total, counts(data[attack, track, model], level))
    return total


def short(model):
    return NAMES[model].replace(" (thinking)", "\n(thinking)")


def tick(model):
    return NAMES[model].split("-")[0].replace("gpt", "gpt-oss") + ("\n(thinking)" if "thinking" in model else "")


def confusion_matrices(data):
    fig, axes = plt.subplots(2, len(MODELS), figsize=(7, 2.9), constrained_layout=True)
    for row, (track, track_name) in enumerate(TRACKS.items()):
        for col, model in enumerate(MODELS):
            tp, fn, fp, tn, _ = pooled(data, track, model, "diagnosed")
            cells = [[tp, fn], [fp, tn]]
            ax = axes[row, col]
            ax.imshow(cells, cmap=RAMP, vmin=0, vmax=400)
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, cells[i][j], ha="center", va="center", fontsize=8,
                            color="white" if cells[i][j] > 220 else INK)
            ax.set_xticks([0, 1], ["Yes", "No"] if row else ["", ""])
            ax.set_yticks([0, 1], ["Vuln.", "Secure" if track == "source" else "Benign"] if col == 0 else ["", ""])
            ax.tick_params(length=0)
            for spine in ax.spines.values():
                spine.set_visible(False)
            if row == 0:
                ax.set_title(short(model), fontsize=7.5)
        axes[row, 0].set_ylabel(track_name, fontsize=8)
    fig.supxlabel("Model's answer", fontsize=8)
    fig.savefig(HERE / "confusion-matrices.pdf")
    plt.close(fig)


def flagged_vs_diagnosed(data):
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.5), sharey=True, constrained_layout=True)
    bars = [("Said vulnerable", BLUE), ("Named the planted bug", ORANGE), ("False alarm", AQUA)]
    width = 0.26
    for ax, (track, track_name) in zip(axes, TRACKS.items()):
        for i, model in enumerate(MODELS):
            flag_tp, _, fp, _, _ = pooled(data, track, model, "flagged")
            diag_tp = pooled(data, track, model, "diagnosed")[0]
            for k, value in enumerate([flag_tp, diag_tp, fp]):
                ax.bar(i + (k - 1) * width, value / 4, width * 0.92, color=bars[k][1],
                       label=bars[k][0] if i == 0 else None)
        ax.set_title(track_name, fontsize=8.5)
        ax.set_xticks(range(len(MODELS)), [tick(m) for m in MODELS], fontsize=7)
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("% of 400 runs")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=7, ncol=3, loc="outside upper center")
    fig.savefig(HERE / "flagged-vs-diagnosed.pdf")
    plt.close(fig)


def metrics_table(data, track):
    blocked = track == "trace"
    cols = "ll" + "rrr" * 2 + ("r" if blocked else "")
    head = (r" & & \multicolumn{3}{c}{Flagged} & \multicolumn{3}{c}{Diagnosed}"
            + (r" & Blocked \\" if blocked else r" \\"))
    sub = r"Attack & Model & Recall & F1 & Acc. & Recall & F1 & Acc." + (r" & flagged \\" if blocked else r" \\")
    lines = [r"\begin{tabular}{" + cols + "}", r"\toprule", head,
             r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}", sub, r"\midrule"]
    md_head = ["Attack", "Model", "Flagged recall", "Flagged F1", "Flagged accuracy",
               "Diagnosed recall", "Diagnosed F1", "Diagnosed accuracy"] + (["Blocked flagged"] if blocked else [])
    md = [f"# {TRACKS[track]}: recall, F1, accuracy (adjudicated)", "",
          "| " + " | ".join(md_head) + " |", "|" + "---|" * len(md_head)]
    groups = [(ATTACK_NAMES[a], {m: data[a, track, m] for m in MODELS}) for a in ATTACKS]
    groups.append(("All pooled", None))
    for g, (name, rows) in enumerate(groups):
        for i, model in enumerate(MODELS):
            cells = [name if i == 0 else "", NAMES[model]]
            for level in ("flagged", "diagnosed"):
                c = counts(rows[model], level) if rows else pooled(data, track, model, level)
                _, recall, f1, accuracy = scores(*c[:4])
                cells += [f"{recall:.2f}", f"{f1:.2f}", f"{accuracy:.2f}"]
            if blocked:
                cells.append(str(c[4]))
            lines.append(" & ".join(cells) + r" \\")
            md.append("| " + " | ".join([name] + cells[1:]) + " |")
        lines.append(r"\midrule" if g < len(groups) - 1 else r"\bottomrule")
    lines.append(r"\end{tabular}")
    (TABLES / f"metrics-{track}.tex").write_text("\n".join(lines) + "\n")
    (TABLES / f"metrics-{track}.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    TABLES.mkdir(exist_ok=True)
    data = load()
    confusion_matrices(data)
    flagged_vs_diagnosed(data)
    for track in TRACKS:
        metrics_table(data, track)
    print(f"wrote figures to {HERE} and tables to {TABLES}")
