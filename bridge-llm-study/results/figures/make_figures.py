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
NONE_GRAY = "#a3a29c"
WRITERS = {"claude": "Claude", "gemini": "Gemini"}
VARIATIONS = {2: "false edge case", 3: "fabricated validation", 5: "false guarantee"}
CONDITION_COLORS = {"No comments": NONE_GRAY, "Original comments": BLUE, "Fake V2": AQUA, "Fake V3": ORANGE,
                    "Fake V5": "#6250d6"}
WRITER_STYLE = {"claude": ("#e87ba4", "o"), "gemini": ("#008300", "s")}
RAMP = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#86b6ef", "#2a78d6", "#0d366b"])
DIVERGING = LinearSegmentedColormap.from_list("red-blue", ["#b52f2f", "#e34948", "#f0efec", "#2a78d6", "#0d366b"])

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


def diagnosed_per_attack(data):
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.6), constrained_layout=True)
    for ax, (track, track_name) in zip(axes, TRACKS.items()):
        cells = [[counts(data[a, track, m], "diagnosed")[0] for a in ATTACKS] for m in MODELS]
        ax.imshow(cells, cmap=RAMP, vmin=0, vmax=100, aspect="auto")
        for i, row in enumerate(cells):
            for j, value in enumerate(row):
                ax.text(j, i, value, ha="center", va="center", fontsize=8, color="white" if value > 55 else INK)
        ax.set_xticks(range(len(ATTACKS)), ["\n".join(ATTACK_NAMES[a].rsplit(" ", 1)) for a in ATTACKS], fontsize=7)
        ax.set_yticks(range(len(MODELS)), [NAMES[m] for m in MODELS] if ax is axes[0] else [""] * len(MODELS),
                      fontsize=7)
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(track_name, fontsize=8.5)
    fig.savefig(HERE / "diagnosed-per-attack.pdf")
    plt.close(fig)


def diagnosed(rows):
    return counts(rows, "diagnosed")[0]


def original_comments():
    graded = RESULTS / "archive" / "source-with-comments" / "graded" / "adjudicated"
    return {(a, m): diagnosed(json.loads((graded / f"{a}-source-{m}.json").read_text()))
            for a in ATTACKS for m in MODELS}


def fake_comments():
    graded = RESULTS / "fake-comments" / "graded" / "adjudicated"
    return {(a, w, v, m): diagnosed(json.loads((graded / f"{a}-{w}-var{v}-{m}.json").read_text()))
            for a in ATTACKS for w in WRITERS for v in VARIATIONS for m in MODELS}


def conditions(data):
    """Detected (of 100) per condition, attack and model."""
    original, fake = original_comments(), fake_comments()
    out = {"No comments": {(a, m): diagnosed(data[a, "source", m]) for a in ATTACKS for m in MODELS},
           "Original comments": original}
    for v in VARIATIONS:
        out[f"Fake V{v}"] = {(a, m): sum(fake[a, w, v, m] for w in WRITERS) for a in ATTACKS for m in MODELS}
    return out


def comments_vs_none(data):
    models = MODELS
    original = original_comments()
    none = {(a, m): diagnosed(data[a, "source", m]) for a in ATTACKS for m in models}

    fig = plt.figure(figsize=(7, 2.9), constrained_layout=True)
    grid = fig.add_gridspec(1, 3, width_ratios=[1.4, 1, 1.35])
    width = 0.38

    def bars(ax, labels, pairs, total, title):
        for i, (n, o) in enumerate(pairs):
            ax.bar(i - width / 2, 100 * n / total, width * 0.92, color=NONE_GRAY, label="No comments" if i == 0 else None)
            ax.bar(i + width / 2, 100 * o / total, width * 0.92, color=BLUE, label="Original comments" if i == 0 else None)
        ax.set_xticks(range(len(labels)), labels, fontsize=7, rotation=30 if len(labels) > 4 else 0,
                      ha="right" if len(labels) > 4 else "center", rotation_mode="anchor")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.set_title(title, fontsize=8.5)

    ax = fig.add_subplot(grid[0])
    bars(ax, [tick(m) for m in models],
         [(sum(none[a, m] for a in ATTACKS), sum(original[a, m] for a in ATTACKS)) for m in models],
         400, "(a) Per model")
    ax.set_ylabel("% named the planted bug")
    ax = fig.add_subplot(grid[1])
    bars(ax, [ATTACK_NAMES[a].split()[0] for a in ATTACKS],
         [(sum(none[a, m] for m in models), sum(original[a, m] for m in models)) for a in ATTACKS],
         600, "(b) Per attack")

    ax = fig.add_subplot(grid[2])
    change = [[original[a, m] - none[a, m] for a in ATTACKS] for m in models]
    ax.imshow(change, cmap=DIVERGING, vmin=-100, vmax=100, aspect="auto")
    for i, m in enumerate(models):
        for j, a in enumerate(ATTACKS):
            ax.text(j, i, f"{none[a, m]}→{original[a, m]}", ha="center", va="center", fontsize=7,
                    color="white" if abs(change[i][j]) > 60 else INK)
    ax.set_xticks(range(len(ATTACKS)), [ATTACK_NAMES[a].split()[0] for a in ATTACKS], fontsize=7)
    ax.set_yticks(range(len(models)), [tick(m) for m in models], fontsize=7)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("(c) No → original, of 100", fontsize=8.5)

    fig.legend(*fig.axes[0].get_legend_handles_labels(), frameon=False, fontsize=7, ncol=2, loc="outside upper center")
    fig.savefig(HERE / "comments-vs-none.pdf")
    plt.close(fig)


