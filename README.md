# LLMs as Validators for Cross-Chain Bridges

Artifact for the paper *LLMs as Validators for Cross-Chain Bridges: Evaluating Source-Level and
Transaction-Level Attack Detection on Solana*.

We build a lock-and-mint bridge as a native Rust Solana program, plant four known validation bugs
(one per variant), exploit each one on a local validator, and ask open-weight LLMs whether they
can find the attack from the program's source code (auditor) or from the on-chain record of one
session (monitor).

All model answers, grader labels, adjudicated labels, tables and figures are committed. Nothing
needs to be re-run to check the paper's numbers.

## Where to start

| What | Where |
|---|---|
| The four planted bugs | `bridge-llm-study/programs/variants/*/README.md` (one diff each) |
| Exploit runs, on the buggy variant and on the secure bridge | `bridge-llm-study/traces/<attack>/{vulnerable,baseline}.json` |
| What a model was shown | prompts in `detection/source_task.py` and `detection/trace_task.py`; trace cleaning in `detection/lib/gather.py` |
| How answers were graded | `detection/judge_prompt.md` (grader prompt and per-attack rubric), `detection/GRADING.md` (plain English) |
| Tables and figures | `bridge-llm-study/results/` |
| One attack in depth | `bridge-llm-study/docs/attack-*.md` |

## Attack names

| Paper | Repository folder | Attack | Real-world basis |
|---|---|---|---|
| A1 | `v1-mint-confusion` | collateral mint not checked in `lock` | Cashio (2022) |
| A2 | `v2-sysvar-spoof` | instructions sysvar address not checked in `release` | Wormhole (2022) |
| B1 | `v5-missing-signer` | admin key compared but signature not required | Solana audit class |
| B2 | `v6-arbitrary-cpi` | token program not pinned in `redeem` | Solana audit class |

## Experiments and data

Six model configurations (five open-weight models, DeepSeek-V3.2 with thinking off and on), all via
DeepInfra at temperature 0 with at most 16,000 output tokens.

| Experiment | Answers | Graded | Model answers | Grader labels |
|---|---|---|---|---|
| Source code, no comments | 4,800 | 2,400 | `detection/results/<attack>-source-<model>.json` | `detection/judging*/<attack>-source/` |
| Source code, original comments | 4,800 | 2,400 | `detection/results/archive/source-with-comments/` | `detection/judging-archive/source-with-comments/` |
| Transaction record | 7,200 | 2,400 | `detection/results/<attack>-trace-<model>.json` | `detection/judging*/<attack>-trace/` |
| **Total** | **16,800** | **7,200** | | |

Only answers on vulnerable input are graded for diagnosis; answers on the secure program, a benign
session or a blocked attempt only need the yes/no. `detection/judging/` holds gpt-oss, DeepSeek,
Llama and Nemotron; `judging-gemma/` and `judging-deepseek-thinking/` hold the other two.

Each grading folder has `answers.jsonl` (shuffled, model names removed), `labels-claude-opus-5-5.jsonl`,
`labels-gemini-3.8-flash.jsonl` and `labels-adjudicated.jsonl`. The id-to-answer keys are in
`keys/`, which the graders never saw. Merged labels per model are in `detection/results/graded/`.
How many answers each grader marked as naming the bug, and how often the two agreed, is in
`results/tables/setup.md`.

Answers that hit the 16,000-token limit were asked again; the cut-off originals are in
`detection/results/archive/cutoffs*/`.

## Repository layout

```
bridge-llm-study/
  programs/bridge-secure/     secure bridge (native Rust Solana program)
  programs/variants/v*-...    the four buggy copies, each with a README of its one-check diff
  programs/with-comments/     the same programs with their original comments (comments experiment)
  mock-oracle/                price oracle used by the bridge
  blob-writer/                helper program for the A2 fake-sysvar account
  attacker-program/           malicious token program used by B2
  client/                     TypeScript: honest sessions and the four exploits
  scripts/run-attack-v*.sh    one script per attack, from fresh validator to traces
  traces/                     recorded traces (benign, vulnerable, baseline) per attack
  detection/                  Python: model runs, blind grading and metrics
  docs/attack-*.md            full write-up and results for each attack
  results/                    tables, figures and summaries used in the paper
```

In traces, `baseline.json` is the exploit attempted against the secure bridge, which rejects it
(the "blocked attempt" in the paper).

## Setup

### 1. Tools

| Tool | Version | Install |
|---|---|---|
| Rust | stable | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Solana CLI (Agave) | tested 4.3.0 | `sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"` |
| Node.js | 18+ | <https://nodejs.org> |
| Python | 3.9+ | <https://python.org> |

The Solana installer provides `solana`, `solana-test-validator` and `cargo build-sbf`.

### 2. Solana wallet

