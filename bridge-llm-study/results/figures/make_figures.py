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


ATTACK_ROWS = [
    ("A1 mint confusion", "Cashio (2022)", "lock", "deposited mint equals the approved collateral mint",
     "deposits 500,000 of a worthless self-made token and receives 500,000 real wrapped tokens", "WrongMint"),
    ("A2 sysvar spoof", "Wormhole (2022)", "release", "instructions sysvar is the real sysvar address",
     "passes a fake instruction list with a dummy Ed25519 check; wrapped tokens are minted with no relay signature",
     "UnsupportedSysvar"),
    ("B1 missing signer", "Signer authorization (Solana audit class)", "require_admin",
     "admin account signed (key match kept)",
     "calls set_admin with the real admin's key but no signature and makes itself admin", "MissingSignature"),
    ("B2 arbitrary CPI", "Arbitrary CPI (Solana audit class)", "redeem", "token program is the real SPL Token program",
     "passes its own program as the token program; redeeming one wrapped token drains the vault", "WrongTokenProgram"),
]


def tex(text):
    return text.replace("_", r"\_")


def attacks_table():
    head = ["Attack", "Real-world basis", "Function", "Check removed", "Exploit (attacker)", "Secure bridge"]
    lines = [r"\begin{tabular}{lp{2.4cm}lp{3cm}p{4.2cm}l}", r"\toprule", " & ".join(head) + r" \\", r"\midrule"]
    md = ["# The four planted attacks", "",
          "Each variant removes this check from the secure bridge (B2 also forwards the call to the caller's program). "
          "Real-world basis: Cashio and Wormhole "
          "are incidents; B1 and B2 are classes from the Ackee Blockchain list of common Solana attack vectors "
          "(https://github.com/Ackee-Blockchain/solana-common-attack-vectors).", "",
          "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for attack, basis, function, check, exploit, error in ATTACK_ROWS:
        lines.append(" & ".join([attack, basis, rf"\texttt{{{tex(function)}}}", check, tex(exploit),
                                 rf"\texttt{{{error}}}"]) + r" \\")
        md.append(f"| {attack} | {basis} | `{function}` | {check} | {exploit} | `{error}` |")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TABLES / "attacks.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "attacks.md").write_text("\n".join(md) + "\n")


DETECTION = HERE.parent.parent / "detection"
MAIN_POOLS = ["judging", "judging-gemma", "judging-deepseek-thinking"]
WITH_COMMENTS_POOLS = ["judging-archive/source-with-comments/" + d for d in MAIN_POOLS]
# experiment, input given to the model, runs per model and input, inputs per attack, judging folders, cell suffix
EXPERIMENTS = [
    ("Source code, no comments", "secure and vulnerable program", 100, 2, MAIN_POOLS, "-source"),
    ("Source code, original comments", "same, with the code's comments", 100, 2, WITH_COMMENTS_POOLS, "-source"),
    ("Transaction record", "attack, normal and blocked-attempt session", 100, 3, MAIN_POOLS, "-trace"),
]


def graders_agree(pools, suffix):
    def labels(path):
        return {row["id"]: row["label"] for row in map(json.loads, path.open()) if row}

    pairs = []
    for pool in pools:
        for answers in sorted((DETECTION / pool).glob(f"*{suffix}*/answers.jsonl")):
            claude = labels(answers.parent / "labels-claude-opus-5-5.jsonl")
            gemini = labels(answers.parent / "labels-gemini-3.8-flash.jsonl")
            pairs += [(claude[i], gemini[i]) for i in claude]
    final = sum(row["label"] == "correct" for pool in pools
                for path in (DETECTION / pool).glob(f"*{suffix}/labels-adjudicated.jsonl")
                for row in map(json.loads, path.open()) if row)
    claude, gemini = (sum(x[k] == "correct" for x in pairs) for k in (0, 1))
    return len(pairs), claude, gemini, sum(a == b for a, b in pairs), final


def setup_table():
    head = ["Experiment", "Input", "Runs per model and input", "Answers", "Graded", "Claude: correct",
            "Gemini: correct", "Graders agree", "Decided by author", "Final: correct"]
    lines = [r"\begin{tabular}{p{3.4cm}p{3.6cm}rrrrrrrr}", r"\toprule",
             r"Experiment & Input & Runs & Answers & Graded & Claude & Gemini & Agree & Decided & Final \\",
             r"\midrule"]
    md = ["# Runs and grading", "",
          "Six model configurations, all through DeepInfra at temperature 0 with at most 16,000 output tokens. "
          "Answers = 6 models x 4 attacks x inputs per attack x runs. Graded = answers on vulnerable input "
          "(the attack session for transactions), each labelled blind by Claude Opus 5.5 and Gemini 3.8 Flash; "
          "the author decided every disagreement. Claude, Gemini and Final count the answers labelled as "
          "naming the planted bug.", "",
          "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    totals = [0, 0, 0]
    for name, given, runs, inputs, pools, suffix in EXPERIMENTS:
        answers = len(MODELS) * len(ATTACKS) * inputs * runs
        n, claude, gemini, agree, final = graders_agree(pools, suffix)
        totals[0] += answers
        totals[1] += n
        totals[2] += agree
        cells = [f"{answers:,}", f"{n:,}", f"{claude:,}", f"{gemini:,}", f"{agree:,} ({100 * agree / n:.2f}\\%)",
                 str(n - agree), f"{final:,}"]
        lines.append(" & ".join([name, given, str(runs)] + cells) + r" \\")
        md.append("| " + " | ".join([name, given, str(runs)] + [c.replace("\\%", "%") for c in cells]) + " |")
    agree = f"{totals[2]:,} ({100 * totals[2] / totals[1]:.2f}\\%)"
    lines += [r"\midrule", f"Total & & & {totals[0]:,} & {totals[1]:,} & & & {agree} & {totals[1] - totals[2]} & \\\\",
              r"\bottomrule", r"\end{tabular}"]
    md.append(f"| Total | | | {totals[0]:,} | {totals[1]:,} | | | {agree.replace(chr(92), '')} | {totals[1] - totals[2]} | |")
    (TABLES / "setup.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "setup.md").write_text("\n".join(md) + "\n")


def comments_table(data):
    original = original_comments()
    none = {(a, m): diagnosed(data[a, "source", m]) for a in ATTACKS for m in MODELS}
    lines = [r"\begin{tabular}{lrr}", r"\toprule", r"Model & No comments & Original comments \\", r"\midrule"]
    md = ["# Source code: no comments vs. original comments (adjudicated)", "",
          "Answers that named the planted bug, out of 400 per model (100 per attack).", "",
          "| Model | No comments | Original comments |", "|---|---|---|"]
    for m in MODELS:
        cells = [NAMES[m], str(sum(none[a, m] for a in ATTACKS)), str(sum(original[a, m] for a in ATTACKS))]
        lines.append(" & ".join(cells) + r" \\")
        md.append("| " + " | ".join(cells) + " |")
    cells = ["All models (of 2,400)", f"{sum(none.values()):,}", f"{sum(original.values()):,}"]
    lines += [r"\midrule", " & ".join(cells) + r" \\", r"\bottomrule", r"\end{tabular}"]
    md.append("| " + " | ".join(cells) + " |")
    (TABLES / "comments.tex").write_text("\n".join(lines) + "\n")
    (TABLES / "comments.md").write_text("\n".join(md) + "\n")


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
    attacks_table()
    setup_table()
    comments_table(data)
    summary_table(data)
    for track in TRACKS:
        metrics_table(data, track)
    print(f"wrote figures to {HERE} and tables to {TABLES}")