def plain_axes(ax):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)


def fake_overview(data):
    cond = conditions(data)
    fig = plt.figure(figsize=(7, 2.7), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1, 2.4])

    ax = fig.add_subplot(grid[0])
    for i, (name, cells) in enumerate(cond.items()):
        share = 100 * sum(cells.values()) / (100 * len(cells))
        ax.bar(i, share, 0.8, color=CONDITION_COLORS[name], label=name)
        ax.text(i, share + 1.5, f"{share:.0f}%", ha="center", fontsize=7)
    ax.set_xticks(range(len(cond)), ["None", "Original", "V2", "V3", "V5"], fontsize=7)
    ax.set_ylim(0, 100)
    ax.set_ylabel("% named the planted bug")
    ax.set_title("(a) All attacks and models", fontsize=8.5)
    plain_axes(ax)

    ax = fig.add_subplot(grid[1])
    width = 0.8 / len(cond)
    for k, (name, cells) in enumerate(cond.items()):
        for i, a in enumerate(ATTACKS):
            ax.bar(i + (k - 2) * width, 100 * sum(cells[a, m] for m in MODELS) / (100 * len(MODELS)),
                   width * 0.92, color=CONDITION_COLORS[name])
    ax.set_xticks(range(len(ATTACKS)), [ATTACK_NAMES[a] for a in ATTACKS], fontsize=7)
    ax.set_ylim(0, 100)
    ax.set_title("(b) Per attack, all models", fontsize=8.5)
    plain_axes(ax)

    labels = ["No comments", "Original comments"] + [f"Fake V{v}: {d}" for v, d in VARIATIONS.items()]
    handles = fig.axes[0].get_legend_handles_labels()[0]
    fig.legend(handles, labels, frameon=False, fontsize=7, ncol=3, loc="outside upper center")
    fig.savefig(HERE / "fake-comments.pdf")
    plt.close(fig)