The scripts pay for deploys with your default wallet (`~/.config/solana/id.json`), funded by a
local airdrop:

```bash
solana-keygen new --no-bip39-passphrase    # skip if you already have one
```

### 3. Install dependencies

```bash
cd bridge-llm-study
(cd client && npm install)

cd detection
python3 -m venv .venv
.venv/bin/pip install openai httpx python-dotenv matplotlib
```

### 4. API keys

Only needed to ask the models or grade again.

```bash
cp .env.example .env                       # in bridge-llm-study/detection/
```

Then edit `detection/.env`:

```
DEEPINFRA_API_KEY=...    # needed to run the models        (deepinfra.com > Dashboard > API keys)
GEMINI_API_KEY=...       # needed only to grade with Gemini (aistudio.google.com > Get API key)
```

`.env` is gitignored. You don't need `client/.env`, because the scripts set the program ids
themselves.

## How to run

All raw answers, labels and results are already committed. To check the numbers only, run step 5.
Every other step rebuilds part of the data and needs the tools above.

### 1. Build the programs (from `bridge-llm-study/`)

```bash
for d in programs/bridge-secure programs/variants/v{1,2,5,6}-* mock-oracle blob-writer attacker-program; do
  (cd "$d" && cargo build-sbf)
done
```

### 2. Run the attacks and record traces (from `bridge-llm-study/`)

```bash
bash scripts/run-attack-v1.sh     # A1
bash scripts/run-attack-v2.sh     # A2
bash scripts/run-attack-v5.sh     # B1
bash scripts/run-attack-v6.sh     # B2
```

Each script:

1. kills any running `solana-test-validator` and starts a fresh one;
2. deploys a new copy of the program for each run;
3. runs a benign session, the exploit on the buggy variant, and the same exploit on the secure
   bridge;
4. writes `traces/<attack>/{benign,vulnerable,baseline}.json`.

### 3. Ask the models (from `bridge-llm-study/detection/`)

```bash
.venv/bin/python run_study.py --attack v1-mint-confusion --models all --runs 100 --tracks source,trace
```

| Option | Values |
|---|---|
| `--attack` | `v1-mint-confusion`, `v2-sysvar-spoof`, `v5-missing-signer`, `v6-arbitrary-cpi` |
| `--models` | `gpt`, `deepseek`, `llama`, `nemotron`, `gemma`, `deepseek-think` (DeepSeek-V3.2 with thinking on), comma list or `all` |
| `--tracks` | `source`, `trace` (comma list) |
| `--runs` | runs per case (paper: 100) |
| `--workers` | parallel requests per case (default 1) |

Run it once per attack. Results go to `results/<attack>-<track>-<model>.json`. Runs save
checkpoints, so if a run stops, the same command resumes it. To re-ask answers that hit the
16K-token limit:

```bash
.venv/bin/python rerun_cutoffs.py --attack v1-mint-confusion --track source --model nemotron
```

The original-comments run uses the same script on the commented programs:

```bash
PROGRAMS=../programs/with-comments RESULTS=results/archive/source-with-comments \
  .venv/bin/python run_study.py --attack v1-mint-confusion --models all --tracks source --runs 100
```

### 4. Grade (from `bridge-llm-study/detection/`)

```bash
.venv/bin/python judge.py build                 # blind, shuffled pools for source and trace
PROVIDER=gemini MODEL=gemini-3.8-flash .venv/bin/python judge.py grade
```

Gemma and DeepSeek with thinking have their own pools: prefix each `judge.py` command with
`JUDGING=judging-gemma` or `JUDGING=judging-deepseek-thinking`. For the original-comments answers,
add `RESULTS=results/archive/source-with-comments`, point `JUDGING` at the matching folder in
`judging-archive/source-with-comments/` and build with `judge.py build source`.

Gemini writes `<pool>/<cell>/labels-gemini-3.8-flash.jsonl`. Answers it could not parse go to
`errors-*.jsonl`; run `grade` again to retry them. The Claude labels
(`labels-claude-opus-5-5.jsonl`) and the adjudicated labels (`labels-adjudicated.jsonl`) are
committed. Then merge and score:

```bash
for g in claude-opus-5-5 gemini-3.8-flash adjudicated; do
  .venv/bin/python judge.py merge $g            # -> results/graded/<g>/
  .venv/bin/python metrics.py $g                # -> results/metrics-<g>.md
done
```

### 5. Rebuild the paper's tables and figures (from `bridge-llm-study/`)

```bash
detection/.venv/bin/python results/figures/make_figures.py
```

This reads the committed adjudicated labels and rewrites `results/tables/*` and
`results/figures/*.pdf`. No API key or validator is needed.

## Safety

Everything runs on a local `solana-test-validator`. Nothing touches a public network, and the
exploits only work against the deliberately buggy variants in this repository.