def fake_writers():
    fake = fake_comments()
    fig = plt.figure(figsize=(7, 3.0), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.5, 1])

    ax = fig.add_subplot(grid[0])
    rows = [(a, v) for a in ATTACKS for v in VARIATIONS]
    for i, (a, v) in enumerate(rows):
        y = len(rows) - 1 - i
        shares = {w: 100 * sum(fake[a, w, v, m] for m in MODELS) / (50 * len(MODELS)) for w in WRITERS}
        ax.plot(list(shares.values()), [y, y], color=GRID, linewidth=2, zorder=1)
        for w, share in shares.items():
            color, marker = WRITER_STYLE[w]
            ax.scatter(share, y, s=28, color=color, marker=marker, zorder=2, edgecolor="white", linewidth=0.8,
                       label=f"Comment written by {WRITERS[w]}" if i == 0 else None)
    ax.set_yticks(range(len(rows)), [f"{ATTACK_NAMES[a].split()[0]} V{v}" for a, v in reversed(rows)], fontsize=7)
    for k in range(1, len(ATTACKS)):
        ax.axhline(k * len(VARIATIONS) - 0.5, color=GRID, linewidth=0.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% named the planted bug (all models, 300 runs per comment)")
    ax.set_title("(a) Per attack and variation", fontsize=8.5)
    ax.tick_params(length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    ax = fig.add_subplot(grid[1])
    ax.plot([0, 50], [0, 50], color=MUTED, linewidth=0.8, linestyle="--", zorder=1)
    for v in VARIATIONS:
        xs = [fake[a, "claude", v, m] for a in ATTACKS for m in MODELS]
        ys = [fake[a, "gemini", v, m] for a in ATTACKS for m in MODELS]
        ax.scatter(xs, ys, s=18, color=CONDITION_COLORS[f"Fake V{v}"], edgecolor="white", linewidth=0.6,
                   zorder=2, label=f"V{v}")
    ax.set_xlim(-2, 52)
    ax.set_ylim(-2, 52)
    ax.set_aspect("equal")
    ax.set_xlabel("Claude's comment (of 50)")
    ax.set_ylabel("Gemini's comment (of 50)")
    ax.set_title("(b) Each model, attack, variation", fontsize=8.5)
    ax.tick_params(length=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    handles, labels = fig.axes[0].get_legend_handles_labels()
    more, names = ax.get_legend_handles_labels()
    fig.legend(handles + more, labels + [f"V{v}: {VARIATIONS[v]}" for v in VARIATIONS], frameon=False, fontsize=7,
               ncol=3, loc="outside upper center", columnspacing=1.2, handletextpad=0.3)
    fig.savefig(HERE / "fake-comments-writers.pdf")
    plt.close(fig)


def fake_table(data):
    cond = conditions(data)
    names = list(cond)
    lines = [r"\begin{tabular}{l" + "r" * len(names) + "}", r"\toprule",
             "Model & " + " & ".join(n.replace("Fake ", "") for n in names) + r" \\", r"\midrule"]
    md = ["# Named the planted bug, per model and condition (adjudicated)", "",
          "Source code, 400 runs per model and condition (4 attacks x 100); fake conditions are 50 runs on "
          "Claude's comment plus 50 on Gemini's, per attack.", "",
          "| Model | " + " | ".join(names) + " |", "|" + "---|" * (len(names) + 1)]
    for m in MODELS:
        cells = [str(sum(cond[n][a, m] for a in ATTACKS)) for n in names]
        lines.append(f"{NAMES[m]} & " + " & ".join(cells) + r" \\")
        md.append(f"| {NAMES[m]} | " + " | ".join(f"{c} / 400" for c in cells) + " |")
    totals = [sum(cond[n].values()) for n in names]
    lines += [r"\midrule", "All models (of 2,400) & " + " & ".join(f"{t:,} ({100 * t / 2400:.0f}\\%)" for t in totals)
              + r" \\", r"\bottomrule", r"\end{tabular}"]
    md.append("| All models | " + " | ".join(f"{t:,} / 2,400 ({100 * t / 2400:.0f}%)" for t in totals) + " |")
    (TABLES / "fake-comments.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "fake-comments.md").write_text("\n".join(md) + "\n")


def summary_table(data):
    lines = [r"\begin{tabular}{llrrrrrrr}", r"\toprule",
             r" & & \multicolumn{3}{c}{Flagged} & \multicolumn{3}{c}{Diagnosed} & Blocked \\",
             r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
             r"Track & Model & Recall & F1 & Acc. & Recall & F1 & Acc. & flagged \\", r"\midrule"]
    md_head = ["Track", "Model", "Flagged recall", "Flagged F1", "Flagged accuracy",
               "Diagnosed recall", "Diagnosed F1", "Diagnosed accuracy", "Blocked flagged"]
    md = ["# Detection, all four attacks pooled (adjudicated)", "",
          "400 vulnerable and 400 secure or benign runs per row; blocked attempts (400) are counted "
          "separately. Per-attack rows: `metrics-source.md`, `metrics-trace.md`.", "",
          "| " + " | ".join(md_head) + " |", "|" + "---|" * len(md_head)]
    for t, (track, track_name) in enumerate(TRACKS.items()):
        for i, model in enumerate(MODELS):
            cells = [track_name if i == 0 else "", NAMES[model]]
            for level in ("flagged", "diagnosed"):
                c = pooled(data, track, model, level)
                _, recall, f1, accuracy = scores(*c[:4])
                cells += [f"{recall:.2f}", f"{f1:.2f}", f"{accuracy:.2f}"]
            cells.append(str(c[4]) if track == "trace" else "--")
            lines.append(" & ".join(cells) + r" \\")
            md.append("| " + " | ".join([track_name] + cells[1:]) + " |")
        lines.append(r"\midrule" if t == 0 else r"\bottomrule")
    lines.append(r"\end{tabular}")
    (TABLES / "detection-metrics.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "detection-metrics.md").write_text("\n".join(md) + "\n")


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
    diagnosed_per_attack(data)
    comments_vs_none(data)
    fake_overview(data)
    fake_writers()
    fake_table(data)
    summary_table(data)
    for track in TRACKS:
        metrics_table(data, track)
    print(f"wrote figures to {HERE} and tables to {TABLES}")
